"""Exercise P5 from the session table through queue dispatch and its final launcher."""
import importlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

from tests.governance_helpers import consumer, make_environment, make_sources, make_spec
from tests.test_governed_queue import ROOT, queue
from tests.test_resource_budget import GIB, observation, requirements, selected
from tools import execution_registry as execution
from tools import resource_budget as budget
from tools import resource_planner as planner
from tools.environment_registry import EnvironmentRegistry
from tools.registry_common import atomic_write, read_record


@pytest.fixture
def queue_budget(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'tools'))
    return importlib.import_module('resource_budget')


def live_host(root, *, cards=2, gpu_free=12, ram_free=32, disk_free=64):
    """Return controlled live capacities while keeping known physical totals."""
    live = observation(root)
    live['gpus'] = [{'id': str(index), 'uuid': f'GPU-{index}', 'total_bytes': 24 * GIB,
                     'used_bytes': (24 - gpu_free) * GIB, 'free_bytes': gpu_free * GIB,
                     'utilization_percent': 0, 'process_ids': []} for index in range(cards)]
    live['ram']['available_bytes'] = ram_free * GIB
    for row in live['disks'].values():
        row.update(free_bytes=disk_free * GIB, used_bytes=(100 - disk_free) * GIB)
    return live


def task(root, *, count=1, peak=4, ram=4, disk=4, **changes):
    request = requirements(root, ram_bytes=ram * GIB)
    del request['gpus']
    request['storage'][0]['checkpoint_peak_bytes'] = disk * GIB
    return dict(request, gpu_options=[{'count': count, 'peak_bytes': peak * GIB}], **changes)


def binding(template):
    return {'session_id': 'session-a', 'task': template}


def gpu_ids(request):
    return [row['id'] for row in request['gpus']]


def test_visible_devices_intersect_both_allowlists_and_session_cap(tmp_path, monkeypatch):
    live = live_host(tmp_path, cards=8)
    monkeypatch.setattr(budget, 'probe', lambda *args: live)
    selected(tmp_path, allowed_gpu_ids=['0', '1'], max_parallel_jobs=1)
    frozen = binding(task(tmp_path))
    result = planner.plan(tmp_path, frozen, pending_jobs=8)
    assert result['slots'] == 1 and gpu_ids(result['request']) == ['GPU-0']
    assert [row['id'] for row in result['effective_capacity']['gpus']] == ['0', '1']
    assert result['remaining_capacity_check']['checks'][0]['resource'] == 'max_parallel_jobs'
    context = {'allowed_gpu_ids': ['1', '2'], 'max_parallel_jobs': 4}
    check = budget.check_launch(tmp_path, frozen, queue_context=context)
    assert gpu_ids(check['request']) == ['GPU-1']


@pytest.mark.parametrize('factor,resource', [('vram', 'vram:'), ('ram', 'ram_bytes'), ('disk', 'disk_filesystem:')])
def test_batch_slots_shrink_with_each_overlapping_peak(tmp_path, monkeypatch, factor, resource):
    live = live_host(tmp_path, cards=1, gpu_free=24)
    monkeypatch.setattr(budget, 'probe', lambda *args: live)
    selected(tmp_path)
    frozen = binding(task(tmp_path))
    for available, expected in ((16, 4), (8, 2), (4, 1)):
        if factor == 'vram':
            live['gpus'][0].update(free_bytes=available * GIB, used_bytes=(24 - available) * GIB)
        if factor == 'ram':
            live['ram']['available_bytes'] = available * GIB
        if factor == 'disk':
            live['disks'][str(tmp_path)]['free_bytes'] = available * GIB
        result = planner.plan(tmp_path, frozen, pending_jobs=4)
        assert result['slots'] == expected
        if expected < 4:
            assert any(row['resource'].startswith(resource) and row['status'] == 'WAIT_RESOURCE'
                       for row in result['remaining_capacity_check']['batch_checks'])


def test_same_filesystem_paths_consume_one_pool_with_concurrent_checkpoints(tmp_path, monkeypatch):
    live = live_host(tmp_path, disk_free=10)
    monkeypatch.setattr(budget, 'probe', lambda *args: live)
    selected(tmp_path)
    frozen = binding(task(tmp_path, disk=3))
    frozen['task']['storage'].append(dict(frozen['task']['storage'][0],
        path=str(tmp_path / 'weights'), checkpoint_peak_bytes=3 * GIB))
    result = planner.plan(tmp_path, frozen, pending_jobs=2)
    assert result['slots'] == 1
    disk_checks = [check for check in result['remaining_capacity_check']['batch_checks']
                   if check['resource'].startswith('disk_filesystem:')]
    assert len(disk_checks) == 1 and disk_checks[0]['required'] == 12 * GIB


