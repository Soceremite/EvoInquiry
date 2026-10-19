"""Import explicit Codex JSONL exports into the existing, compact meta event log.

Reads only the project-relative trace named by the caller. Raw commands, prompts,
tool output, credentials and model responses are never copied into the normalized
log. Source-line hashes bind observations without making earlier events stale
when an append-only trace grows. This importer is not an installed session hook.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

try:
    from .registry_common import (RegistryError, atomic_write, configure_utf8_output,
                                  digest, file_lock, identifier, local_path, now)
    from .state_paths import resolve_state_root, state_writer
except ImportError:
    from registry_common import (RegistryError, atomic_write, configure_utf8_output,
                                 digest, file_lock, identifier, local_path, now)
    from state_paths import resolve_state_root, state_writer


_SKILL_PATH = re.compile(r'(?:^|[\s\"\x27])([^\s\"\x27]*skills/(skills-codex/)?([a-z0-9-]+)/SKILL\.md)')
_SECRET = re.compile(r'(?:sk[-_][A-Za-z0-9_-]{10,}|Bearer\s+\S+|https?://[^\s/]+:[^\s/@]+@)', re.I)
_FIELDS = {'event', 'session', 'workflow_run_id', 'phase', 'action_id', 'skill',
           'tool', 'status', 'exit_code', 'usage', 'source', 'input_sha256', 'surface'}
_EVENTS = {'session_start', 'session_end', 'tool_start', 'tool_result', 'skill_reference', 'tool_failure'}


def _read_log(path):
    raw = path.read_bytes() if path.exists() else b''
    if raw and not raw.endswith(b'\n'):
        raise RegistryError('Interrupted meta event log; preserve and reconcile it before writing')
    try:
        records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    except ValueError:
        raise RegistryError('Invalid meta event log; existing evidence was not changed') from None
    if any(not isinstance(record, dict) for record in records):
        raise RegistryError('Meta event records must be objects')
    return raw, records


def _validate_event(payload):
    if not isinstance(payload, dict) or set(payload) - _FIELDS:
        raise RegistryError('Event contains unsupported fields; raw payloads are not logged')
    if payload.get('event') not in _EVENTS:
        raise RegistryError('Unknown normalized event')
    identifier(payload.get('session'))
    for key in ('workflow_run_id', 'phase', 'action_id', 'tool'):
        if key in payload:
            identifier(payload[key])
    for key in ('status', 'surface'):
        if key in payload and (not isinstance(payload[key], str) or not re.fullmatch(r'[a-z_-]{1,40}', payload[key])):
            raise RegistryError(f'Invalid event {key}')
    if 'skill' in payload and not re.fullmatch(r'(?:evo-inquiry:)?[a-z0-9-]{1,80}', payload['skill']):
        raise RegistryError('Invalid skill name')
    if 'exit_code' in payload and (isinstance(payload['exit_code'], bool) or not isinstance(payload['exit_code'], int)):
        raise RegistryError('Exit code must be an integer')
    if 'input_sha256' in payload and not re.fullmatch(r'[a-f0-9]{64}', payload['input_sha256']):
        raise RegistryError('Invalid command fingerprint')
    if 'usage' in payload:
        usage = payload['usage']
        if (not isinstance(usage, dict) or set(usage) - {'input_tokens', 'cached_input_tokens', 'output_tokens'}
                or any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in usage.values())):
            raise RegistryError('Invalid token usage observation')
    if 'source' in payload:
        source = payload['source']
        if (not isinstance(source, dict) or set(source) != {'path', 'line', 'sha256'}
                or not isinstance(source['path'], str) or not source['path']
                or isinstance(source['line'], bool) or not isinstance(source['line'], int) or source['line'] < 1
                or not re.fullmatch(r'[a-f0-9]{64}', source['sha256'])):
            raise RegistryError('Invalid source-line identity')
    if _SECRET.search(json.dumps(payload)):
        raise RegistryError('Credential-like data cannot enter the normalized log')


def append_event(root, payload, *, event_id=None):
    """Append an allowlisted observation idempotently, preserving legacy meta events.

    Only explicit fields are accepted. ``event_id`` binds one immutable observation;
    conflicting reuse fails. Source identity must verify when supplied. This records
    execution evidence, never phase acceptance or whether a scientific claim holds.
    """
    _validate_event(payload)
    if 'source' in payload:
        _verify_source(root, payload['source'])
    event_id = event_id or digest(payload)
    identifier(event_id)
    if _SECRET.search(event_id):
        raise RegistryError('Credential-like event IDs are not logged')
    with state_writer(root) as state:
        log = local_path(root, (state / 'meta/events.jsonl').relative_to(Path(root).resolve()).as_posix())
        with file_lock(log.with_suffix('.lock')):
            raw, records = _read_log(log)
            for record in records:
                if record.get('event_id') == event_id:
                    if {key: value for key, value in record.items()
                            if key not in ('event_id', 'schema_version', 'ts')} != payload:
                        raise RegistryError('Event ID already records a different observation')
                    return {'appended': False, 'event_id': event_id}
            record = {'schema_version': 1, 'event_id': event_id, 'ts': now(), **payload}
            atomic_write(log, raw + json.dumps(record, ensure_ascii=False, sort_keys=True,
                                              allow_nan=False).encode() + b'\n')
    return {'appended': True, 'event_id': event_id}


def _verify_source(root, source):
    path = local_path(root, source['path'])
    try:
        line = path.read_bytes().splitlines()[source['line'] - 1]
    except (OSError, IndexError) as error:
        raise RegistryError('Missing source event line') from error
    if digest(line) != source['sha256']:
        raise RegistryError('Source event line changed')


def _check_import_history(records, lines, source, session):
    for row in records:
        reference = row.get('source', {})
        if (not row.get('event_id') or row.get('session') != session
                or not isinstance(reference, dict) or reference.get('path') != source):
            continue
        index = reference.get('line')
        if (isinstance(index, bool) or not isinstance(index, int) or index < 1
                or index > len(lines) or digest(lines[index - 1]) != reference.get('sha256')):
            raise RegistryError('Previously imported source changed; preserve the original trace')


def _append_import(root, raw, source, session, events):
    """Commit one validated import atomically, reading the source/log in batches.

    Holding the existing namespace and event locks keeps cooperating importers
    idempotent. Readers see either the previous log or the complete import; a
    failed replacement retains the previous observations. An actively growing
    source is allowed when the captured byte prefix remains unchanged.
    """
    if not events:
        log = resolve_state_root(root, 'read') / 'meta/events.jsonl'
        _, existing = _read_log(log)
        _check_import_history(existing, raw.splitlines(), source, session)
        return 0
    with state_writer(root) as state:
        log = local_path(root, (state / 'meta/events.jsonl').relative_to(Path(root).resolve()).as_posix())
        with file_lock(log.with_suffix('.lock')):
            current = local_path(root, source).read_bytes()
            if not current.startswith(raw):
                raise RegistryError('Codex source changed during import; preserve the original trace')
            previous, records = _read_log(log)
            _check_import_history(records, current.splitlines(), source, session)
            known = {row.get('event_id'): row for row in records if row.get('event_id')}
            additions = []
            for event_id, payload in events:
                if event_id in known:
                    if {key: value for key, value in known[event_id].items()
                            if key not in ('event_id', 'schema_version', 'ts')} != payload:
                        raise RegistryError('Previously imported source changed; preserve the original trace')
                    continue
                record = {'schema_version': 1, 'event_id': event_id, 'ts': now(), **payload}
                additions.append(json.dumps(record, ensure_ascii=False, sort_keys=True,
                                            allow_nan=False).encode() + b'\n')
                known[event_id] = record
            if additions:
                atomic_write(log, previous + b''.join(additions))
            return len(additions)


def _normalize(event, base):
    kind = event.get('type')
    if kind == 'thread.started':
        yield {**base, 'event': 'session_start'}
    elif kind in ('turn.completed', 'turn.failed'):
        row = {**base, 'event': 'session_end', 'status': 'completed' if kind == 'turn.completed' else 'failed'}
        usage = event.get('usage')
        if isinstance(usage, dict):
            row['usage'] = {key: value for key, value in usage.items()
                            if key in ('input_tokens', 'cached_input_tokens', 'output_tokens')
                            and isinstance(value, int) and not isinstance(value, bool) and value >= 0}
        yield row
    elif kind in ('item.started', 'item.completed'):
        item = event.get('item')
        if not isinstance(item, dict) or item.get('type') not in ('command_execution', 'mcp_tool_call', 'web_search'):
            return
        row = {**base, 'event': 'tool_start' if kind == 'item.started' else 'tool_result', 'tool': item['type']}
        command = item.get('command')
        if isinstance(command, str):
            row['input_sha256'] = digest(command.encode())
        if kind == 'item.completed':
            code = item.get('exit_code')
            if isinstance(code, int) and not isinstance(code, bool):
                row.update(exit_code=code, status='succeeded' if code == 0 else 'failed')
            elif item.get('status') == 'failed':
                row['status'] = 'failed'
            else:
                row['status'] = 'unknown'
            yield row
            if row['status'] == 'failed':
                yield {**row, 'event': 'tool_failure'}
            # A command mentioning a skill path is a reference candidate, not
            # proof of a read, invocation or compliance. Shell text alone cannot
            # establish execution of each subcommand. Cached guidance is unseen.
            if row['status'] == 'succeeded' and isinstance(command, str):
                # Native CLI commands commonly wrap reads in /bin/bash -lc.
                # Keep path mentions observable without pretending to parse or
                # certify what the shell executed. Bare paths are not assigned
                # to the EvoInquiry namespace without a Codex package surface.
                for path, codex, name in sorted(set(_SKILL_PATH.findall(command))):
                    yield {**base, 'event': 'skill_reference',
                           'skill': 'evo-inquiry:' + name if codex else name,
                           'surface': 'codex' if codex else 'unclassified'}
        else:
            yield row


def import_codex(root, source, session, *, workflow_run_id=None):
    """Import a caller-selected project JSONL trace; never scan private Codex history.

    Reimporting an unchanged prefix does not duplicate events. A malformed complete
    JSON line fails before any import; an unfinished final line is left unimported
    and reported. Appended evidence can be imported later. Completed turns, command
    outcomes, cached guidance and unrecognized event types remain distinct facts.
    """
    identifier(session)
    if workflow_run_id is not None:
        identifier(workflow_run_id)
    path = local_path(root, source)
    raw = path.read_bytes()
    complete = raw.splitlines(keepends=True)
    partial = bool(complete and not complete[-1].endswith(b'\n'))
    if partial:
        complete = complete[:-1]
    parsed = []
    for index, line in enumerate(complete, 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError as error:
            raise RegistryError(f'Invalid Codex event JSON at line {index}') from error
        if not isinstance(event, dict):
            raise RegistryError(f'Codex event at line {index} is not an object')
        identity = {'path': str(source), 'line': index, 'sha256': digest(line.rstrip(b'\r\n'))}
        parsed.append((index, event, identity))
    events = []
    for index, event, identity in parsed:
        base = {'session': session, 'source': identity}
        if workflow_run_id is not None:
            base['workflow_run_id'] = workflow_run_id
        for ordinal, normalized in enumerate(_normalize(event, base)):
            _validate_event(normalized)
            events.append((digest({'session': session, 'source': str(source),
                                   'line': index, 'observation': ordinal}), normalized))
    appended = _append_import(root, raw, str(source), session, events)
    endings = [event['type'] for _, event, _ in parsed if event.get('type') in ('turn.completed', 'turn.failed')]
    completion = 'unknown'
    for _, event, _ in parsed:
        if event.get('type') in ('turn.completed', 'turn.failed'):
            completion = event['type'].split('.')[1]
        elif event.get('type') in ('thread.started', 'turn.started', 'item.started', 'item.completed'):
            completion = 'unknown'
    return {'events_appended': appended, 'events_observed': len(events),
            'partial_final_line': partial, 'completed_turns': endings.count('turn.completed'),
            'failed_turns': endings.count('turn.failed'),
            'completion': 'unknown' if partial else completion,
            'scientific_verdict': 'not-assessed'}


def summarize(root):
    """Count recorded observations without inferring current session completion.

    An observed completed turn can be followed by unfinished work. Legacy ends
    with no explicit status remain unknown. Invocation events from a legacy hook
    and inferred skill references are counted separately.
    """
    _, records = _read_log(resolve_state_root(root, 'read') / 'meta/events.jsonl')
    endings = [row for row in records if row.get('event') == 'session_end']
    return {'events': len(records),
            'completed_turn_observations': sum(r.get('status') == 'completed' for r in endings),
            'failed_turn_observations': sum(r.get('status') == 'failed' for r in endings),
            'unknown_end_observations': sum(r.get('status') not in ('completed', 'failed') for r in endings),
            'recorded_skill_invocations': sum(r.get('event') == 'skill_invoke' for r in records),
            'skill_reference_candidates': sum(r.get('event') == 'skill_reference' for r in records),
            'tool_failures': sum(r.get('event') == 'tool_failure' for r in records),
            'session_completion': 'not-inferred', 'workflow_completeness': 'not-established',
            'scientific_verdict': 'not-assessed'}


def main():
    configure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--source', help='Explicit project-relative Codex JSONL export')
    parser.add_argument('--session')
    parser.add_argument('--run-id')
    parser.add_argument('--summary', action='store_true', help='Read existing event counts without importing')
    args = parser.parse_args()
    try:
        if args.summary:
            result = summarize(args.root)
        else:
            if not args.source or not args.session:
                parser.error('Import requires --source and --session')
            result = import_codex(args.root, args.source, args.session, workflow_run_id=args.run_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (RegistryError, OSError, ValueError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
