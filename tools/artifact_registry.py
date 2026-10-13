"""Immutable artifact identities with hash-chained events and CAS navigation.

Local locks and atomic single-file renames are required. A publish is a journaled
multi-file protocol, not an atomic transaction. Repair/reconcile are explicit.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

try:
    from .registry_common import (RegistryError, configure_utf8_output, atomic_write, canonical, digest, file_digest,
                                  file_lock, identifier, local_path, now, read_record,
                                  validate_schema, verify_ref)
    from .state_paths import resolve_state_root, state_writer
    from .project_registry import discover_project
except ImportError:
    from registry_common import (RegistryError, configure_utf8_output, atomic_write, canonical, digest, file_digest,
                                 file_lock, identifier, local_path, now, read_record,
                                 validate_schema, verify_ref)
    from state_paths import resolve_state_root, state_writer
    from project_registry import discover_project


class CurrentConflict(RegistryError):
    """Both revisions are retained, but the caller's current precondition failed."""
    def __init__(self, reference):
        self.reference = reference
        super().__init__('current changed; revision retained at ' + reference['path'])


def artifact_ref(record):
    """Return a fixed identity independent of the navigation alias."""
    return {'artifact_id': record['artifact_id'], 'revision': record['revision'],
            'path': record['authority_path'], 'sha256': record['sha256']}


def validate_record(record, root=None):
    """Validate identity and input/review digests, without issuing a scientific verdict."""
    validate_schema('artifact', record)
    identifier(record['artifact_id'])
    identifier(record['revision'])
    identifier(record['transaction_id'])
    if 'current' in Path(record['authority_path']).parts:
        raise RegistryError('An alias cannot be an authority path')
    if record['review_status'] in ('accepted', 'provisional', 'blocked') and not record['verdict_ref']:
        raise RegistryError('Review status requires a real digest-bound review receipt')
    if root is not None:
        local_path(root, record['authority_path'])
        for reference in record['inputs']:
            verify_ref(root, reference)
        if record['verdict_ref']:
            receipt = read_record(verify_ref(root, record['verdict_ref']))
            if receipt.get('subject_sha256') != record['sha256']:
                raise RegistryError('Review receipt addresses another content digest')
            if record['review_status'] in ('accepted', 'provisional'):
                if receipt.get('verdict') != 'PASS' or receipt.get('acceptance_status') != record['review_status']:
                    raise RegistryError('Review receipt does not support the requested status')
                independence = receipt.get('review_independence')
                if record['review_status'] == 'accepted' and independence not in ('cross-family', 'deterministic'):
                    raise RegistryError('Same-family review cannot establish accepted')
                if record['review_status'] == 'provisional' and independence != 'same-family':
                    raise RegistryError('Provisional must preserve the same-family review distinction')
            if not receipt.get('reviewer') or not receipt.get('verdict_id'):
                raise RegistryError('Review receipt requires reviewer and durable verdict ID')
    return record


def resolve_ref(reference, root='.', profile=None, *, legacy_read=False):
    """Resolve a fixed revision; profile never silently substitutes current."""
    return verify_ref(root, reference, legacy_read=legacy_read)


