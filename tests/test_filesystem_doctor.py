"""Deployment checks exercise real process exclusion without creating state."""
import os

import pytest

from tools import filesystem_doctor as doctor
from tools.registry_common import RegistryError


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
