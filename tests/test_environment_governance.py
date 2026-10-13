"""Environment safety checks use real isolated interpreter probes and CPU checks."""
import json

import pytest

from tests.governance_helpers import consumer, make_environment
from tools.environment_registry import EnvironmentRegistry, environment_diff, verify_environment
from tools.registry_common import RegistryError, atomic_write, fixed_ref, read_record, verify_ref


def test_frozen_reuse_does_not_edit_packages_and_failed_candidate_leaves_old_binding(tmp_path):
    registry = EnvironmentRegistry(tmp_path)
    first = make_environment(tmp_path)
    frozen = read_record(tmp_path / first['path'])
    assert registry.find_compatible({'python': frozen['observed_fingerprint']['python']}) == [first]
    registry.bind_consumer(consumer(first))
    before = (tmp_path / first['path']).read_bytes()
    second = make_environment(tmp_path, revision='r002', fail_stage='numerical')
    assert read_record(tmp_path / second['path'])['lifecycle'] == 'rejected'
    with pytest.raises(RegistryError, match='failed'):
        registry.promote_candidate(second, {'approved': True, 'candidate_ref': second})
    assert (tmp_path / first['path']).read_bytes() == before
    assert read_record(tmp_path / '.ei/consumers/job-1.json')['env_revision'] == first
    assert verify_environment(tmp_path, first) == frozen['observed_fingerprint']


def test_recipe_sources_can_change_after_promotion_without_drifting_old_environment(tmp_path):
    first = make_environment(tmp_path)
    (tmp_path / 'env/recipes/cpu/r001/lock.json').write_text('{"development":"changed"}')
    assert verify_environment(tmp_path, first)


def test_busy_consumer_cannot_rebind_and_expired_lease_needs_real_termination(tmp_path):
    registry = EnvironmentRegistry(tmp_path)
    first = make_environment(tmp_path)
    second = make_environment(tmp_path, revision='r002')
    registry.bind_consumer(consumer(first))
    registry.acquire_lease('job-1', 'lease-1', 'job-1', expires_at='2020-01-01T00:00:00+00:00')
    with pytest.raises(RegistryError, match='cannot be rebound'):
        registry.bind_consumer(consumer(second))
    reconciliation = registry.reconcile_leases({})
    assert reconciliation[0]['expired'] and reconciliation[0]['status'] == 'protected-needs-reconciliation'
    assert 'lease:lease-1' in registry.plan_retirement(first)['blockers']
    atomic_write(tmp_path / 'queue/termination.json', {'job_ref':'job-1','execution_run_id':'job-1','status':'completed',
                 'confirmed_at':'2026-10-12T00:00:00Z','source':'test-process-observer',
                 'queued':False,'process_alive':False})
    receipt = fixed_ref(tmp_path, 'queue/termination.json')
    assert registry.reconcile_leases({'job-1':receipt})[0]['status'] == 'released'


@pytest.mark.parametrize('lifecycle', ['unknown', 'abandoned', 'completed'])
def test_unknown_provenance_and_paper_pins_protect_retirement(tmp_path, lifecycle):
    registry = EnvironmentRegistry(tmp_path)
    environment = make_environment(tmp_path)
    atomic_write(tmp_path / 'paper/evidence.json', {'revision':'r001'})
    record = consumer(environment, lifecycle=lifecycle)
    record['pin'] = [{'reason':'published paper reproduction','ref':fixed_ref(tmp_path,'paper/evidence.json')}]
    if lifecycle == 'unknown':
        record.update(importance='unknown',source=None,confirmed_by=None,confirmed_at=None)
    registry.bind_consumer(record)
    plan = registry.plan_retirement(environment)
    assert plan['status'] == 'BLOCKED' and not plan['deletion_authorized']
    assert 'reproducibility-pin:job-1' in plan['blockers']
    with pytest.raises(RegistryError, match='pins'):
        registry.bind_consumer(dict(record, pin=[]))


def test_diff_retains_removed_transitive_versions_and_sources():
    diff = environment_diff({'packages':{'a':{'version':'2','source':'trusted'},'b':'1'}},
                            {'packages':{'a':{'version':'1','source':'changed'}}})
    assert {row['path'] for row in diff} == {'packages.a.version','packages.a.source','packages.b'}
    assert next(row for row in diff if row['path']=='packages.b')['kind'] == 'removed'


def test_binding_reference_remains_fixed_after_lease_and_lifecycle_updates(tmp_path):
    registry = EnvironmentRegistry(tmp_path)
    environment = make_environment(tmp_path)
    record = consumer(environment)
    reference = registry.bind_consumer(record)
    registry.acquire_lease('job-1','lease-1','job-1',expires_at='2030-01-01T00:00:00Z')
    assert read_record(verify_ref(tmp_path, reference)) == record
    updated = read_record(tmp_path / '.ei/consumers/job-1.json') | {'lifecycle':'completed'}
    registry.bind_consumer(updated)
    assert read_record(verify_ref(tmp_path, reference)) == record


def test_pin_release_intent_recovers_and_blocks_other_mutations(tmp_path, monkeypatch):
    import tools.environment_registry as module
    registry = EnvironmentRegistry(tmp_path)
    environment = make_environment(tmp_path)
    atomic_write(tmp_path / 'paper/evidence.json', {'fixed':True})
    record = consumer(environment, lifecycle='completed')
    record['pin'] = [{'reason':'reproduction', 'ref':fixed_ref(tmp_path,'paper/evidence.json')}]
    before = registry.bind_consumer(record)
    plan = registry.plan_pin_release('job-1',record['pin'],'approved end of reproduction retention')
    approval = {'approved':True, 'plan_sha256':plan['plan_sha256'],
                'confirmed_by':'test-maintainer', 'confirmed_at':'2026-10-12T00:00:00Z'}
    original = module.atomic_write
    def fail_receipt(path, data):
        if Path(path).parent.name == 'pin-releases' and data.get('status') == 'complete':
            raise OSError('interrupted final receipt')
        return original(path, data)
    from pathlib import Path
    monkeypatch.setattr(module,'atomic_write',fail_receipt)
    with pytest.raises(OSError,match='interrupted'):
        registry.release_pins(plan,approval)
    assert 'unfinished-pin-release:job-1' in registry.plan_retirement(environment)['blockers']
    with pytest.raises(RegistryError,match='Unfinished'):
        registry.bind_consumer(read_record(tmp_path / '.ei/consumers/job-1.json'))
    monkeypatch.setattr(module,'atomic_write',original)
    result = registry.release_pins(plan,approval)
    assert registry.release_pins(plan,approval) == result
    assert read_record(verify_ref(tmp_path,before))['pin'] == record['pin']
    assert read_record(verify_ref(tmp_path,result['binding_ref']))['pin'] == []
