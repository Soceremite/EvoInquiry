"""Continuation invariants over actual run-state and fixed evidence files."""
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest

from tools import research_control as control, run_state
from tools.registry_common import RegistryError, fixed_ref


def test_two_cooperating_processes_claim_one_attempt(project):
    program = '''from tools.research_control import claim_action
import json,sys
result=claim_action(sys.argv[1], 'pilot', 'parallel-check', 'explore', 'Inspect the same evidence', costs={'gpu_seconds':5})
print(json.dumps(result))
'''
    children = [subprocess.Popen([sys.executable, '-c', program, str(project)],
                cwd=Path(__file__).resolve().parents[1], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                for _ in range(2)]
    outcomes = []
    try:
        for child in children:
            stdout, stderr = child.communicate(timeout=30)
            assert child.returncode == 0, stderr.decode()
            outcomes.append(json.loads(stdout))
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.wait()
    assert sorted(row['claim'] for row in outcomes) == ['existing', 'new']
    assert outcomes[0]['action']['id'] == outcomes[1]['action']['id']
    observed = control.inspect(project, 'pilot')
    assert observed['actions_used'] == 1 and observed['spent_or_reserved'] == {'gpu_seconds': 5}


@pytest.mark.parametrize('change', ['negative-cost', 'reserved-actual', 'wrong-version'])
def test_corrupted_accounting_cannot_release_or_expand_budget(project, change):
    claim(project)
    def corrupt(metadata, state):
        if change == 'negative-cost':
            metadata['actions'][0]['reserved_costs']['gpu_seconds'] = -100
        elif change == 'reserved-actual':
            metadata['actions'][0]['actual_costs'] = {'gpu_seconds': 0}
        else:
            metadata['schema_version'] = 99
        return metadata
    run_state.update_coordination(str(project), 'pilot', corrupt)
    before = run_state.load_run(str(project), 'pilot')
    with pytest.raises(RegistryError):
        control.inspect(project, 'pilot')
    with pytest.raises(RegistryError):
        claim(project, action_key='another')
    assert run_state.load_run(str(project), 'pilot') == before


@pytest.fixture
def project(tmp_path):
    run_state.start_run(str(tmp_path), 'pilot', ['explore', 'analyse'], executor='gpt-6.1-sol')
    control.configure(tmp_path, 'pilot', 'Save an evidence-backed report', {
        'max_actions': 5, 'wall_seconds': 600, 'max_attempts_per_key': 2,
        'resources': {'gpu_seconds': 30}})
    return tmp_path


def claim(project, **changes):
    request = dict(action_key='compare', phase='explore', question='Does the control explain the effect?',
                   costs={'gpu_seconds': 10})
    request.update(changes)
    return control.claim_action(project, 'pilot', **request)


def result(project, name='result.json'):
    (project / name).write_text('{"effect":0}', encoding='utf-8')
    return fixed_ref(project, name)


def test_duplicate_claim_reserves_once_and_requires_reconciliation(project):
    first, again = claim(project), claim(project)
    assert first['claim'] == 'new' and again['claim'] == 'existing'
    assert first['action'] == again['action']
    observed = control.inspect(project, 'pilot')
    assert observed['status'] == 'RECONCILE'
    assert observed['actions_used'] == 1
    assert observed['spent_or_reserved'] == {'gpu_seconds': 10}
    with pytest.raises(RegistryError, match='RECONCILE'):
        claim(project, action_key='another')


def test_failed_attempts_retry_with_new_identity_and_stop_at_limit(project):
    first = claim(project)['action']
    control.finish_action(project, 'pilot', first['id'], 'failed', actual_costs={'gpu_seconds': 2}, reason='OOM')
    second = claim(project)['action']
    assert second['id'] != first['id'] and second['attempt'] == 2
    control.finish_action(project, 'pilot', second['id'], 'failed', actual_costs={'gpu_seconds': 3}, reason='OOM')
    before = run_state.load_run(str(project), 'pilot')
    with pytest.raises(RegistryError, match='retry limit'):
        claim(project)
    assert run_state.load_run(str(project), 'pilot') == before
    assert control.inspect(project, 'pilot')['spent_or_reserved']['gpu_seconds'] == 5


def test_spent_plus_reservation_cannot_exceed_budget(project):
    first = claim(project, costs={'gpu_seconds': 25})['action']
    control.finish_action(project, 'pilot', first['id'], 'failed', actual_costs={'gpu_seconds': 25}, reason='failed')
    with pytest.raises(RegistryError, match='Insufficient remaining'):
        claim(project)


def test_overrun_is_recorded_and_blocks_future_work(project):
    first = claim(project)['action']
    control.finish_action(project, 'pilot', first['id'], 'succeeded', actual_costs={'gpu_seconds': 31},
                          result_refs=[result(project)])
    observed = control.inspect(project, 'pilot')
    assert observed['status'] == 'BUDGET_EXCEEDED'
    assert observed['spent_or_reserved']['gpu_seconds'] == 31


def test_done_needs_review_and_same_family_policy_is_preserved(project):
    run_state.set_status(str(project), 'pilot', 'explore', 'done')
    assert control.inspect(project, 'pilot')['status'] == 'REVIEW_REQUIRED'
    run_state.mark_provisional(str(project), 'pilot', 'explore', 'review-1', 'gpt-6.1-sol')
    assert control.inspect(project, 'pilot')['status'] == 'REVIEW_REQUIRED'
    run_state.accept(str(project), 'pilot', 'explore', 'external-1', 'claude-opus-4-8')
    assert control.inspect(project, 'pilot')['phase']['phase'] == 'analyse'


def test_snapshot_transition_cannot_modify_phase_gate_or_policy(project):
    before = run_state.load_run(str(project), 'pilot')
    def attempt(metadata, state):
        state['phases'][0]['status'] = 'accepted'
        state['policy']['provisional_advances'] = True
        metadata['note'] = 'coordination-only'
        return metadata
    after = run_state.update_coordination(str(project), 'pilot', attempt)
    assert after['phases'] == before['phases'] and after['policy'] == before['policy']
    assert after['coordination']['note'] == 'coordination-only'


def test_completion_does_not_accept_phase_and_cannot_be_rewritten(project):
    action = claim(project)['action']
    refs = [result(project)]
    for _ in range(2):
        control.finish_action(project, 'pilot', action['id'], 'succeeded', actual_costs={'gpu_seconds': 3}, result_refs=refs)
    assert run_state.load_run(str(project), 'pilot')['phases'][0]['status'] == 'pending'
    with pytest.raises(RegistryError, match='history'):
        control.finish_action(project, 'pilot', action['id'], 'failed', actual_costs={'gpu_seconds': 3}, reason='changed mind')
    with pytest.raises(RegistryError, match='Completed action'):
        claim(project)


def test_changed_evidence_blocks_next_action(project):
    input_ref = result(project, 'input.json')
    action = claim(project, input_refs=[input_ref])['action']
    control.finish_action(project, 'pilot', action['id'], 'failed', actual_costs={'gpu_seconds': 1}, reason='failed')
    (project / 'input.json').write_text('{"effect":1}')
    assert control.inspect(project, 'pilot')['status'] == 'EVIDENCE_CHANGED'
    with pytest.raises(RegistryError, match='EVIDENCE_CHANGED'):
        claim(project, action_key='new')


def test_changed_question_does_not_reuse_reservation(project):
    claim(project)
    with pytest.raises(RegistryError, match='new action key'):
        claim(project, question='A different mechanism?')


def test_expired_contract_does_not_reset_on_reconfigure(project):
    def age(metadata, state):
        metadata['started_at'] = (datetime.now(timezone.utc) - timedelta(seconds=700)).isoformat()
        return metadata
    run_state.update_coordination(str(project), 'pilot', age)
    assert control.inspect(project, 'pilot')['status'] == 'BUDGET_EXHAUSTED'
    with pytest.raises(RegistryError, match='fixed'):
        control.configure(project, 'pilot', 'New finish line', {'max_actions': 50, 'wall_seconds': 999,
                          'max_attempts_per_key': 2, 'resources': {'gpu_seconds': 300}})


def test_stop_preserves_live_reservation_and_then_blocks(project):
    action = claim(project)['action']
    control.stop(project, 'pilot', 'User ended this direction')
    assert control.inspect(project, 'pilot')['status'] == 'RECONCILE'
    control.finish_action(project, 'pilot', action['id'], 'cancelled', actual_costs={'gpu_seconds': 1}, reason='process confirmed stopped')
    assert control.inspect(project, 'pilot')['status'] == 'STOPPED'
    assert control.inspect(project, 'pilot')['host_goal_modified'] is False


def test_zero_gpu_budget_allows_a_cpu_investigation(tmp_path):
    run_state.start_run(str(tmp_path), 'cpu', ['inspect'])
    control.configure(tmp_path, 'cpu', 'Inspect existing results', {'max_actions': 2, 'wall_seconds': 30,
                      'max_attempts_per_key': 1, 'resources': {'gpu_seconds': 0}})
    action = control.claim_action(tmp_path, 'cpu', 'read', 'inspect', 'What do the records show?', costs={'gpu_seconds': 0})
    assert action['claim'] == 'new'


def test_read_only_inspection_does_not_initialize_project(tmp_path):
    with pytest.raises(FileNotFoundError):
        control.inspect(tmp_path, 'missing')
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('value', [True, -1, float('nan'), float('inf')])
def test_invalid_resource_bounds_do_not_mutate_run(tmp_path, value):
    run_state.start_run(str(tmp_path), 'pilot', ['inspect'])
    before = (tmp_path / '.ei/runs/pilot.json').read_bytes()
    with pytest.raises(RegistryError):
        control.configure(tmp_path, 'pilot', 'Inspect', {'max_actions': 2, 'wall_seconds': 30,
                          'max_attempts_per_key': 1, 'resources': {'gpu_seconds': value}})
    assert (tmp_path / '.ei/runs/pilot.json').read_bytes() == before


def test_terminal_workflow_is_distinct_from_scientific_acceptance(project):
    for phase in ('explore', 'analyse'):
        run_state.set_status(str(project), 'pilot', phase, 'skipped')
    result = control.inspect(project, 'pilot')
    assert result['status'] == 'WORKFLOW_TERMINAL'
    assert result['scientific_verdict'] == 'not-assessed'
