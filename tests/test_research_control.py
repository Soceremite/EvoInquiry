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


def clock(monkeypatch):
    current = [datetime(2025, 1, 1, tzinfo=timezone.utc)]
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return current[0].astimezone(tz) if tz else current[0].replace(tzinfo=None)
    monkeypatch.setattr(control, 'datetime', Clock)
    return current


def timed_run(tmp_path, start):
    run_state.start_run(str(tmp_path), 'timed', ['explore'])
    limits = {'max_actions': 4, 'wall_seconds': 100, 'max_attempts_per_key': 1,
              'resources': {'gpu_seconds': 0}}
    control.configure(tmp_path, 'timed', 'Save observations before the deadline', limits,
                      started_at=start.isoformat(), closeout_seconds=20)
    return limits


def test_closeout_blocks_new_dispatch_without_changing_phases(tmp_path, monkeypatch):
    current = clock(monkeypatch)
    timed_run(tmp_path, current[0])
    current[0] += timedelta(seconds=79)
    inspection = control.inspect(tmp_path, 'timed')
    assert inspection['status'] == 'READY'
    assert inspection['timing']['dispatch_seconds_remaining'] == 1
    current[0] += timedelta(seconds=1)
    before = (tmp_path / '.ei/runs/timed.json').read_bytes()
    inspection = control.inspect(tmp_path, 'timed')
    assert inspection['status'] == 'CLOSEOUT_REQUIRED'
    assert inspection['timing']['remaining_seconds'] == 20
    assert inspection['timing']['dispatch_seconds_remaining'] == 0
    with pytest.raises(RegistryError, match='CLOSEOUT_REQUIRED'):
        control.claim_action(tmp_path, 'timed', 'late', 'explore', 'Another fit?', costs={'gpu_seconds': 0})
    assert (tmp_path / '.ei/runs/timed.json').read_bytes() == before


def test_closeout_keeps_real_execution_reconciliation_and_allows_finish(tmp_path, monkeypatch):
    current = clock(monkeypatch)
    timed_run(tmp_path, current[0])
    action = control.claim_action(tmp_path, 'timed', 'fit', 'explore', 'Check a fit', costs={'gpu_seconds': 0})['action']
    current[0] += timedelta(seconds=85)
    assert control.inspect(tmp_path, 'timed')['status'] == 'RECONCILE'
    control.finish_action(tmp_path, 'timed', action['id'], 'failed', actual_costs={'gpu_seconds': 0},
                          reason='Actual process exited with failure')
    assert control.inspect(tmp_path, 'timed')['status'] == 'CLOSEOUT_REQUIRED'
    run_state.set_status(str(tmp_path), 'timed', 'explore', 'done')
    assert control.inspect(tmp_path, 'timed')['status'] == 'REVIEW_REQUIRED'
    current[0] += timedelta(seconds=15)
    assert control.inspect(tmp_path, 'timed')['status'] == 'BUDGET_EXHAUSTED'


def test_configuring_late_uses_original_start_and_never_renews_it(tmp_path, monkeypatch):
    current = clock(monkeypatch)
    original = current[0] - timedelta(seconds=90)
    limits = timed_run(tmp_path, original)
    initial = run_state.load_run(str(tmp_path), 'timed')['coordination']
    assert control.inspect(tmp_path, 'timed')['timing']['remaining_seconds'] == 10
    assert initial['configured_at'] != initial['started_at']
    current[0] += timedelta(seconds=20)
    control.configure(tmp_path, 'timed', initial['objective'], limits)
    assert run_state.load_run(str(tmp_path), 'timed')['coordination'] == initial
    assert control.inspect(tmp_path, 'timed')['status'] == 'BUDGET_EXHAUSTED'
    for changes in ({'started_at': current[0].isoformat()}, {'closeout_seconds': 0}):
        with pytest.raises(RegistryError, match='fixed'):
            control.configure(tmp_path, 'timed', initial['objective'], limits, **changes)
    assert run_state.load_run(str(tmp_path), 'timed')['coordination'] == initial


def test_legacy_contract_without_timing_options_keeps_zero_reserve(project):
    def legacy(metadata, state):
        metadata.pop('closeout_seconds', None)
        metadata.pop('configured_at', None)
        return metadata
    run_state.update_coordination(str(project), 'pilot', legacy)
    initial = run_state.load_run(str(project), 'pilot')['coordination']
    control.configure(project, 'pilot', initial['objective'], initial['limits'])
    assert run_state.load_run(str(project), 'pilot')['coordination'] == initial
    assert control.inspect(project, 'pilot')['timing']['closeout_seconds'] == 0


