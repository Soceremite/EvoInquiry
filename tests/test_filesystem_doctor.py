"""Deployment probes and actual shared/exclusive OS locking regressions."""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from tools import filesystem_doctor as doctor
from tools.registry_common import RegistryError, file_lock


REPO = Path(__file__).resolve().parents[1]


def _lock_probe(path, *, shared):
    program = '''
from tools.registry_common import RegistryError, file_lock
import sys
try:
    with file_lock(sys.argv[1], shared=sys.argv[2] == 'shared', blocking=False):
        print('acquired')
except RegistryError:
    print('blocked')
'''
    result = subprocess.run([sys.executable, '-B', '-c', program, str(path),
                             'shared' if shared else 'exclusive'], cwd=REPO,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _wait_ready(child, path):
    deadline = time.monotonic() + 10
    while not path.exists() and child.poll() is None and time.monotonic() < deadline:
        time.sleep(.01)
    assert path.exists(), 'Lock worker did not become ready'


@pytest.mark.parametrize('holder_shared', [False, True])
@pytest.mark.parametrize('probe_shared', [False, True])
def test_cross_process_shared_locks_coexist_and_exclusive_locks_exclude(
        tmp_path, holder_shared, probe_shared):
    path = tmp_path / 'namespace.lock'
    with file_lock(path, shared=holder_shared):
        expected = 'acquired' if holder_shared and probe_shared else 'blocked'
        assert _lock_probe(path, shared=probe_shared) == expected
    assert path.read_bytes() == b''  # Shared admission must not write a sentinel.
    assert _lock_probe(path, shared=probe_shared) == 'acquired'


def test_shared_namespace_lock_allows_another_thread_to_record_review(tmp_path):
    path = tmp_path / 'namespace.lock'

    def review_writer():
        with file_lock(path, shared=True, blocking=False):
            (tmp_path / 'review.txt').write_text('recorded', encoding='utf-8')

    with ThreadPoolExecutor(max_workers=1) as pool:
        with file_lock(path, shared=True):
            pool.submit(review_writer).result(timeout=10)
            assert (tmp_path / 'review.txt').read_text() == 'recorded'


def test_blocking_lock_waiter_acquires_after_exclusive_owner_releases(tmp_path):
    path = tmp_path / 'namespace.lock'
    ready, acquired = tmp_path / 'ready', tmp_path / 'acquired'
    program = '''
from tools.registry_common import file_lock
from pathlib import Path
import sys
Path(sys.argv[2]).touch()
with file_lock(sys.argv[1]):
    Path(sys.argv[3]).touch()
'''
    child = None
    try:
        with file_lock(path):
            child = subprocess.Popen([sys.executable, '-B', '-c', program,
                                      str(path), str(ready), str(acquired)],
                                     cwd=REPO, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            _wait_ready(child, ready)
            assert _lock_probe(path, shared=True) == 'blocked'
            assert child.poll() is None
            assert not acquired.exists()
        _, errors = child.communicate(timeout=10)
        assert child.returncode == 0, errors
        assert acquired.exists()
    finally:
        if child is not None and child.poll() is None:
            child.kill()
            child.communicate(timeout=10)


def test_crashed_owner_releases_its_os_lock(tmp_path):
    path, ready = tmp_path / 'namespace.lock', tmp_path / 'ready'
    program = '''
from tools.registry_common import file_lock
from pathlib import Path
import sys, time
with file_lock(sys.argv[1]):
    Path(sys.argv[2]).touch()
    while True:
        time.sleep(1)
'''
    child = subprocess.Popen([sys.executable, '-B', '-c', program, str(path), str(ready)],
                             cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        _wait_ready(child, ready)
        assert _lock_probe(path, shared=True) == 'blocked'
        child.kill()
        child.communicate(timeout=10)
        assert _lock_probe(path, shared=False) == 'acquired'
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=10)


def test_inspection_is_read_only(tmp_path, monkeypatch):
    (tmp_path / 'manual.txt').write_text('keep')
    monkeypatch.setattr(doctor.tempfile, 'TemporaryDirectory',
                        lambda **kw: pytest.fail('Inspection attempted a write'))
    result = doctor.inspect_directory(tmp_path)
    assert result['status'] == 'NOT_TESTED'
    assert result['persistence'] == 'operator-confirmation-required'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['manual.txt']


@pytest.mark.skipif(os.name not in ('posix', 'nt'), reason='Requires an OS lock backend')
def test_actual_process_lock_and_replacement(tmp_path):
    result = doctor.probe_directory(tmp_path)
    assert result['status'] == 'PASS', result
    assert result['checks']['cross_process_lock_exclusion'] == 'PASS'
    assert result['checks']['file_fsync_replace_readback'] == 'PASS'
    assert result['temporary_probe_removed']
    assert list(tmp_path.iterdir()) == []


def test_unsafe_backend_fails_closed_and_removes_owned_probe(tmp_path, monkeypatch):
    def reject(*args, **kwargs):
        raise RegistryError('Filesystem lock exclusion failed')
    monkeypatch.setattr(doctor, 'file_lock', reject)
    result = doctor.probe_directory(tmp_path)
    assert result['status'] == 'FAIL'
    assert 'exclusion' in result['error']
    assert result['temporary_probe_removed']
    assert list(tmp_path.iterdir()) == []
