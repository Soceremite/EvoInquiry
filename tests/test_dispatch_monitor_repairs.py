"""Behavioral regressions for the 1.6.3 audit: disposable CPU children only."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time

import pytest

from tests.governance_helpers import make_environment, make_sources, make_spec
from tests.test_execution_governance import _await_file, _prepare_review_worker
from tests.test_governed_queue import queue, queued_job
from tests.test_resource_budget import observation, requirements, GIB
from tools import execution_registry as execution, research_control, resource_budget, run_state
from tools.registry_common import atomic_write, read_record


@pytest.mark.parametrize('hold', ['review', 'stop'])
def test_hold_committed_during_resource_check_prevents_actual_dispatch(tmp_path, monkeypatch, hold):
    args, output, _ = _prepare_review_worker(tmp_path)
    original = execution.check_execution_resources

    def late_hold(*values):
        result = original(*values)
        if hold == 'stop':
            research_control.stop(tmp_path, 'review-workflow', 'Do not dispatch new work')
        else:
            research_control.require_reflection(tmp_path, 'review-workflow', ['Review before dispatch'])
        return result

    monkeypatch.setattr(execution, 'check_execution_resources', late_hold)
    with pytest.raises(execution.DispatchDeferred) as failure:
        execution.launch_execution(tmp_path, 'review-worker', args)
    assert failure.value.result['status'] == ('WORKFLOW_STOPPED' if hold == 'stop' else 'WAIT_REVIEW')
    directory = output.parent
    assert read_record(directory / 'execution.json')['status'] == 'prepared'
    assert not (directory / 'process.json').exists() and not output.exists()


def test_coordination_update_serializes_with_process_creation_then_preserves_live_training(tmp_path, monkeypatch):
    args, output, _ = _prepare_review_worker(tmp_path)
    original = execution.subprocess.Popen
    updates = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        def popen(*values, **kwargs):
            if 'start_new_session' in kwargs:
                update = pool.submit(research_control.require_reflection, tmp_path, 'review-workflow',
                                     ['Review after the dispatch already in progress'])
                updates.append(update)
                time.sleep(0.15)
                assert not update.done(), 'A control writer must not commit between final check and Popen'
            return original(*values, **kwargs)
        monkeypatch.setattr(execution.subprocess, 'Popen', popen)
        future = pool.submit(execution.launch_execution, tmp_path, 'review-worker', args)
        try:
            _await_file(output / 'ready.json', future)
            updates[0].result(timeout=5)
            assert not future.done()
            assert research_control.execution_directive(tmp_path, 'review-workflow')['reflection_gate']
        finally:
            output.mkdir(parents=True, exist_ok=True)
            (output / 'release').touch()
            result = future.result(timeout=15)
    assert result['exit_code'] == 0 and not (output.parent / 'termination.json').exists()


def test_late_review_queue_deferral_resumes_same_attempt_without_spending_retry(tmp_path, monkeypatch):
    run_state.start_run(str(tmp_path), 'queue-review', ['explore'])
    research_control.configure(tmp_path, 'queue-review', 'Review queue', {
        'max_actions': None, 'wall_seconds': None, 'max_attempts_per_key': 1, 'resources': {}})
    job = queued_job(tmp_path, workflow_run_id='queue-review')
    gate = research_control.require_reflection(tmp_path, 'queue-review', ['Review next comparison'],
                                               kind='checkpoint')['reflection_gate']
    with pytest.raises(execution.DispatchDeferred):
        execution.launch_execution(tmp_path, job['execution']['execution_run_id'], job['execution']['arguments'])
    job.update(status='running', attempts=1, phase='explore')
    manifest = {'cwd': str(tmp_path), 'gpus': [0], 'max_parallel': 1,
                'phases': [{'name': 'explore', 'depends_on': [], 'jobs': [{'id': job['id']}]}]}
    state = {'meta': {}, 'jobs': [job], 'phases': [{'name': 'explore', 'depends_on': [], 'status': 'active'}]}
    monkeypatch.setattr(queue, 'screen_exists', lambda *a: False)
    monkeypatch.setattr(queue, 'resolve_conda_hook', lambda *a: '')
    monkeypatch.setattr(queue, 'free_gpus', lambda *a: [0])
    monkeypatch.setattr(queue, 'launch_job', lambda *a: pytest.fail('Pending review cannot dispatch a screen'))
    queue.step(manifest, state, str(tmp_path / 'queue-state.json'), str(tmp_path))
    assert job['status'] == 'pending' and job['attempts'] == 0
    assert job['execution']['execution_run_id'] == 'queue-attempt-1'
    # Complete the real review using its own run identity, then launch the same snapshot.
    research_control.record_reflection(tmp_path, 'queue-review', 'explore', {
        'schema_version':1, 'kind':gate['kind'], 'gate_id':gate['id'], 'decision':'CONTINUE',
        'reason':'Checked the frozen comparison and resource evidence',
        'evidence_refs':['runs/queue-attempt-1/snapshot/manifest.json'],
        'next_action':{'skill':'run-experiment', 'description':'Dispatch original authorized comparison'}})
    completed = subprocess.run(shlex.split(queue.governed_launch_command(job)),
                               capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stderr
    assert queue.job_status_check(job, str(tmp_path), str(tmp_path)) == ('completed', None)
    assert job['execution']['execution_run_id'] == 'queue-attempt-1'


@pytest.mark.parametrize('alive', [True, None])
def test_missing_screen_never_settles_a_live_or_unknown_pid_from_partial_output(tmp_path, monkeypatch, alive):
    partial = tmp_path / 'partial.json'
    partial.write_text('{"partial":true}')
    job = {'id': 'partial', 'screen_name': 'missing', 'pid': 12345, 'expected_output': str(partial)}
    monkeypatch.setattr(queue, 'screen_exists', lambda *a: False)
    monkeypatch.setattr(queue, '_process_alive', lambda *a: alive)
    assert queue.job_status_check(job, str(tmp_path), str(tmp_path)) == ('running', None)


def test_missing_screen_protects_an_actual_live_cpu_child(tmp_path, monkeypatch):
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(0.6)'])
    try:
        monkeypatch.setattr(queue, 'screen_exists', lambda *a: False)
        (tmp_path / 'partial').touch()
        job = {'id': 'live', 'screen_name': 'missing', 'pid': child.pid, 'expected_output': str(tmp_path/'partial')}
        assert queue.job_status_check(job, str(tmp_path), str(tmp_path)) == ('running', None)
    finally:
        child.wait(timeout=5)
    assert queue.job_status_check(job, str(tmp_path), str(tmp_path))[0] == 'failed_other'


@pytest.mark.skipif(shutil.which('bash') is None, reason='Legacy screen wrapper requires bash')
@pytest.mark.parametrize('code,output,expected', [(0, True, 'completed'), (7, True, 'failed_other'),
                                               (0, False, 'failed_other')])
def test_real_tee_wrapper_keeps_trainer_exit_and_checks_expected_output(tmp_path, monkeypatch, code, output, expected):
    result = tmp_path / 'result.json'
    program = ('from pathlib import Path; Path(' + repr(str(result)) + ').write_text("partial"); ' if output else '')
    program += f'raise SystemExit({code})'
    command = shlex.join([sys.executable, '-c', program])
    job = {'id': 'pipeline', 'screen_name': None, 'pid': None, 'expected_output': str(result)}
    shell = queue.job_shell(job, command, str(tmp_path), str(tmp_path/'pipeline.log'))
    process = subprocess.run(['bash', '-c', shell], capture_output=True, text=True, timeout=10)
    assert process.returncode == code, process.stderr
    receipt = read_record(job['exit_receipt'])
    assert receipt['trainer_exit_code'] == code and receipt['log_exit_code'] == 0
    monkeypatch.setattr(queue, 'screen_exists', lambda *a: False)
    assert queue.job_status_check(job, str(tmp_path), str(tmp_path))[0] == expected
    # A receipt from another launch cannot complete this attempt.
    job['launch_token'] = 'different-attempt'
    assert queue.job_status_check(job, str(tmp_path), str(tmp_path))[0] == 'failed_other'


@pytest.mark.parametrize('process_ids,utilization,expected', [([], 0, 'AUTO_APPROVED'), ([123], 0, 'WAIT_RESOURCE'),
    (None, 0, 'NEEDS_ESTIMATE'), ([], 3, 'WAIT_RESOURCE')])
def test_exclusive_gpu_uses_occupants_including_idle_contexts_not_driver_memory(tmp_path, process_ids, utilization, expected):
    table = resource_budget.select(tmp_path, 'session-a', preset='exclusive', selected_by='fixture-user')
    hardware = observation(tmp_path)
    hardware['gpus'][0].update(used_bytes=8*1024**2, free_bytes=24*GIB-8*1024**2,
                               utilization_percent=utilization, process_ids=process_ids)
    request = requirements(tmp_path, gpus=[{'id': '0', 'peak_bytes': GIB}])
    assert resource_budget.evaluate(table, request, hardware, stage='launch')['status'] == expected


def test_gpu_probe_reads_compute_and_graphics_process_inventory(monkeypatch):
    def probe(command, **kwargs):
        value = ('0, GPU-0, 24576, 8, 24568, 0\n1, GPU-1, 24576, 8, 24568, 0\n' if '--query-gpu=' in ' '.join(command)
                 else '<nvidia_smi_log><gpu><uuid>GPU-0</uuid><processes/></gpu><gpu><uuid>GPU-1</uuid>'
                      '<processes><process_info><pid>321</pid><type>G</type></process_info></processes></gpu></nvidia_smi_log>')
        return subprocess.CompletedProcess(command, 0, value, '')
    monkeypatch.delenv('CUDA_VISIBLE_DEVICES', raising=False)
    monkeypatch.setattr(resource_budget.subprocess, 'run', probe)
    devices, error = resource_budget._gpus()
    assert error is None and devices[0]['process_ids'] == [] and devices[1]['process_ids'] == [321]


def test_parent_only_stop_cannot_release_a_process_tree_lease(tmp_path, monkeypatch):
    job = queued_job(tmp_path)
    finished = subprocess.run(shlex.split(queue.governed_launch_command(job)),
                              capture_output=True, text=True, timeout=30)
    assert finished.returncode == 0, finished.stderr
    directory = tmp_path/'runs/queue-attempt-1'
    atomic_write(directory/'termination.json', {'termination_scope':'windows-parent-only'})
    job['status'] = 'completed'
    monkeypatch.setattr(queue, 'screen_exists', lambda *a: False)
    queue.release_governed_lease(job)
    assert job['lease_release'] == 'protected-needs-process-tree-reconciliation'
    assert read_record(tmp_path/'.ei/leases/queue-lease.json')['status'] == 'queued'


def test_missing_or_mismatched_checkpoint_receipt_cannot_claim_a_successful_save(tmp_path):
    directory = tmp_path/'runs/save'
    directory.mkdir(parents=True)
    record = {'execution_run_id':'save', 'snapshot_ref':{'path':'snapshot', 'sha256':'0'*64}}
    configuration = {'stop_protocol':{'mode':'checkpoint_then_stop', 'receipt_path':'runs/save/receipt.json'}}
    assert execution._checkpoint_stop_evidence(tmp_path, record, configuration)['checkpoint_saved'] is False
    atomic_write(directory/'receipt.json', {'execution_run_id':'another-run', 'validation':{'passed':True}})
    evidence = execution._checkpoint_stop_evidence(tmp_path, record, configuration)
    assert evidence['status'] == 'unverified' and evidence['checkpoint_saved'] is False


@pytest.mark.parametrize('malformed', [False, True])
def test_existing_execution_observer_consumes_first_step_clock_and_keeps_running(tmp_path, malformed):
    sources, spec, environment = make_sources(tmp_path), make_spec(tmp_path), make_environment(tmp_path)
    resource_budget.select(tmp_path, 'clock-session', preset='custom', selected_by='fixture-user',
        overrides={'auto_approve_job_seconds': 0.6, 'job_notice_after_seconds': 0.15})
    (tmp_path/'src/train.py').write_text('''import datetime, json, pathlib, sys, time
output=pathlib.Path(sys.argv[1]); output.mkdir(parents=True, exist_ok=True)
(output/'preparing').touch(); time.sleep(0.45)
record={'schema_version':1,'experiment_id':'clock-experiment','segments':[]}
record['segments'].append({'attempt_id':'clock-worker','first_step_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ended_at':None})
if MALFORMED: record['segments'][0]['first_step_at']='invalid'
def save():
    temp=output/'clock.tmp'; temp.write_text(json.dumps(record)); temp.replace(output/'clock.json')
save(); (output/'first-step').touch()
deadline=time.monotonic()+1.5
while time.monotonic()<deadline: time.sleep(0.02)
if not MALFORMED: record['segments'][0]['ended_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
save(); (output/'metrics.json').write_text('{}')
'''.replace('MALFORMED', repr(malformed)))
    arguments = [str(tmp_path/'runs/clock-worker/outputs')]
    configuration = {'variant': {'augmentation':0.1}, 'seed':22,
        'resource_budget': {'session_id':'clock-session', 'request':requirements(tmp_path, job_seconds=0.02)},
        'training_clock': {'path':'runs/clock-worker/outputs/clock.json', 'experiment_id':'clock-experiment'}}
    snapshot = execution.freeze_snapshot(tmp_path, 'clock-worker', spec, environment, sources, configuration,
                                        'src/train.py', 'method-b', 22, arguments=arguments, output_argument_indices=[0])
    execution.start_execution(tmp_path, 'clock-worker', snapshot)
    output = Path(arguments[0]); observations = output.parent/'training-budget-observations.json'
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(execution.launch_execution, tmp_path, 'clock-worker', arguments)
        _await_file(output/'preparing', future)
        assert not observations.exists(), 'Preparation must not consume training time'
        _await_file(observations, future)
        deadline = time.monotonic()+5
        wanted = 'INVALID_TRAINING_CLOCK' if malformed else 'NEEDS_APPROVAL'
        while time.monotonic()<deadline:
            report = read_record(observations)
            if report['latest']['status'] == wanted:
                break
            time.sleep(0.03)
        assert report['latest']['status'] == wanted and not future.done()
        result = future.result(timeout=10)
    report = read_record(observations)
    statuses = [row['status'] for row in report['notices']]
    assert statuses.count(wanted) == 1
    assert all(row['process_interrupted'] is False for row in report['notices'])
    assert result['exit_code'] == 0 and not (output.parent/'termination.json').exists()
    if not malformed:
        assert statuses == ['NOTICE_CONTINUE', 'NEEDS_APPROVAL']
        assert report['latest']['training_state'] == 'ended'
        assert 1.3 < report['latest']['seconds'] < 2.5


@pytest.mark.skipif(os.name != 'posix', reason='Cooperative SIGTERM checkpoint fixture is POSIX')
def test_checkpoint_stop_waits_for_a_real_slow_save_and_validates_its_receipt(tmp_path):
    sources, spec, environment = make_sources(tmp_path), make_spec(tmp_path), make_environment(tmp_path)
    (tmp_path/'src/train.py').write_text('''import hashlib, json, pathlib, signal, sys, time
output=pathlib.Path(sys.argv[1]); output.mkdir(parents=True, exist_ok=True)
directory=output.parent; project=directory.parent.parent
def fixed(path): return {'path':path.relative_to(project).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def stop(signum, frame):
    (output/'saving').touch(); time.sleep(6)
    checkpoint=output/'latest.json'; checkpoint.write_text(json.dumps({'step':42}))
    assert json.loads(checkpoint.read_text())['step']==42
    receipt={'execution_run_id':'slow-save','snapshot_ref':fixed(directory/'snapshot/manifest.json'),
             'checkpoint_ref':fixed(checkpoint),'validation':{'passed':True,'label':'json-loader'}}
    (output/'save-receipt.json').write_text(json.dumps(receipt))
    raise SystemExit(0)
signal.signal(signal.SIGTERM,stop); (output/'ready').touch()
deadline=time.monotonic()+15
while time.monotonic()<deadline: time.sleep(0.02)
''')
    arguments = [str(tmp_path/'runs/slow-save/outputs')]
    snapshot = execution.freeze_snapshot(tmp_path, 'slow-save', spec, environment, sources,
        {'variant':{'augmentation':0.1}, 'seed':22,
         'stop_protocol': {'mode':'checkpoint_then_stop', 'receipt_path':'runs/slow-save/outputs/save-receipt.json'}},
        'src/train.py', 'method-b', 22, arguments=arguments, output_argument_indices=[0])
    execution.start_execution(tmp_path, 'slow-save', snapshot)
    output = Path(arguments[0])
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(execution.launch_execution, tmp_path, 'slow-save', arguments)
        _await_file(output/'ready', future)
        started = time.monotonic()
        execution.request_stop_execution(tmp_path, 'slow-save', 'Save and stop this disposable fixture',
                                         confirmed_by='fixture-user-save-stop-choice')
        result = future.result(timeout=12)
    receipt = read_record(output.parent/'termination.json')
    assert time.monotonic()-started >= 6
    assert receipt['force_used'] is False and receipt['checkpoint_stop']['status'] == 'verified'
    assert read_record(output/'latest.json')['step'] == 42
    assert result['exit_code'] == 0
    assert read_record(output.parent/'execution.final.json')['status'] == 'stopped'