@pytest.mark.parametrize('start', ['2025-01-01T00:00:00', '2025-01-01T00:00:01Z', True])
def test_invalid_original_clock_cannot_mutate_run(tmp_path, monkeypatch, start):
    clock(monkeypatch)
    run_state.start_run(str(tmp_path), 'pilot', ['explore'])
    before = (tmp_path / '.ei/runs/pilot.json').read_bytes()
    with pytest.raises(RegistryError, match='timezone-aware'):
        control.configure(tmp_path, 'pilot', 'Inspect', {'max_actions': 1, 'wall_seconds': 100,
                          'max_attempts_per_key': 1, 'resources': {}}, started_at=start)
    assert (tmp_path / '.ei/runs/pilot.json').read_bytes() == before


@pytest.mark.parametrize('reserve', [True, -1, 101, float('nan')])
def test_invalid_closeout_cannot_mutate_run(tmp_path, reserve):
    run_state.start_run(str(tmp_path), 'pilot', ['explore'])
    before = (tmp_path / '.ei/runs/pilot.json').read_bytes()
    with pytest.raises(RegistryError):
        control.configure(tmp_path, 'pilot', 'Inspect', {'max_actions': 1, 'wall_seconds': 100,
                          'max_attempts_per_key': 1, 'resources': {}}, closeout_seconds=reserve)
    assert (tmp_path / '.ei/runs/pilot.json').read_bytes() == before


def prepared_execution(project, *, execution_id='cpu-1', workflow_run_id='pilot', exit_code=0):
    """Real registered child with deliberately list-valued attempt evidence."""
    from tests.governance_helpers import make_environment, make_spec
    from tools.execution_registry import freeze_snapshot, start_execution
    environment = make_environment(project)
    spec = make_spec(project)
    source = project / 'src/study.py'
    source.parent.mkdir(exist_ok=True)
    source.write_text('''import json, pathlib, sys, time
if sys.argv[2] == 'stop':
    time.sleep(20)
pathlib.Path(sys.argv[1]).write_text(json.dumps([{'slot': 1}, {'slot': 2}]))
raise SystemExit(int(sys.argv[2]))
''')
    arguments = [str(project / 'runs' / execution_id / 'attempts.json'), str(exit_code)]
    configuration = {'variant': {'augmentation': 0}, 'seed': 11}
    if exit_code == 'stop':
        configuration['stop_authorization'] = {
            'confirmed_by': 'fixture-user-approved-timeout', 'conditions': ['timeout']}
    snapshot = freeze_snapshot(project, execution_id, spec, environment, ['src/study.py'],
                               configuration, 'src/study.py', 'baseline', 11,
                               arguments=arguments, output_argument_indices=[0])
    start_execution(project, execution_id, snapshot, workflow_run_id=workflow_run_id)
    return snapshot, arguments


@pytest.mark.parametrize('exit_code,expected', [(0, 'succeeded'), (7, 'failed')])
def test_registered_terminal_settlement_handles_list_outputs_and_keeps_gates(project, exit_code, expected):
    from tools.execution_registry import launch_execution
    from tools.registry_common import read_record
    snapshot, arguments = prepared_execution(project, exit_code=exit_code)
    action = claim(project, input_refs=[snapshot])['action']
    terminal = launch_execution(project, 'cpu-1', arguments, timeout=15)
    assert terminal['exit_code'] == exit_code
    attempts = fixed_ref(project, 'runs/cpu-1/attempts.json')
    # The record helper stays strict; settlement verifies arbitrary file bytes
    # without assuming that the scientific payload is an object.
    with pytest.raises(RegistryError, match='Expected an object'):
        read_record(project / attempts['path'])
    request = dict(actual_costs={'gpu_seconds': 0}, result_refs=[attempts])
    phases = run_state.load_run(str(project), 'pilot')['phases']
    first = control.settle_execution(project, 'pilot', action['id'], 'cpu-1', **request)
    again = control.settle_execution(project, 'pilot', action['id'], 'cpu-1', **request)
    assert again == first
    settled = first['actions'][0]
    assert settled['status'] == expected and settled['actual_costs'] == {'gpu_seconds': 0}
    assert settled['result_refs'] == [terminal['execution_ref'], attempts]
    assert control.inspect(project, 'pilot')['unresolved_actions'] == []
    assert run_state.load_run(str(project), 'pilot')['phases'] == phases
    assert control.inspect(project, 'pilot')['scientific_verdict'] == 'not-assessed'
    with pytest.raises(RegistryError, match='history'):
        control.settle_execution(project, 'pilot', action['id'], 'cpu-1', actual_costs={'gpu_seconds': 1})


