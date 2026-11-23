"""Exercise priority dispatch, evaluation placement and monitoring through current entrypoints."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import subprocess
import sys
import time

import pytest

from tests.governance_helpers import consumer, make_environment, make_spec
from tests.test_governed_queue import ROOT, queue
from tests.test_resource_budget import GIB, requirements, selected
from tests.test_resource_planner import live_host, queue_budget  # noqa: F401
from tools import evaluation_profiles, execution_registry as runner
from tools import resource_budget as budget
from tools.environment_registry import EnvironmentRegistry
from tools.registry_common import atomic_write, fixed_ref, read_record


@pytest.fixture
def project(tmp_path):
    root = tmp_path.resolve()
    spec, environment = make_spec(root), make_environment(root)
    registry = EnvironmentRegistry(root)

    def prepare(name, *, gpus=(), cpu=1, io=None, options=None, program='print("done")', **schedule):
        source = root / 'worker.py'
        source.write_text(program, encoding='utf-8')
        request = requirements(root, gpus=[{'id': uuid, 'peak_bytes': peak * GIB} for uuid, peak in gpus],
                               ram_bytes=128 * 1024**2, cpu_cores=cpu)
        for key in budget.STORAGE_FIELDS:
            request['storage'][0][key] = 0
        if io is not None:
            request['io_bytes_per_second'] = io
        resources = {'session_id': 'session-a', 'request': request}
        if options is not None:
            request.pop('gpus')
            resources = {'session_id': 'session-a', 'task': dict(request, **options)}
        configuration = {'variant': {'augmentation': 0.1}, 'seed': 22, 'resource_budget': resources}
        snapshot = runner.freeze_snapshot(root, name, spec, environment, ['worker.py'], configuration,
                                          'worker.py', 'method-b', 22, arguments=[str(root)])
        runner.start_execution(root, name, snapshot, job_ref=name)
        registry.bind_consumer(consumer(environment, name))
        registry.acquire_lease(name, f'{name}-lease', name, expires_at='2030-01-01T00:00:00Z')
        return dict(id=name, execution={'project_root': str(root), 'registry_tools_dir': str(ROOT / 'tools'),
            'execution_run_id': name, 'snapshot_ref': snapshot, 'env_revision': environment,
            'arguments': [str(root)], 'consumer_id': name, 'lease_id': f'{name}-lease'}, **schedule)

    return root, spec, environment, prepare


def manifest(root, jobs, **kwargs):
    return dict(schema_version=2, cwd=str(root), phases=[{'name': 'work', 'jobs': list(jobs)}], **kwargs)


def state_for(root, plan):
    path = root / 'queue-state.json'
    state = queue.load_state(path, plan)
    queue.assign_jobs_to_phases(plan, state)
    return path, state


def by_id(state):
    return {row['id']: row for row in state['jobs']}


def test_waiting_two_card_job_protects_devices_and_leaves_an_unrelated_slot(project, monkeypatch, queue_budget):
    root, _, _, prepare = project
    live = live_host(root, cards=3, gpu_free=24)
    monkeypatch.setattr(queue_budget, 'probe', lambda *args: live)
    selected(root, allow_gpu_sharing=False)
    original = prepare('original', gpus=[('GPU-0', 4)])
    plan = manifest(root, [original], max_parallel=2)
    path, state = state_for(root, plan)
    launched = []

    def transport(job, gpu, *args):
        assert by_id(read_record(path))[job['id']]['status'] == 'running'
        launched.append(job['id'])
        return job['id'], None

    monkeypatch.setattr(queue, 'launch_job', transport)
    monkeypatch.setattr(queue, 'job_status_check', lambda *args: ('running', None))
    monkeypatch.setattr(queue, 'release_governed_lease', lambda job: None)
    queue.step(plan, state, path, root)
    high = prepare('two-card', gpus=[('GPU-0', 8), ('GPU-1', 8)], priority=20)
    overlapping = prepare('would-delay', gpus=[('GPU-1', 4)], priority=1)
    spare = prepare('spare', gpus=[('GPU-2', 4)], priority=1)
    plan = manifest(root, [original, overlapping, spare, high], max_parallel=2)
    queue.assign_jobs_to_phases(plan, state)
    queue.step(plan, state, path, root)
    assert launched == ['original', 'spare']
    assert state['meta']['reservation']['job_id'] == high['id']
    assert state['meta']['reservation']['releasing_jobs'] == [original['id']]
    assert by_id(state)['would-delay']['attempts'] == 0
    assert 'WAIT_RESOURCE' in by_id(state)['would-delay']['error']
    resumed = queue.load_state(path, plan)
    monkeypatch.setattr(queue, 'job_status_check',
                        lambda job, *_: ('completed', None) if job['id'] == original['id'] else ('running', None))
    queue.step(plan, resumed, path, root)
    assert launched == ['original', 'spare', 'two-card']
    assert by_id(resumed)['original']['attempts'] == 1 and by_id(resumed)['spare']['attempts'] == 1


def test_future_priority_window_accepts_only_evidenced_finish_before_ready(project, monkeypatch, queue_budget):
    root, _, _, prepare = project
    monkeypatch.setattr(queue_budget, 'probe', lambda *args: live_host(root, cards=1, gpu_free=24))
    selected(root)
    atomic_write(root / 'short-run.json', {'elapsed_seconds': 1.2})
    until = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
    high = prepare('future', gpus=[('GPU-0', 4)], priority=9, ready_at=until)
    wait = prepare('unestimated', gpus=[('GPU-0', 2)])
    short = prepare('known-short', gpus=[('GPU-0', 2)],
                    backfill={'seconds': 5, 'evidence': fixed_ref(root, 'short-run.json')})
    plan = manifest(root, [wait, short, high])
    path, state = state_for(root, plan)
    launched = []
    monkeypatch.setattr(queue, 'launch_job', lambda job, *_: (launched.append(job['id']) or 'fixture-screen', None))
    queue.step(plan, state, path, root)
    assert launched == ['known-short']
    assert by_id(state)['future']['attempts'] == 0
    assert by_id(state)['unestimated']['attempts'] == 0
    assert not (root / 'runs/future/resource-admission.json').exists()


def test_priority_and_fifo_preserve_dependency_and_read_only_inspection(project):
    root, _, _, prepare = project
    low = prepare('first', priority=1)
    same = prepare('second', priority=1)
    high = prepare('urgent', priority=2)
    dependent = prepare('dependent', priority=100)
    plan = manifest(root, [low, same, high])
    plan['phases'].append({'name': 'followup', 'depends_on': 'work', 'jobs': [dependent]})
    path, state = state_for(root, plan)
    queue.save_state(state, path)
    source = root / 'manifest.json'
    atomic_write(source, plan)
    before = path.read_bytes()
    output = subprocess.run([sys.executable, queue.__file__, '--manifest', str(source),
                             '--state', str(path), '--inspect'], capture_output=True, text=True, check=True)
    assert json.loads(output.stdout)['pending_order'] == ['urgent', 'first', 'second']
    assert path.read_bytes() == before


def profiles_request(root, spec, environment):
    ids = ['x1', 'x2', 'x3', 'x4', 'x5']
    atomic_write(root / 'cohort.json', {'sample_ids': ids})
    rows = [{'id': name, 'prediction': index % 2, 'metrics': {'correct': int(index < 3)}}
            for index, name in enumerate(ids)]
    for filename, samples in [('single', rows), ('shard-0', rows[::2]), ('shard-1', rows[1::2])]:
        atomic_write(root / (filename + '.json'), {'samples': samples})
    profile = {'variant_id': 'method-b', 'seed': 22, 'spec_ref': spec, 'env_revision': environment,
               'host': budget.probe(root)['host'], 'precision': 'float32',
               'sample_ids_ref': fixed_ref(root, 'cohort.json'), 'metrics': {'correct': {'reducer': 'mean'}},
               'baseline': {'id': 'single', 'batch_size': 1, 'gpu_uuids': ['GPU-0'],
                            'shards': [fixed_ref(root, 'single.json')]},
               'alternatives': [{'id': 'sharded', 'batch_size': 4, 'gpu_uuids': ['GPU-0', 'GPU-1'],
                                 'shards': [fixed_ref(root, 'shard-0.json'), fixed_ref(root, 'shard-1.json')]}]}
    for row, peak, elapsed in [(profile['baseline'], 3, 2), (profile['alternatives'][0], 6, 0.75)]:
        name = f"{row['id']}-measurement.json"
        atomic_write(root / name, dict(row, host=profile['host'], precision=profile['precision'],
                                      isolated=True, peak_bytes_per_gpu=peak * GIB, elapsed_seconds=elapsed))
        row['measurement_ref'] = fixed_ref(root, name)
    return profile


@pytest.mark.parametrize('capacity_changed', [False, True])
def test_validated_profiles_choose_and_pin_batch_size_and_devices(project, monkeypatch, queue_budget, capacity_changed):
    root, spec, environment, prepare = project
    observed = live_host(root, cards=2, gpu_free=24)
    monkeypatch.setattr(budget, 'probe', lambda *args: observed)
    monkeypatch.setattr(queue_budget, 'probe', lambda *args: observed)
    selected(root)
    request = profiles_request(root, spec, environment)
    report = evaluation_profiles.validate(root, request)
    assert all(row['metrics']['correct'] == 3/5 for row in report['profiles'])
    combined = evaluation_profiles.collect_results(root, dict(
        request['alternatives'][0], sample_ids_ref=request['sample_ids_ref'], metrics=request['metrics']))
    assert combined['sample_count'] == 5 and combined['metrics']['correct'] == 3/5
    atomic_write(root/'profiles.json', report)
    worker = '''import json, os
print(json.dumps({key: os.environ[key] for key in ('CUDA_VISIBLE_DEVICES', 'EVOINQUIRY_EVAL_BATCH_SIZE',
      'EVOINQUIRY_EVAL_GPU_COUNT', 'EVOINQUIRY_EVAL_PROFILE')}))
'''
    job = prepare('evaluate', program=worker, options={'evaluation_profiles_ref': fixed_ref(root,'profiles.json')})
    plan = manifest(root, [job])
    path, state = state_for(root, plan)
    monkeypatch.setattr(queue, 'launch_job', lambda *args: ('fixture-screen', None))
    queue.step(plan, state, path, root)
    assignment = state['jobs'][0]['resource_assignment']
    assert assignment['evaluation_profile']['batch_size'] == 4
    if capacity_changed:
        observed['gpus'][1]['free_bytes'] = 4 * GIB
        with pytest.raises(budget.ResourceAdmissionError):
            runner.launch_execution(root, 'evaluate', [str(root)], queue_state=path)
        assert not (root/'runs/evaluate/process.json').exists()
        # Replan the prepared identity with its proven single-card option.
        monkeypatch.setattr(queue, 'screen_exists', lambda name: False)
        queue.step(plan, state, path, root)
        assert state['jobs'][0]['resource_assignment']['evaluation_profile']['id'] == 'single'
    assert runner.launch_execution(root, 'evaluate', [str(root)], queue_state=path)['exit_code'] == 0
    actual = json.loads((root/'runs/evaluate/process.log').read_text(encoding='utf-8'))
    expected = ('GPU-0', '1', '1', 'single') if capacity_changed else ('GPU-0,GPU-1', '4', '2', 'sharded')
    assert tuple(actual.values()) == expected


@pytest.mark.parametrize('defect', ['duplicate', 'missing', 'prediction', 'precision'])
def test_unverified_profile_cannot_enable_a_faster_dispatch(project, defect):
    root, spec, environment, _ = project
    request = profiles_request(root, spec, environment)
    alternative = request['alternatives'][0]
    if defect == 'duplicate':
        alternative['shards'].append(alternative['shards'][0])
    elif defect == 'missing':
        alternative['shards'].pop()
    elif defect == 'prediction':
        shard = read_record(root/'shard-0.json')
        shard['samples'][0]['prediction'] = 9
        atomic_write(root/'shard-0.json', shard)
        alternative['shards'][0] = fixed_ref(root, 'shard-0.json')
    else:
        alternative['precision'] = 'float16'
    if defect != 'precision':
        name = 'sharded-measurement.json'
        measurement = read_record(root / name)
        atomic_write(root / name, dict(measurement, shards=alternative['shards']))
        alternative['measurement_ref'] = fixed_ref(root, name)
    with pytest.raises(ValueError):
        evaluation_profiles.validate(root, request)


def test_real_cpu_companion_advances_while_primary_process_is_monitored(project, monkeypatch, queue_budget):
    root, _, _, prepare = project
    monkeypatch.setattr(queue_budget, 'probe', budget.probe)
    selected(root, max_io_bytes_per_second=12)
    main_code = '''import json, sys, time
from pathlib import Path
root = Path(sys.argv[1])
for step in range(600):
    print(json.dumps({'step': step}), flush=True)
    if (root / 'finish-primary').exists():
        break
    time.sleep(0.02)
'''
    cpu_code = '''import os, sys
from pathlib import Path
result = 'no GPU' if os.environ['CUDA_VISIBLE_DEVICES'] == '' else 'GPU visible'
target = Path(sys.argv[1]) / 'runs/review-code/outputs/cpu-result.txt'
target.parent.mkdir(parents=True)
target.write_text(result, encoding='utf-8')
'''
    primary = prepare('primary', cpu=.25, io=5, program=main_code, priority=5)
    too_heavy = prepare('io-heavy', cpu=.25, io=9, during='primary')
    companion = prepare('review-code', cpu=.25, io=5, program=cpu_code, during='primary')
    plan = manifest(root, [primary, too_heavy, companion])
    path, state = state_for(root, plan)
    monkeypatch.setattr(queue, 'screen_exists', lambda name: False)
    jobs = {}

    def wait_for_running():
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if runner.monitor_health(root, 'primary')['decision'] == 'CONTINUE':
                return
            time.sleep(0.025)
        raise AssertionError('primary never published a live process receipt')

    with ThreadPoolExecutor(max_workers=2) as group:
        def transport(job, _gpu, *args):
            jobs[job['id']] = group.submit(runner.launch_execution, root, job['id'], [str(root)], queue_state=path)
            if job['id'] == 'primary':
                wait_for_running()
                runner.monitor_health(root, 'primary', {'decision': 'WAIT', 'reason': 'Inspect latest metric anomaly'})
            return job['id'], None

        monkeypatch.setattr(queue, 'launch_job', transport)
        try:
            queue.step(plan, state, path, root)
            assert set(jobs) == {'primary'}
            assert not jobs['primary'].done()
            health = runner.monitor_health(root, 'primary')
            assert health['decision'] == 'WAIT'
            runner.monitor_health(root, 'primary', {'decision': 'CONTINUE', 'reason': 'Latest checks are healthy'})
            resumed = queue.load_state(path, plan)
            queue.step(plan, resumed, path, root)
            assert set(jobs) == {'primary', 'review-code'}
            assert jobs['review-code'].result(timeout=10)['exit_code'] == 0
            assert not jobs['primary'].done()
            assert runner.monitor_health(root, 'primary')['decision'] == 'CONTINUE'
            assert (root/'runs/review-code/outputs/cpu-result.txt').read_text() == 'no GPU'
            assert by_id(resumed)['io-heavy']['attempts'] == 0
        finally:
            (root / 'finish-primary').touch()
        assert jobs['primary'].result(timeout=10)['exit_code'] == 0
    queue.step(plan, resumed, path, root)
    assert by_id(resumed)['io-heavy']['status'] == 'deferred'
    assert queue.all_done(resumed)


def test_waiting_reservation_from_a_later_job_does_not_delay_an_earlier_launch():
    from tools.resource_planner import queue_context

    earlier = {'id': 'earlier', 'status': 'running', 'priority': 2}
    later = {'id': 'later', 'status': 'pending', 'priority': 1}
    state = {'jobs': [earlier, later], 'meta': {'resource_limits': {}, 'reservation': {'job_id': 'later'}}}
    assert 'reservation' not in queue_context(state, earlier)


def test_timing_isolation_blocks_competing_work(project, monkeypatch, queue_budget):
    root, _, _, prepare = project
    monkeypatch.setattr(queue_budget, 'probe', lambda *args: live_host(root))
    selected(root)
    timed = prepare('timing', priority=2, isolate_host=True)
    peer = prepare('competing')
    plan = manifest(root, [peer, timed])
    path, state = state_for(root, plan)
    launched = []
    monkeypatch.setattr(queue, 'launch_job', lambda job, *_: (launched.append(job['id']) or 'fixture', None))
    queue.step(plan, state, path, root)
    assert launched == ['timing']
    receipt = read_record(root/'runs/competing/resource-admission.json')
    assert receipt['check']['checks'][0]['resource'] == 'host_measurement_isolation'
