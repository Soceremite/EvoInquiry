"""Exercise queue bindings with real CPU processes; no screen or GPU allocation."""
import importlib.util
import ctypes
from pathlib import Path
import shlex
import subprocess
import sys
from unittest.mock import Mock

import pytest

from tests.governance_helpers import consumer, make_environment, make_sources, make_spec
from tools.environment_registry import EnvironmentRegistry
from tools.execution_registry import freeze_snapshot, rebase_execution_output, start_execution, verify_snapshot
from tools.registry_common import read_record

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('governed_queue_fixture', ROOT / 'skills/experiment-queue/scripts/queue_manager.py')
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


def queued_job(root, failure=False, resource_binding=None):
    sources, spec_ref, environment = make_sources(root), make_spec(root), make_environment(root)
    run_id = 'queue-attempt-1'
    arguments = [str(root / 'runs' / run_id / 'outputs/metrics.json')]
    config = {'variant':{'augmentation':0.1},'seed':22,'inject_failure':failure}
    if resource_binding is not None:
        config['resource_budget'] = resource_binding
    snapshot = freeze_snapshot(root,run_id,spec_ref,environment,sources, config,
        'src/train.py','method-b',22,arguments=arguments,output_argument_indices=[0])
    start_execution(root,run_id,snapshot,job_ref='queue-job')
    registry = EnvironmentRegistry(root)
    binding = consumer(environment,'queue-job') | {'execution_run_id':run_id}
    registry.bind_consumer(binding)
    registry.acquire_lease('queue-job','queue-lease','queue-job',expires_at='2030-01-01T00:00:00Z')
    return {'id':'queue-job','status':'pending','attempts':0,'screen_name':None,
            'execution_attempts':[], 'expected_output':arguments[0], 'cmd':'python mutable-code.py',
            'execution':{'project_root':str(root),'registry_tools_dir':str(ROOT / 'tools'),
                         'registry_python':sys.executable,'execution_run_id':run_id,
                         'snapshot_ref':snapshot,'env_revision':environment,'arguments':arguments,
                         'consumer_id':'queue-job','lease_id':'queue-lease'}}


def test_queue_launch_uses_snapshot_and_terminal_process_releases_matching_lease(tmp_path,monkeypatch):
    job = queued_job(tmp_path)
    (tmp_path / 'src/train.py').write_text('raise RuntimeError("mutable checkout")')
    command = queue.governed_launch_command(job)
    assert 'mutable-code.py' not in command
    completed = subprocess.run(shlex.split(command),capture_output=True,text=True,timeout=25)
    assert completed.returncode==0, completed.stderr
    job.update(status='running',attempts=1)
    assert queue.job_status_check(job,str(tmp_path),str(tmp_path))==('completed',None)
    job['status']='completed'
    monkeypatch.setattr(queue,'screen_exists',lambda name:False)
    queue.release_governed_lease(job)
    assert read_record(tmp_path / '.ei/leases/queue-lease.json')['status']=='released'
    assert read_record(tmp_path / '.ei/consumers/queue-job.json')['lifecycle']=='completed'


def test_queue_rejects_parameter_drift_and_retry_allocation_is_recoverable(tmp_path):
    job = queued_job(tmp_path,failure=True)
    frozen = list(job['execution']['arguments'])
    job['execution']['arguments'].append('--undeclared-method-override')
    with pytest.raises(ValueError,match='arguments fixed'):
        queue.governed_launch_command(job)
    job['execution']['arguments']=frozen
    result = subprocess.run(shlex.split(queue.governed_launch_command(job)),capture_output=True,timeout=25)
    assert result.returncode==7
    job['attempts']=1
    command = queue.governed_launch_command(job)
    retry = job['execution']['execution_run_id']
    assert retry!='queue-attempt-1' and job['execution_attempts']==['queue-attempt-1',retry]
    assert read_record(tmp_path / 'runs' / retry / 'execution.json')['retry_of']=='queue-attempt-1'
    expected = str(tmp_path / 'runs' / retry / 'outputs/metrics.json')
    assert job['expected_output'] == expected
    assert job['execution']['arguments'] == [expected]
    assert verify_snapshot(tmp_path, job['execution']['snapshot_ref'])['arguments'] == [expected]
    assert read_record(tmp_path / 'runs/queue-attempt-1/execution.final.json')['exit_code'] == 7
    assert queue.governed_launch_command(job)==command
    assert read_record(tmp_path / '.ei/leases/queue-lease.json')['status']=='queued'


@pytest.mark.parametrize('value,expected', [
    ('runs/failed/outputs/*.json', 'runs/retry/outputs/*.json'),
    ('/project with spaces/runs/failed/outputs/metrics.json',
     '/project with spaces/runs/retry/outputs/metrics.json'),
    (r'C:\Research project\runs\failed\outputs\metrics.json',
     r'C:\Research project\runs\retry\outputs\metrics.json'),
    ('C:/Research project/runs/failed/outputs/*.json',
     'C:/Research project/runs/retry/outputs/*.json'),
    (r'\\server\share\runs\failed\outputs\metrics.json',
     r'\\server\share\runs\retry\outputs\metrics.json'),
    (r'C:\project\runs/failed\outputs/*.json', r'C:\project\runs/retry\outputs/*.json'),
    (r'C:\project\runs\failed', r'C:\project\runs\retry'),
    ('runs/failed-extra/outputs/metrics.json', 'runs/failed-extra/outputs/metrics.json'),
    ('not-runs/failed/metrics.json', 'not-runs/failed/metrics.json'),
])
def test_retry_output_paths_handle_native_and_portable_separators(value, expected):
    assert rebase_execution_output(value, 'failed', 'retry') == expected


