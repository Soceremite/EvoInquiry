"""Resolve the EvoInquiry state root without silently creating or merging roots.

Default reads/writes use .ei. Legacy state needs explicit legacy-read or an
approved migration. This module is stdlib-only so existing helpers stay usable.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import warnings

try:
    from .registry_common import RegistryError, atomic_write, digest, file_digest, file_lock, local_path, read_record
except ImportError:
    from registry_common import RegistryError, atomic_write, digest, file_digest, file_lock, local_path, read_record


def tree_inventory(path):
    """Return content identity including safe link locators, never following links."""
    path = Path(path)
    records = []
    if not path.exists():
        return records
    for directory, folders, files in os.walk(path, followlinks=False):
        for name in sorted(folders + files):
            item = Path(directory) / name
            rel = item.relative_to(path).as_posix()
            if item.is_symlink():
                records.append({'path': rel, 'kind': 'symlink', 'target': os.readlink(item)})
            elif item.is_file():
                records.append({'path': rel, 'kind': 'file', 'sha256': file_digest(item)})
            elif item.is_dir():
                records.append({'path': rel, 'kind': 'directory'})
            else:
                raise RegistryError(f'Unsupported special file: {item}')
    return sorted(records, key=lambda record: record['path'])


def _migration_receipt(project):
    receipt = project / '.ei' / 'namespace-migration.json'
    if not receipt.is_file() or receipt.is_symlink():
        raise RegistryError('Both .aris and .ei exist without a verified migration receipt')
    try:
        data = json.loads(receipt.read_text())
        if (data['status'] != 'committed' or data['source'] != '.aris'
                or data['target'] != '.ei' or data['root'] != str(project)
                or digest(tree_inventory(project / '.aris')) != data['source_inventory_sha256']):
            raise RegistryError('Migration receipt is incomplete or the legacy backup changed')
        journal = local_path(project, '.ei-migration/' + data['transaction_id'])
        plan, progress = read_record(journal / 'plan.json'), read_record(journal / 'progress.json')
        expected = digest({key: value for key, value in plan.items() if key != 'plan_sha256'})
        if (progress['status'] != 'committed' or expected != plan['plan_sha256']
                or data['plan_sha256'] != expected or progress['plan_sha256'] != expected
                or plan['root'] != str(project) or data['mapping'] != plan['mapping']
                or data['source_inventory_sha256'] != plan['source_inventory_sha256']
                or tree_inventory(journal / 'backup') != plan['source_inventory']):
            raise RegistryError('Migration plan, backup and commit receipt do not agree')
        return data
    except (KeyError, json.JSONDecodeError):
        raise RegistryError('Invalid namespace migration receipt') from None


def resolve_state_root(root, mode='write'):
    """Return a root with no writes; modes are read, write, legacy-read, migration.

    EI_STATE_ROOT is an optional assertion, not an arbitrary redirection. The
    deprecated ARIS_STATE_ROOT is read-only and contradictory values fail.
    """
    project = Path(root).resolve()
    repository = os.environ.get('EI_REPO')
    old_repository = os.environ.get('ARIS_REPO')
    if repository and old_repository and Path(repository).resolve() != Path(old_repository).resolve():
        raise RegistryError('EI_REPO conflicts with the deprecated ARIS_REPO alias')
    if old_repository:
        warnings.warn('ARIS_REPO is a deprecated read-only repository alias; prefer EI_REPO',
                      FutureWarning)
    if mode not in ('read', 'write', 'legacy-read', 'migration'):
        raise RegistryError(f'Unknown resolver mode: {mode}')
    active, old = project / '.ei', project / '.aris'
    if active.is_symlink() or old.is_symlink():
        raise RegistryError('State roots must be real directories')
    for path in (active, old):
        if path.exists() and not path.is_dir():
            raise RegistryError(f'State root is not a directory: {path}')
    modern, legacy = os.environ.get('EI_STATE_ROOT'), os.environ.get('ARIS_STATE_ROOT')
    if modern and Path(modern).resolve() != active:
        raise RegistryError('EI_STATE_ROOT conflicts with the project state root')
    if legacy:
        if modern and Path(legacy).resolve() != Path(modern).resolve():
            raise RegistryError('New and deprecated state-root settings conflict')
        if mode != 'legacy-read' or Path(legacy).resolve() != old:
            raise RegistryError('ARIS_STATE_ROOT is supported only for explicit legacy-read')
        warnings.warn('ARIS_STATE_ROOT is deprecated; migrate to .ei', DeprecationWarning)
    journal_root = project / '.ei-migration'
    if mode != 'migration' and journal_root.is_dir():
        for receipt in journal_root.glob('*/progress.json'):
            try:
                status = json.loads(receipt.read_text()).get('status')
            except json.JSONDecodeError:
                raise RegistryError(f'Corrupt migration journal: {receipt}') from None
            if status not in ('committed', 'rolled-back'):
                raise RegistryError(f'Unfinished namespace migration: {receipt}; resume or roll back')
    if mode == 'migration':
        return active
    if mode == 'write':
        for receipt in (active / 'layout-transactions').glob('*/receipt.json'):
            if read_record(receipt).get('status') not in ('committed', 'rolled-back'):
                raise RegistryError(f'Unfinished layout change: {receipt}; resume or roll back')
    if active.exists() and old.exists():
        _migration_receipt(project)
        if mode == 'legacy-read':
            return old
        return active
    if old.exists():
        if mode == 'legacy-read':
            warnings.warn('Reading legacy .aris state; writing requires migration', DeprecationWarning)
            return old
        raise RegistryError('Legacy .aris state requires explicit legacy-read or approved migration')
    if mode == 'legacy-read':
        raise RegistryError('No legacy state root to read')
    return active


@contextmanager
def state_writer(root):
    """Prevent namespace switching while a participating writer runs."""
    project = Path(root).resolve()
    resolve_state_root(project, 'write')
    with file_lock(project / '.ei-namespace.lock', shared=True):
        yield resolve_state_root(project, 'write')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--mode', choices=['read', 'write', 'legacy-read', 'migration'], default='write')
    parser.add_argument('--guard-command', nargs=argparse.REMAINDER)
    parser.add_argument('--set-repo-pointer', help='Update the optional repository pointer under the namespace lock')
    arguments = list(sys.argv[1:])
    if '--guard-command' in arguments:
        separator = arguments.index('--guard-command') + 1
        if separator < len(arguments) and arguments[separator] == '--':
            arguments.pop(separator)
    args = parser.parse_args(arguments)
    try:
        if args.set_repo_pointer:
            if args.guard_command:
                raise RegistryError('Select either a command guard or repository-pointer update')
            repository = Path(args.set_repo_pointer).resolve()
            if not repository.is_dir():
                raise RegistryError('Repository pointer target must be an existing directory')
            with state_writer(args.root) as state:
                atomic_write(state / 'repo', (str(repository) + '\n').encode())
            return 0
        if args.guard_command:
            command = args.guard_command
            if command[0] == '--':
                command = command[1:]
            with state_writer(args.root):
                return subprocess.call(command)
        print(resolve_state_root(args.root, args.mode))
        return 0
    except RegistryError as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
