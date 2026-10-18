"""Bound research actions inside the existing run-state coordinator.

This helper reserves declared costs and records attempts; it never launches a
process, creates a Codex Goal, accepts a phase, or estimates a scientific verdict.
An unresolved reservation requires inspection of the actual execution before
retry. Resource amounts are caller-supplied bounds/observations, not billing or
GPU telemetry. Existing checkpoint policy owns retained storage and save peaks.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import re
import sys

try:
    from . import run_state
    from .registry_common import (RegistryError, configure_utf8_output, digest,
                                  identifier, now, read_record, verify_ref)
except ImportError:
    import run_state
    from registry_common import (RegistryError, configure_utf8_output, digest,
                                 identifier, now, read_record, verify_ref)


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


def _validate_metadata(metadata):
    """Reject malformed accounting rather than treating it as available budget."""
    if (not isinstance(metadata, dict) or metadata.get('schema_version') != 1
            or not isinstance(metadata.get('objective'), str) or not metadata['objective'].strip()):
        raise RegistryError('Invalid continuation identity/schema')
    limits = _validate_limits(metadata.get('limits'))
    try:
        start = datetime.fromisoformat(metadata['started_at'])
        if start.utcoffset() is None:
            raise ValueError('timezone')
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
    return start


def configure(root, run_id, objective, limits):
    """Attach a fixed completion objective and declared bounds to an existing run.

    Idempotent for identical input; changed objectives or limits need a separately
    authorized run, rather than silently resetting spent budgets. Does not start
    a workflow or a host Goal. Example: configure(root, 'pilot', 'Save the audit',
    {'max_actions': 4, 'wall_seconds': 600, 'max_attempts_per_key': 2,
     'resources': {'gpu_seconds': 300}}).
    """
    if not isinstance(objective, str) or not objective.strip():
        raise RegistryError('A verifiable objective is required')
    limits = _validate_limits(limits)
    def update(metadata, state):
        if metadata:
            _validate_metadata(metadata)
            if metadata.get('objective') != objective or metadata.get('limits') != limits:
                raise RegistryError('Existing continuation objective and limits are fixed')
            return metadata
        return {'schema_version': 1, 'objective': objective, 'limits': limits,
                'started_at': now(), 'actions': [], 'stopped': None}
    return run_state.update_coordination(str(root), run_id, update)['coordination']


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
    elapsed = max(0, (datetime.now(timezone.utc) - start).total_seconds())
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
    else:
        status = 'READY'
    return {'status': status, 'run_id': state['run_id'], 'phase': phase,
            'spent_or_reserved': spent, 'actions_used': len(actions),
            'elapsed_seconds': elapsed, 'unresolved_actions': unresolved,
            'evidence_issues': violations, 'exceeded_resources': over,
            'exhausted_resources': exhausted,
            'scientific_verdict': 'not-assessed', 'host_goal_modified': False}


def inspect(root, run_id):
    """Read a continuation decision without creating files or changing statuses.

    WORKFLOW_TERMINAL means original phase gates are terminal, not that research
    claims are true or a native Goal may be completed without its own evidence.
    """
    return _inspection(root, run_state.load_run(str(root), run_id))


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
        decision = _inspection(root, state)
        if decision['status'] != 'READY':
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
        return metadata
    return run_state.update_coordination(str(root), run_id, update)['coordination']


def stop(root, run_id, reason):
    """Persist an authorized stop reason without killing jobs or releasing reservations.

    Outstanding actions still return RECONCILE until their real execution ends.
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


def main():
    configure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--run-id', required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('configure')
    create.add_argument('--objective', required=True)
    create.add_argument('--limits', required=True, help='Path to JSON with explicit bounds/units')
    sub.add_parser('inspect')
    claim = sub.add_parser('claim')
    claim.add_argument('--request', required=True)
    finish = sub.add_parser('finish')
    finish.add_argument('--request', required=True)
    end = sub.add_parser('stop')
    end.add_argument('--reason', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'configure':
            result = configure(args.root, args.run_id, args.objective, read_record(args.limits))
        elif args.command == 'inspect':
            result = inspect(args.root, args.run_id)
        elif args.command == 'claim':
            result = claim_action(args.root, args.run_id, **read_record(args.request))
        elif args.command == 'finish':
            result = finish_action(args.root, args.run_id, **read_record(args.request))
        else:
            result = stop(args.root, args.run_id, args.reason)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (RegistryError, ValueError, OSError, KeyError, TypeError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
