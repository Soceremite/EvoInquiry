"""Read-only project inventory and approved, journaled namespace migration.

Namespace migration and artifact layout selection are separate operations.
Legacy bytes are retained; recovery never silently discards post-switch writes.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

try:
    from .registry_common import (RegistryError, atomic_write, digest, file_digest,
                                  file_lock, fixed_ref, identifier, local_path, now, read_record, sync_directory, validate_schema)
    from .state_paths import resolve_state_root, state_writer, tree_inventory
except ImportError:
    from registry_common import (RegistryError, atomic_write, digest, file_digest,
                                 file_lock, fixed_ref, identifier, local_path, now, read_record, sync_directory, validate_schema)
    from state_paths import resolve_state_root, state_writer, tree_inventory


def discover_project(root, mode='read'):
    """Read a profile or return compat-v1 without creating files."""
    project = Path(root).resolve()
    state = resolve_state_root(project, mode)
    profile_path = state / 'project.yaml'
    if profile_path.exists():
        profile = validate_schema('project', read_record(profile_path))
        if profile['root'] != str(project):
            raise RegistryError('Project profile root differs; relocation needs an explicit update')
        return profile
    return {'schema_version': 1, 'namespace_version': 1, 'project_id': project.name,
            'layout_profile': 'compat-v1', 'root': str(project), 'authority_map': {},
            'compatibility_map': {}, 'migration_manifest_ref': None}


def init_project(root, project_id, profile='compat-v1', authority_map=None):
    """Create an explicitly selected profile; never overwrite an existing one."""
    project = Path(root).resolve()
    record = {'schema_version': 1, 'namespace_version': 1, 'project_id': identifier(project_id),
              'layout_profile': profile, 'root': str(project),
              'authority_map': authority_map or {}, 'compatibility_map': {},
              'migration_manifest_ref': None}
    validate_schema('project', record)
    with state_writer(project) as state:
        path = state / 'project.yaml'
        if path.exists():
            old = read_record(path)
            if old != record:
                raise RegistryError('Existing project profile differs; plan a separate layout change')
            return old
        atomic_write(path, record)
    return record


def inventory(root):
    """Inventory identity, ownership, potential writers and legacy artifacts, read-only."""
    project = Path(root).resolve()
    result = {'root': str(project), 'roots': {}, 'writers': [], 'legacy_artifacts': []}
    for namespace in ('.aris', '.ei'):
        state = project / namespace
        if state.is_symlink():
            raise RegistryError(f'Refusing symlink state root: {state}')
        records = tree_inventory(state)
        result['roots'][namespace] = {'exists': state.exists(), 'records': records,
                                      'sha256': digest(records)}
        result['roots'][namespace]['owners'] = [
            {'path': row['path'], 'owner_uid': (state / row['path']).lstat().st_uid,
             'mode': (state / row['path']).lstat().st_mode} for row in records]
        if not state.exists():
            continue
        for item in state.glob('runs/*.json'):
            record = read_record(item)
            active = [phase['phase'] for phase in record.get('phases', [])
                      if phase.get('status') == 'running']
            if active:
                result['writers'].append({'kind': 'workflow', 'id': record.get('run_id'),
                                          'path': item.relative_to(project).as_posix(), 'phases': active})
        for lock in state.rglob('*.lock.d'):
            if lock.is_dir():
                result['writers'].append({'kind': 'installer', 'path': lock.relative_to(project).as_posix()})
        for lease in state.glob('leases/*.json'):
            record = read_record(lease)
            if record.get('status') != 'released':
                result['writers'].append({'kind': 'lease', 'id': record.get('lease_id'),
                                          'path': lease.relative_to(project).as_posix()})
        for queue_file in state.glob('queue/**/*.json'):
            queue = read_record(queue_file)
            jobs = [job.get('id') for job in queue.get('jobs', [])
                    if job.get('status') in ('pending', 'running', 'failed_oom')]
            if jobs:
                result['writers'].append({'kind': 'queue', 'path': queue_file.relative_to(project).as_posix(),
                                          'jobs': jobs})
    for directory in ('idea-stage', 'refine-logs', 'review-stage', 'paper'):
        target = project / directory
        if target.is_dir():
            for path in sorted(target.rglob('*')):
                if path.is_file() and not path.is_symlink():
                    result['legacy_artifacts'].append({
                        **fixed_ref(project, path.relative_to(project)),
                        'owner_uid': path.stat().st_uid,
                        'review_status': 'legacy-unverified'})
    return result


def plan_migration(root, profile='compat-v1', *, transaction_id=None):
    """Return an immutable dry-run plan with zero filesystem changes."""
    if profile not in ('compat-v1', 'governed-v1'):
        raise RegistryError('Unknown artifact layout profile')
    project = Path(root).resolve()
    info = inventory(project)
    if not info['roots']['.aris']['exists']:
        raise RegistryError('There is no legacy state to migrate')
    if info['roots']['.ei']['exists']:
        raise RegistryError('Both roots exist; verify/reconcile an earlier migration first')
    plan = {'schema_version': 1, 'root': str(project), 'source': '.aris', 'target': '.ei',
            'profile': profile, 'transaction_id': identifier(transaction_id or 'migration-' +
                                                       info['roots']['.aris']['sha256'][:16]),
            'source_inventory': info['roots']['.aris']['records'],
            'source_inventory_sha256': info['roots']['.aris']['sha256'],
            'writers': info['writers'], 'declared_path_field_changes': [],
            'mapping': {'.aris/' + row['path']: '.ei/' + row['path']
                        for row in info['roots']['.aris']['records']},
            'rollback': 'Stop writers; preserve any post-switch files; restore the unchanged legacy root',
            'artifact_layout_change': False}
    # Artifact profile activation belongs to a separate, explicit operation.
    # Namespace conversion always retains compat-v1 for unprofiled legacy data.
    plan['plan_sha256'] = digest(plan)
    return plan


def _verified_copy(source, destination, expected):
    """Recover an interrupted local copy, retaining the incomplete tree for diagnosis."""
    if destination.is_symlink():
        raise RegistryError('Migration staging/backup cannot be a symlink')
    if destination.exists() and tree_inventory(destination) != expected:
        partial = destination.with_name(destination.name + '.partial-' + digest(tree_inventory(destination))[:16])
        if partial.exists():
            raise RegistryError('An earlier incomplete copy has the same identity; inspect it before recovery')
        os.replace(destination, partial)
        sync_directory(destination.parent)
    if not destination.exists():
        shutil.copytree(source, destination, symlinks=True)
    if tree_inventory(destination) != expected:
        raise RegistryError('Migration copy failed content verification; retained for retry/diagnosis')


def _check_plan(plan, approval):
    expected = digest({key: value for key, value in plan.items() if key != 'plan_sha256'})
    if plan.get('plan_sha256') != expected:
        raise RegistryError('Migration plan digest changed')
    if not (approval.get('approved') is True
            and approval.get('plan_sha256') == expected
            and approval.get('writers_stopped') is True
            and approval.get('confirmed_by') and approval.get('confirmed_at')):
        raise RegistryError('Migration requires plan-bound approval and verified writer shutdown')
    if plan.get('writers'):
        raise RegistryError('Plan lists active/unknown writers; stop them and generate a fresh plan')


def apply_migration(plan, approval, *, fail_at=None):
    """Apply an approved plan or resume its own journal; preserve every legacy byte.

    Caller must confirm external queue/process shutdown. Participating writers
    are also excluded by the namespace lock. fail_at is for fault-injection tests.
    """
    _check_plan(plan, approval)
    project = Path(plan['root']).resolve()
    transaction = identifier(plan['transaction_id'])
    journal = local_path(project, '.ei-migration/' + transaction)
    old, target = project / '.aris', project / '.ei'
    with file_lock(project / '.ei-namespace.lock', blocking=False):
        if journal.exists():
            if (journal / 'plan.json').exists():
                saved = read_record(journal / 'plan.json')
                if saved != plan:
                    raise RegistryError('Migration transaction is already bound to another plan')
            elif any(not item.name.startswith('.plan.json.') for item in journal.iterdir()):
                raise RegistryError('Migration journal is missing its plan; preserve and inspect unknown content')
            else:
                atomic_write(journal / 'plan.json', plan)
            progress = read_record(journal / 'progress.json') if (journal / 'progress.json').exists() else {
                'transaction_id': transaction, 'plan_sha256': plan['plan_sha256'],
                'root': str(project), 'status': 'prepared', 'created_at': now()}
            if progress['status'] == 'committed':
                resolve_state_root(project)
                return progress
            if progress['status'] == 'rolled-back':
                raise RegistryError('A rolled-back transaction needs a new plan/transaction ID')
        else:
            if target.exists() or not old.is_dir():
                raise RegistryError('State roots changed since migration planning')
            if digest(tree_inventory(old)) != plan['source_inventory_sha256']:
                raise RegistryError('Legacy content changed since migration planning')
            if inventory(project)['writers']:
                raise RegistryError('Writers became active since migration planning')
            if project.stat().st_dev != old.stat().st_dev:
                raise RegistryError('Cross-filesystem migration needs a separately verified copy protocol')
            atomic_write(journal / 'plan.json', plan)
            progress = {'transaction_id': transaction, 'plan_sha256': plan['plan_sha256'],
                        'root': str(project), 'status': 'prepared', 'created_at': now()}
            atomic_write(journal / 'progress.json', progress)
        if digest(tree_inventory(old)) != plan['source_inventory_sha256']:
            raise RegistryError('Legacy backup changed; recovery must not merge competing writers')
        for status in ('backed-up', 'staged', 'switched', 'committed'):
            order = ['prepared', 'backed-up', 'staged', 'switched', 'committed']
            if order.index(progress['status']) >= order.index(status):
                continue
            if status == 'backed-up':
                backup = journal / 'backup'
                _verified_copy(old, backup, plan['source_inventory'])
            elif status == 'staged':
                staging = journal / 'staging'
                _verified_copy(journal / 'backup', staging, plan['source_inventory'])
                progress['target_initial_sha256'] = digest(tree_inventory(staging))
            elif status == 'switched':
                staging = journal / 'staging'
                if not target.exists():
                    os.replace(staging, target)
                    sync_directory(project)
                if digest(tree_inventory(target)) != progress['target_initial_sha256']:
                    raise RegistryError('Switched target differs from the verified staging')
            elif status == 'committed':
                receipt = {'schema_version': 1, 'transaction_id': transaction,
                           'status': 'committed', 'root': str(project), 'source': '.aris', 'target': '.ei',
                           'source_inventory_sha256': plan['source_inventory_sha256'],
                           'plan_sha256': plan['plan_sha256'], 'mapping': plan['mapping'],
                           'backup': str(journal / 'backup'), 'approved_by': approval['confirmed_by'],
                           'approved_at': approval['confirmed_at'], 'committed_at': now()}
                if (target / 'namespace-migration.json').exists():
                    previous = read_record(target / 'namespace-migration.json')
                    if any(previous.get(key) != value for key, value in receipt.items() if key != 'committed_at'):
                        raise RegistryError('Interrupted migration receipt differs from this transaction')
                else:
                    atomic_write(target / 'namespace-migration.json', receipt)
                # Do not fabricate a governance profile for old evidence. The
                # unprofiled fallback keeps compat-v1 independently of migration.
            progress['status'] = status
            progress['updated_at'] = now()
            atomic_write(journal / 'progress.json', progress)
            if fail_at == status:
                raise RuntimeError(f'Injected migration interruption after {status}')
        return progress


def rollback_migration(root, transaction_id, approval):
    """Restore the unique legacy writer only after approval; never discard new data."""
    project = Path(root).resolve()
    journal = local_path(project, '.ei-migration/' + identifier(transaction_id))
    plan = read_record(journal / 'plan.json')
    _check_plan(plan, approval)
    with file_lock(project / '.ei-namespace.lock', blocking=False):
        progress = read_record(journal / 'progress.json')
        if progress['status'] == 'rolled-back':
            return progress
        old, target = project / '.aris', project / '.ei'
        if digest(tree_inventory(old)) != plan['source_inventory_sha256']:
            raise RegistryError('Legacy backup changed; rollback requires reconciliation')
        if target.exists():
            actual = [row for row in tree_inventory(target) if row['path'] != 'namespace-migration.json']
            if actual != plan['source_inventory']:
                preserved = journal / 'post-switch-preserved'
                if not preserved.exists():
                    shutil.copytree(target, preserved, symlinks=True)
                raise RegistryError('New post-switch data preserved; reconcile it before rollback')
            retired = journal / 'rolled-back-target'
            if retired.exists():
                raise RegistryError('Rollback target archive already exists; inspect before recovery')
            os.replace(target, retired)
        progress.update(status='rolled-back', updated_at=now())
        atomic_write(journal / 'progress.json', progress)
        return progress


def plan_layout(root, profile, *, transaction_id=None):
    """Plan a profile-only transition; authoritative historical bodies stay in place.

    Namespace migration must already be committed. This separate operation does
    not move stage files or classify their scientific quality.
    """
    project = Path(root).resolve()
    state = resolve_state_root(project, 'read')
    if not (state / 'project.yaml').exists():
        raise RegistryError('Initialize an explicit project profile before planning a layout change')
    before = discover_project(project)
    after = validate_schema('project', dict(before, layout_profile=profile))
    if before == after:
        raise RegistryError('Project already uses the selected layout')
    info = inventory(project)
    navigation = []
    if (state / 'index.json').is_file():
        navigation.append(fixed_ref(project, (state / 'index.json').relative_to(project)))
    for path in sorted((project / 'reports/current').glob('*.json')):
        # Alias snapshots are navigation, never evidence input references.
        navigation.append({'path': path.relative_to(project).as_posix(), 'sha256': file_digest(path)})
    plan = {'operation': 'switch-artifact-layout', 'root': str(project),
            'transaction_id': identifier(transaction_id or 'layout-' + digest(after)[:16]),
            'before': before, 'after': after, 'profile_sha256': file_digest(state / 'project.yaml'),
            'navigation': navigation, 'writers': info['writers'],
            'legacy_artifacts': info['legacy_artifacts'], 'body_moves': [],
            'rollback': 'Restore the profile; rebuild navigation from retained committed events'}
    plan['plan_sha256'] = digest(plan)
    return plan


def apply_layout(plan, approval, *, fail_at=None):
    """Apply a plan-bound profile change and preserve previous navigation snapshots."""
    _check_plan(plan, approval)
    project = Path(plan['root']).resolve()
    with file_lock(project / '.ei-namespace.lock', blocking=False):
        state = resolve_state_root(project, 'read')
        journal = local_path(project, '.ei/layout-transactions/' + identifier(plan['transaction_id']))
        profile = state / 'project.yaml'
        if (journal / 'receipt.json').exists():
            receipt = read_record(journal / 'receipt.json')
            if receipt['plan'] != plan:
                raise RegistryError('Layout transaction is bound to another plan')
            if receipt['status'] == 'committed':
                if read_record(profile) != plan['after']:
                    raise RegistryError('Committed layout profile changed; reconcile instead of replaying')
                return receipt
            if receipt['status'] == 'rolled-back':
                raise RegistryError('Rolled-back layout needs a new transaction')
        else:
            if file_digest(profile) != plan['profile_sha256'] or inventory(project)['writers']:
                raise RegistryError('Profile or active writers changed since layout planning')
            atomic_write(journal / 'before-project.yaml', profile.read_bytes())
            for reference in plan['navigation']:
                path = local_path(project, reference['path'])
                if file_digest(path) != reference['sha256']:
                    raise RegistryError('Navigation changed since layout planning')
                atomic_write(local_path(journal / 'navigation', reference['path']), path.read_bytes())
            receipt = {'plan': plan, 'approval': approval, 'status': 'prepared', 'created_at': now()}
            atomic_write(journal / 'receipt.json', receipt)
        if fail_at == 'prepared':
            raise RuntimeError('Injected layout interruption after prepared')
        current = read_record(profile)
        if current not in (plan['before'], plan['after']):
            raise RegistryError('Interrupted layout has a competing profile change')
        if current == plan['before']:
            atomic_write(profile, plan['after'])
        if fail_at == 'switched':
            raise RuntimeError('Injected layout interruption after switched')
        receipt.update(status='committed', committed_at=now())
        atomic_write(journal / 'receipt.json', receipt)
        return receipt


def rollback_layout(root, transaction_id, approval):
    """Restore layout selection while retaining all bodies, events and fixed references."""
    project = Path(root).resolve()
    with file_lock(project / '.ei-namespace.lock', blocking=False):
        state = resolve_state_root(project, 'read')
        journal = local_path(project, '.ei/layout-transactions/' + identifier(transaction_id))
        receipt = read_record(journal / 'receipt.json')
        plan = receipt['plan']
        _check_plan(plan, approval)
        if receipt['status'] == 'rolled-back':
            return receipt
        if inventory(project)['writers']:
            raise RegistryError('Stop and confirm all writers before layout rollback')
        current = read_record(state / 'project.yaml')
        if current not in (plan['before'], plan['after']):
            raise RegistryError('Profile changed since layout switch; preserve it for reconciliation')
        before = read_record(journal / 'before-project.yaml')
        if before != plan['before']:
            raise RegistryError('Layout backup profile changed')
        try:
            from .artifact_registry import ArtifactRegistry
        except ImportError:
            from artifact_registry import ArtifactRegistry
        registry = ArtifactRegistry(project)
        with file_lock(state / 'locks/artifacts.lock'):
            registry._pending()
            projection = registry._projection()
            for reference in projection['current'].values():
                from_ref = local_path(project, reference['path'])
                if file_digest(from_ref) != reference['sha256']:
                    raise RegistryError('Committed historical body changed; rollback requires reconciliation')
            atomic_write(state / 'project.yaml', before)
            for reference in projection['current'].values():
                atomic_write(registry._alias(reference['artifact_id']), reference)
            atomic_write(state / 'index.json', projection)
        receipt.update(status='rolled-back', rolled_back_at=now(),
                       retained='All published revisions and their metadata events')
        atomic_write(journal / 'receipt.json', receipt)
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init')
    init.add_argument('--project-id', required=True)
    init.add_argument('--profile', choices=['compat-v1', 'governed-v1'], default='compat-v1')
    sub.add_parser('audit')
    plan = sub.add_parser('plan-migration')
    plan.add_argument('--transaction-id')
    apply = sub.add_parser('apply-migration')
    apply.add_argument('--plan', required=True)
    apply.add_argument('--approval', required=True)
    rollback = sub.add_parser('rollback-migration')
    rollback.add_argument('--transaction-id', required=True)
    rollback.add_argument('--approval', required=True)
    layout = sub.add_parser('plan-layout')
    layout.add_argument('--profile', required=True, choices=['compat-v1', 'governed-v1'])
    layout.add_argument('--transaction-id')
    layout_apply = sub.add_parser('apply-layout')
    layout_apply.add_argument('--plan', required=True)
    layout_apply.add_argument('--approval', required=True)
    layout_rollback = sub.add_parser('rollback-layout')
    layout_rollback.add_argument('--transaction-id', required=True)
    layout_rollback.add_argument('--approval', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            result = init_project(args.root, args.project_id, args.profile)
        elif args.command == 'audit':
            result = inventory(args.root)
        elif args.command == 'plan-migration':
            result = plan_migration(args.root, transaction_id=args.transaction_id)
        elif args.command == 'apply-migration':
            result = apply_migration(read_record(args.plan), read_record(args.approval))
        elif args.command == 'rollback-migration':
            result = rollback_migration(args.root, args.transaction_id, read_record(args.approval))
        elif args.command == 'plan-layout':
            result = plan_layout(args.root, args.profile, transaction_id=args.transaction_id)
        elif args.command == 'apply-layout':
            result = apply_layout(read_record(args.plan), read_record(args.approval))
        else:
            result = rollback_layout(args.root, args.transaction_id, read_record(args.approval))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (RegistryError, OSError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
