"""New framing contracts cannot change an old run or weaken review receipts."""
import copy

import pytest

from tests.test_idea_discovery_gate import _complete_run
from tools import idea_discovery_gate as gate, run_state


def test_old_run_without_contract_is_still_readable_and_resumable(tmp_path):
    _complete_run(tmp_path)
    state = run_state.load_run(tmp_path, 'idea-run')
    assert 'workflow_contract' not in state
    assert gate.evaluate(tmp_path, state).verdict == 'PASS'
    # The report gate does not grant owed phase acceptance on an old run.
    assert run_state.resume_point(tmp_path, 'idea-run')['phase'] == 'research-lit'
    assert run_state.start_run(tmp_path, 'idea-run', list(gate.REQUIRED_PHASES)) == state


def test_new_run_requires_ordered_framing_contract_and_never_migrates_old_run(tmp_path):
    _complete_run(tmp_path)
    before = run_state.load_run(tmp_path, 'idea-run')
    with pytest.raises(ValueError, match='original workflow contract'):
        run_state.start_run(tmp_path, 'idea-run', list(gate.V2_PHASES), workflow_contract='idea-discovery/v2')
    assert run_state.load_run(tmp_path, 'idea-run') == before
    with pytest.raises(ValueError, match='ordered phase contract'):
        run_state.start_run(tmp_path, 'new-run', list(gate.REQUIRED_PHASES), workflow_contract='idea-discovery/v2')
    state = run_state.start_run(tmp_path, 'new-run', list(gate.V2_PHASES), workflow_contract='idea-discovery/v2')
    assert state['workflow_contract'] == 'idea-discovery/v2'
    assert run_state.resume_point(tmp_path, 'new-run')['phase'] == 'problem-framing'


def test_v2_requires_real_framing_artifact_without_granting_acceptance(tmp_path):
    _complete_run(tmp_path, review_status='provisional')
    old = run_state.load_run(tmp_path, 'idea-run')
    state = dict(copy.deepcopy(old), workflow_contract='idea-discovery/v2')
    assert gate.evaluate(tmp_path, state).verdict == 'BLOCKED'
    framing = {'phase': 'problem-framing', 'status': 'done',
               'artifact': 'idea-stage/IDEA_REPORT.md#problem-framing'}
    state['phases'].insert(0, framing)
    assert gate.evaluate(tmp_path, state).verdict == 'BLOCKED'
    report = tmp_path / 'idea-stage/IDEA_REPORT.md'
    report.write_text(report.read_text(encoding='utf-8') + '\n## Problem framing\n\nQuestion, constraints and alternatives.\n', encoding='utf-8')
    assert gate.evaluate(tmp_path, state).verdict == 'PASS'
    assert {p['status'] for p in state['phases'] if p['phase'] in gate.REVIEW_REQUIRED_PHASES} == {'provisional'}
    state['phases'][0], state['phases'][1] = state['phases'][1], state['phases'][0]
    assert gate.evaluate(tmp_path, state).verdict == 'BLOCKED'


def test_unknown_contract_is_not_guessed(tmp_path):
    _complete_run(tmp_path)
    state = run_state.load_run(tmp_path, 'idea-run')
    state['workflow_contract'] = 'future-producer/v99'
    result = gate.evaluate(tmp_path, state)
    assert result.verdict == 'BLOCKED'
    assert 'unknown' in result.reasons[0]


def test_v2_cannot_use_blank_framing_file_as_evidence(tmp_path):
    _complete_run(tmp_path)
    state = run_state.load_run(tmp_path, 'idea-run')
    state['workflow_contract'] = 'idea-discovery/v2'
    (tmp_path / 'blank.md').write_text('  \n', encoding='utf-8')
    state['phases'].insert(0, {'phase': 'problem-framing', 'status': 'done', 'artifact': 'blank.md'})
    result = gate.evaluate(tmp_path, state)
    assert result.verdict == 'BLOCKED'
    assert any('empty artifact' in reason for reason in result.reasons)


def test_mechanical_framing_completion_allows_resume_without_accepting_research(tmp_path):
    run_state.start_run(tmp_path, 'new-run', list(gate.V2_PHASES),
                        workflow_contract='idea-discovery/v2')
    report = tmp_path / 'framing.md'
    report.write_text('# Problem Framing\n\nQuestion and competing explanations.\n', encoding='utf-8')
    run_state.set_status(tmp_path, 'new-run', 'problem-framing', 'done',
                         artifact='framing.md#problem-framing')
    assert gate.complete_framing(tmp_path, 'new-run').verdict == 'PASS'
    state = run_state.load_run(tmp_path, 'new-run')
    framing = state['phases'][0]
    assert framing['status'] == 'accepted'
    assert framing['review_independence'] == 'deterministic'
    assert framing['verdict_id'].startswith('framing.md@')
    assert all(p['status'] == 'pending' for p in state['phases'][1:])
    assert run_state.resume_point(tmp_path, 'new-run')['phase'] == 'research-lit'
    assert gate.evaluate(tmp_path, state).verdict == 'BLOCKED'


@pytest.mark.parametrize('contents', ['', '# Problem Framing\n\n', '# Different Section\n\nText\n'])
def test_missing_framing_content_grants_no_completion_receipt(tmp_path, contents):
    run_state.start_run(tmp_path, 'new-run', list(gate.V2_PHASES),
                        workflow_contract='idea-discovery/v2')
    (tmp_path / 'framing.md').write_text(contents, encoding='utf-8')
    run_state.set_status(tmp_path, 'new-run', 'problem-framing', 'done',
                         artifact='framing.md#problem-framing')
    assert gate.complete_framing(tmp_path, 'new-run').verdict == 'BLOCKED'
    state = run_state.load_run(tmp_path, 'new-run')
    assert state['phases'][0]['status'] == 'done'
    assert state['phases'][0].get('verdict_id') is None
    assert run_state.resume_point(tmp_path, 'new-run')['phase'] == 'problem-framing'


def test_framing_completion_cannot_rewrite_a_legacy_contract(tmp_path):
    _complete_run(tmp_path)
    before = run_state.load_run(tmp_path, 'idea-run')
    assert gate.complete_framing(tmp_path, 'idea-run').verdict == 'BLOCKED'
    assert run_state.load_run(tmp_path, 'idea-run') == before
