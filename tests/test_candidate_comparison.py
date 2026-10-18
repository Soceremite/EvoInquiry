"""Measured skill changes keep failures and regressions in the comparison."""
import json

import pytest

from tools.meta_opt.compare_candidates import compare
from tools.registry_common import RegistryError, fixed_ref


def save(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value) + '\n', encoding='utf-8')
    return fixed_ref(root, path)


@pytest.fixture
def study(tmp_path):
    settings = {'model': 'gpt-6.1-sol', 'model_reasoning_effort': 'medium', 'model_provider': 'fixture'}
    environments = {}
    for variant in ('baseline', 'candidate'):
        environments[variant] = save(tmp_path, variant + '/environment.json', {
            'codex': 'codex-fixture', 'harness_sha256': 'a' * 64, 'case_manifest_sha256': 'b' * 64,
            'jobs': 1, 'public_budget_context': False, 'model_settings': settings,
            'evaluation_protocol': 'request-only-v1', 'plugin_selector': 'evo-inquiry@' + variant,
            'discovery': {'skill_sha256': {'research-guide': variant}, 'support_resource_sha256': {'tools': variant},
                          'selector': 'evo-inquiry@' + variant, 'version': '1.5.0.dev1'}})
    protocol = {'schema_version': 1, 'frozen_at': '2026-10-18T00:00:00Z',
        'cases': {'development': ['D01'], 'held_out': ['H01']}, 'repetitions': 2,
        'model_settings': settings, 'evaluation_protocol': 'request-only-v1',
        'case_budgets': {case: {'timeout_seconds': 60, 'max_tool_actions': 8} for case in ('D01', 'H01')},
        'case_inputs': {case: {'request_sha256': 'c' * 64, 'fixture_sha256': 'd' * 64}
                        for case in ('D01', 'H01')},
        'environments': environments}
    observations = []
    for variant in ('baseline', 'candidate'):
        for case in ('D01', 'H01'):
            for repetition in (1, 2):
                directory = f'{variant}/{case}/{repetition}'
                run = {'case': case, 'started_at': '2026-10-18T00:01:00Z', 'exit_code': 0,
                    'limit': None, 'session_completed': True, 'tool_actions': 3, 'seconds': 20,
                    'variant_mismatch': False, 'noncanonical_skill_entrypoints': [], 'failure_kind': None,
                    'model_settings': settings, 'evaluation_protocol': 'request-only-v1',
                    'plugin_selector': 'evo-inquiry@' + variant, 'toolkit_version': '1.5.0.dev1',
                    'case_budget': protocol['case_budgets'][case]}
                run.update(protocol['case_inputs'][case])
                run_ref = save(tmp_path, directory + '/run.json', run)
                assessment_ref = save(tmp_path, directory + '/assessment.json', {
                    'run_ref': run_ref, 'verdict': 'FAIL' if variant == 'baseline' else 'PASS',
                    'reviewer': 'fresh-review-fixture', 'rationale': 'Source-bound fixture assessment'})
                observations.append({'variant': variant, 'case': case, 'repetition': repetition,
                                     'run_ref': run_ref, 'assessment_ref': assessment_ref})
    return tmp_path, protocol, observations


def evaluate(study):
    root, protocol, observations = study
    return compare(root, save(root, 'protocol.json', protocol), observations)


def revise(study, index, *, run_changes=None, assessment_changes=None):
    root, _, observations = study
    row = observations[index]
    run = json.loads((root / row['run_ref']['path']).read_text())
    run.update(run_changes or {})
    row['run_ref'] = save(root, row['run_ref']['path'], run)
    assessment = json.loads((root / row['assessment_ref']['path']).read_text())
    assessment.update(assessment_changes or {}, run_ref=row['run_ref'])
    row['assessment_ref'] = save(root, row['assessment_ref']['path'], assessment)


def test_paired_signal_does_not_authorize_landing_or_certify_general_rsi(study):
    report = evaluate(study)
    assert report['verdict'] == 'CANDIDATE_SIGNAL' and len(report['improvements']) == 4
    assert report['summaries']['held_out']['candidate']['passed'] == 2
    assert not report['landing_authorized'] and report['limits']


def test_timeout_is_retained_in_denominator_and_cannot_pass(study):
    revise(study, 4, run_changes={'exit_code': -15, 'limit': 'timeout', 'session_completed': False},
           assessment_changes={'verdict': 'FAIL'})
    report = evaluate(study)
    assert report['summaries']['development']['candidate']['planned_attempts'] == 2
    assert report['summaries']['development']['candidate']['passed'] == 1
    assert report['summaries']['development']['candidate']['failed'] == 1
    revise(study, 4, assessment_changes={'verdict': 'PASS'})
    assert evaluate(study)['verdict'] == 'NOT_COMPARABLE'


def test_omitted_failure_leaves_missing_attempt(study):
    study[2].pop(4)
    report = evaluate(study)
    assert report['verdict'] == 'INSUFFICIENT_EVIDENCE'
    assert report['missing_attempts'] == [('candidate', 'D01', 1)]


def test_regression_is_visible_despite_improved_overall_score(study):
    revise(study, 0, assessment_changes={'verdict': 'PASS'})
    revise(study, 4, assessment_changes={'verdict': 'FAIL'})
    report = evaluate(study)
    assert report['verdict'] == 'REGRESSION_OBSERVED'
    assert len(report['regressions']) == 1 and len(report['improvements']) == 3


@pytest.mark.parametrize('changes', [
    {'model_settings': {'model': 'other'}}, {'case_budget': {'timeout_seconds': 300, 'max_tool_actions': 8}},
    {'started_at': '2026-10-17T00:00:00Z'}, {'plugin_selector': 'evo-inquiry@unrelated'},
    {'request_sha256': 'e' * 64}, {'fixture_sha256': 'f' * 64}])
def test_unmatched_settings_or_posthoc_protocol_are_not_comparable(study, changes):
    revise(study, 4, run_changes=changes)
    assert evaluate(study)['verdict'] == 'NOT_COMPARABLE'


def test_self_written_pass_inside_run_is_not_an_assessment(study):
    revise(study, 4, run_changes={'assessment': 'PASS'}, assessment_changes={'verdict': 'UNASSESSED'})
    report = evaluate(study)
    assert report['verdict'] == 'INSUFFICIENT_EVIDENCE'
    assert report['summaries']['development']['candidate']['unassessed'] == 1


def test_reused_trace_cannot_substitute_an_independent_repeat(study):
    study[2][5]['run_ref'] = study[2][4]['run_ref']
    with pytest.raises(RegistryError, match='multiple independent'):
        evaluate(study)


def test_changed_fixed_evidence_is_rejected(study):
    root, protocol, observations = study
    ref = observations[0]['run_ref']
    (root / ref['path']).write_text('{"assessment":"PASS"}')
    with pytest.raises(RegistryError):
        compare(root, save(root, 'protocol.json', protocol), observations)


def test_no_held_out_tasks_is_explicitly_insufficient(study):
    root, protocol, observations = study
    protocol['cases']['development'] = ['D01', 'H01']
    protocol['cases']['held_out'] = []
    assert evaluate(study)['verdict'] == 'INSUFFICIENT_EVIDENCE'


def test_boolean_exit_status_cannot_certify_success(study):
    revise(study, 4, run_changes={'exit_code': False})
    assert evaluate(study)['verdict'] == 'NOT_COMPARABLE'
