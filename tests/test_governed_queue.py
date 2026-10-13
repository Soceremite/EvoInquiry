"""Exercise queue bindings with real CPU processes; no screen or GPU allocation."""
import importlib.util
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

from tests.governance_helpers import consumer, make_environment, make_sources, make_spec
from tools.environment_registry import EnvironmentRegistry
from tools.execution_registry import freeze_snapshot, start_execution
from tools.registry_common import read_record

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('governed_queue_fixture', ROOT / 'skills/experiment-queue/scripts/queue_manager.py')
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


def queued_job(root, failure=False):
    sources, spec_ref, environment = make_sources(root), make_spec(root), make_environment(root)
    run_id = 'queue-attempt-1'
    arguments = [str(root / 'runs' / run_id / 'outputs/metrics.json')]
    snapshot = freeze_snapshot(root,run_id,spec_ref,environment,sources,
        {'variant':{'augmentation':0.1},'seed':22,'inject_failure':failure},
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
    assert retry in job['expected_output']
    assert queue.governed_launch_command(job)==command
    assert read_record(tmp_path / '.ei/leases/queue-lease.json')['status']=='queued'