def test_preferences_choose_among_declared_execution_equivalents(tmp_path, monkeypatch):
    monkeypatch.setattr(budget, 'probe', lambda *args: live_host(tmp_path))
    selected(tmp_path)
    frozen = binding(task(tmp_path))
    frozen['task']['gpu_options'].append({'count': 2, 'peak_bytes': 4 * GIB, 'job_seconds': 60})
    assert gpu_ids(planner.plan(tmp_path, frozen)['request']) == ['GPU-0']
    frozen['task']['preference'] = 'fastest'
    assert gpu_ids(planner.plan(tmp_path, frozen)['request']) == ['GPU-0', 'GPU-1']


def test_distinguishes_impossible_unknown_and_unapproved_candidates(tmp_path, monkeypatch):
    live = live_host(tmp_path, cards=1)
    monkeypatch.setattr(budget, 'probe', lambda *args: live)
    selected(tmp_path)
    frozen = binding(task(tmp_path, peak=25))
    original = json.dumps(frozen, sort_keys=True)
    result = planner.plan(tmp_path, frozen)
    assert result['status'] == 'REPLAN_REQUIRED'
    assert result['candidates'][0]['checks'] and json.dumps(frozen, sort_keys=True) == original
    live.update(gpus=[], gpu_probe_error='NVIDIA observer unavailable')
    assert planner.plan(tmp_path, frozen)['status'] == 'NEEDS_ESTIMATE'
    cpu = binding(task(tmp_path, count=0, peak=0))
    assert planner.plan(tmp_path, cpu)['status'] == 'AUTO_APPROVED'
    cpu['task']['new_spend'] = 1
    assert planner.plan(tmp_path, cpu)['status'] == 'NEEDS_APPROVAL'


def make_queue(root, templates, **options):
    sources = make_sources(root)
    with (root / 'src/train.py').open('a', encoding='utf-8') as source:
        source.write('import os\nprint("visible-devices=" + os.environ.get("CUDA_VISIBLE_DEVICES", "unset"))\n')
    spec_ref, environment = make_spec(root), make_environment(root)
    registry = EnvironmentRegistry(root)
    jobs = []
    for index, template in enumerate(templates):
        attempt = f'planned-{index}'
        job_ref = f'job-{index}'
        arguments = [str(root / 'runs' / attempt / 'outputs/metrics.json')]
        config = {'variant': {'augmentation': 0.1}, 'seed': 22, 'resource_budget': binding(template)}
        snapshot = execution.freeze_snapshot(root, attempt, spec_ref, environment, sources,
                    config, 'src/train.py', 'method-b', 22, arguments=arguments, output_argument_indices=[0])
        execution.start_execution(root, attempt, snapshot, job_ref=job_ref)
        registry.bind_consumer(consumer(environment, job_ref) | {'execution_run_id': attempt})
        registry.acquire_lease(job_ref, job_ref + '-lease', job_ref, expires_at='2030-01-01T00:00:00Z')
        jobs.append({'id': job_ref, 'expected_output': arguments[0],
            'execution': {'project_root': str(root), 'registry_tools_dir': str(ROOT / 'tools'),
                'execution_run_id': attempt, 'snapshot_ref': snapshot, 'env_revision': environment,
                'arguments': arguments, 'consumer_id': job_ref, 'lease_id': job_ref + '-lease'}})
    manifest = dict(schema_version=2, cwd=str(root), phases=[{'name': 'compare', 'jobs': jobs}], **options)
    state = queue.load_state(root / 'queue-state.json', manifest)
    queue.assign_jobs_to_phases(manifest, state)
    return manifest, state


