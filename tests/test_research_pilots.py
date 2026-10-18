"""Exercise actual CPU fits, paired outputs, evidence and recovery bookkeeping."""
import csv
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

import pytest

from tools import research_control as control, run_state
from tools.registry_common import fixed_ref, RegistryError, verify_ref
from tools.research_memory import retrieve

PILOT = Path(__file__).parent / 'research_pilots/run_study.py'


def test_action_uses_original_execution_snapshot_and_terminal_receipt(tmp_path):
    from tests.governance_helpers import make_environment, make_sources, make_spec
    from tools.execution_registry import freeze_snapshot, start_execution, launch_execution, inspect_terminal
    sources, spec, environment = make_sources(tmp_path), make_spec(tmp_path), make_environment(tmp_path)
    run_state.start_run(str(tmp_path), 'existing-workflow', ['pilot'], executor='gpt-6.1-sol')
    control.configure(tmp_path, 'existing-workflow', 'Collect the existing CPU execution evidence', {
        'max_actions': 2, 'wall_seconds': 60, 'max_attempts_per_key': 1,
        'resources': {'gpu_seconds': 0, 'process_wall_seconds': 30}})
    snapshot = freeze_snapshot(tmp_path, 'cpu-attempt-1', spec, environment, sources,
        {'variant': {'augmentation': 0.1}, 'seed': 22}, 'src/train.py', 'method-b', 22)
    start_execution(tmp_path, 'cpu-attempt-1', snapshot, workflow_run_id='existing-workflow')
    request = dict(action_key='measure', phase='pilot', question='Does the declared pilot run?',
        costs={'gpu_seconds': 0, 'process_wall_seconds': 15}, input_refs=[spec, snapshot])
    claimed = control.claim_action(tmp_path, 'existing-workflow', **request)
    original = run_state.load_run(str(tmp_path), 'existing-workflow')
    # A second controller after an interruption finds the same reservation and
    # the original execution identity through its pinned snapshot, not a new DB.
    assert control.claim_action(tmp_path, 'existing-workflow', **request)['claim'] == 'existing'
    assert original['coordination']['actions'][0]['input_refs'][-1] == snapshot
    started = time.monotonic()
    result = launch_execution(tmp_path, 'cpu-attempt-1',
        [str(tmp_path / 'runs/cpu-attempt-1/outputs/metrics.json')], timeout=15)
    elapsed = time.monotonic() - started
    terminal, reference = inspect_terminal(tmp_path, 'cpu-attempt-1')
    assert terminal['workflow_run_id'] == 'existing-workflow' and result['exit_code'] == 0
    control.finish_action(tmp_path, 'existing-workflow', claimed['action']['id'], 'succeeded',
        actual_costs={'gpu_seconds': 0, 'process_wall_seconds': elapsed}, result_refs=[reference])
    with pytest.raises(RegistryError, match='only once'):
        launch_execution(tmp_path, 'cpu-attempt-1')
    assert control.inspect(tmp_path, 'existing-workflow')['actions_used'] == 1
    assert run_state.load_run(str(tmp_path), 'existing-workflow')['phases'][0]['status'] == 'pending'


@pytest.mark.parametrize('scenario, expected', [
    ('positive', 'supported-in-synthetic-setting'), ('negative', 'negative-in-synthetic-setting'),
    ('pivot', 'pivot-with-original-not-supported')])
def test_real_cpu_study_preserves_measurements_cases_decisions_and_original_gate(tmp_path, scenario, expected):
    run_state.start_run(str(tmp_path), scenario, ['pilot'], executor='gpt-6.1-sol')
    control.configure(tmp_path, scenario, 'Save measured results, paired cases and the scoped decision', {
        'max_actions': 2, 'wall_seconds': 60, 'max_attempts_per_key': 1,
        'resources': {'gpu_seconds': 0, 'process_wall_seconds': 30}})
    request = dict(action_key='cpu-pilot', phase='pilot', question='Does this feature help on matched held-out data?',
                   costs={'gpu_seconds': 0, 'process_wall_seconds': 15})
    claim = control.claim_action(tmp_path, scenario, **request)
    assert control.claim_action(tmp_path, scenario, **request)['claim'] == 'existing'
    run_state.set_status(str(tmp_path), scenario, 'pilot', 'running')
    started = time.monotonic()
    completed = subprocess.run([sys.executable, str(PILOT), '--output', str(tmp_path / 'study'),
                                '--scenario', scenario], capture_output=True, timeout=15, text=True)
    elapsed = time.monotonic() - started
    assert completed.returncode == 0, completed.stderr
    report = json.loads((tmp_path / 'study/results.json').read_text())
    assert report['decision'] == expected and report['review_status'] == 'not-reviewed'
    rows = list(csv.DictReader((tmp_path / 'study/predictions.csv').open(newline='')))
    for study in report['studies']:
        for metrics in study['seeds']:
            group = [row for row in rows if row['feature'] == study['feature'] and int(row['seed']) == metrics['seed']]
            assert len(group) == metrics['test_count'] == 256
            actual = statistics.mean((float(row['prediction']) - float(row['target'])) ** 2 for row in group)
            assert actual == pytest.approx(metrics['method_mse'])
    if scenario == 'pivot':
        assert not report['original_claim_supported']
        assert report['studies'][0]['mean_delta_mse'] > -0.1
        assert report['studies'][1]['mean_delta_mse'] < -0.1
    cases = json.loads((tmp_path / 'study/cases.json').read_text())
    assert cases['population'] == len(rows) and len(cases['typical']) == 3
    references = [fixed_ref(tmp_path, 'study/' + name) for name in (
        'results.json', 'predictions.csv', 'cases.json', 'DECISIONS.md')]
    control.finish_action(tmp_path, scenario, claim['action']['id'], 'succeeded',
                          actual_costs={'gpu_seconds': 0, 'process_wall_seconds': elapsed}, result_refs=references)
    run_state.attach_references(str(tmp_path), scenario, 'pilot', artifact_refs=references)
    run_state.set_status(str(tmp_path), scenario, 'pilot', 'done', artifact='study/results.json')
    assert control.inspect(tmp_path, scenario)['status'] == 'REVIEW_REQUIRED'
    assert all(verify_ref(tmp_path, ref).is_file() for ref in references)
    recalled = retrieve(tmp_path, 'pilot decision original', ['study/DECISIONS.md'])
    assert recalled['matches'] and recalled['matches'][0]['evidence_status'] == 'unbound'
    with pytest.raises(RegistryError, match='Completed action'):
        control.claim_action(tmp_path, scenario, **request)
    assert run_state.load_run(str(tmp_path), scenario)['phases'][0]['status'] == 'done'
