"""Bound research actions inside the existing run-state coordinator.

This helper reserves declared costs and records attempts; it never launches a
process, creates a Codex Goal, accepts a phase, or estimates a scientific verdict.
An unresolved reservation requires inspection of the actual execution before
retry. Resource amounts are caller-supplied bounds/observations, not billing or
GPU telemetry. Existing checkpoint policy owns retained storage and save peaks.
An optional reflection gate uses the same coordination record to pause new
actions until the workflow owner records a trajectory or problem-synthesis
reflection in the existing iteration ledger. It is not a scientific verdict.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import re
import sys
from uuid import uuid4

try:
    from . import run_state
    from .registry_common import (RegistryError, configure_utf8_output, digest,
                                  file_digest, fixed_ref, identifier, local_path, now,
                                  read_record, verify_ref)
    from .state_paths import resolve_state_root
except ImportError:
    import run_state
    from registry_common import (RegistryError, configure_utf8_output, digest,
                                 file_digest, fixed_ref, identifier, local_path, now,
                                 read_record, verify_ref)
    from state_paths import resolve_state_root


def _amount(value, name, *, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0 or (positive and value == 0)):
        raise RegistryError(f'{name} must be a finite {"positive" if positive else "nonnegative"} number')
    return value


def _costs(values):
    if not isinstance(values, dict):
        raise RegistryError('Resource costs must be an object with explicit units')
    for key, value in values.items():
        identifier(key)
        _amount(value, key)
    return dict(values)


def _validate_limits(limits):
    if not isinstance(limits, dict) or set(limits) != {
            'max_actions', 'wall_seconds', 'max_attempts_per_key', 'resources'}:
        raise RegistryError('Limits require max_actions, wall_seconds, max_attempts_per_key and resources')
    for key in ('max_actions', 'max_attempts_per_key'):
        if isinstance(limits[key], bool) or not isinstance(limits[key], int) or limits[key] < 1:
            raise RegistryError(f'{key} must be a positive integer')
    _amount(limits['wall_seconds'], 'wall_seconds', positive=True)
    _costs(limits['resources'])
    return json.loads(json.dumps(limits, allow_nan=False))


def _verify_refs(root, references):
    if not isinstance(references, list):
        raise RegistryError('Evidence references must be a list')
    for reference in references:
        verify_ref(root, reference)


def _start_time(value):
    try:
        start = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if start.utcoffset() is None or start > datetime.now(timezone.utc):
            raise ValueError('timezone or future start')
        return start.astimezone(timezone.utc)
    except (AttributeError, ValueError, TypeError) as error:
        raise RegistryError('Start time must be timezone-aware and not in the future') from error


def _timing(metadata, start):
    limits = metadata['limits']
    reserve = _amount(metadata.get('closeout_seconds', 0), 'closeout_seconds')
    if reserve > limits['wall_seconds']:
        raise RegistryError('Closeout reserve exceeds the original wall budget')
    try:
        deadline = start + timedelta(seconds=limits['wall_seconds'])
    except (OverflowError, ValueError) as error:
        raise RegistryError('Wall budget is outside the supported datetime range') from error
    elapsed = max(0, (datetime.now(timezone.utc) - start).total_seconds())
    remaining = max(0, limits['wall_seconds'] - elapsed)
    return {'started_at': metadata['started_at'], 'deadline_at': deadline.isoformat(),
            'remaining_seconds': remaining, 'elapsed_seconds': elapsed,
            'closeout_seconds': reserve,
            'dispatch_seconds_remaining': max(0, remaining - reserve)}


def _validate_metadata(metadata):
    """Reject malformed accounting rather than treating it as available budget."""
    if (not isinstance(metadata, dict) or metadata.get('schema_version') != 1
            or not isinstance(metadata.get('objective'), str) or not metadata['objective'].strip()):
        raise RegistryError('Invalid continuation identity/schema')
    limits = _validate_limits(metadata.get('limits'))
    try:
        start = _start_time(metadata['started_at'])
        _timing(metadata, start)
    except (ValueError, TypeError, KeyError) as error:
        raise RegistryError('Invalid continuation start time') from error
    actions = metadata.get('actions')
    if not isinstance(actions, list):
        raise RegistryError('Invalid continuation actions')
    attempts = {}
    for index, action in enumerate(actions, 1):
        if not isinstance(action, dict) or action.get('id') != f'a{index:06d}':
            raise RegistryError('Invalid or reordered action identity')
        key = identifier(action.get('key'))
        attempts[key] = attempts.get(key, 0) + 1
        if (isinstance(action.get('attempt'), bool) or action.get('attempt') != attempts[key]
                or action.get('status') not in ('reserved', 'succeeded', 'failed', 'cancelled')
                or not isinstance(action.get('phase'), str) or not action['phase']
                or not isinstance(action.get('question'), str) or not action['question'].strip()
                or not isinstance(action.get('signature'), str)
                or not re.fullmatch(r'[a-f0-9]{64}', action['signature'])):
            raise RegistryError('Invalid action accounting')
        for field in ('reserved_costs',) + (() if action['status'] == 'reserved' else ('actual_costs',)):
            if set(_costs(action.get(field))) != set(limits['resources']):
                raise RegistryError('Action accounting changed resource units')
        for field in ('input_refs', 'result_refs'):
            if not isinstance(action.get(field), list):
                raise RegistryError('Invalid action evidence list')
        if action['status'] == 'succeeded' and not action['result_refs']:
            raise RegistryError('Completed action is missing result evidence')
        if action['status'] == 'reserved' and 'actual_costs' in action:
            raise RegistryError('Unresolved action cannot reclaim its reservation')
    stopped = metadata.get('stopped')
    if stopped is not None and (not isinstance(stopped, dict)
            or not isinstance(stopped.get('reason'), str) or not stopped['reason'].strip()):
        raise RegistryError('Invalid continuation stop record')
    cadence = metadata.get('reflection_every_actions')
    interval = metadata.get('reflection_interval_seconds')
    if interval is not None:
        _amount(interval, 'reflection_interval_seconds', positive=True)
    if cadence is not None:
        if type(cadence) is not int or cadence < 1:
            raise RegistryError('Reflection cadence must be a positive action count')
    if cadence is not None or interval is not None:
        reviewed = metadata.get('reflection_reviewed_actions', [])
        completed = {row['id'] for row in actions if row['status'] in ('succeeded', 'failed')}
        if (not isinstance(reviewed, list) or any(not isinstance(item, str) for item in reviewed)
                or len(set(reviewed)) != len(reviewed) or not set(reviewed) <= completed):
            raise RegistryError('Invalid reviewed action identities')
    gate = metadata.get('reflection_gate')
    if gate is not None:
        if (not isinstance(gate, dict) or gate.get('status') != 'required'
                or not isinstance(gate.get('id'), str) or not re.fullmatch(r'[a-f0-9]{32}', gate['id'])
                or gate.get('kind') not in ('synthesis', 'checkpoint')
                or not isinstance(gate.get('phase'), str) or not gate['phase']
                or gate.get('level') not in ('block', 'milestone', 'direction')
                or not isinstance(gate.get('requested_at'), str)
                or not isinstance(gate.get('reasons'), list)
                or not gate['reasons']
                or not all(isinstance(reason, str) and reason.strip() for reason in gate['reasons'])):
            raise RegistryError('Invalid reflection gate')
        _start_time(gate['requested_at'])
        if 'action_ids' in gate:
            ids = gate['action_ids']
            completed = {row['id'] for row in actions if row['status'] in ('succeeded', 'failed')}
            if (not isinstance(ids, list) or any(not isinstance(item, str) for item in ids)
                    or len(set(ids)) != len(ids) or not set(ids) <= completed):
                raise RegistryError('Invalid reflection action identities')
    return start


def configure(root, run_id, objective, limits, *, started_at=None, closeout_seconds=None,
              reflection_every_actions=None, reflection_interval_seconds=None):
    """Attach a fixed completion objective and declared bounds to an existing run.

    Idempotent for identical input; changed objectives or limits need a separately
    authorized run, rather than silently resetting spent budgets. Does not start
    a workflow or a host Goal. Example: configure(root, 'pilot', 'Save the audit',
    {'max_actions': 4, 'wall_seconds': 600, 'max_attempts_per_key': 2,
     'resources': {'gpu_seconds': 300}}, closeout_seconds=90).

    Pass an existing authorized task's original started_at when attaching late;
    this records no fictional historical actions. Omitted timing options retain
    existing values on reconfigure. Old callers reserve no closeout window.

    reflection_every_actions optionally fixes a positive count of settled
    successful/failed actions between reviews. Cancellation is not evidence.
    Settlement opens a gate, without choosing its verdict. Omission preserves
    an existing setting; old contracts remain opt-in.
    reflection_interval_seconds optionally fixes elapsed seconds between addressed
    reviews. Existing monitoring calls inspect to observe it; claim checks it
    before dispatch. This creates no background service.
    """
    if not isinstance(objective, str) or not objective.strip():
        raise RegistryError('A verifiable objective is required')
    limits = _validate_limits(limits)
    explicit_start = _start_time(started_at) if started_at is not None else None
    if reflection_every_actions is not None and (
            type(reflection_every_actions) is not int or reflection_every_actions < 1):
        raise RegistryError('Reflection cadence must be a positive action count')
    if reflection_interval_seconds is not None:
        _amount(reflection_interval_seconds, 'reflection_interval_seconds', positive=True)
    if closeout_seconds is not None:
        _amount(closeout_seconds, 'closeout_seconds')
        if closeout_seconds > limits['wall_seconds']:
            raise RegistryError('Closeout reserve exceeds the original wall budget')
    def update(metadata, state):
        if metadata:
            _validate_metadata(metadata)
            if metadata.get('objective') != objective or metadata.get('limits') != limits:
                raise RegistryError('Existing continuation objective and limits are fixed')
            if ((explicit_start is not None and _start_time(metadata['started_at']) != explicit_start)
                    or (closeout_seconds is not None
                        and metadata.get('closeout_seconds', 0) != closeout_seconds)
                    or (reflection_every_actions is not None
                        and metadata.get('reflection_every_actions') != reflection_every_actions)
                    or (reflection_interval_seconds is not None
                        and metadata.get('reflection_interval_seconds') != reflection_interval_seconds)):
                raise RegistryError('Existing continuation clock and closeout reserve are fixed')
            return metadata
        configured = now()
        metadata = {'schema_version': 1, 'objective': objective, 'limits': limits,
                    'started_at': explicit_start.isoformat() if explicit_start is not None else configured,
                    'configured_at': configured, 'closeout_seconds': closeout_seconds or 0,
                    'actions': [], 'stopped': None}
        if reflection_every_actions is not None:
            metadata.update(reflection_every_actions=reflection_every_actions,
                            reflection_reviewed_actions=[])
        if reflection_interval_seconds is not None:
            metadata['reflection_interval_seconds'] = reflection_interval_seconds
        _validate_metadata(metadata)
        return metadata
    return run_state.update_coordination(str(root), run_id, update)['coordination']


def execution_directive(root, run_id):
    """Read stop intent and original remaining dispatch time for a local launcher.

    Return None for a missing/unconfigured legacy workflow; otherwise return
    stopped (record or None) and timing (seconds/deadline). This read-only path
    validates coordination without rehashing all research files on each poll.
    It never settles actions or declares a process dead. Malformed state raises;
    an already-bound launcher must fail closed if its contract disappears.
    """
    try:
        state = run_state.load_run(str(root), identifier(run_id))
    except FileNotFoundError:
        return None
    metadata = state.get('coordination')
    if not metadata:
        return None
    start = _validate_metadata(metadata)
    return {'stopped': metadata['stopped'], 'timing': _timing(metadata, start)}


def _unreviewed_actions(metadata):
    reviewed = set(metadata.get('reflection_reviewed_actions', []))
    return [row['id'] for row in metadata['actions']
            if row['status'] in ('succeeded', 'failed') and row['id'] not in reviewed]


def _new_reflection_gate(metadata, state, reasons, level, kind):
    gate = {'id': uuid4().hex, 'status': 'required', 'kind': kind,
            'phase': run_state.first_open_phase(state)['phase'], 'level': level,
            'reasons': reasons, 'requested_at': now()}
    if any(metadata.get(key) is not None for key in ('reflection_every_actions', 'reflection_interval_seconds')):
        gate['action_ids'] = _unreviewed_actions(metadata)
    return gate


def _automatic_reflection(metadata, state):
    cadence = metadata.get('reflection_every_actions')
    interval = metadata.get('reflection_interval_seconds')
    reasons = []
    if cadence is not None and len(_unreviewed_actions(metadata)) >= cadence:
        reasons.append('completed_action_cadence')
    if interval is not None:
        last = metadata.get('last_reflection') or {}
        start = _start_time(last.get('addressed_at', last.get('at', metadata['started_at'])))
        if (datetime.now(timezone.utc) - start).total_seconds() >= interval:
            reasons.append('elapsed_review_interval')
    if (reasons and not metadata['stopped'] and not metadata.get('reflection_gate')
            and run_state.first_open_phase(state) is not None):
        metadata['reflection_gate'] = _new_reflection_gate(
            metadata, state, reasons, 'block', 'checkpoint')
        return True
    return False


def _inspection(root, state):
    metadata = state.get('coordination')
    if not metadata:
        raise RegistryError('No continuation contract; configure the existing run first')
    start = _validate_metadata(metadata)
    actions = metadata['actions']
    spent = {key: 0 for key in metadata['limits']['resources']}
    violations = []
    for action in actions:
        for key, value in action.get('actual_costs', action['reserved_costs']).items():
            if key in spent:
                spent[key] += value
        for group in ('input_refs', 'result_refs'):
            for reference in action.get(group, []):
                try:
                    verify_ref(root, reference)
                except (RegistryError, OSError) as error:
                    violations.append({'action_id': action['id'], 'reference': reference,
                                       'reason': str(error)})
    for phase in state['phases']:
        for group in ('artifact_refs', 'execution_refs', 'spec_refs'):
            for reference in phase.get(group, []):
                try:
                    verify_ref(root, reference)
                except (RegistryError, OSError) as error:
                    violations.append({'phase': phase['phase'], 'reference': reference,
                                       'reason': str(error)})
    handoff = metadata.get('reflection_plan_ref')
    if handoff is not None:
        try:
            verify_ref(root, handoff)
        except (RegistryError, OSError) as error:
            violations.append({'reference': handoff, 'reason': str(error)})
    timing = _timing(metadata, start)
    elapsed = timing['elapsed_seconds']
    phase = run_state.first_open_phase(state)
    unresolved = [action['id'] for action in actions if action['status'] == 'reserved']
    limits = metadata['limits']
    over = [key for key, value in spent.items() if value > limits['resources'][key]]
    exhausted = [key for key, value in spent.items() if value >= limits['resources'][key]]
    if unresolved:
        status = 'RECONCILE'
    elif violations:
        status = 'EVIDENCE_CHANGED'
    elif metadata['stopped']:
        status = 'STOPPED'
    elif over:
        status = 'BUDGET_EXCEEDED'
    elif phase is None:
        status = 'WORKFLOW_TERMINAL'
    elif elapsed >= limits['wall_seconds'] or len(actions) >= limits['max_actions']:
        status = 'BUDGET_EXHAUSTED'
    elif phase['status'] in ('done', 'provisional'):
        status = 'REVIEW_REQUIRED'
    elif phase['status'] == 'running':
        status = 'RECONCILE'
    elif timing['remaining_seconds'] <= timing['closeout_seconds']:
        status = 'CLOSEOUT_REQUIRED'
    elif metadata.get('reflection_gate'):
        status = ('SYNTHESIS_REQUIRED' if metadata['reflection_gate']['kind'] == 'synthesis'
                  else 'REFLECTION_REQUIRED')
    else:
        status = 'READY'
    return {'status': status, 'run_id': state['run_id'], 'phase': phase,
            'spent_or_reserved': spent, 'actions_used': len(actions),
            'elapsed_seconds': elapsed, 'unresolved_actions': unresolved,
            'timing': timing,
            'reflection_gate': metadata.get('reflection_gate'),
            'evidence_issues': violations, 'exceeded_resources': over,
            'exhausted_resources': exhausted,
            'scientific_verdict': 'not-assessed', 'host_goal_modified': False}


def inspect(root, run_id):
    """Read a continuation decision without creating files or changing statuses.

    WORKFLOW_TERMINAL means original phase gates are terminal, not that research
    claims are true or a native Goal may be completed without its own evidence.
    An explicitly configured elapsed-review policy may atomically open a gate;
    old contracts remain read-only. Repeated inspection preserves the gate ID.
    """
    state = run_state.load_run(str(root), run_id)
    metadata = state.get('coordination')
    if metadata:
        _validate_metadata(metadata)
        if _automatic_reflection(metadata, state):
            def update(current, current_state):
                _validate_metadata(current)
                _automatic_reflection(current, current_state)
                return current
            state = run_state.update_coordination(str(root), run_id, update)
    return _inspection(root, state)


def _watched_file(root, relative):
    if not isinstance(relative, str):
        raise RegistryError('Handoff watch paths must be project-relative strings')
    path = local_path(root, relative)
    name = path.relative_to(Path(root).resolve()).as_posix()
    try:
        path.stat()
    except FileNotFoundError:
        return {'path': name, 'state': 'absent'}
    return {'path': name, 'state': 'file', 'sha256': file_digest(path)}


def handoff_snapshot(root, run_id, *, watch_paths=None):
    """Capture selected current identities without initializing or changing state.

    Missing selected files are recorded explicitly. Two observations detect
    concurrent changes; this is not a filesystem transaction or scientific
    acceptance receipt. Save AFTER the last relevant state change, outside the
    watched files, and check it before resuming. No file contents are returned.
    """
    identifier(run_id)
    if watch_paths is None:
        watch_paths = []
    if not isinstance(watch_paths, list):
        raise RegistryError('Handoff watch paths must be a list')
    root = Path(root).resolve()
    for _ in range(3):
        path = resolve_state_root(root, 'read') / 'runs' / f'{run_id}.json'
        local_path(root, path.relative_to(root).as_posix()).stat()
        run_ref = {'path': path.relative_to(root).as_posix(), 'sha256': file_digest(path)}
        state = run_state.load_run(str(root), run_id)
        decision = (_inspection(root, state) if state.get('coordination') else
                    {'status': 'UNCONFIGURED', 'timing': None, 'unresolved_actions': []})
        files = sorted((_watched_file(root, name) for name in watch_paths), key=lambda row: row['path'])
        if len({row['path'] for row in files}) != len(files):
            raise RegistryError('Duplicate handoff watch paths')
        if (file_digest(path) != run_ref['sha256'] or
                files != [_watched_file(root, row['path']) for row in files]):
            continue
        return {'schema_version': 1, 'captured_at': now(), 'run_id': run_id,
                'run_ref': run_ref, 'files': files,
                'phase': run_state.first_open_phase(state),
                'continuation_status': decision['status'], 'timing': decision['timing'],
                'unresolved_actions': decision['unresolved_actions'],
                'scientific_verdict': 'not-assessed', 'host_goal_modified': False}
    raise RegistryError('State changed during handoff capture; refresh before resuming')


def check_handoff(root, run_id, receipt):
    """Compare a saved snapshot with current sources; never trust saved timing.

    CURRENT covers only the selected identities at inspection, not all project
    facts or scientific validity. STALE requires reading the changed sources and
    reconciling live work before dispatch. Both outcomes leave state untouched.
    """
    identifier(run_id)
    if (not isinstance(receipt, dict) or type(receipt.get('schema_version')) is not int
            or receipt['schema_version'] != 1 or receipt.get('run_id') != run_id
            or not isinstance(receipt.get('files'), list)):
        raise RegistryError('Invalid handoff identity/schema')
    reference = receipt.get('run_ref')
    if (not isinstance(reference, dict) or reference.get('path') not in
            (f'.ei/runs/{run_id}.json', f'.aris/runs/{run_id}.json')
            or not isinstance(reference.get('sha256'), str)
            or not re.fullmatch(r'[a-f0-9]{64}', reference['sha256'])):
        raise RegistryError('Invalid handoff run reference')
    local_path(root, reference['path'])
    saved = {}
    for row in receipt['files']:
        if not isinstance(row, dict) or not isinstance(row.get('path'), str):
            raise RegistryError('Invalid handoff file entry')
        path = local_path(root, row['path'])
        name = path.relative_to(Path(root).resolve()).as_posix()
        if name != row['path'] or name in saved:
            raise RegistryError('Handoff paths must be unique and canonical')
        if ((row.get('state') == 'absent' and set(row) != {'path', 'state'}) or
                (row.get('state') == 'file' and (set(row) != {'path', 'state', 'sha256'}
                 or not isinstance(row['sha256'], str)
                 or not re.fullmatch(r'[a-f0-9]{64}', row['sha256']))) or
                row.get('state') not in ('absent', 'file')):
            raise RegistryError('Invalid handoff file identity')
        saved[name] = row
    try:
        current = handoff_snapshot(root, run_id, watch_paths=list(saved))
    except FileNotFoundError:
        # A vanished run cannot authorize a new execution or initialize a replacement.
        return {'status': 'STALE', 'changed_paths': [reference['path']],
                'current': None, 'reason': 'Run state is unavailable; reconcile before resuming'}
    changed = [row['path'] for row in current['files'] if row != saved[row['path']]]
    if reference != current['run_ref']:
        changed.extend([reference['path'], current['run_ref']['path']])
    return {'status': 'STALE' if changed else 'CURRENT',
            'changed_paths': sorted(set(changed)), 'current': current}


def claim_action(root, run_id, action_key, phase, question, *, costs=None, input_refs=None):
    """Reserve one action and its costs before dispatch; duplicate claims do not dispatch.

    Return ``claim=new`` only for a new attempt. ``claim=existing`` identifies an
    unresolved duplicate that MUST be reconciled, not launched again. Identical
    failed attempts may retry within the fixed limit; changed inputs/questions
    need a distinct action_key. The caller still owns resource authorization and
    launching through the existing execution registry/queue.
    """
    identifier(action_key)
    if not isinstance(question, str) or not question.strip():
        raise RegistryError('Record the uncertainty this action addresses')
    costs = _costs({} if costs is None else costs)
    references = [] if input_refs is None else input_refs
    _verify_refs(root, references)
    signature = digest({'key': action_key, 'phase': phase, 'question': question,
                        'inputs': references})
    answer = {}
    def update(metadata, state):
        state['coordination'] = metadata
        if not metadata:
            raise RegistryError('Configure continuation before claiming actions')
        _validate_metadata(metadata)
        previous = [row for row in metadata['actions'] if row['key'] == action_key]
        if previous:
            latest = previous[-1]
            if latest['signature'] != signature:
                raise RegistryError('Changed action inputs/question require a new action key')
            if latest['status'] == 'reserved':
                answer.update(claim='existing', action=latest)
                return metadata
            if latest['status'] == 'succeeded':
                raise RegistryError('Completed action cannot be dispatched again')
            if len(previous) >= metadata['limits']['max_attempts_per_key']:
                raise RegistryError('Action retry limit reached; reassess or stop')
        opened = _automatic_reflection(metadata, state)
        decision = _inspection(root, state)
        if decision['status'] != 'READY':
            if opened:
                answer['blocked'] = decision['status']
                return metadata
            raise RegistryError('Cannot dispatch: ' + decision['status'])
        if decision['phase']['phase'] != phase:
            raise RegistryError('Action must belong to the original resume phase')
        limits = metadata['limits']['resources']
        if set(costs) != set(limits):
            raise RegistryError('Declare a bound for every configured resource, with no unknown units')
        for key, value in costs.items():
            if decision['spent_or_reserved'][key] + value > limits[key]:
                raise RegistryError(f'Insufficient remaining {key}')
        action = {'id': f'a{len(metadata["actions"]) + 1:06d}', 'key': action_key,
                  'phase': phase, 'question': question, 'signature': signature,
                  'attempt': len(previous) + 1, 'status': 'reserved',
                  'reserved_costs': costs, 'input_refs': references, 'result_refs': [],
                  'claimed_at': now(), 'finished_at': None}
        metadata['actions'].append(action)
        answer.update(claim='new', action=action)
        return metadata
    run_state.update_coordination(str(root), run_id, update)
    if 'blocked' in answer:
        raise RegistryError('Cannot dispatch: ' + answer['blocked'])
    return answer


def finish_action(root, run_id, action_id, outcome, *, actual_costs, result_refs=None, reason=''):
    """Record observed terminal evidence; never retry an unconfirmed live process.

    outcome is succeeded, failed or cancelled. All configured resource units need
    observed values. An overrun is retained and blocks later work; it is never
    clipped to the reservation. The caller verifies process termination first.
    Repeating an identical completion is idempotent; conflicting history fails.
    """
    if outcome not in ('succeeded', 'failed', 'cancelled'):
        raise RegistryError('Outcome must be succeeded, failed or cancelled')
    costs = _costs(actual_costs)
    references = [] if result_refs is None else result_refs
    _verify_refs(root, references)
    if not isinstance(reason, str) or (outcome != 'succeeded' and not reason.strip()):
        raise RegistryError('Failed/cancelled actions need a reason')
    if outcome == 'succeeded' and not references:
        raise RegistryError('Success needs fixed result evidence')
    def update(metadata, state):
        _validate_metadata(metadata)
        matches = [row for row in metadata.get('actions', []) if row['id'] == action_id]
        if len(matches) != 1:
            raise RegistryError('Unknown action reservation')
        if set(costs) != set(metadata['limits']['resources']):
            raise RegistryError('Observed costs must cover all configured resource units')
        action = matches[0]
        changes = {'status': outcome, 'actual_costs': costs, 'result_refs': references, 'reason': reason}
        if action['status'] != 'reserved':
            if any(action.get(key) != value for key, value in changes.items()):
                raise RegistryError('Terminal action history cannot be rewritten')
            return metadata
        action.update(changes, finished_at=now())
        _automatic_reflection(metadata, state)
        return metadata
    return run_state.update_coordination(str(root), run_id, update)['coordination']


def settle_execution(root, run_id, action_id, execution_run_id, *, actual_costs,
                     result_refs=None, reason=''):
    """Settle an action from its existing registered terminal execution, without launch.

    Before dispatch, include the prepared execution's snapshot_ref in the action's
    input_refs and bind its workflow_run_id to this run. This prevents attaching
    a different successful job during recovery. The execution registry validates
    its terminal receipt, snapshot and fixed outputs; absent/live/changed evidence
    leaves the reservation untouched. Repeating the same settlement is idempotent,
    including after the wall budget expires. Phase/review gates never advance.

    actual_costs is an explicit unit-to-number object of observed costs, not an
    estimate inferred from arbitrary result schemas. result_refs is an optional
    list of fixed references; payloads may be JSON objects, lists, CSV or binaries.
    Process success does not establish experimental completeness or claim support.
    Example: settle_execution(root, 'pilot', 'a000001', 'fit-1',
        actual_costs={'model_fits': 2}, result_refs=[attempts_ref]).
    """
    try:
        from .execution_registry import inspect_terminal
    except ImportError:
        from execution_registry import inspect_terminal
    state = run_state.load_run(str(root), run_id)
    metadata = state.get('coordination')
    _validate_metadata(metadata)
    actions = [row for row in metadata['actions'] if row['id'] == action_id]
    if len(actions) != 1:
        raise RegistryError('Unknown action reservation')
    terminal, reference = inspect_terminal(root, execution_run_id)
    if (terminal['workflow_run_id'] != run_id
            or terminal['snapshot_ref'] not in actions[0]['input_refs']):
        raise RegistryError('Execution must match this run and the action\'s pre-bound snapshot')
    references = [] if result_refs is None else result_refs
    _verify_refs(root, references)
    references = [reference] + [ref for ref in references if ref != reference]
    outcome = {'completed': 'succeeded', 'failed': 'failed', 'stopped': 'cancelled'}[terminal['status']]
    return finish_action(root, run_id, action_id, outcome, actual_costs=actual_costs,
                         result_refs=references, reason=reason or
                         f"Registered execution {execution_run_id}: {terminal['status']} (exit {terminal['exit_code']})")


def stop(root, run_id, reason):
    """Persist an authorized stop that bound local launchers observe.

    Outstanding actions still return RECONCILE until their real execution ends.
    The controller sends no signals or releases reservations. The local launcher
    enforces this intent; remote/unbound jobs still require their execution owner.
    This does not pause or complete a Codex native Goal.
    """
    if not isinstance(reason, str) or not reason.strip():
        raise RegistryError('A stop reason is required')
    def update(metadata, state):
        if not metadata:
            raise RegistryError('No continuation contract')
        _validate_metadata(metadata)
        if metadata['stopped'] and metadata['stopped']['reason'] != reason:
            raise RegistryError('Existing stop reason is immutable')
        metadata['stopped'] = metadata['stopped'] or {'reason': reason, 'at': now()}
        return metadata
    return run_state.update_coordination(str(root), run_id, update)['coordination']


def require_reflection(root, run_id, reasons, *, level='block', kind='synthesis'):
    """Pause new claims at an existing workflow boundary, without changing phases.

    The gate ID binds a later reflection to this checkpoint. Ordinary trajectory
    reviews use kind=checkpoint; only multi-problem synthesis uses synthesis.
    Repeated requests merge reasons without opening another gate or resetting costs.
    """
    if level not in ('block', 'milestone', 'direction') or kind not in ('synthesis', 'checkpoint'):
        raise RegistryError('Invalid reflection level or kind')
    if (not isinstance(reasons, list) or not reasons
            or not all(isinstance(reason, str) and reason.strip() for reason in reasons)):
        raise RegistryError('Reflection gate needs non-empty reasons')
    normalized = sorted({reason.strip() for reason in reasons})

    def update(metadata, state):
        if not metadata:
            raise RegistryError('No continuation contract; reflection gate is unavailable')
        _validate_metadata(metadata)
        existing = metadata.get('reflection_gate')
        if existing:
            if existing['kind'] != kind:
                raise RegistryError('Resolve the active reflection before changing its kind')
            existing['reasons'] = sorted(set(existing['reasons']) | set(normalized))
            order = ('block', 'milestone', 'direction')
            existing['level'] = max((level, existing['level']), key=order.index)
            return metadata
        phase = run_state.first_open_phase(state)
        if phase is None:
            raise RegistryError('Cannot request reflection on a terminal workflow')
        metadata['reflection_gate'] = _new_reflection_gate(metadata, state, normalized, level, kind)
        return metadata
    return run_state.update_coordination(str(root), run_id, update)['coordination']


def _validate_reflection(payload):
    """Validate structure only; evidence truth and scientific review stay with skills."""
    if not isinstance(payload, dict):
        raise RegistryError('Reflection must be an object')
    if payload.get('kind', 'synthesis') == 'synthesis':
        try:
            from .problem_synthesis import validate_request
        except ImportError:
            from problem_synthesis import validate_request
        return validate_request(payload)
    allowed = {'kind', 'schema_version', 'gate_id', 'decision', 'reason',
               'evidence_refs', 'next_action', 'blocker'}
    if (payload.get('kind') != 'checkpoint' or set(payload) - allowed
            or type(payload.get('schema_version')) is not int or payload['schema_version'] != 1
            or payload.get('decision') not in ('CONTINUE', 'REPLAN', 'DEFER', 'BLOCKED', 'STOP')):
        raise RegistryError('Invalid workflow checkpoint schema/decision')
    for field in ('reason',):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise RegistryError(f'Checkpoint requires {field}')
    refs = payload.get('evidence_refs')
    if not isinstance(refs, list) or not refs or not all(isinstance(ref, str) and ref.strip() for ref in refs):
        raise RegistryError('Checkpoint requires evidence references')
    gate_id = payload.get('gate_id')
    if gate_id is not None and (not isinstance(gate_id, str) or not re.fullmatch(r'[a-f0-9]{32}', gate_id)):
        raise RegistryError('Invalid checkpoint gate_id')
    if payload['decision'] in ('DEFER', 'BLOCKED'):
        if not isinstance(payload.get('blocker'), str) or not payload['blocker'].strip():
            raise RegistryError('Deferred/blocked checkpoint requires a blocker')
    if payload['decision'] in ('CONTINUE', 'REPLAN'):
        action = payload.get('next_action')
        if (not isinstance(action, dict) or set(action) != {'skill', 'description'}
                or not all(isinstance(value, str) and value.strip() for value in action.values())):
            raise RegistryError('Checkpoint requires the next skill and action')
    return json.loads(json.dumps(payload, allow_nan=False))


def _latest_reflection(root, run_id, gate):
    """Read a valid envelope for this gate and phase; unrelated records cannot clear it."""
    try:
        from .iteration_log import show
    except ImportError:
        from iteration_log import show
    latest = None
    for line in show(str(root), run_id).splitlines():
        try:
            row = json.loads(line)
            if not isinstance(row, dict) or row.get('event') != 'reflection':
                continue
            payload = row.get('reflection')
            if (not isinstance(payload, dict) or payload.get('gate_id') != gate['id']
                    or payload.get('kind') != gate['kind'] or row.get('phase') != gate['phase']):
                continue
            if (_validate_reflection(payload) != payload or row.get('reflection_id') !=
                    digest({'phase': row['phase'], 'reflection': payload})):
                continue
            latest = row
        except (ValueError, KeyError, TypeError):
            continue
    return latest


def _resolve_reflection(root, run_id, metadata, *, handoff_ref=None, state=None):
    """Resolve under the run lock. The ledger append may precede an interrupted save."""
    gate = metadata.get('reflection_gate')
    if not gate:
        if handoff_ref is not None:
            previous = (metadata.get('last_reflection') or {}).get('handoff_ref')
            if previous != handoff_ref:
                raise RegistryError('No active reflection accepts this handoff')
            verify_ref(root, handoff_ref)
        return metadata
    latest = _latest_reflection(root, run_id, gate)
    if latest is None:
        raise RegistryError('Reflection ledger has no valid record for the active gate')
    payload = latest['reflection']
    decision = payload['decision']
    gate.pop('blocker', None)
    gate.pop('handoff_required', None)
    gate['decision'] = decision
    gate['reflection_id'] = latest['reflection_id']
    if decision in ('DEFER', 'BLOCKED'):
        if handoff_ref is not None:
            raise RegistryError('Resolve the blocker with a new reflection before handing off')
        gate['blocker'] = payload['blocker']
        return metadata
    if decision in ('MERGE', 'ABSTRACTION_PIVOT', 'REPLAN') and handoff_ref is None:
        gate['handoff_required'] = True
        return metadata
    if handoff_ref is not None:
        if decision not in ('MERGE', 'ABSTRACTION_PIVOT', 'REPLAN'):
            raise RegistryError('This reflection does not request a revised plan')
        verify_ref(root, handoff_ref)
    receipt = {'id': latest['reflection_id'], 'gate_id': gate['id'],
               'at': latest['ts'], 'decision': decision,
               'ledger': (resolve_state_root(root, 'read') / 'runs' /
                          f'{run_id}.iterations.jsonl').relative_to(Path(root).resolve()).as_posix()}
    if handoff_ref is not None:
        receipt['handoff_ref'] = handoff_ref
        # Later CONTINUE/KEEP_SEPARATE records must not forget the active plan.
        metadata['reflection_plan_ref'] = handoff_ref
    if decision == 'STOP':
        metadata['stopped'] = metadata['stopped'] or {'reason': payload['reason'], 'at': now()}
    metadata['last_reflection'] = receipt
    if any(metadata.get(key) is not None for key in ('reflection_every_actions', 'reflection_interval_seconds')):
        addressed = gate.get('action_ids', [])
        metadata['reflection_reviewed_actions'] = list(dict.fromkeys(
            metadata.get('reflection_reviewed_actions', []) + addressed))
        receipt['action_ids'] = list(addressed)
        receipt['addressed_at'] = now()
    metadata.pop('reflection_gate')
    if state is not None:
        _automatic_reflection(metadata, state)
    return metadata


def record_reflection(root, run_id, phase, payload):
    """Record a checkpoint for an existing run; never initialize state for a short task.

    A configured gate requires its exact ID/kind/phase. Append-before-save makes
    crash recovery possible: repeating the same request reuses the ledger entry.
    DEFER/BLOCKED retain the brake; merge/pivot/replan wait for a fixed plan handoff.
    """
    try:
        from .iteration_log import record_reflection as append
    except ImportError:
        from iteration_log import record_reflection as append
    payload = _validate_reflection(payload)
    state = run_state.load_run(str(root), run_id)
    if phase not in [row['phase'] for row in state['phases']]:
        raise RegistryError('Reflection phase must belong to the existing run')
    if not state.get('coordination'):
        if payload.get('gate_id') is not None:
            raise RegistryError('No active reflection gate for this record')
        return {**append(str(root), run_id, phase, payload), 'reflection_gate': 'unconfigured'}
    answer = {}
    def update(metadata, snapshot):
        _validate_metadata(metadata)
        gate = metadata.get('reflection_gate')
        previous = metadata.get('last_reflection') or {}
        reflection_id = digest({'phase': phase, 'reflection': payload})
        if gate:
            if (payload.get('gate_id') != gate['id'] or payload['kind'] != gate['kind']
                    or phase != gate['phase']):
                raise RegistryError('Reflection must match the active gate ID, kind and phase')
        elif payload.get('gate_id') is not None and previous.get('id') != reflection_id:
            raise RegistryError('Reflection does not match an active gate or completed record')
        answer.update(append(str(root), run_id, phase, payload))
        if gate:
            _resolve_reflection(root, run_id, metadata, state=state)
        answer['reflection_gate'] = 'required' if metadata.get('reflection_gate') else 'cleared'
        return metadata
    run_state.update_coordination(str(root), run_id, update)
    return answer


def clear_reflection(root, run_id, *, handoff_ref=None):
    """Reconcile a recorded reflection; a changed frame requires a fixed plan handoff."""
    def update(metadata, state):
        if not metadata:
            raise RegistryError('No continuation contract')
        _validate_metadata(metadata)
        return _resolve_reflection(root, run_id, metadata, handoff_ref=handoff_ref, state=state)
    return run_state.update_coordination(str(root), run_id, update)['coordination']


def main():
    configure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--run-id', required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('configure')
    create.add_argument('--objective', required=True)
    create.add_argument('--limits', required=True, help='Path to JSON with explicit bounds/units')
    create.add_argument('--started-at', help='Original authorized task start (timezone-aware ISO timestamp)')
    create.add_argument('--closeout-seconds', type=float, help='Reserve inside the original wall budget')
    create.add_argument('--reflection-every-actions', type=int,
                        help='Fixed settled-success/failure cadence; old contracts stay opt-in')
    create.add_argument('--reflection-interval-seconds', type=float,
                        help='Fixed interval observed by monitor/claim calls; no background scheduler')
    sub.add_parser('inspect')
    handoff = sub.add_parser('handoff')
    handoff.add_argument('--watch', action='append', default=[], help='Selected project-relative file; may be absent')
    check = sub.add_parser('check-handoff')
    check.add_argument('--receipt', required=True, help='Path to a previously saved handoff JSON')
    claim = sub.add_parser('claim')
    claim.add_argument('--request', required=True)
    finish = sub.add_parser('finish')
    finish.add_argument('--request', required=True)
    settle = sub.add_parser('settle-execution', help='Settle from a pre-bound registered terminal execution; never relaunch')
    settle.add_argument('--request', required=True,
                        help='JSON object: action_id, execution_run_id, actual_costs, optional result_refs/reason')
    end = sub.add_parser('stop')
    end.add_argument('--reason', required=True)
    gate = sub.add_parser('require-reflection')
    gate.add_argument('--reason', action='append', required=True)
    gate.add_argument('--level', choices=('block', 'milestone', 'direction'), default='block')
    gate.add_argument('--kind', choices=('synthesis', 'checkpoint'), default='synthesis')
    reflect = sub.add_parser('record-reflection')
    reflect.add_argument('--phase', required=True)
    reflect.add_argument('--request', required=True, help='Path to a checkpoint JSON artifact')
    clear = sub.add_parser('clear-reflection')
    clear.add_argument('--handoff', help='Project-relative revised plan after merge/pivot/replan')
    args = parser.parse_args()
    try:
        if args.command == 'configure':
            result = configure(args.root, args.run_id, args.objective, read_record(args.limits),
                               started_at=args.started_at, closeout_seconds=args.closeout_seconds,
                               reflection_every_actions=args.reflection_every_actions,
                               reflection_interval_seconds=args.reflection_interval_seconds)
        elif args.command == 'inspect':
            result = inspect(args.root, args.run_id)
        elif args.command == 'handoff':
            result = handoff_snapshot(args.root, args.run_id, watch_paths=args.watch)
        elif args.command == 'check-handoff':
            result = check_handoff(args.root, args.run_id, read_record(args.receipt))
        elif args.command == 'claim':
            result = claim_action(args.root, args.run_id, **read_record(args.request))
        elif args.command == 'finish':
            result = finish_action(args.root, args.run_id, **read_record(args.request))
        elif args.command == 'settle-execution':
            result = settle_execution(args.root, args.run_id, **read_record(args.request))
        elif args.command == 'require-reflection':
            result = require_reflection(args.root, args.run_id, args.reason, level=args.level, kind=args.kind)
        elif args.command == 'record-reflection':
            result = record_reflection(args.root, args.run_id, args.phase, read_record(args.request))
        elif args.command == 'clear-reflection':
            result = clear_reflection(args.root, args.run_id, handoff_ref=(
                fixed_ref(args.root, args.handoff) if args.handoff else None))
        else:
            result = stop(args.root, args.run_id, args.reason)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 3 if args.command == 'check-handoff' and result['status'] == 'STALE' else 0
    except (RegistryError, ValueError, OSError, KeyError, TypeError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
