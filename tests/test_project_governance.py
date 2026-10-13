"""Behavioral checks for namespace migration and evidence publication."""
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tools.artifact_registry import ArtifactRegistry, CurrentConflict, artifact_ref
from tools.project_registry import (apply_migration, discover_project, init_project,
                                    inventory, plan_migration, rollback_migration,
                                    plan_layout, apply_layout, rollback_layout)
from tools.registry_common import RegistryError, digest, fixed_ref, verify_ref
from tools.state_paths import resolve_state_root, state_writer, tree_inventory


def artifact(revision='r001', transaction='publish-1', content=b'fixed evidence'):
    return {'schema_version': 1, 'artifact_id': 'report', 'revision': revision,
            'sha256': digest(content), 'authority_path': f'reports/history/report/{revision}/body.md',
            'inputs': [], 'producer': {'kind': 'tool', 'id': 'test'},
            'transaction_id': transaction, 'lifecycle_status': 'published',
            'review_status': 'unreviewed', 'verdict_ref': None}


def approval(plan):
    return {'approved': True, 'plan_sha256': plan['plan_sha256'], 'writers_stopped': True,
            'confirmed_by': 'test-maintainer', 'confirmed_at': '2026-10-12T00:00:00Z'}


def legacy_project(root):
    directory = root / '.aris/runs'
    directory.mkdir(parents=True)
    data = {'run_id': 'workflow-001', 'executor_family': 'openai',
            'policy': {'provisional_advances': True},
            'phases': [{'phase': 'experiment', 'status': 'done', 'artifact': '.aris/results.json'},
                       {'phase': 'review', 'status': 'provisional', 'verdict_id': 'actual-review',
                        'reviewer': 'openai', 'review_independence': 'same-family'}]}
    (directory / 'workflow-001.json').write_text(json.dumps(data))
    return directory / 'workflow-001.json'


def test_discovery_without_profile_is_read_only(tmp_path):
    before = list(tmp_path.iterdir())
    assert discover_project(tmp_path)['layout_profile'] == 'compat-v1'
    assert inventory(tmp_path)['roots']['.ei']['exists'] is False
    assert list(tmp_path.iterdir()) == before


def test_legacy_requires_explicit_read_and_rejects_new_writer(tmp_path):
    legacy_project(tmp_path)
    before = tree_inventory(tmp_path)
    assert resolve_state_root(tmp_path, 'legacy-read') == tmp_path / '.aris'
    with pytest.raises(RegistryError, match='Legacy'):
        with state_writer(tmp_path):
            pytest.fail('Unexpected writable legacy root')
    assert tree_inventory(tmp_path) == before
    assert not (tmp_path / '.ei').exists()


@pytest.mark.parametrize('override',['','.ei/pending_review','.aris/pending_review'])
def test_manual_review_cannot_bypass_legacy_namespace_with_default_directory(tmp_path,override):
    legacy_project(tmp_path)
    server=Path(__file__).resolve().parents[1] / 'mcp-servers/manual-review/server.py'
    command=[sys.executable,'-B','-c',
        'import importlib.util, sys; spec=importlib.util.spec_from_file_location("probe",sys.argv[1]); '
        'module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)',str(server)]
    environment={**os.environ,'MANUAL_REVIEW_PENDING_DIR':override}
    result=subprocess.run(command,cwd=tmp_path,env=environment,capture_output=True,text=True,timeout=15)
    assert result.returncode!=0 and 'Legacy' in result.stderr
    assert not (tmp_path / '.ei').exists()


def test_conflicting_roots_and_environment_settings_are_rejected(tmp_path, monkeypatch):
    (tmp_path / '.aris').mkdir()
    (tmp_path / '.ei').mkdir()
    with pytest.raises(RegistryError, match='Both'):
        resolve_state_root(tmp_path)
    monkeypatch.setenv('EI_STATE_ROOT', str(tmp_path / '.ei'))
    monkeypatch.setenv('ARIS_STATE_ROOT', str(tmp_path / '.aris'))
    with pytest.raises(RegistryError, match='conflict'):
        resolve_state_root(tmp_path, 'legacy-read')


