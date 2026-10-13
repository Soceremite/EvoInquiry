"""Local governance primitives; locks require POSIX flock or Windows locking.

Records use canonical UTF-8 JSON and SHA-256. Reference checks establish file
identity, not scientific validity. All mutations stay inside the project root.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import threading

_VERIFIED_LOCK_DEVICES = set()
_HELD_LOCKS = threading.local()


class RegistryError(ValueError):
    """A record, reference, or recovery condition prevents the requested change."""


def _regular_ancestors(path):
    """Reject symlink traversal even when a caller constructs a state subpath directly."""
    path = Path(path).absolute()
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink():
            raise RegistryError(f'Symlink is outside the local registry contract: {ancestor}')
    return path


def now():
    """Return an explicit UTC timestamp for a receipt."""
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    """Serialize JSON without NaN or ordering-dependent identity."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    """Hash bytes, or the canonical representation of a JSON value."""
    return hashlib.sha256(value if isinstance(value, bytes) else canonical(value)).hexdigest()


def file_digest(path):
    """Stream a regular file without following a final symlink."""
    path = _regular_ancestors(path)
    if not path.is_file() or path.is_symlink():
        raise RegistryError(f'Missing regular file: {path}')
    result = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def identifier(value):
    """Reject IDs that can escape or ambiguously address a registry directory."""
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', value):
        raise RegistryError(f'Invalid identifier: {value!r}')
    return value


def local_path(root, relative):
    """Resolve an explicit project path; reject traversal and symlink ancestors."""
    root = Path(root).resolve()
    relative = Path(relative)
    if relative.is_absolute() or not relative.parts or '..' in relative.parts:
        raise RegistryError(f'Expected a project-relative path: {relative}')
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise RegistryError(f'Symlink is outside the local registry contract: {path}')
    if not path.is_relative_to(root):
        raise RegistryError(f'Path escapes project: {path}')
    return path


def read_record(path):
    """Read JSON, or project YAML with safe_load when PyYAML is available."""
    path = _regular_ancestors(path)
    text = path.read_text(encoding='utf-8')
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        if path.suffix not in ('.yaml', '.yml'):
            raise RegistryError(f'Invalid JSON: {path}') from None
        try:
            import yaml
        except ImportError:
            raise RegistryError('Reading YAML requires PyYAML; JSON is also valid project YAML') from None
        result = yaml.safe_load(text)
    if not isinstance(result, dict):
        raise RegistryError(f'Expected an object in {path}')
    return result


def sync_directory(path):
    """Persist a rename on supported local POSIX filesystems."""
    if os.name == 'posix':
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def atomic_write(path, data):
    """Replace one local file with a flushed unique temporary file."""
    path = _regular_ancestors(path)
    if path.is_symlink():
        raise RegistryError(f'Refusing to replace symlink: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.')
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data if isinstance(data, bytes) else canonical(data) + b'\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _verify_lock_backend(parent):
    """Verify exclusion on this filesystem before using a POSIX registry lock.

    Some virtual mounts accept flock yet fail to exclude a second writer. A
    successful syscall alone is insufficient. The owned probe is temporary;
    this runs only for a mutation, never for inventory or a migration dry-run.
    """
    device = parent.stat().st_dev
    if os.name != 'posix' or device in _VERIFIED_LOCK_DEVICES:
        return
    import fcntl
    descriptor, name = tempfile.mkstemp(prefix='.ei-lock-probe-',dir=parent)
    try:
        with os.fdopen(descriptor,'w+b') as first, open(name,'a+b') as second:
            fcntl.flock(first,fcntl.LOCK_SH)
            try:
                fcntl.flock(second,fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                raise RegistryError('Filesystem lock exclusion failed; use a verified local filesystem before writing state')
            fcntl.flock(second,fcntl.LOCK_SH)
            fcntl.flock(second,fcntl.LOCK_UN)
            fcntl.flock(first,fcntl.LOCK_UN)
        _VERIFIED_LOCK_DEVICES.add(device)
    except OSError as error:
        raise RegistryError('Filesystem lock verification failed: ' + str(error)) from error
    finally:
        Path(name).unlink(missing_ok=True)


@contextmanager
def file_lock(path, *, shared=False, blocking=True):
    """Hold an OS lock; a crash releases it, but a timeout never proves quiescence."""
    path = _regular_ancestors(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _verify_lock_backend(path.parent)
    held = getattr(_HELD_LOCKS, 'paths', None)
    if held is None:
        held = _HELD_LOCKS.paths = {}
    key = str(path)
    if key in held:
        if held[key] and not shared:
            raise RegistryError(f'Active writer holds {path}; a shared lock cannot be upgraded')
        yield
        return
    if path.is_symlink():
        raise RegistryError(f'Refusing symlink lock: {path}')
    with path.open('a+b') as handle:
        if os.name == 'posix':
            import fcntl
            operation = fcntl.LOCK_SH if shared else fcntl.LOCK_EX
            if not blocking:
                operation |= fcntl.LOCK_NB
            try:
                fcntl.flock(handle, operation)
            except BlockingIOError:
                raise RegistryError(f'Active writer holds {path}') from None
            try:
                held[key] = shared
                yield
            finally:
                held.pop(key, None)
                fcntl.flock(handle, fcntl.LOCK_UN)
        elif os.name == 'nt':  # Exclusive fallback on Windows.
            import msvcrt
            if path.stat().st_size == 0:
                handle.write(b'\0')
                handle.flush()
            handle.seek(0)
            mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
            msvcrt.locking(handle.fileno(), mode, 1)
            try:
                held[key] = shared
                yield
            finally:
                held.pop(key, None)
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            raise RegistryError('Registry writes require a verified local filesystem lock backend')


def validate_schema(kind, record):
    """Validate one versioned local schema without retrieving network references."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        raise RegistryError('Governance record validation requires jsonschema>=4,<5') from None
    schema = json.loads((Path(__file__).resolve().parent / 'schemas' / (kind + '.schema.json')).read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(record), key=lambda error: str(error.path))
    if errors:
        raise RegistryError('; '.join(f'{list(e.path)}: {e.message}' for e in errors))
    return record