class ArtifactRegistry:
    """One local registry using .ei events as authority and index as a projection."""
    def __init__(self, root):
        self.root = Path(root).resolve()

    @property
    def state(self):
        return resolve_state_root(self.root, 'read')

    def events(self):
        """Reject half events, broken chains and duplicate transaction event identities."""
        path = self.state / 'artifact-events.jsonl'
        if not path.exists():
            return []
        data = path.read_bytes()
        if data and not data.endswith(b'\n'):
            raise RegistryError('Partial artifact event; preserve and explicitly repair before publishing')
        result, previous, identities = [], None, set()
        for line in data.splitlines():
            try:
                event = json.loads(line)
                identity = (event['transaction_id'], event['kind'])
                signed = {key: value for key, value in event.items() if key != 'event_sha256'}
                if (event['previous_sha256'] != previous or event['event_sha256'] != digest(signed)
                        or identity in identities or event['kind'] not in ('publish', 'current-update')):
                    raise RegistryError('Artifact event chain or transaction identity is corrupt')
            except (KeyError, TypeError, json.JSONDecodeError):
                raise RegistryError('Corrupt artifact metadata event') from None
            result.append(event)
            identities.add(identity)
            previous = event['event_sha256']
        return result

    def _append_event(self, payload):
        events = self.events()
        for event in events:
            if (event['transaction_id'], event['kind']) == (payload['transaction_id'], payload['kind']):
                old_payload = {key: value for key, value in event.items()
                               if key not in ('previous_sha256', 'event_sha256', 'recorded_at')}
                if old_payload != payload:
                    raise RegistryError('Transaction event retry conflicts with committed metadata')
                return event
        event = {**payload, 'previous_sha256': events[-1]['event_sha256'] if events else None,
                 'recorded_at': now()}
        event['event_sha256'] = digest(event)
        path = self.state / 'artifact-events.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('ab') as handle:
            handle.write(canonical(event) + b'\n')
            handle.flush()
            os.fsync(handle.fileno())
        return event

    def _alias(self, artifact_id):
        return local_path(self.root, f'reports/current/{identifier(artifact_id)}.json')

    def current(self, artifact_id):
        """Read a mutable alias only for navigation or CAS preconditions."""
        path = self._alias(artifact_id)
        return read_record(path) if path.exists() else None

    def _projection(self):
        revisions, currents = {}, {}
        for event in self.events():
            if event['kind'] == 'publish':
                record = event['record']
                key = record['artifact_id'] + '@' + record['revision']
                if key in revisions and revisions[key] != record:
                    raise RegistryError('Conflicting revision identities in the event log')
                revisions[key] = record
            elif event['status'] == 'committed':
                currents[event['reference']['artifact_id']] = event['reference']
        return {'schema_version': 1, 'revisions': revisions, 'current': currents}

    def rebuild_index(self):
        """Rebuild a disposable projection; never repair evidence by choosing latest."""
        with state_writer(self.root) as state, file_lock(state / 'locks/artifacts.lock'):
            projection = self._projection()
            atomic_write(state / 'index.json', projection)
            return projection

    def _pending(self, exclude=None):
        pending = []
        for path in self.state.glob('event-repairs/*.receipt.json'):
            if read_record(path)['status'] == 'prepared':
                raise RegistryError('Unfinished event repair; complete its approved plan before publishing')
        for directory in self.state.glob('transactions/*'):
            path = directory / 'journal.json'
            if not path.exists():
                raise RegistryError(f'Orphan staged content {directory.name}; inspect before publishing')
            journal = read_record(path)
            if journal['transaction_id'] != exclude and journal['status'] not in ('complete', 'conflict'):
                pending.append(journal['transaction_id'])
        if pending:
            raise RegistryError(f'Unreconciled publications {pending}; recover before another publish')

    def _manifest(self, record):
        path = local_path(self.root, 'MANIFEST.md')
        marker = '<!-- ei-transaction:' + record['transaction_id'] + ' -->'
        existing = path.read_text() if path.exists() else ''
        if marker not in existing:
            entry = (f"\n{marker}\n- `{record['artifact_id']}@{record['revision']}`: "
                     f"`{record['authority_path']}` SHA-256 `{record['sha256']}`; "
                     f"review `{record['review_status']}`.\n")
            atomic_write(path, (existing + entry).encode())

    def _complete(self, journal, directory, fail_at=None):
        record, reference = journal['record'], artifact_ref(journal['record'])
        validate_record(record, self.root)
        target = local_path(self.root, record['authority_path'])
        if target.exists():
            if file_digest(target) != record['sha256']:
                raise RegistryError('History is immutable; conflicting content at authority path')
        else:
            content = directory / 'content'
            if file_digest(content) != record['sha256']:
                raise RegistryError('Staged artifact digest changed')
            target.parent.mkdir(parents=True, exist_ok=True)
            # All participating writers share the artifact lock. Pre-existing
            # manual files are verified above and are never overwritten.
            os.replace(content, target)
        journal['status'] = 'body'
        atomic_write(directory / 'journal.json', journal)
        if fail_at == 'body':
            raise RuntimeError('Injected interruption after body')
        self._append_event({'kind': 'publish', 'transaction_id': record['transaction_id'], 'record': record})
        journal['status'] = 'event'
        atomic_write(directory / 'journal.json', journal)
        if fail_at == 'event':
            raise RuntimeError('Injected interruption after event')
        status = 'registered'
        if journal['update_current']:
            old_update = next((event for event in self.events() if event['kind'] == 'current-update'
                               and event['transaction_id'] == record['transaction_id']), None)
            current = self.current(record['artifact_id'])
            if old_update:
                status = old_update['status']
            elif current == journal['expected_current'] or current == reference:
                atomic_write(self._alias(record['artifact_id']), reference)
                status = 'committed'
            else:
                status = 'conflict'
            if fail_at == 'alias':
                raise RuntimeError('Injected interruption after alias')
            self._append_event({'kind': 'current-update', 'transaction_id': record['transaction_id'],
                                'status': status, 'reference': reference,
                                'expected_current': journal['expected_current']})
        self._manifest(record)
        atomic_write(self.state / 'index.json', self._projection())
        if fail_at == 'projection':
            raise RuntimeError('Injected interruption after projection')
        journal['status'] = 'conflict' if status == 'conflict' else 'complete'
        atomic_write(directory / 'journal.json', journal)
        if status == 'conflict':
            raise CurrentConflict(reference)
        return reference

    def publish_artifact(self, record, content, expected_current=None, *, fail_at=None, update_current=True):
        """Publish a new fixed revision; CAS failure preserves it and raises CurrentConflict."""
        validate_record(record, self.root)
        content = content.encode() if isinstance(content, str) else content
        if digest(content) != record['sha256']:
            raise RegistryError('Supplied artifact content does not match its declared SHA-256')
        profile = discover_project(self.root)
        parts = Path(record['authority_path']).parts
        if profile['layout_profile'] == 'governed-v1':
            prefix = ('reports', 'history', record['artifact_id'], record['revision'])
            if parts[:4] != prefix or len(parts) < 5:
                raise RegistryError('governed-v1 history must encode artifact and revision IDs')
        elif len(parts) < 2 or parts[0] not in ('idea-stage', 'refine-logs', 'review-stage', 'paper', 'reports'):
            raise RegistryError('compat-v1 publications need an explicit versioned stage path')
        if record['artifact_id'] in profile['authority_map']:
            if record['authority_path'] != profile['authority_map'][record['artifact_id']]:
                raise RegistryError('Authority map does not authorize this path')
        with state_writer(self.root) as state, file_lock(state / 'locks/artifacts.lock'):
            self.events()
            transaction = record['transaction_id']
            self._pending(exclude=transaction)
            for old in self._projection()['revisions'].values():
                if (old['artifact_id'], old['revision']) == (record['artifact_id'], record['revision']) and old != record:
                    raise RegistryError('Same artifact revision cannot be registered with different metadata or content')
            directory = state / 'transactions' / transaction
            desired = {'transaction_id': transaction, 'record': record,
                       'expected_current': expected_current, 'update_current': update_current}
            if (directory / 'journal.json').exists():
                journal = read_record(directory / 'journal.json')
                if any(journal[key] != value for key, value in desired.items()):
                    raise RegistryError('Transaction ID is already bound to a different publication')
                if journal['status'] == 'complete':
                    verify_ref(self.root, artifact_ref(record))
                    return artifact_ref(record)
                if journal['status'] == 'conflict':
                    raise CurrentConflict(artifact_ref(record))
            else:
                journal = {**desired, 'status': 'prepared'}
                atomic_write(directory / 'content', content)
                atomic_write(directory / 'journal.json', journal)
            return self._complete(journal, directory, fail_at)

    def register_existing(self, record):
        """Register bytes without moving or overwriting them; unverifiable history stays legacy."""
        validate_record(record, self.root)
        target = local_path(self.root, record['authority_path'])
        if file_digest(target) != record['sha256']:
            raise RegistryError('Existing artifact digest differs')
        if not record['inputs'] and not record['verdict_ref']:
            if record['review_status'] != 'legacy-unverified' or record['lifecycle_status'] != 'legacy-unverified':
                raise RegistryError('Unverifiable legacy evidence must remain legacy-unverified')
        # Registration reuses exactly the same publication protocol. compat-v1
        # also permits old root files through this explicit registration path.
        with state_writer(self.root) as state, file_lock(state / 'locks/artifacts.lock'):
            self.events()
            self._pending(exclude=record['transaction_id'])
            for old in self._projection()['revisions'].values():
                if (old['artifact_id'], old['revision']) == (record['artifact_id'], record['revision']) and old != record:
                    raise RegistryError('Conflicting existing revision identity')
            directory = state / 'transactions' / record['transaction_id']
            desired = {'transaction_id': record['transaction_id'], 'record': record,
                       'expected_current': None, 'update_current': False}
            if (directory / 'journal.json').exists():
                journal = read_record(directory / 'journal.json')
                if any(journal[key] != value for key, value in desired.items()):
                    raise RegistryError('Transaction identity conflict')
            else:
                journal = {**desired, 'status': 'prepared'}
                atomic_write(directory / 'journal.json', journal)
            return self._complete(journal, directory)

    def reconcile(self, transaction_id=None):
        """Resume verified intent and repair aliases/projection from committed events."""
        with state_writer(self.root) as state, file_lock(state / 'locks/artifacts.lock'):
            self.events()
            if transaction_id:
                directory = state / 'transactions' / identifier(transaction_id)
                journal = read_record(directory / 'journal.json')
                if journal['status'] not in ('complete', 'conflict'):
                    self._complete(journal, directory)
            else:
                self._pending()
            projection = self._projection()
            for reference in projection['current'].values():
                verify_ref(self.root, reference)
                atomic_write(self._alias(reference['artifact_id']), reference)
            atomic_write(state / 'index.json', projection)
            return projection

    def audit(self):
        """Report stale aliases, missing/damaged content and recoverable pending intents."""
        problems = []
        try:
            projection = self._projection()
        except RegistryError as error:
            return {'status': 'BLOCKED', 'problems': [str(error)]}
        for record in projection['revisions'].values():
            try:
                validate_record(record, self.root)
                verify_ref(self.root, artifact_ref(record))
            except RegistryError as error:
                problems.append(str(error))
        for key, reference in projection['current'].items():
            if self.current(key) != reference:
                problems.append('Alias drift: ' + key)
        for directory in self.state.glob('transactions/*'):
            path = directory / 'journal.json'
            if not path.exists():
                problems.append('Orphan staged content: ' + directory.name)
            elif read_record(path)['status'] not in ('complete', 'conflict'):
                problems.append('Unfinished publication: ' + directory.name)
        for path in self.state.glob('event-repairs/*.receipt.json'):
            if read_record(path)['status'] == 'prepared':
                problems.append('Unfinished event repair: ' + path.name)
        return {'status': 'BLOCKED' if problems else 'PASS', 'problems': problems,
                'limitation': 'File integrity is independent of scientific acceptance.'}

    def plan_partial_event_repair(self):
        """Diagnose only an unterminated tail; complete corrupt events need manual review."""
        path = self.state / 'artifact-events.jsonl'
        raw = path.read_bytes()
        return self._partial_event_plan(raw)

    def _partial_event_plan(self, raw):
        if not raw or raw.endswith(b'\n'):
            raise RegistryError('No partial tail to repair')
        prefix, _, tail = raw.rpartition(b'\n')
        prefix = prefix + b'\n' if prefix else b''
        # Validate the complete prefix without mutating the original log.
        previous, identities = None, set()
        for line in prefix.splitlines():
            try:
                event = json.loads(line)
                identity = (event['transaction_id'], event['kind'])
                body = {key: value for key, value in event.items() if key != 'event_sha256'}
                if event['previous_sha256'] != previous or digest(body) != event['event_sha256'] or identity in identities:
                    raise RegistryError('Complete event prefix is corrupt; automatic tail repair is unsafe')
                previous = event['event_sha256']
                identities.add(identity)
            except (KeyError, json.JSONDecodeError):
                raise RegistryError('Complete event prefix is corrupt; preserve it for manual recovery') from None
        plan = {'operation': 'quarantine-partial-event-tail', 'root': str(self.root), 'event_file_sha256': digest(raw),
                'keep_bytes': len(prefix), 'tail_sha256': digest(tail),
                'backup': '.ei/event-repairs/' + digest(raw) + '.jsonl'}
        plan['plan_sha256'] = digest(plan)
        return plan

    def repair_partial_event(self, plan, approval, *, fail_at=None):
        """Preserve all damaged bytes, then apply a digest-bound approved tail repair."""
        if not (approval.get('approved') is True and approval.get('plan_sha256') == plan.get('plan_sha256')
                and approval.get('confirmed_by') and approval.get('confirmed_at')):
            raise RegistryError('Event repair requires plan-bound authorization')
        with state_writer(self.root) as state, file_lock(state / 'locks/artifacts.lock'):
            path = state / 'artifact-events.jsonl'
            backup = local_path(self.root, plan['backup'])
            receipt_path = backup.with_suffix('.receipt.json')
            raw = backup.read_bytes() if backup.exists() else path.read_bytes()
            if self._partial_event_plan(raw) != plan:
                raise RegistryError('Event bytes or repair plan changed')
            if receipt_path.exists():
                receipt = read_record(receipt_path)
                if receipt['plan'] != plan:
                    raise RegistryError('Event repair receipt conflicts with this plan')
                if receipt['status'] == 'tail-quarantined':
                    self.events()
                    return receipt
            current = path.read_bytes()
            prefix = raw[:plan['keep_bytes']]
            if current not in (raw, prefix):
                raise RegistryError('Event log changed during interrupted repair; preserve and reconcile')
            if not backup.exists():
                atomic_write(backup, raw)
            receipt = {'plan': plan, 'approval': approval, 'status': 'prepared',
                       'backup_sha256': digest(raw)}
            atomic_write(receipt_path, receipt)
            if fail_at == 'prepared':
                raise RuntimeError('Injected event repair interruption after prepared')
            if current == raw:
                atomic_write(path, prefix)
            if fail_at == 'truncated':
                raise RuntimeError('Injected event repair interruption after truncated')
            receipt.update(status='tail-quarantined', repaired_at=now())
            atomic_write(receipt_path, receipt)
            self.events()
            return receipt