@pytest.mark.parametrize('stage', ['backed-up', 'staged', 'switched', 'committed'])
def test_migration_is_byte_preserving_and_recovers_each_commit_stage(tmp_path, stage):
    old = legacy_project(tmp_path)
    reference = fixed_ref(tmp_path, old.relative_to(tmp_path))
    before = tree_inventory(tmp_path)
    plan = plan_migration(tmp_path)
    assert tree_inventory(tmp_path) == before  # dry-run must not create a lock.
    with pytest.raises(RuntimeError, match='Injected'):
        apply_migration(plan, approval(plan), fail_at=stage)
    result = apply_migration(plan, approval(plan))
    assert result['status'] == 'committed'
    assert resolve_state_root(tmp_path) == tmp_path / '.ei'
    assert (tmp_path / '.ei/runs/workflow-001.json').read_bytes() == old.read_bytes()
    assert verify_ref(tmp_path, reference) == tmp_path / '.ei/runs/workflow-001.json'
    assert apply_migration(plan, approval(plan)) == result
    rollback_migration(tmp_path, plan['transaction_id'], approval(plan))
    assert not (tmp_path / '.ei').exists()
    assert old.read_bytes() == (tmp_path / '.ei-migration' / plan['transaction_id'] /
                                'rolled-back-target/runs/workflow-001.json').read_bytes()


def test_changed_source_missing_approval_and_active_writer_block_migration(tmp_path):
    old = legacy_project(tmp_path)
    plan = plan_migration(tmp_path)
    with pytest.raises(RegistryError, match='approval'):
        apply_migration(plan, {})
    old.write_text('{}')
    with pytest.raises(RegistryError, match='changed'):
        apply_migration(plan, approval(plan))
    old.write_text(json.dumps({'run_id': 'active', 'phases': [{'phase': 'train', 'status': 'running'}]}))
    plan = plan_migration(tmp_path)
    with pytest.raises(RegistryError, match='writers'):
        apply_migration(plan, approval(plan))


def test_namespace_lock_blocks_migration_and_new_data_blocks_rollback(tmp_path):
    legacy_project(tmp_path)
    plan = plan_migration(tmp_path)
    from tools.registry_common import file_lock
    with file_lock(tmp_path / '.ei-namespace.lock', shared=True):
        with pytest.raises(RegistryError, match='Active writer'):
            apply_migration(plan, approval(plan))
    apply_migration(plan, approval(plan))
    (tmp_path / '.ei/new-event.json').write_text('{"new":true}')
    with pytest.raises(RegistryError, match='preserved'):
        rollback_migration(tmp_path, plan['transaction_id'], approval(plan))
    assert (tmp_path / '.ei/new-event.json').exists()
    assert (tmp_path / '.ei-migration' / plan['transaction_id'] /
            'post-switch-preserved/new-event.json').exists()


@pytest.mark.parametrize('stage', ['body', 'event', 'alias', 'projection'])
def test_publication_crash_recovers_without_duplicates(tmp_path, stage):
    init_project(tmp_path, 'project-1', 'governed-v1')
    registry = ArtifactRegistry(tmp_path)
    record = artifact()
    with pytest.raises(RuntimeError, match='Injected'):
        registry.publish_artifact(record, b'fixed evidence', fail_at=stage)
    assert (tmp_path / record['authority_path']).read_bytes() == b'fixed evidence'
    assert registry.audit()['status'] == 'BLOCKED'
    registry.reconcile(record['transaction_id'])
    assert registry.publish_artifact(record, b'fixed evidence') == artifact_ref(record)
    assert registry.audit()['status'] == 'PASS'
    assert len(registry.events()) == 2
    assert (tmp_path / 'MANIFEST.md').read_text().count('<!-- ei-transaction:publish-1 -->') == 1


def test_fixed_references_survive_alias_drift_and_reconcile(tmp_path):
    init_project(tmp_path, 'project-1', 'governed-v1')
    registry = ArtifactRegistry(tmp_path)
    first = registry.publish_artifact(artifact(), b'fixed evidence')
    second = registry.publish_artifact(artifact('r002', 'publish-2', b'next'), b'next', first)
    (tmp_path / 'reports/current/report.json').write_text(json.dumps(first))
    assert verify_ref(tmp_path, second).read_bytes() == b'next'
    assert registry.audit()['problems'] == ['Alias drift: report']
    registry.reconcile()
    assert registry.current('report') == second
    with pytest.raises(RegistryError, match='floating'):
        verify_ref(tmp_path, fixed_ref(tmp_path, 'reports/history/report/r002/body.md') |
                   {'path': 'reports/current/report.json'})


