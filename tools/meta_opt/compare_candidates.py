"""Compare frozen, paired skill evaluations; report evidence, never land patches.

Consumes existing evaluate_skill_behavior.py run.json and environment.json files
plus separate source-bound assessments. Coverage is relative to the predeclared
cases/repetitions; this tool cannot detect undisclosed attempts outside that plan,
certify reviewer independence, or establish general capability from a small set.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.registry_common import RegistryError, configure_utf8_output, read_record, verify_ref


def _positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _date(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.utcoffset() is None:
            raise ValueError('timezone')
        return result
    except (ValueError, TypeError, AttributeError) as error:
        raise RegistryError('Evaluation dates must include a timezone') from error


def compare(root, protocol_ref, observations):
    """Assess complete paired attempts under a fixed protocol and equal settings.

    Protocol: schema_version, frozen_at, cases={development: [...], held_out: [...]},
    repetitions, model_settings, evaluation_protocol, case_budgets={case: {...}},
    case_inputs={case: {request_sha256, fixture_sha256}},
    environments={baseline: fixed_ref, candidate: fixed_ref}.
    Observation: variant, case, repetition, run_ref, assessment_ref. Assessments
    bind run_ref and contain verdict PASS/FAIL/UNASSESSED, reviewer and rationale.
    Native execution failures stay in the denominator and cannot be graded PASS.
    """
    protocol = read_record(verify_ref(root, protocol_ref))
    if protocol.get('schema_version') != 1 or not _positive_int(protocol.get('repetitions')):
        raise RegistryError('Expected a version 1 protocol and positive repetitions')
    frozen = _date(protocol.get('frozen_at'))
    splits = protocol.get('cases', {})
    if (set(splits) != {'development', 'held_out'} or not splits['development']
            or any(not isinstance(values, list) or any(not isinstance(c, str) or not c for c in values)
                   for values in splits.values())):
        raise RegistryError('Declare development and held-out case lists')
    cases = splits['development'] + splits['held_out']
    if len(set(cases)) != len(cases):
        raise RegistryError('Development and held-out cases must be distinct')
    if set(protocol.get('environments', {})) != {'baseline', 'candidate'}:
        raise RegistryError('Pin both evaluation environments')
    budgets = protocol.get('case_budgets', {})
    if set(budgets) != set(cases) or any(
            not isinstance(b, dict) or set(b) != {'timeout_seconds', 'max_tool_actions'}
            or not all(_positive_int(value) for value in b.values()) for b in budgets.values()):
        raise RegistryError('Declare equal per-case time and tool budgets')
    inputs = protocol.get('case_inputs', {})
    if set(inputs) != set(cases) or any(
            not isinstance(row, dict) or set(row) != {'request_sha256', 'fixture_sha256'}
            or any(not isinstance(value, str) or not re.fullmatch(r'[a-f0-9]{64}', value)
                   for value in row.values()) for row in inputs.values()):
        raise RegistryError('Pin the same request and raw fixture identity for every case')
    if (not isinstance(protocol.get('model_settings'), dict)
            or not protocol['model_settings'].get('model') or not protocol.get('evaluation_protocol')):
        raise RegistryError('Freeze a model and execution protocol')
    environments, issues = {}, []
    for variant, reference in protocol['environments'].items():
        environment = read_record(verify_ref(root, reference))
        if (environment.get('model_settings') != protocol['model_settings']
                or environment.get('evaluation_protocol') != protocol['evaluation_protocol']):
            issues.append(f'{variant}: environment/model/protocol mismatch')
        discovery = environment.get('discovery', {})
        if (not discovery.get('skill_sha256') or not discovery.get('support_resource_sha256')
                or discovery.get('selector') != environment.get('plugin_selector')
                or not environment.get('plugin_selector') or not discovery.get('version')):
            issues.append(f'{variant}: no discovery snapshot')
        environments[variant] = environment
    for key in ('codex', 'harness_sha256', 'case_manifest_sha256', 'jobs', 'public_budget_context'):
        if (key not in environments['baseline'] or key not in environments['candidate']
                or environments['baseline'][key] != environments['candidate'][key]):
            issues.append(f'Unequal or absent environment setting: {key}')
    expected = {(variant, case, repetition) for variant in environments for case in cases
                for repetition in range(1, protocol['repetitions'] + 1)}
    if not isinstance(observations, list):
        raise RegistryError('Observations must be a list of all planned attempts')
    rows, references = {}, set()
    for observation in observations:
        if not isinstance(observation, dict):
            raise RegistryError('Observation must be an object')
        repetition = observation.get('repetition')
        if not _positive_int(repetition):
            raise RegistryError('Repetition must be a positive integer')
        key = (observation.get('variant'), observation.get('case'), repetition)
        if key not in expected or key in rows:
            raise RegistryError('Unexpected or duplicate attempt; retain each planned attempt once')
        run_ref = observation.get('run_ref')
        run = read_record(verify_ref(root, run_ref))
        identity = (run_ref['path'], run_ref['sha256'])
        if identity in references:
            raise RegistryError('One run cannot stand for multiple independent attempts')
        references.add(identity)
        assessment = read_record(verify_ref(root, observation.get('assessment_ref')))
        if (assessment.get('run_ref') != run_ref or assessment.get('verdict') not in ('PASS', 'FAIL', 'UNASSESSED')
                or not isinstance(assessment.get('reviewer'), str) or not assessment['reviewer'].strip()
                or not isinstance(assessment.get('rationale'), str) or not assessment['rationale'].strip()):
            raise RegistryError('Assessments must bind the actual run and identify reviewer and rationale')
        if _date(run.get('started_at')) < frozen:
            issues.append(f'{key}: run predates the frozen protocol')
        if (run.get('case') != key[1] or run.get('model_settings') != protocol['model_settings']
                or run.get('evaluation_protocol') != protocol['evaluation_protocol']
                or run.get('case_budget') != budgets[key[1]]
                or any(run.get(field) != value for field, value in inputs[key[1]].items())
                or run.get('plugin_selector') != environments[key[0]].get('plugin_selector')
                or run.get('toolkit_version') != environments[key[0]].get('discovery', {}).get('version')):
            issues.append(f'{key}: case/model/protocol/budget mismatch')
        valid_execution = (run.get('session_completed') is True
            and isinstance(run.get('exit_code'), int) and not isinstance(run['exit_code'], bool)
            and run['exit_code'] == 0
            and run.get('limit') is None and not run.get('variant_mismatch')
            and not run.get('noncanonical_skill_entrypoints') and not run.get('failure_kind'))
        if valid_execution and (not isinstance(run.get('tool_actions'), int)
                or isinstance(run['tool_actions'], bool) or run['tool_actions'] < 0
                or run['tool_actions'] > budgets[key[1]]['max_tool_actions']
                or isinstance(run.get('seconds'), bool) or not isinstance(run.get('seconds'), (int, float))
                or not 0 <= run['seconds'] <= budgets[key[1]]['timeout_seconds']):
            valid_execution = False
        if not valid_execution and assessment['verdict'] == 'PASS':
            issues.append(f'{key}: invalid execution was assessed PASS')
        verdict = 'FAIL' if not valid_execution else assessment['verdict']
        rows[key] = {**observation, 'verdict': verdict, 'execution_valid': valid_execution,
                     'tool_actions': run.get('tool_actions'), 'seconds': run.get('seconds'),
                     'reviewer': assessment['reviewer']}
    missing = sorted(expected - set(rows))
    summaries, improvements, regressions, unpaired = {}, [], [], []
    for split, identifiers in splits.items():
        summary = {}
        for variant in environments:
            group = [row for (v, case, _), row in rows.items() if v == variant and case in identifiers]
            denominator = len(identifiers) * protocol['repetitions']
            passed = sum(row['verdict'] == 'PASS' for row in group)
            summary[variant] = {'planned_attempts': denominator, 'observed_attempts': len(group),
                'passed': passed, 'failed': sum(row['verdict'] == 'FAIL' for row in group),
                'unassessed': sum(row['verdict'] == 'UNASSESSED' for row in group),
                'pass_fraction_of_planned': passed / denominator if denominator else None}
        summaries[split] = summary
        for case in identifiers:
            for repetition in range(1, protocol['repetitions'] + 1):
                baseline, candidate = (rows.get((v, case, repetition), {}) for v in ('baseline', 'candidate'))
                pair = {'case': case, 'repetition': repetition, 'split': split}
                if not baseline or not candidate or 'UNASSESSED' in (baseline['verdict'], candidate['verdict']):
                    unpaired.append(pair)
                elif baseline['verdict'] == 'FAIL' and candidate['verdict'] == 'PASS':
                    improvements.append(pair)
                elif baseline['verdict'] == 'PASS' and candidate['verdict'] == 'FAIL':
                    regressions.append(pair)
    if issues:
        verdict = 'NOT_COMPARABLE'
    elif missing or unpaired or not splits['held_out'] or protocol['repetitions'] < 2:
        verdict = 'INSUFFICIENT_EVIDENCE'
    elif regressions:
        verdict = 'REGRESSION_OBSERVED'
    elif improvements:
        verdict = 'CANDIDATE_SIGNAL'
    else:
        verdict = 'NO_CLEAR_GAIN'
    return {'verdict': verdict, 'protocol_ref': protocol_ref, 'issues': issues,
        'missing_attempts': missing, 'unpaired_or_unassessed': unpaired,
        'summaries': summaries, 'improvements': improvements, 'regressions': regressions,
        'attempts': list(rows.values()), 'landing_authorized': False,
        'limits': ['Finite task-set evidence; no claim of general RSI or statistical significance.',
                   'Reviewer independence requires trace review; identity fields do not certify it.',
                   'Coverage uses the declared protocol; undisclosed attempts cannot be discovered here.']}


def main():
    configure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--request', required=True, help='JSON object: protocol_ref and observations')
    args = parser.parse_args()
    try:
        request = read_record(args.request)
        print(json.dumps(compare(args.root, request['protocol_ref'], request['observations']), ensure_ascii=False, indent=2))
        return 0
    except (RegistryError, OSError, ValueError, KeyError, TypeError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
