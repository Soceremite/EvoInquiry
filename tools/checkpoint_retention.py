#!/usr/bin/env python3
"""Bounded local checkpoint publication and retention; no model serialization.

Use a dedicated run directory. Writers and loader validators are supplied by
the training program. CLI pruning is a preview unless --apply is supplied.
Only cooperating processes are synchronized; this is not a hostile filesystem
security boundary, distributed writer, or object-store transaction protocol.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager, ExitStack
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
from typing import Callable, Iterator
import uuid

MANIFEST = '.evo-checkpoints.json'
LOCK = '.evo-checkpoints.lock'
ID = re.compile(r'ckpt-[a-f0-9]{32}\Z')


class RetentionError(RuntimeError):
    """A save or rotation cannot satisfy this run's established policy."""


def _integer(value: object, name: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise RetentionError(f'{name} must be an integer >= {minimum}')
    return value


def _atomic_json(path: Path, data: dict) -> None:
    temporary = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    try:
        with temporary.open('x', encoding='utf-8') as output:
            json.dump(data, output, indent=2, sort_keys=True, allow_nan=False)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        if hasattr(os, 'O_DIRECTORY'):
            descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def _files(directory: Path) -> dict:
    """Hash regular files only, refusing symlinks and special files."""
    if directory.is_symlink() or not directory.is_dir():
        raise RetentionError(f'Artifact is not a regular directory: {directory.name}')
    result = {}
    for current, directories, files in os.walk(directory, followlinks=False):
        for name in directories + files:
            path = Path(current) / name
            mode = path.lstat().st_mode
            if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise RetentionError(f'Unsupported artifact path: {path.relative_to(directory)}')
        for name in files:
            path = Path(current) / name
            digest = hashlib.sha256()
            with path.open('rb') as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b''):
                    digest.update(chunk)
            result[path.relative_to(directory).as_posix()] = {
                'bytes': path.stat().st_size, 'sha256': digest.hexdigest()}
    return result


def _flush_directories(directory: Path) -> None:
    """Persist nested directory entries before committing a local artifact."""
    if not hasattr(os, 'O_DIRECTORY'):
        return
    for current, _, _ in os.walk(directory, topdown=False, followlinks=False):
        descriptor = os.open(current, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


@contextmanager
def _lock(root: Path) -> Iterator[None]:
    path = root / LOCK
    if path.is_symlink():
        raise RetentionError('Refusing a symlinked lock file')
    flags = os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0)
    with os.fdopen(os.open(path, flags, 0o600), 'r+b') as handle:
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise RetentionError('Another writer owns this checkpoint store') from error
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                raise RetentionError('Another writer owns this checkpoint store') from error
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


