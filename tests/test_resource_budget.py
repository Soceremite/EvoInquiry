"""Session choices, actual admission and changing resource state, without training costs."""
import json
from pathlib import Path
import platform
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from tools import execution_registry, resource_budget as budget
from tools.registry_common import RegistryError, read_record
from tests.governance_helpers import make_environment, make_sources, make_spec


GIB = 1024**3


def requirements(root, **changes):
    """A 90-minute CPU job; zero GPU and storage growth are explicit estimates."""
    request = {'host': platform.node(), 'job_seconds': 5400, 'cpu_cores': 1, 'ram_bytes': 16 * 1024**2,
               'gpus': [], 'new_spend': 0, 'storage': [dict(path=str(Path(root).resolve()),
               dataset_bytes=0, weight_bytes=0, checkpoint_peak_bytes=0, other_bytes=0, reserve_bytes=0)]}
    request.update(changes)
    return request


def observation(root, **changes):
    """Two busy but shareable devices; two paths on the same physical filesystem."""
    disk = {'path': str(root), 'filesystem': 'disk-a', 'total_bytes': 100 * GIB,
            'used_bytes': 80 * GIB, 'free_bytes': 20 * GIB}
    result = {'observed_at': '2026-10-24T00:00:00+00:00', 'host': platform.node(), 'cpu_cores': 8,
              'ram': {'total_bytes': 32 * GIB, 'available_bytes': 16 * GIB},
              'gpus': [{'id': str(index), 'uuid': f'GPU-{index}', 'total_bytes': 24 * GIB,
                        'used_bytes': 16 * GIB, 'free_bytes': 8 * GIB, 'utilization_percent': 20}
                       for index in range(2)], 'gpu_probe_error': None,
              'disks': {str(root.resolve()): disk, str((root / 'weights').resolve()): dict(disk)}}
    result.update(changes)
    return result


def selected(root, **overrides):
    return budget.select(root, 'session-a', preset='custom' if overrides else 'maximum',
                         selected_by='fixture-user-choice', overrides=overrides)


def test_initialization_waits_for_first_choice_and_continuation_reuses_the_only_table(tmp_path):
    table = budget.initialize(tmp_path, 'session-a')
    assert table['status'] == 'selection_required'
    assert budget.evaluate(table, requirements(tmp_path), observation(tmp_path), stage='launch')['status'] == 'SELECTION_REQUIRED'
    approved = selected(tmp_path)
    assert budget.initialize(tmp_path, 'session-a') == approved
    assert selected(tmp_path) == approved
    assert len(list((tmp_path / '.ei/resource-sessions').glob('*.json'))) == 1
    assert budget.initialize(tmp_path, 'session-b')['status'] == 'selection_required'
    assert budget.read_table(tmp_path, 'session-a') == approved


def test_two_initializers_cannot_reset_an_existing_selection(tmp_path):
    approved = selected(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: budget.initialize(tmp_path, 'session-a'), range(2)))
    assert results == [approved, approved]
    assert budget.read_table(tmp_path, 'session-a')['revision'] == 1


def test_changing_one_custom_ceiling_preserves_other_user_restrictions(tmp_path):
    original = selected(tmp_path, allowed_gpu_ids=['1'], allow_gpu_sharing=False, max_ram_bytes=GIB)
    changed = budget.select(tmp_path, 'session-a', preset='custom', selected_by='user-raised-duration',
                             overrides={'auto_approve_job_seconds': 24 * 3600})
    assert changed['revision'] == original['revision'] + 1
    assert changed['policy']['allowed_gpu_ids'] == ['1']
    assert changed['policy']['allow_gpu_sharing'] is False
    assert changed['policy']['max_ram_bytes'] == GIB