@pytest.mark.parametrize('handle,error,wait_result,expected', [
    (123, 0, 258, True),   # Running process.
    (123, 0, 0, False),    # Exited process whose handle still exists.
    (None, 87, 0, False),  # PID no longer exists.
    (None, 5, 0, None),    # Access denied is not proof of exit.
    (123, 0, 0xFFFFFFFF, None),
])
def test_windows_liveness_uses_non_signaling_handles(monkeypatch, handle, error, wait_result, expected):
    kernel = Mock()
    kernel.OpenProcess.return_value = handle
    kernel.WaitForSingleObject.return_value = wait_result
    monkeypatch.setattr(ctypes, 'WinDLL', lambda *args, **kwargs: kernel, raising=False)
    monkeypatch.setattr(ctypes, 'get_last_error', lambda: error, raising=False)
    assert queue._windows_process_alive(12345) is expected
    kernel.OpenProcess.assert_called_once_with(0x00100000, False, 12345)
    if handle:
        kernel.WaitForSingleObject.assert_called_once_with(handle, 0)
        kernel.CloseHandle.assert_called_once_with(handle)
    else:
        kernel.WaitForSingleObject.assert_not_called()
        kernel.CloseHandle.assert_not_called()


def test_process_liveness_observes_real_owned_child_and_its_exit():
    child = subprocess.Popen([sys.executable, '-u', '-c',
        'import time; print("ready", flush=True); time.sleep(30)'], stdout=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline() == 'ready\n'
        assert queue._process_alive(child.pid) is True
    finally:
        child.terminate()
        child.wait(timeout=10)
        child.stdout.close()
    assert queue._process_alive(child.pid) is False


@pytest.mark.parametrize('alive', [True, None])
def test_lease_release_protects_live_or_unknown_process(tmp_path, monkeypatch, alive):
    job = queued_job(tmp_path)
    completed = subprocess.run(shlex.split(queue.governed_launch_command(job)),
                               capture_output=True, text=True, timeout=25)
    assert completed.returncode == 0, completed.stderr
    job['status'] = 'completed'
    monkeypatch.setattr(queue, '_process_alive', lambda pid: alive)
    queue.release_governed_lease(job)
    assert read_record(tmp_path / '.ei/leases/queue-lease.json')['status'] == 'queued'
    assert read_record(tmp_path / '.ei/consumers/queue-job.json')['lifecycle'] == 'queued'
    assert not (tmp_path / '.ei/queue/termination-receipts/queue-attempt-1.json').exists()


@pytest.mark.parametrize('kind', ['capacity', 'first-choice', 'duration'])
def test_session_resource_deferral_does_not_launch_or_spend_queue_retry(tmp_path, monkeypatch, kind):
    from tools import resource_budget
    from tests.test_resource_budget import requirements
    if kind != 'first-choice':
        resource_budget.select(tmp_path,'queue-session',preset='maximum',selected_by='fixture-user')
    request = requirements(tmp_path)
    if kind == 'capacity':
        request['ram_bytes'] = 10**25
    if kind == 'duration':
        request['job_seconds'] = 43201
    job = queued_job(tmp_path,resource_binding={'session_id':'queue-session','request':request})
    job['phase'] = 'compare'
    state = {'meta':{},'phases':[{'name':'compare','depends_on':[],'status':'active'}], 'jobs':[job]}
    manifest = {'cwd':str(tmp_path),'gpus':[0],'max_parallel':1,
                'phases':[{'name':'compare','depends_on':[],'jobs':[{'id':job['id']}]}]}
    monkeypatch.setattr(queue,'resolve_conda_hook',lambda *a:'')
    monkeypatch.setattr(queue,'free_gpus',lambda *a:[0])
    monkeypatch.setattr(queue,'launch_job',lambda *a:pytest.fail('Deferred resource use must never reach screen launch'))
    queue.step(manifest,state,str(tmp_path/'queue-state.json'),str(tmp_path))
    assert job['status']=='pending' and job['attempts']==0
    assert read_record(tmp_path/'runs/queue-attempt-1/execution.json')['status']=='prepared'
    assert read_record(tmp_path/'.ei/leases/queue-lease.json')['status']=='queued'
    assert not (tmp_path/'runs/queue-attempt-1/process.json').exists()


def test_late_admission_failure_returns_to_pending_instead_of_failed_training(tmp_path, monkeypatch):
    from tools import execution_registry, resource_budget
    from tests.test_resource_budget import requirements
    resource_budget.select(tmp_path,'queue-session',preset='maximum',selected_by='fixture-user')
    job = queued_job(tmp_path,resource_binding={'session_id':'queue-session',
                                               'request':requirements(tmp_path,ram_bytes=10**25)})
    with pytest.raises(ValueError,match='WAIT_RESOURCE'):
        execution_registry.launch_execution(tmp_path,'queue-attempt-1',job['execution']['arguments'])
    monkeypatch.setattr(queue,'screen_exists',lambda *a:False)
    assert queue.job_status_check(job,str(tmp_path),str(tmp_path))==('pending','Session resources WAIT_RESOURCE')
    assert read_record(tmp_path/'runs/queue-attempt-1/execution.json')['status']=='prepared'