def fixed_ref(root, path):
    """Create a fixed reference to a regular file, excluding mutable current aliases."""
    relative = Path(path)
    if 'current' in relative.parts:
        raise RegistryError('current is navigation, not a fixed evidence reference')
    target = local_path(root, relative)
    return {'path': relative.as_posix(), 'sha256': file_digest(target)}


def verify_ref(root, reference, *, legacy_read=False):
    """Verify a fixed digest; map historical namespace paths only through a receipt."""
    if not isinstance(reference, dict) or not reference.get('path') or not re.fullmatch(
            '[0-9a-f]{64}', reference.get('sha256', '')):
        raise RegistryError('A fixed reference requires path and SHA-256')
    relative = Path(reference['path'])
    if 'current' in relative.parts:
        raise RegistryError('A floating current alias is not evidence')
    if relative.parts[:1] == ('.aris',):
        try:
            from .state_paths import resolve_state_root
        except ImportError:
            from state_paths import resolve_state_root
        active = resolve_state_root(root, mode='legacy-read' if legacy_read else 'read')
        if active.name == '.ei':
            receipt = read_record(active / 'namespace-migration.json')
            mapped = receipt['mapping'].get(relative.as_posix())
            if mapped != Path('.ei', *relative.parts[1:]).as_posix():
                raise RegistryError('Historical reference is absent from the verified migration mapping')
            relative = Path(mapped)
    path = local_path(root, relative)
    if file_digest(path) != reference['sha256']:
        raise RegistryError(f'Reference digest mismatch: {reference["path"]}')
    return path