class CheckpointStore:
    """Manage explicitly owned artifact directories on a local filesystem.

    A validator must load the new artifact and check its required training state.
    A passed validator is a caller receipt, not universal proof of recoverability.
    The byte budget covers all non-metadata files under root, including orphans.
    """

    def __init__(self, root: str | Path):
        path = Path(root)
        if path.is_symlink():
            raise RetentionError('Use a real checkpoint directory, not a symlink')
        self.root = path.resolve()
        if not self.root.is_dir():
            raise RetentionError('Checkpoint directory does not exist')
        self._read()

    @classmethod
    def create(cls, root: str | Path, *, run_id: str, budget_bytes: int,
               keep_last: int = 2, reserve_bytes: int = 0) -> 'CheckpointStore':
        path = Path(root)
        if path.is_symlink():
            raise RetentionError('Use a real checkpoint directory, not a symlink')
        if not isinstance(run_id, str) or not run_id.strip():
            raise RetentionError('run_id is required')
        _integer(budget_bytes, 'budget_bytes', 1)
        _integer(keep_last, 'keep_last', 2)
        _integer(reserve_bytes, 'reserve_bytes')
        path.mkdir(parents=True, exist_ok=True)
        path = path.resolve()
        with _lock(path):
            if (path / MANIFEST).exists() or (path / MANIFEST).is_symlink():
                raise RetentionError('A checkpoint manifest already exists; open this store instead')
            _atomic_json(path / MANIFEST, {
                'schema_version': 1, 'run_id': run_id,
                'policy': {'budget_bytes': budget_bytes, 'keep_last': keep_last,
                           'reserve_bytes': reserve_bytes},
                'generation': 0, 'entries': [], 'garbage': [], 'roles': {},
                'lifecycle': {'state': 'active'}})
        return cls(path)

    def _read(self) -> dict:
        path = self.root / MANIFEST
        if path.is_symlink():
            raise RetentionError('Refusing a symlinked manifest')
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if data['schema_version'] != 1 or not isinstance(data['run_id'], str):
                raise ValueError('identity/schema')
            policy = data['policy']
            _integer(policy['budget_bytes'], 'budget_bytes', 1)
            _integer(policy['keep_last'], 'keep_last', 2)
            _integer(policy['reserve_bytes'], 'reserve_bytes')
            _integer(data['generation'], 'generation')
            ids = set()
            for group in ('entries', 'garbage'):
                if not isinstance(data[group], list):
                    raise ValueError(group)
                for entry in data[group]:
                    identifier = entry['id']
                    if not isinstance(identifier, str) or not ID.fullmatch(identifier) or identifier in ids:
                        raise ValueError('artifact id')
                    ids.add(identifier)
                    if entry['kind'] not in ('resume', 'weights'):
                        raise ValueError('artifact kind')
                    _integer(entry['step'], 'step')
                    _integer(entry['sequence'], 'sequence')
                    if not isinstance(entry['pins'], list) or not all(isinstance(p, str) and p for p in entry['pins']):
                        raise ValueError('pins')
                    if not isinstance(entry['files'], dict) or not entry['files']:
                        raise ValueError('file manifest')
                    for name, metadata in entry['files'].items():
                        parts = Path(name).parts
                        if not parts or Path(name).is_absolute() or '..' in parts or '\\' in name:
                            raise ValueError('file path')
                        _integer(metadata['bytes'], 'file bytes')
                        if not re.fullmatch(r'[a-f0-9]{64}', metadata['sha256']):
                            raise ValueError('file hash')
                    if not isinstance(entry['validation'], dict) or entry['validation'].get('passed') is not True:
                        raise ValueError('validation receipt')
            active = {entry['id'] for entry in data['entries']}
            if not isinstance(data['roles'], dict) or any(
                    name not in ('best', 'final') or identifier not in active
                    for name, identifier in data['roles'].items()):
                raise ValueError('roles')
            lifecycle = data.setdefault('lifecycle', {'state': 'active'})
            if not isinstance(lifecycle, dict) or lifecycle.get('state') not in ('active', 'completed', 'stopped'):
                raise ValueError('lifecycle')
            if lifecycle['state'] != 'active':
                _integer(lifecycle['step'], 'terminal step')
                if not isinstance(lifecycle['reason'], str) or not lifecycle['reason'].strip():
                    raise ValueError('terminal reason')
                archive = lifecycle['archive']
                if not isinstance(archive, dict) or not isinstance(archive['root'], str) or not archive['root']:
                    raise ValueError('archive receipt')
                if not isinstance(archive['id'], str) or not ID.fullmatch(archive['id']):
                    raise ValueError('archive artifact id')
                if archive.get('scope', 'local') not in ('local', 'comparison'):
                    raise ValueError('archive scope')
                if (not isinstance(archive['run_id'], str) or not archive['run_id']
                        or not isinstance(archive['files'], dict) or not archive['files']):
                    raise ValueError('archive identity/files')
            return data
        except (OSError, ValueError, TypeError, KeyError) as error:
            raise RetentionError(f'Invalid checkpoint manifest: {error}') from error

    def _write(self, data: dict) -> None:
        data['generation'] += 1
        _atomic_json(self.root / MANIFEST, data)

    def _valid(self, entry: dict, *, partial: bool = False) -> bool:
        path = self.root / entry['id']
        if partial and not path.exists() and not path.is_symlink():
            return True
        try:
            actual = _files(path)
            return (all(name in entry['files'] and entry['files'][name] == value
                        for name, value in actual.items()) if partial else actual == entry['files'])
        except (OSError, RetentionError):
            return False

    def _bytes(self) -> int:
        total = 0
        for current, directories, files in os.walk(self.root, followlinks=False):
            for name in files:
                path = Path(current) / name
                if path.parent == self.root and name in (MANIFEST, LOCK):
                    continue
                try:
                    total += path.lstat().st_size
                except FileNotFoundError:
                    # A monitoring reader can observe an atomic metadata rename
                    # or completed deletion while traversing the directory.
                    continue
            for name in directories:
                path = Path(current) / name
                if path.is_symlink():
                    total += path.lstat().st_size
        return total

    def _plan(self, data: dict) -> dict:
        valid = {entry['id'] for entry in data['entries'] if self._valid(entry)}
        resumes = sorted((e for e in data['entries'] if e['kind'] == 'resume' and e['id'] in valid),
                         key=lambda e: (e['step'], e['sequence']), reverse=True)
        keep = ({e['id'] for e in resumes[:data['policy']['keep_last']]}
                if data['lifecycle']['state'] == 'active' else set())
        keep.update(data['roles'].values())
        keep.update(e['id'] for e in data['entries'] if e['pins'])
        corrupt = sorted(e['id'] for e in data['entries'] if e['id'] not in valid)
        # Changed files need diagnosis; never delete them as ordinary old artifacts.
        keep.update(corrupt)
        remove = sorted(e['id'] for e in data['entries'] if e['id'] not in keep)
        garbage = [e['id'] for e in data['garbage'] if self._valid(e, partial=True)]
        blocked = [e['id'] for e in data['garbage'] if e['id'] not in garbage]
        known = {e['id'] for e in data['entries'] + data['garbage']} | {MANIFEST, LOCK}
        unregistered = sorted(p.name for p in self.root.iterdir() if p.name not in known)
        return {'run_id': data['run_id'], 'generation': data['generation'],
                'policy': data['policy'], 'bytes_used': self._bytes(),
                'lifecycle': data['lifecycle'],
                'filesystem_free_bytes': shutil.disk_usage(self.root).free,
                'latest': resumes[0]['id'] if resumes else None,
                'latest_step': resumes[0]['step'] if resumes else None,
                'keep': sorted(keep), 'remove': remove,
                'garbage_remove': garbage, 'garbage_blocked': blocked,
                'corrupt_or_missing': corrupt, 'unregistered': unregistered,
                'roles': data['roles']}

    def status(self) -> dict:
        # Avoid blocking a writer for a potentially large hash scan. Retry a
        # reader snapshot if a cooperating publication changed its generation.
        for _ in range(5):
            data = self._read()
            result = self._plan(data)
            if self._read()['generation'] == data['generation']:
                return result
        raise RetentionError('Checkpoint state changed during inspection; retry the status query')

    def latest(self) -> Path | None:
        identifier = self.status()['latest']
        return self.root / identifier if identifier else None

    def _clean_garbage(self, data: dict) -> list[str]:
        removed = []
        for entry in list(data['garbage']):
            if not self._valid(entry, partial=True):
                continue
            path = self.root / entry['id']
            if path.exists():
                shutil.rmtree(path)
            data['garbage'].remove(entry)
            self._write(data)
            removed.append(entry['id'])
        return removed

    def _archive_store(self, data: dict) -> 'CheckpointStore':
        if (data['lifecycle']['state'] == 'active'
                or data['lifecycle']['archive'].get('scope', 'local') == 'local'):
            return self
        return CheckpointStore(data['lifecycle']['archive']['root'])

    def _verify_archive(self, data: dict) -> None:
        if data['lifecycle']['state'] == 'active':
            return
        receipt = data['lifecycle']['archive']
        store = self._archive_store(data)
        archived_data = data if store.root == self.root else store._read()
        archived = next((e for e in archived_data['entries'] if e['id'] == receipt['id']), None)
        if (archived is None or archived['kind'] != 'weights'
                or archived_data['run_id'] != receipt['run_id']
                or archived['files'] != receipt['files'] or not store._valid(archived)):
            raise RetentionError('Archived inference weights are unavailable or changed; cleanup retained')

    def _prune(self, data: dict) -> dict:
        # A prior finish may have committed before deletion was interrupted.
        # Never continue that deletion journal using a now-damaged survivor.
        # Callers hold the local and (when applicable) archive store locks.
        self._verify_archive(data)
        plan = self._plan(data)
        candidates = [e for e in data['entries'] if e['id'] in plan['remove']]
        if candidates:
            # Persist ownership before deleting; an interrupted deletion can resume
            # only if the surviving files are an unchanged subset of this receipt.
            data['entries'] = [e for e in data['entries'] if e['id'] not in plan['remove']]
            data['garbage'].extend(candidates)
            self._write(data)
        removed = self._clean_garbage(data)
        return {'deleted': removed, 'status': self._plan(data)}

    def prune(self, *, apply: bool = False) -> dict:
        if not apply:
            return {'applied': False, 'status': self.status()}
        initial = self._read()
        archive_store = self._archive_store(initial)
        with ExitStack() as locks:
            for root in sorted({self.root, archive_store.root}, key=str):
                locks.enter_context(_lock(root))
            data = self._read()
            if data['lifecycle'] != initial['lifecycle']:
                raise RetentionError('Training lifecycle changed during cleanup; retry the preview')
            result = self._prune(data)
        return {'applied': True, **result}

    def finish(self, *, outcome: str, step: int, reason: str,
               archive_to: str | Path | None = None, apply: bool = False) -> dict:
        """End training after verified weight export; preview unless applied.

        Call only after the trainer has stopped and results are persisted.
        Completed/stopped runs no longer retain resume generations by default.
        Pins, unchanged best/final roles, and changed files remain protected.
        To archive a losing comparison run, explicitly choose a finished winner
        store with validated best weights. Its model is pinned before any local
        roles are released; this helper does not rank models or assess research
        dependencies. Both stores are locked in canonical order.
        """
        if outcome not in ('completed', 'stopped'):
            raise RetentionError('Training outcome must be completed or stopped')
        _integer(step, 'terminal step')
        if not isinstance(reason, str) or not reason.strip():
            raise RetentionError('A training completion or explicit stop reason is required')
        archive_store = CheckpointStore(archive_to) if archive_to is not None else self
        external = archive_store.root != self.root
        with ExitStack() as locks:
            if apply:
                for root in sorted({self.root, archive_store.root}, key=str):
                    locks.enter_context(_lock(root))
            data = self._read()
            archive_data = archive_store._read() if external else data
            if external and archive_data['lifecycle']['state'] == 'active':
                raise RetentionError('The comparison winner must finish training before archiving other runs')
            role = 'best' if external else 'final'
            identifier = archive_data['roles'].get(role)
            archived = next((e for e in archive_data['entries'] if e['id'] == identifier), None)
            if archived is None or archived['kind'] != 'weights' or not archive_store._valid(archived):
                raise RetentionError(f'Validated {role} inference weights are required before ending recovery retention')
            if step < max((e['step'] for e in data['entries']), default=0):
                raise RetentionError('Terminal step precedes registered run progress')
            proposed = {'state': outcome, 'step': step, 'reason': reason,
                        'archive': {'root': str(archive_store.root) if external else '.',
                                    'scope': 'comparison' if external else 'local',
                                    'run_id': archive_data['run_id'],
                                    'id': archived['id'], 'step': archived['step'],
                                    'files': archived['files'], 'validation': archived['validation']}}
            previous = data['lifecycle']
            if previous['state'] != 'active' and previous != proposed:
                # A completed run may later consolidate its models into the
                # explicitly selected winner. Its training outcome cannot change.
                if (not external or previous['state'] != outcome or previous['step'] != step):
                    raise RetentionError('This run is already finished; its training outcome cannot change')
                if previous['archive'].get('scope', 'local') != 'local':
                    raise RetentionError('This run is already archived; keep its recorded winner and dependency pin')
            released_roles = dict(data['roles']) if external else {}
            data['lifecycle'] = proposed
            if external:
                data['roles'] = {}
            plan = self._plan(data)
            if not apply:
                return {'applied': False, 'current_lifecycle': previous,
                        'proposed_lifecycle': proposed, 'released_roles': released_roles, 'status': plan}
            if external:
                # Persist the survivor's dependency before committing any local
                # deletion. A failed later write may leave an extra pin, never a
                # deleted survivor. Repeated finalization reuses the same pin.
                pin = 'archive for ' + data['run_id'] + ':' + hashlib.sha256(str(self.root).encode()).hexdigest()[:16]
                if pin not in archived['pins']:
                    archived['pins'].append(pin)
                    archive_store._write(archive_data)
            self._write(data)
            result = self._prune(data)
            return {'applied': True, 'released_roles': released_roles, **result}

    def publish(self, *, step: int, kind: str, expected_bytes: int,
                writer: Callable[[Path], object], validator: Callable[[Path], dict | None],
                validation_label: str, roles: tuple[str, ...] = (),
                pins: tuple[str, ...] = ()) -> dict:
        """Write, load-validate, commit, then prune under one per-run lock.

        Writers must synchronously finish all files before returning. Validators
        must raise on failure. Their optional JSON receipt is recorded verbatim.
        Do not deserialize untrusted checkpoints in a validator.
        """
        _integer(step, 'step')
        _integer(expected_bytes, 'expected_bytes', 1)
        if kind not in ('resume', 'weights') or not callable(writer) or not callable(validator):
            raise RetentionError('kind, writer, and loader validator are required')
        if not isinstance(validation_label, str) or not validation_label.strip():
            raise RetentionError('A loader validation label is required')
        if any(role not in ('best', 'final') for role in roles):
            raise RetentionError('Only best/final roles are supported')
        if any(not isinstance(pin, str) or not pin.strip() for pin in pins):
            raise RetentionError('Pins require a nonempty dependency reason')
        with _lock(self.root):
            data = self._read()
            if data['lifecycle']['state'] != 'active':
                raise RetentionError('Training has finished; publish exports before finish or use a new run')
            self._clean_garbage(data)
            policy = data['policy']
            current = self._bytes()
            if current + expected_bytes > policy['budget_bytes']:
                raise RetentionError('New-save peak exceeds the artifact byte budget; old recovery points retained')
            if shutil.disk_usage(self.root).free < expected_bytes + policy['reserve_bytes']:
                raise RetentionError('Insufficient filesystem space for a complete new save and reserve')
            latest = self._plan(data)
            if kind == 'resume' and latest['latest_step'] is not None and step < latest['latest_step']:
                raise RetentionError('Resume step precedes valid run progress; use a new run for a fork')
            identifier = 'ckpt-' + uuid.uuid4().hex
            staging = self.root / ('.pending-' + uuid.uuid4().hex)
            staging.mkdir()
            destination = self.root / identifier
            try:
                writer(staging)
                before = _files(staging)
                if not before:
                    raise RetentionError('An empty artifact cannot be published')
                receipt = validator(staging)
                if receipt is not None and not isinstance(receipt, dict):
                    raise RetentionError('A loader receipt must be a JSON object or None')
                json.dumps(receipt, allow_nan=False)
                files = _files(staging)
                if files != before:
                    raise RetentionError('Loader validation changed artifact files')
                if self._bytes() > policy['budget_bytes']:
                    raise RetentionError('Actual new-save peak exceeds the artifact byte budget')
                if shutil.disk_usage(self.root).free < policy['reserve_bytes']:
                    raise RetentionError('New save consumed the required filesystem reserve')
                # Flush completed files before publishing their manifest. Parent
                # metadata is flushed by the atomic manifest update below.
                for name in files:
                    with (staging / name).open('rb') as saved:
                        os.fsync(saved.fileno())
                _flush_directories(staging)
                os.replace(staging, destination)
                entry = {'id': identifier, 'step': step, 'kind': kind,
                         'sequence': data['generation'] + 1, 'files': files,
                         'pins': sorted(set(pins)),
                         'validation': {'passed': True, 'label': validation_label,
                                        'receipt': receipt}}
                data['entries'].append(entry)
                for role in roles:
                    data['roles'][role] = identifier
                self._write(data)
                self._prune(data)
                return entry
            finally:
                # Never remove a published destination after a manifest write may
                # have committed. An orphan is reported and consumes the budget.
                if staging.exists() and not staging.is_symlink():
                    shutil.rmtree(staging)

    def pin(self, identifier: str, reason: str, *, remove: bool = False) -> None:
        if not isinstance(reason, str) or not reason.strip():
            raise RetentionError('A nonempty pin reason is required')
        with _lock(self.root):
            data = self._read()
            entry = next((e for e in data['entries'] if e['id'] == identifier), None)
            if entry is None:
                raise RetentionError('Unknown active artifact id')
            if remove:
                entry['pins'] = [p for p in entry['pins'] if p != reason]
            elif reason not in entry['pins']:
                entry['pins'].append(reason)
            self._write(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    initialize = commands.add_parser('init', help='Establish an explicitly owned run store')
    initialize.add_argument('root', type=Path)
    initialize.add_argument('--run-id', required=True)
    initialize.add_argument('--budget-bytes', type=int, required=True)
    initialize.add_argument('--keep-last', type=int, default=2)
    initialize.add_argument('--reserve-bytes', type=int, default=0)
    for name in ('status', 'latest', 'prune', 'finish', 'pin', 'unpin'):
        command = commands.add_parser(name)
        command.add_argument('root', type=Path)
        if name in ('prune', 'finish'):
            command.add_argument('--apply', action='store_true')
        if name == 'finish':
            command.add_argument('--outcome', required=True, choices=('completed', 'stopped'))
            command.add_argument('--step', type=int, required=True)
            command.add_argument('--reason', required=True)
            command.add_argument('--archive-to', type=Path)
        if name in ('pin', 'unpin'):
            command.add_argument('identifier')
            command.add_argument('--reason', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            store = CheckpointStore.create(args.root, run_id=args.run_id,
                                           budget_bytes=args.budget_bytes,
                                           keep_last=args.keep_last, reserve_bytes=args.reserve_bytes)
            result = store.status()
        else:
            store = CheckpointStore(args.root)
            if args.command == 'prune':
                result = store.prune(apply=args.apply)
            elif args.command == 'finish':
                result = store.finish(outcome=args.outcome, step=args.step, reason=args.reason,
                                      archive_to=args.archive_to, apply=args.apply)
            elif args.command in ('pin', 'unpin'):
                store.pin(args.identifier, args.reason, remove=args.command == 'unpin')
                result = store.status()
            elif args.command == 'latest':
                latest = store.latest()
                result = {'path': str(latest) if latest else None, 'status': store.status()}
            else:
                result = store.status()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (RetentionError, OSError) as error:
        print(json.dumps({'error': str(error)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
