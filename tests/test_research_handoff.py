"""Handoff freshness follows actual selected files and never advances a gate."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys

import pytest

from tools import research_control as control, run_state
from tools.registry_common import RegistryError


@pytest.fixture
def project(tmp_path):
    run_state.start_run(str(tmp_path), 'pilot', ['explore', 'analyse'])
    (tmp_path / 'environment.json').write_text('{"ready":true}', encoding='utf-8')
    return tmp_path


def contents(project):
    return {str(path.relative_to(project)): path.read_bytes()
            for path in project.rglob('*') if path.is_file()}


def snapshot(project):
    return control.handoff_snapshot(project, 'pilot', watch_paths=['environment.json', 'dataset.json'])


def test_snapshot_and_check_are_read_only_and_do_not_initialize_contract(project):
    before = contents(project)
    receipt = snapshot(project)
    assert receipt['continuation_status'] == 'UNCONFIGURED' and receipt['timing'] is None
    assert receipt['files'][0] == {'path': 'dataset.json', 'state': 'absent'}
    result = control.check_handoff(project, 'pilot', receipt)
    assert result['status'] == 'CURRENT' and result['changed_paths'] == []
    assert contents(project) == before
    assert 'ready' not in json.dumps(receipt)  # Contents stay in the selected source, not the receipt.


@pytest.mark.parametrize('change,name', [('arrives', 'dataset.json'), ('changes', 'environment.json'),
                                       ('deleted', 'environment.json')])
def test_selected_source_changes_make_handoff_stale(project, change, name):
    receipt = snapshot(project)
    if change == 'deleted':
        (project / name).unlink()
    else:
        (project / name).write_text('{"new":true}', encoding='utf-8')
    before = contents(project)
    observed = control.check_handoff(project, 'pilot', receipt)
    assert observed['status'] == 'STALE' and observed['changed_paths'] == [name]
    assert contents(project) == before


def test_state_change_invalidates_handoff_without_accepting_phase(project):
    receipt = snapshot(project)
    run_state.set_status(str(project), 'pilot', 'explore', 'done')
    before = contents(project)
    observed = control.check_handoff(project, 'pilot', receipt)
    assert observed['status'] == 'STALE'
    assert observed['changed_paths'] == ['.ei/runs/pilot.json']
    assert observed['current']['phase']['status'] == 'done'
    assert contents(project) == before


def test_live_reservation_is_exposed_without_duplicate_launch(project):
    control.configure(project, 'pilot', 'Inspect', {'max_actions': 2, 'wall_seconds': 600,
                      'max_attempts_per_key': 1, 'resources': {'gpu_seconds': 0}})
    action = control.claim_action(project, 'pilot', 'check', 'explore', 'Check the evidence',
                                  costs={'gpu_seconds': 0})
    receipt = snapshot(project)
    observed = control.check_handoff(project, 'pilot', receipt)
    assert observed['current']['continuation_status'] == 'RECONCILE'
    assert observed['current']['unresolved_actions'] == [action['action']['id']]
    assert len(run_state.load_run(str(project), 'pilot')['coordination']['actions']) == 1


def test_current_snapshot_recomputes_budget_without_resetting_clock(project, monkeypatch):
    moment = [datetime(2025, 1, 1, tzinfo=timezone.utc)]
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return moment[0].astimezone(tz) if tz else moment[0].replace(tzinfo=None)
    monkeypatch.setattr(control, 'datetime', Clock)
    control.configure(project, 'pilot', 'Inspect', {'max_actions': 2, 'wall_seconds': 100,
                      'max_attempts_per_key': 1, 'resources': {}},
                      started_at=moment[0].isoformat(), closeout_seconds=20)
    receipt = snapshot(project)
    moment[0] += timedelta(seconds=85)
    observed = control.check_handoff(project, 'pilot', receipt)
    assert observed['status'] == 'CURRENT'  # File identity is current; old remaining time is not.
    assert observed['current']['continuation_status'] == 'CLOSEOUT_REQUIRED'
    assert observed['current']['timing']['remaining_seconds'] == 15
    assert receipt['timing']['remaining_seconds'] == 100


def test_missing_project_or_run_is_not_initialized(tmp_path, project):
    absent = tmp_path / 'absent'
    absent.mkdir()
    with pytest.raises(FileNotFoundError):
        control.handoff_snapshot(absent, 'missing')
    assert list(absent.iterdir()) == []
    receipt = snapshot(project)
    (project / '.ei/runs/pilot.json').unlink()
    assert control.check_handoff(project, 'pilot', receipt)['status'] == 'STALE'


@pytest.mark.parametrize('name', ['../secret', '/absolute', 'C:/secret', 'C:secret',
                                 'nested\\secret', '.', '', 'environment.json/../other'])
def test_unsafe_watch_paths_are_rejected_without_writes(project, name):
    before = contents(project)
    with pytest.raises(RegistryError):
        control.handoff_snapshot(project, 'pilot', watch_paths=[name])
    assert contents(project) == before


def test_symlink_watch_is_rejected(project, tmp_path):
    target = tmp_path / 'real'
    target.write_text('private')
    try:
        (project / 'link').symlink_to(target)
    except OSError:
        pytest.skip('Symlink privileges vary on Windows')
    with pytest.raises(RegistryError, match='Symlink|Junction'):
        control.handoff_snapshot(project, 'pilot', watch_paths=['link'])


def test_concurrent_change_cannot_produce_fresh_receipt(project, monkeypatch):
    original = control._watched_file
    count = [0]
    def changing(root, name):
        count[0] += 1
        (project / name).write_text(str(count[0]))
        return original(root, name)
    monkeypatch.setattr(control, '_watched_file', changing)
    with pytest.raises(RegistryError, match='changed during handoff'):
        control.handoff_snapshot(project, 'pilot', watch_paths=['environment.json'])


@pytest.mark.parametrize('change', ['hash', 'run', 'path', 'state', 'duplicate', 'version'])
def test_malformed_handoff_cannot_authorize_a_resume(project, change):
    receipt = deepcopy(snapshot(project))
    if change == 'hash':
        receipt['run_ref']['sha256'] = 'not-a-hash'
    elif change == 'run':
        receipt['run_id'] = 'other'
    elif change == 'path':
        receipt['files'][0]['path'] = '../outside'
    elif change == 'state':
        receipt['files'][0]['state'] = 'accepted'
    elif change == 'duplicate':
        receipt['files'].append(receipt['files'][0])
    else:
        receipt['schema_version'] = True
    before = contents(project)
    with pytest.raises(RegistryError):
        control.check_handoff(project, 'pilot', receipt)
    assert contents(project) == before


def test_cli_reports_stale_with_distinct_exit_and_preserves_state(project):
    command = [sys.executable, '-m', 'tools.research_control', '--root', str(project), '--run-id', 'pilot']
    def invoke(*args):
        return subprocess.run(command + list(args), cwd=Path(__file__).resolve().parents[1],
                              capture_output=True, text=True, encoding='utf-8', timeout=30)
    captured = invoke('handoff', '--watch', 'dataset.json')
    assert captured.returncode == 0, captured.stderr
    receipt = project / 'HANDOFF_STATE.json'
    receipt.write_text(captured.stdout, encoding='utf-8')
    current = invoke('check-handoff', '--receipt', str(receipt))
    assert current.returncode == 0 and json.loads(current.stdout)['status'] == 'CURRENT'
    (project / 'dataset.json').write_text('{"rows":10}', encoding='utf-8')
    before = contents(project)
    stale = invoke('check-handoff', '--receipt', str(receipt))
    assert stale.returncode == 3 and json.loads(stale.stdout)['status'] == 'STALE'
    assert contents(project) == before