def main():
    configure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('publish', 'register'):
        command = sub.add_parser(name)
        command.add_argument('--record', required=True)
        if name == 'publish':
            command.add_argument('--content', required=True)
            command.add_argument('--expected-current')
    resolve = sub.add_parser('resolve')
    resolve.add_argument('--ref', required=True)
    resolve.add_argument('--legacy-read', action='store_true')
    sub.add_parser('audit')
    sub.add_parser('rebuild-index')
    sub.add_parser('plan-event-repair')
    repair = sub.add_parser('repair-events')
    repair.add_argument('--plan', required=True)
    repair.add_argument('--approval', required=True)
    recover = sub.add_parser('reconcile')
    recover.add_argument('--transaction-id')
    args = parser.parse_args()
    registry = ArtifactRegistry(args.root)
    try:
        if args.command == 'publish':
            result = registry.publish_artifact(read_record(args.record), Path(args.content).read_bytes(),
                                              read_record(args.expected_current) if args.expected_current else None)
        elif args.command == 'register':
            result = registry.register_existing(read_record(args.record))
        elif args.command == 'resolve':
            result = {'path': str(resolve_ref(read_record(args.ref), args.root, legacy_read=args.legacy_read))}
        elif args.command == 'audit':
            result = registry.audit()
        elif args.command == 'rebuild-index':
            result = registry.rebuild_index()
        elif args.command == 'plan-event-repair':
            result = registry.plan_partial_event_repair()
        elif args.command == 'repair-events':
            result = registry.repair_partial_event(read_record(args.plan), read_record(args.approval))
        else:
            result = registry.reconcile(args.transaction_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get('status') != 'BLOCKED' else 2
    except (RegistryError, OSError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 3 if isinstance(error, CurrentConflict) else 2


if __name__ == '__main__':
    raise SystemExit(main())