def publish_worker(root, revision, gate, output):
    gate.wait()
    registry = ArtifactRegistry(root)
    record = artifact(revision, 'tx-' + revision, revision.encode())
    try:
        registry.publish_artifact(record, revision.encode())
        output.put('committed')
    except CurrentConflict:
        output.put('conflict')


def test_concurrent_publications_keep_both_revisions_and_report_cas_conflict(tmp_path):
    init_project(tmp_path, 'project-1', 'governed-v1')
    context = multiprocessing.get_context('spawn')
    gate, output = context.Event(), context.Queue()
    workers = [context.Process(target=publish_worker, args=(str(tmp_path), revision, gate, output))
               for revision in ('r001', 'r002')]
    for worker in workers:
        worker.start()
    gate.set()
    assert sorted(output.get(timeout=20) for _ in workers) == ['committed', 'conflict']
    for worker in workers:
        worker.join(timeout=10)
        assert worker.exitcode == 0
    registry = ArtifactRegistry(tmp_path)
    assert len(registry.rebuild_index()['revisions']) == 2
    assert registry.audit()['status'] == 'PASS'


def test_transaction_conflict_corruption_and_scientific_boundary(tmp_path):
    init_project(tmp_path, 'project-1', 'governed-v1')
    registry = ArtifactRegistry(tmp_path)
    record = artifact()
    registry.publish_artifact(record, b'fixed evidence')
    with pytest.raises(RegistryError, match='revision'):
        registry.publish_artifact(artifact(transaction='other'), b'fixed evidence')
    accepted = artifact('r002', 'approved') | {'review_status': 'accepted'}
    with pytest.raises(RegistryError, match='receipt'):
        registry.publish_artifact(accepted, b'fixed evidence')
    events = tmp_path / '.ei/artifact-events.jsonl'
    with events.open('ab') as handle:
        handle.write(b'{"half":')
    with pytest.raises(RegistryError, match='Partial'):
        registry.publish_artifact(artifact('r003', 'tx3'), b'fixed evidence')
    assert registry.audit()['status'] == 'BLOCKED'


def test_existing_manual_content_stays_legacy_without_inventing_review(tmp_path):
    (tmp_path / 'IDEA_REPORT.md').write_bytes(b'old manual notes')
    record = artifact(content=b'old manual notes') | {
        'authority_path': 'IDEA_REPORT.md', 'lifecycle_status': 'legacy-unverified',
        'review_status': 'legacy-unverified'}
    registry = ArtifactRegistry(tmp_path)
    registry.register_existing(record)
    assert (tmp_path / 'IDEA_REPORT.md').read_bytes() == b'old manual notes'
    assert registry.rebuild_index()['revisions']['report@r001']['review_status'] == 'legacy-unverified'


@pytest.mark.parametrize('stage', ['prepared', 'switched'])
def test_layout_switch_is_separate_recovers_and_keeps_post_switch_revisions(tmp_path, stage):
    init_project(tmp_path, 'project-1')
    manual = tmp_path / 'paper/notes.md'
    manual.parent.mkdir()
    manual.write_bytes(b'manual historical evidence')
    before = tree_inventory(tmp_path)
    plan = plan_layout(tmp_path, 'governed-v1')
    assert tree_inventory(tmp_path) == before and plan['body_moves'] == []
    with pytest.raises(RuntimeError, match='Injected'):
        apply_layout(plan, approval(plan), fail_at=stage)
    with pytest.raises(RegistryError, match='Unfinished layout'):
        with state_writer(tmp_path):
            pytest.fail('Competing writer admitted')
    apply_layout(plan, approval(plan))
    registry = ArtifactRegistry(tmp_path)
    reference = registry.publish_artifact(artifact(), b'fixed evidence')
    rollback_layout(tmp_path, plan['transaction_id'], approval(plan))
    assert discover_project(tmp_path)['layout_profile'] == 'compat-v1'
    assert verify_ref(tmp_path, reference).read_bytes() == b'fixed evidence'
    assert manual.read_bytes() == b'manual historical evidence'
    assert registry.audit()['status'] == 'PASS'