def test_host_thread_id_stays_stable_across_skills_and_sessions(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_THREAD_ID', 'thread-one')
    budget.select(tmp_path, preset='maximum', selected_by='user')
    path = budget.table_path(tmp_path)
    assert budget.initialize(tmp_path)['status'] == 'active'
    monkeypatch.setenv('CODEX_THREAD_ID', 'thread-two')
    assert budget.table_path(tmp_path) != path
    assert budget.initialize(tmp_path)['status'] == 'selection_required'


@pytest.mark.parametrize('seconds,expected', [(5400, 'AUTO_APPROVED'), (43200, 'AUTO_APPROVED'), (43201, 'NEEDS_APPROVAL')])
def test_90_minutes_and_12_hours_need_no_repeat_approval(tmp_path, seconds, expected):
    result = budget.evaluate(selected(tmp_path), requirements(tmp_path, job_seconds=seconds),
                             observation(tmp_path), stage='launch')
    assert result['status'] == expected


def test_shared_gpu_uses_per_device_free_and_total_occupied_vram(tmp_path):
    request = requirements(tmp_path, gpus=[{'id': '0', 'peak_bytes': 4 * GIB}, {'id': '1', 'peak_bytes': 3 * GIB}])
    result = budget.evaluate(selected(tmp_path), request, observation(tmp_path), stage='launch')
    assert result['status'] == 'AUTO_APPROVED'
    assert result['current_total_vram_bytes'] == 32 * GIB
    assert result['projected_total_vram_bytes'] == 39 * GIB
    request['gpus'][0]['peak_bytes'] = 9 * GIB
    assert budget.evaluate(selected(tmp_path), request, observation(tmp_path), stage='launch')['status'] == 'WAIT_RESOURCE'


def test_exclusive_gpu_waits_for_occupants_instead_of_asking_for_permission(tmp_path):
    table = budget.select(tmp_path, 'session-a', preset='exclusive', selected_by='user')
    request = requirements(tmp_path, gpus=[{'id': '0', 'peak_bytes': GIB}])
    assert budget.evaluate(table, request, observation(tmp_path), stage='launch')['status'] == 'WAIT_RESOURCE'


def test_allowlist_and_total_vram_cap_are_independent_of_physical_fit(tmp_path):
    table = selected(tmp_path, allowed_gpu_ids=['1'], max_total_vram_bytes=33 * GIB)
    request = requirements(tmp_path, gpus=[{'id': '0', 'peak_bytes': GIB}])
    assert budget.evaluate(table, request, observation(tmp_path), stage='launch')['status'] == 'NEEDS_APPROVAL'
    request['gpus'] = [{'id': '1', 'peak_bytes': 2 * GIB}]
    result = budget.evaluate(table, request, observation(tmp_path), stage='launch')
    assert result['status'] == 'NEEDS_APPROVAL'
    assert any(row['resource'] == 'total_vram_bytes' and row['status'] == 'NEEDS_APPROVAL' for row in result['checks'])


def test_gpu_aliases_cannot_count_one_card_as_two(tmp_path):
    request = requirements(tmp_path, gpus=[{'id': '0', 'peak_bytes': GIB}, {'id': 'GPU-0', 'peak_bytes': GIB}])
    with pytest.raises(RegistryError, match='same device'):
        budget.evaluate(selected(tmp_path), request, observation(tmp_path), stage='launch')


def test_missing_device_or_host_memory_does_not_fabricate_capacity(tmp_path):
    table = selected(tmp_path)
    request = requirements(tmp_path, gpus=[{'id': 'GPU-hidden', 'peak_bytes': GIB}])
    assert budget.evaluate(table, request, observation(tmp_path), stage='launch')['status'] == 'NEEDS_ESTIMATE'
    unknown = observation(tmp_path, ram={'total_bytes': None, 'available_bytes': None})
    assert budget.evaluate(table, requirements(tmp_path), unknown, stage='launch')['status'] == 'NEEDS_ESTIMATE'


def test_ram_is_current_available_capacity_not_just_total_memory(tmp_path):
    request = requirements(tmp_path, ram_bytes=17 * GIB)
    assert budget.evaluate(selected(tmp_path), request, observation(tmp_path), stage='launch')['status'] == 'WAIT_RESOURCE'


def test_datasets_weights_and_concurrent_checkpoint_saves_share_one_disk_budget(tmp_path):
    request = requirements(tmp_path)
    request['storage'][0].update(dataset_bytes=9 * GIB, other_bytes=2 * GIB)
    request['storage'].append(dict(path=str((tmp_path / 'weights').resolve()), dataset_bytes=0,
        weight_bytes=4 * GIB, checkpoint_peak_bytes=6 * GIB, other_bytes=0, reserve_bytes=GIB))
    result = budget.evaluate(selected(tmp_path), request, observation(tmp_path), stage='launch')
    assert result['status'] == 'WAIT_RESOURCE'  # 22 GiB needed; only one 20 GiB pool.
    disk_checks = [row for row in result['checks'] if row['resource'].startswith('disk_filesystem:')]
    assert len(disk_checks) == 1 and disk_checks[0]['required'] == 22 * GIB
    request['storage'][1]['checkpoint_peak_bytes'] = 3 * GIB
    assert budget.evaluate(selected(tmp_path), request, observation(tmp_path), stage='launch')['status'] == 'AUTO_APPROVED'


def test_distinct_filesystems_are_not_summed_against_the_smallest_free_space(tmp_path):
    request = requirements(tmp_path)
    request['storage'][0]['dataset_bytes'] = 15 * GIB
    request['storage'].append(dict(request['storage'][0], path=str((tmp_path / 'weights').resolve()),
                                   dataset_bytes=0, weight_bytes=15 * GIB))
    observed = observation(tmp_path)
    observed['disks'][str((tmp_path / 'weights').resolve())]['filesystem'] = 'disk-b'
    assert budget.evaluate(selected(tmp_path), request, observed, stage='launch')['status'] == 'AUTO_APPROVED'


@pytest.mark.parametrize('field', ['max_dataset_bytes', 'max_weight_bytes', 'max_disk_bytes'])
def test_custom_storage_ceilings_apply_even_when_disk_has_capacity(tmp_path, field):
    request = requirements(tmp_path)
    request['storage'][0].update(dataset_bytes=2 * GIB, weight_bytes=2 * GIB)
    result = budget.evaluate(selected(tmp_path, **{field: GIB}), request, observation(tmp_path), stage='launch')
    assert result['status'] == 'NEEDS_APPROVAL'


def test_unapproved_spending_is_not_inferred_from_the_maximum_local_profile(tmp_path):
    assert budget.evaluate(selected(tmp_path), requirements(tmp_path, new_spend=1),
                           observation(tmp_path), stage='launch')['status'] == 'NEEDS_APPROVAL'


def test_plan_and_launch_reload_policy_and_observe_resource_changes(tmp_path, monkeypatch):
    selected(tmp_path)
    request = requirements(tmp_path, gpus=[{'id': '0', 'peak_bytes': 4 * GIB}])
    readings = [observation(tmp_path), observation(tmp_path)]
    readings[1]['gpus'][0]['free_bytes'] = GIB
    monkeypatch.setattr(budget, 'probe', lambda *a: readings.pop(0))
    assert budget.check(tmp_path, 'session-a', stage='plan', request=request)['status'] == 'AUTO_APPROVED'
    assert budget.check(tmp_path, 'session-a', stage='launch', request=request)['status'] == 'WAIT_RESOURCE'
    assert len(list((tmp_path / '.ei/resource-sessions').glob('*.json'))) == 1
    selected(tmp_path, allowed_gpu_ids=[])
    monkeypatch.setattr(budget, 'probe', lambda *a: observation(tmp_path))
    assert budget.check(tmp_path, 'session-a', stage='launch', request=request)['status'] == 'NEEDS_APPROVAL'


def test_read_only_plan_does_not_initialize_a_policy_or_write_state(tmp_path, monkeypatch):
    monkeypatch.setattr(budget, 'probe', lambda *a: observation(tmp_path))
    assert budget.check(tmp_path, 'session-a', stage='plan', persist=False)['status'] == 'SELECTION_REQUIRED'
    assert not (tmp_path / '.ei').exists()
    selected(tmp_path)
    before = budget.table_path(tmp_path, 'session-a').read_bytes()
    assert budget.check(tmp_path, 'session-a', stage='plan', persist=False)['status'] == 'READY_TO_PLAN'
    assert budget.table_path(tmp_path, 'session-a').read_bytes() == before


@pytest.mark.parametrize('change', [
    {'ram_bytes': -1}, {'job_seconds': float('nan')}, {'cpu_cores': True},
    {'storage': []}, {'gpus': [{'id': '0'}]}, {'new_spend': float('inf')},
])
def test_invalid_or_omitted_requirements_cannot_pass_admission(tmp_path, change):
    with pytest.raises(RegistryError):
        budget.evaluate(selected(tmp_path), requirements(tmp_path, **change), observation(tmp_path), stage='launch')


def test_nvidia_probe_honors_visibility_and_does_not_relabel_physical_ids(monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '1')
    monkeypatch.setattr(budget.subprocess, 'run', lambda *a, **k: subprocess.CompletedProcess([], 0,
        '0, GPU-0, 24000, 16000, 8000, 20\n1, GPU-1, 24000, 8000, 16000, 10\n', ''))
    gpus, error = budget._gpus()
    assert error is None and [row['id'] for row in gpus] == ['1']
    assert gpus[0]['free_bytes'] == 16000 * 1024**2


def test_unknown_gpu_telemetry_is_not_reported_as_zero_occupied_memory(tmp_path):
    result = budget.evaluate(selected(tmp_path), requirements(tmp_path),
        observation(tmp_path, gpus=[], gpu_probe_error='not available'), stage='launch')
    assert result['status'] == 'AUTO_APPROVED'  # This CPU job needs no GPU.
    assert result['current_total_vram_bytes'] is None
    limited = selected(tmp_path, max_total_vram_bytes=GIB)
    assert budget.evaluate(limited, requirements(tmp_path),
        observation(tmp_path, gpus=[], gpu_probe_error='not available'), stage='launch')['status'] == 'NEEDS_ESTIMATE'


def test_policy_changed_during_probe_must_be_rechecked(tmp_path, monkeypatch):
    selected(tmp_path)
    def change_policy(*args):
        selected(tmp_path, max_ram_bytes=1)
        return observation(tmp_path)
    monkeypatch.setattr(budget, 'probe', change_policy)
    with pytest.raises(RegistryError, match='changed during check'):
        budget.check(tmp_path, 'session-a', stage='launch', request=requirements(tmp_path))


def test_inaccessible_disk_is_unknown_capacity_not_empty_or_unlimited(tmp_path, monkeypatch):
    def denied(*args):
        raise PermissionError('fixture: disk statistics unavailable')
    monkeypatch.setattr(budget.shutil, 'disk_usage', denied)
    disk = budget._disk(tmp_path)
    assert disk['free_bytes'] is None and disk['filesystem'] is None
    request = requirements(tmp_path)
    request['storage'][0]['dataset_bytes'] = GIB
    observed = observation(tmp_path, disks={str(tmp_path): disk})
    result = budget.evaluate(selected(tmp_path), request, observed, stage='launch')
    assert result['status'] == 'NEEDS_ESTIMATE'
    assert result['storage_peaks']['dataset_bytes'] == GIB


def prepare_job(root, *, binding=True, request=None):
    sources, spec, environment = make_sources(root), make_spec(root), make_environment(root)
    (root / 'src/train.py').write_text('import os; print("visible-devices=" + os.environ.get("CUDA_VISIBLE_DEVICES", "unset"))')
    config = {'variant': {'augmentation': 0.1}, 'seed': 22}
    if binding:
        config['resource_budget'] = {'session_id': 'session-a', 'request': request or requirements(root)}
    snapshot = execution_registry.freeze_snapshot(root, 'resource-worker', spec, environment,
        sources, config, 'src/train.py', 'method-b', 22, arguments=[])
    execution_registry.start_execution(root, 'resource-worker', snapshot)


def test_actual_cpu_launch_uses_90_minute_authorization_and_one_session_table(tmp_path):
    selected(tmp_path)
    prepare_job(tmp_path)
    result = execution_registry.launch_execution(tmp_path, 'resource-worker')
    assert result['exit_code'] == 0
    assert 'visible-devices=\n' in (tmp_path / 'runs/resource-worker/process.log').read_text()
    assert budget.read_table(tmp_path, 'session-a')['last_check']['status'] == 'AUTO_APPROVED'
    assert len(list((tmp_path / '.ei/resource-sessions').glob('*.json'))) == 1


def test_actual_child_receives_only_its_admitted_gpu_uuid(tmp_path, monkeypatch):
    selected(tmp_path, allowed_gpu_ids=['1'])
    request = requirements(tmp_path, gpus=[{'id': '1', 'peak_bytes': GIB}])
    prepare_job(tmp_path, request=request)
    monkeypatch.setattr(budget, 'probe', lambda *a: observation(tmp_path))
    result = execution_registry.launch_execution(tmp_path, 'resource-worker')
    assert result['exit_code'] == 0
    assert 'visible-devices=GPU-1\n' in (tmp_path / 'runs/resource-worker/process.log').read_text()


def test_session_selection_does_not_reset_an_existing_finite_workflow_budget(tmp_path, monkeypatch):
    from tools import research_control, run_state
    run_state.start_run(str(tmp_path), 'original-owner', ['explore'])
    research_control.configure(tmp_path, 'original-owner', 'Keep original finite budget', {
        'max_actions': 1, 'wall_seconds': 60, 'max_attempts_per_key': 1,
        'resources': {'cpu_seconds': 10}})
    original = tmp_path / '.ei/runs/original-owner.json'
    before = original.read_bytes()
    selected(tmp_path)
    monkeypatch.setattr(budget, 'probe', lambda *a: observation(tmp_path))
    assert budget.check(tmp_path, 'session-a', stage='launch', request=requirements(tmp_path))['status'] == 'AUTO_APPROVED'
    assert original.read_bytes() == before


def test_launcher_stays_prepared_when_first_choice_is_missing(tmp_path):
    prepare_job(tmp_path)
    with pytest.raises(RegistryError, match='SELECTION_REQUIRED'):
        execution_registry.launch_execution(tmp_path, 'resource-worker')
    assert not (tmp_path / 'runs/resource-worker/process.json').exists()
    assert read_record(tmp_path / 'runs/resource-worker/execution.json')['status'] == 'prepared'


def test_initialized_session_cannot_bypass_the_table_with_an_unbound_job(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_THREAD_ID', 'session-a')
    selected(tmp_path)
    prepare_job(tmp_path, binding=False)
    with pytest.raises(RegistryError, match='Bind the current session'):
        execution_registry.launch_execution(tmp_path, 'resource-worker')
    assert not (tmp_path / 'runs/resource-worker/process.json').exists()


def test_launch_checks_again_after_environment_verification(tmp_path, monkeypatch):
    selected(tmp_path)
    prepare_job(tmp_path)
    verify = execution_registry.verify_environment
    def verify_then_occupy(*args):
        observed = verify(*args)
        monkeypatch.setattr(budget, 'probe', lambda *a: observation(tmp_path,
            ram={'total_bytes': GIB, 'available_bytes': 0}))
        return observed
    monkeypatch.setattr(execution_registry, 'verify_environment', verify_then_occupy)
    with pytest.raises(RegistryError, match='WAIT_RESOURCE'):
        execution_registry.launch_execution(tmp_path, 'resource-worker')
    assert read_record(tmp_path / 'runs/resource-worker/execution.json')['status'] == 'prepared'


def test_one_table_can_be_referenced_by_another_project_in_the_same_session(tmp_path, monkeypatch):
    owner, execution = tmp_path / 'owner', tmp_path / 'execution'
    owner.mkdir(); execution.mkdir()
    selected(owner)
    monkeypatch.setattr(budget, 'probe', lambda *a: observation(execution))
    binding = {'session_id': 'session-a', 'table_root': str(owner), 'request': requirements(execution)}
    assert budget.check_launch(execution, binding)['status'] == 'AUTO_APPROVED'
    assert not (execution / '.ei/resource-sessions').exists()
    assert budget.read_table(owner, 'session-a')['last_check']['status'] == 'AUTO_APPROVED'


def test_cli_first_use_select_plan_and_render_reuse_the_same_record(tmp_path):
    command = [sys.executable, str(Path(budget.__file__).resolve()), '--root', str(tmp_path), '--session', 'cli-session']
    first = subprocess.run([*command, 'init'], capture_output=True, text=True, check=True)
    assert len(json.loads(first.stdout)['choices']) == 3
    subprocess.run([*command, 'select', '--preset', 'maximum', '--selected-by', 'fixture-user'],
                   capture_output=True, text=True, check=True)
    checked = subprocess.run([*command, 'check', '--stage', 'plan', '--markdown'], capture_output=True, text=True, check=True)
    assert 'READY_TO_PLAN' in checked.stdout
    assert len(list((tmp_path / '.ei/resource-sessions').glob('*.json'))) == 1