@pytest.mark.parametrize('sharing,cap,expected', [(True, None, 2), (False, None, 1), (True, 1, 1)])
def test_real_queue_admission_counts_own_jobs_and_keeps_frozen_science(tmp_path, monkeypatch, queue_budget, sharing, cap, expected):
    # Queue scripts run as standalone modules on the target host.
    monkeypatch.setattr(queue_budget, 'probe', lambda *args: live_host(tmp_path, cards=1))
    selected(tmp_path, allow_gpu_sharing=sharing, max_parallel_jobs=cap)
    manifest, state = make_queue(tmp_path, [task(tmp_path, peak=6) for _ in range(3)])
    state_path = tmp_path / 'queue-state.json'
    launches = []

    def capture(job, gpu, *args):
        persisted = read_record(state_path)
        row = next(item for item in persisted['jobs'] if item['id'] == job['id'])
        assert row['status'] == 'running' and gpu_ids(row['resource_assignment']['request']) == ['GPU-0']
        launches.append(job['id'])
        return 'fixture-screen', None

    monkeypatch.setattr(queue, 'launch_job', capture)
    queue.step(manifest, state, state_path, tmp_path)
    assert len(launches) == expected
    assert [row['attempts'] for row in state['jobs']] == [1] * expected + [0] * (3 - expected)
    if expected == 2:
        assert state['jobs'][1]['resource_assignment']['shared_gpu_uuids'] == ['GPU-0']
        assert state['jobs'][1]['resource_assignment']['concurrent_jobs'] == 2
    for job in state['jobs']:
        snapshot = execution.verify_snapshot(tmp_path, job['execution']['snapshot_ref'])
        assert snapshot['seed'] == 22 and snapshot['variant_id'] == 'method-b'
        assert snapshot['arguments'] == job['execution']['arguments']


def test_final_launcher_refuses_replaced_uuid_then_queue_can_replan_same_attempt(tmp_path, monkeypatch, queue_budget):
    live = live_host(tmp_path, cards=8)
    monkeypatch.setattr(budget, 'probe', lambda *args: live)
    monkeypatch.setattr(queue_budget, 'probe', lambda *args: live)
    selected(tmp_path, allowed_gpu_ids=['0'])
    manifest, state = make_queue(tmp_path, [task(tmp_path)])
    state_path = tmp_path / 'queue-state.json'
    monkeypatch.setattr(queue, 'launch_job', lambda *args: ('fixture-screen', None))
    queue.step(manifest, state, state_path, tmp_path)
    job = state['jobs'][0]
    old = job['execution']['snapshot_ref']
    assert gpu_ids(job['resource_assignment']['request']) == ['GPU-0']
    live['gpus'][0]['uuid'] = 'GPU-replacement'
    with pytest.raises(budget.ResourceAdmissionError) as blocked:
        execution.launch_execution(tmp_path, 'planned-0', job['execution']['arguments'], queue_state=state_path)
    assert blocked.value.result['status'] == 'NEEDS_ESTIMATE'
    assert not (tmp_path / 'runs/planned-0/process.json').exists()
    monkeypatch.setattr(queue, 'screen_exists', lambda name: False)
    queue.step(manifest, state, state_path, tmp_path)
    assert gpu_ids(job['resource_assignment']['request']) == ['GPU-replacement']
    assert job['attempts'] == 1 and job['execution']['snapshot_ref'] == old
    result = execution.launch_execution(tmp_path, 'planned-0', job['execution']['arguments'], queue_state=state_path)
    assert result['exit_code'] == 0
    log = (tmp_path / 'runs/planned-0/process.log').read_text(encoding='utf-8')
    assert 'visible-devices=GPU-replacement\n' in log


@pytest.mark.parametrize('change', ['policy', 'lease'])
def test_launch_rechecks_the_policy_and_lease_after_sampling(tmp_path, monkeypatch, change):
    selected(tmp_path)
    manifest, state = make_queue(tmp_path, [task(tmp_path, count=0, peak=0, ram=0, disk=0)])
    state_path = tmp_path / 'queue-state.json'
    monkeypatch.setattr(queue, 'launch_job', lambda *args: ('fixture-screen', None))
    queue.step(manifest, state, state_path, tmp_path)
    original = execution.check_execution_resources

    def change_after_check(*args, **kwargs):
        result = original(*args, **kwargs)
        if change == 'policy':
            selected(tmp_path, max_parallel_jobs=0)
        else:
            path = tmp_path / '.ei/leases/job-0-lease.json'
            atomic_write(path, dict(read_record(path), status='released'))
        return result

    monkeypatch.setattr(execution, 'check_execution_resources', change_after_check)
    job = state['jobs'][0]
    with pytest.raises(budget.ResourceAdmissionError) as blocked:
        execution.launch_execution(tmp_path, 'planned-0', job['execution']['arguments'], queue_state=state_path)
    expected = 'policy_revision' if change == 'policy' else 'active_queue_lease'
    assert any(check['resource'] == expected for check in blocked.value.result['checks'])
    assert read_record(tmp_path / 'runs/planned-0/execution.json')['status'] == 'prepared'
    assert not (tmp_path / 'runs/planned-0/process.json').exists()