@pytest.mark.parametrize('mismatch', ['workflow', 'snapshot', 'missing-terminal', 'changed-output', 'changed-input'])
def test_settlement_cannot_attach_wrong_or_unverified_execution(project, mismatch):
    from tools.execution_registry import launch_execution
    snapshot, arguments = prepared_execution(project, workflow_run_id='other' if mismatch == 'workflow' else 'pilot')
    action = claim(project, input_refs=[] if mismatch == 'snapshot' else [snapshot])['action']
    if mismatch != 'missing-terminal':
        launch_execution(project, 'cpu-1', arguments, timeout=15)
    if mismatch == 'changed-output':
        (project / 'runs/cpu-1/process.log').write_text('changed')
    if mismatch == 'changed-input':
        (project / 'runs/cpu-1/snapshot/src/study.py').write_text('changed')
    before = (project / '.ei/runs/pilot.json').read_bytes()
    with pytest.raises((RegistryError, FileNotFoundError)):
        control.settle_execution(project, 'pilot', action['id'], 'cpu-1', actual_costs={'gpu_seconds': 0})
    assert (project / '.ei/runs/pilot.json').read_bytes() == before


def test_settle_execution_cli_after_budget_expiry_does_not_relaunch_or_reset(project):
    from tools.execution_registry import launch_execution
    snapshot, arguments = prepared_execution(project)
    action = claim(project, input_refs=[snapshot])['action']
    launch_execution(project, 'cpu-1', arguments, timeout=15)
    def age(metadata, state):
        metadata['started_at'] = (datetime.now(timezone.utc) - timedelta(seconds=700)).isoformat()
        return metadata
    run_state.update_coordination(str(project), 'pilot', age)
    original_start = run_state.load_run(str(project), 'pilot')['coordination']['started_at']
    execution_before = (project / 'runs/cpu-1/execution.json').read_bytes()
    request = project / 'settle.json'
    request.write_text(json.dumps({'action_id': action['id'], 'execution_run_id': 'cpu-1',
                                  'actual_costs': {'gpu_seconds': 0},
                                  'result_refs': [fixed_ref(project, 'runs/cpu-1/attempts.json')]}))
    child = subprocess.run([sys.executable, '-m', 'tools.research_control', '--root', str(project),
                            '--run-id', 'pilot', 'settle-execution', '--request', str(request)],
                           cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout)['actions'][0]['status'] == 'succeeded'
    current = control.inspect(project, 'pilot')
    assert current['status'] == 'BUDGET_EXHAUSTED' and current['unresolved_actions'] == []
    assert current['timing']['started_at'] == original_start
    assert (project / 'runs/cpu-1/execution.json').read_bytes() == execution_before


def test_confirmed_timeout_can_settle_as_cancelled_without_claiming_success(project):
    from tools.execution_registry import launch_execution
    snapshot, arguments = prepared_execution(project, exit_code='stop')
    action = claim(project, input_refs=[snapshot])['action']
    terminal = launch_execution(project, 'cpu-1', arguments, timeout=.2)
    assert terminal['exit_code'] != 0
    settled = control.settle_execution(project, 'pilot', action['id'], 'cpu-1', actual_costs={'gpu_seconds': 0})
    assert settled['actions'][0]['status'] == 'cancelled'
    assert run_state.load_run(str(project), 'pilot')['phases'][0]['status'] == 'pending'


def test_two_recovery_processes_settle_one_terminal_action_idempotently(project):
    from tools.execution_registry import launch_execution
    snapshot, arguments = prepared_execution(project)
    action = claim(project, input_refs=[snapshot])['action']
    launch_execution(project, 'cpu-1', arguments, timeout=15)
    program = '''from tools.research_control import settle_execution
import json,sys
print(json.dumps(settle_execution(sys.argv[1], 'pilot', sys.argv[2], 'cpu-1', actual_costs={'gpu_seconds':0})))
'''
    children = [subprocess.Popen([sys.executable, '-c', program, str(project), action['id']],
                                cwd=Path(__file__).resolve().parents[1], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE) for _ in range(2)]
    results = []
    try:
        for child in children:
            stdout, stderr = child.communicate(timeout=30)
            assert child.returncode == 0, stderr.decode()
            results.append(json.loads(stdout))
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.wait()
    assert results[0] == results[1]
    assert control.inspect(project, 'pilot')['actions_used'] == 1