@pytest.mark.parametrize('destination', ['backup', 'staging'])
def test_migration_recovers_incomplete_copy_and_preserves_partial_bytes(tmp_path, monkeypatch, destination):
    legacy_project(tmp_path)
    plan = plan_migration(tmp_path)
    import tools.project_registry as registry
    original = registry.shutil.copytree
    def interrupted(source, target, *args, **kwargs):
        if Path(target).name == destination:
            Path(target).mkdir()
            (Path(target) / 'partial.log').write_bytes(b'interrupted')
            raise OSError('simulated interrupted file copy')
        return original(source, target, *args, **kwargs)
    monkeypatch.setattr(registry.shutil, 'copytree', interrupted)
    with pytest.raises(OSError, match='interrupted'):
        apply_migration(plan, approval(plan))
    monkeypatch.setattr(registry.shutil, 'copytree', original)
    assert apply_migration(plan, approval(plan))['status'] == 'committed'
    preserved = list((tmp_path / '.ei-migration' / plan['transaction_id']).glob(destination + '.partial-*/partial.log'))
    assert len(preserved) == 1 and preserved[0].read_bytes() == b'interrupted'


@pytest.mark.parametrize('stage', ['prepared', 'truncated'])
def test_partial_event_tail_repair_is_bound_preserved_and_recovers(tmp_path, stage):
    init_project(tmp_path, 'project-1', 'governed-v1')
    registry = ArtifactRegistry(tmp_path)
    reference = registry.publish_artifact(artifact(), b'fixed evidence')
    path = tmp_path / '.ei/artifact-events.jsonl'
    with path.open('ab') as handle:
        handle.write(b'{"unfinished":')
    raw, before = path.read_bytes(), tree_inventory(tmp_path)
    plan = registry.plan_partial_event_repair()
    assert tree_inventory(tmp_path) == before
    with pytest.raises(RegistryError, match='authorization'):
        registry.repair_partial_event(plan, {})
    with pytest.raises(RuntimeError, match='Injected'):
        registry.repair_partial_event(plan, approval(plan), fail_at=stage)
    with pytest.raises(RegistryError):
        registry.publish_artifact(artifact('r002', 'publish-2'), b'fixed evidence', reference)
    receipt = registry.repair_partial_event(plan, approval(plan))
    assert receipt['status'] == 'tail-quarantined'
    assert (tmp_path / plan['backup']).read_bytes() == raw
    assert registry.repair_partial_event(plan, approval(plan)) == receipt
    assert registry.audit()['status'] == 'PASS'


def test_symlinked_state_subdirectory_and_modified_backup_block_writes(tmp_path):
    legacy_project(tmp_path)
    plan = plan_migration(tmp_path)
    apply_migration(plan, approval(plan))
    backup = tmp_path / '.ei-migration' / plan['transaction_id'] / 'backup/runs/workflow-001.json'
    backup.write_bytes(b'changed')
    with pytest.raises(RegistryError, match='do not agree'):
        resolve_state_root(tmp_path)


def crash_publication_worker(root):
    import os
    try:
        ArtifactRegistry(root).publish_artifact(artifact(), b'fixed evidence', fail_at='alias')
    except RuntimeError:
        os._exit(23)


def test_process_exit_releases_publication_lock_and_preserves_recovery_intent(tmp_path):
    init_project(tmp_path, 'project-1', 'governed-v1')
    process = multiprocessing.get_context('spawn').Process(target=crash_publication_worker, args=(str(tmp_path),))
    process.start()
    process.join(20)
    assert process.exitcode == 23
    registry = ArtifactRegistry(tmp_path)
    assert registry.audit()['status'] == 'BLOCKED'
    registry.reconcile('publish-1')
    assert registry.audit()['status'] == 'PASS'


def test_unreliable_lock_backend_stops_before_creating_project_state(tmp_path,monkeypatch):
    import fcntl
    import tools.registry_common as common
    monkeypatch.setattr(common,'_VERIFIED_LOCK_DEVICES',set())
    monkeypatch.setattr(fcntl,'flock',lambda *args:None)
    with pytest.raises(RegistryError,match='lock exclusion failed'):
        init_project(tmp_path,'unsafe-project')
    assert not (tmp_path / '.ei').exists()
    assert list(tmp_path.iterdir())==[]


def test_symlinked_transaction_directory_cannot_write_outside_project(tmp_path):
    outside=tmp_path / 'external-target'
    outside.mkdir()
    init_project(tmp_path,'project-1','governed-v1')
    (tmp_path / '.ei/transactions').symlink_to(outside,target_is_directory=True)
    with pytest.raises(RegistryError,match='Symlink'):
        ArtifactRegistry(tmp_path).publish_artifact(artifact(),b'fixed evidence')
    assert list(outside.iterdir())==[]