def test_cpu_queue_reuses_the_released_slot_through_the_real_frozen_launcher(tmp_path, monkeypatch):
    selected(tmp_path, max_parallel_jobs=1)
    template = task(tmp_path, count=0, peak=0, ram=0, disk=0)
    manifest, state = make_queue(tmp_path, [template, template])
    state_path = tmp_path / 'queue-state.json'

    def launch(job, gpu, conda, cwd, log_dir, hook, saved_state):
        command = shlex.split(queue.governed_launch_command(job, queue_state=saved_state))
        child = subprocess.run(command, capture_output=True, text=True, timeout=30)
        assert child.returncode == 0, child.stderr
        return 'disposable-fixture', None

    monkeypatch.setattr(queue, 'launch_job', launch)
    monkeypatch.setattr(queue, 'screen_exists', lambda name: False)
    queue.step(manifest, state, state_path, tmp_path)
    assert [item['status'] for item in state['jobs']] == ['running', 'pending']
    assert state['jobs'][1]['attempts'] == 0
    queue.step(manifest, state, state_path, tmp_path)
    assert [item['status'] for item in state['jobs']] == ['completed', 'running']
    queue.step(manifest, state, state_path, tmp_path)
    for job in state['jobs']:
        assert job['status'] == 'completed' and job['lease_release'] == 'released' and job['attempts'] == 1
        check = read_record(Path(job['expected_output']).parents[1] / 'resource-admission.json')['check']
        assert check['request']['gpus'] == [] and check['concurrent_jobs'] == 1
        assert read_record(Path(job['expected_output']))['seed'] == 22


def test_manifest_cli_keeps_explicit_legacy_configuration_and_has_no_implicit_card_count(tmp_path):
    config = tmp_path / 'grid.json'
    output = tmp_path / 'manifest.json'
    raw = {'phases': [{'name': 'phase', 'grid': {'seed': [1, 2]},
                     'template': {'id': 'seed-${seed}', 'cmd': 'python train.py --seed ${seed}'}}]}
    command = [sys.executable, str(ROOT / 'tools/experiment_queue/build_manifest.py'),
               '--config', str(config), '--output', str(output)]
    config.write_text(json.dumps(raw))
    rejected = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert rejected.returncode == 2 and 'gpus and max_parallel' in rejected.stderr
    config.write_text(json.dumps(dict(raw, gpus=[1], max_parallel=1)))
    subprocess.run(command, check=True, capture_output=True, timeout=10)
    manifest = read_record(output)
    assert manifest['gpus'] == [1] and manifest['max_parallel'] == 1
    raw['phases'][0]['template']['execution'] = {'execution_run_id': 'run-${seed}'}
    config.write_text(json.dumps(raw))
    subprocess.run(command, check=True, capture_output=True, timeout=10)
    manifest = read_record(output)
    assert 'gpus' not in manifest and 'max_parallel' not in manifest
    assert manifest['phases'][0]['jobs'][1]['execution']['execution_run_id'] == 'run-2'


def test_legacy_queue_keeps_one_task_per_gpu(tmp_path, monkeypatch):
    manifest = {'gpus': [0], 'max_parallel': 3, 'phases': [{'name': 'phase', 'jobs': [
        {'id': f'legacy-{i}', 'cmd': 'python train.py'} for i in range(3)]}]}
    path = tmp_path / 'queue-state.json'
    state = queue.load_state(path, manifest)
    queue.assign_jobs_to_phases(manifest, state)
    monkeypatch.setattr(queue, 'resolve_conda_hook', lambda *args: '')
    monkeypatch.setattr(queue, 'free_gpus', lambda *args: [0])
    monkeypatch.setattr(queue, 'launch_job', lambda *args: ('fixture-screen', None))
    queue.step(manifest, state, path, tmp_path)
    assert [row['status'] for row in state['jobs']] == ['running', 'pending', 'pending']


def test_planner_cli_writes_directly_admissible_request(tmp_path):
    selected(tmp_path)
    source = tmp_path / 'task.json'
    source.write_text(json.dumps(task(tmp_path, count=0, peak=0, ram=0, disk=0)))
    output = tmp_path / 'output'
    command = [sys.executable, str(ROOT / 'tools/resource_planner.py'), '--root', str(tmp_path),
               '--session', 'session-a', '--task', str(source), '--output-dir', str(output), '--markdown']
    child = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert child.returncode == 0, child.stderr
    assert '1 of 1' in (output / 'RESOURCE_PLAN.md').read_text(encoding='utf-8')
    check = budget.check_launch(tmp_path, {'session_id': 'session-a',
                                         'request': read_record(output / 'resource-request.json')})
    assert check['status'] == 'AUTO_APPROVED'
    selected(tmp_path, max_parallel_jobs=0)
    assert subprocess.run(command, capture_output=True, timeout=30).returncode == 3
    assert json.loads((output / 'resource-request.json').read_text(encoding='utf-8')) is None
