"""Observable capacity, recovery, and ownership invariants for local checkpoints."""
from __future__ import annotations

import errno
import json
from pathlib import Path
import random
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from tools.checkpoint_retention import CheckpointStore, MANIFEST, RetentionError


def save(store, step, *, kind='resume', roles=(), pins=(), payload=None):
    content = payload or json.dumps({'step': step, 'state': 'x' * 96}).encode()

    def writer(path):
        (path / 'state.json').write_bytes(content)

    def validator(path):
        assert (path / 'state.json').read_bytes() == content
        return {'probe': 'round-trip payload', 'step': step}

    return store.publish(step=step, kind=kind, expected_bytes=len(content),
                         writer=writer, validator=validator,
                         validation_label='payload round-trip', roles=roles, pins=pins)


@pytest.fixture
def store(tmp_path):
    return CheckpointStore.create(tmp_path / 'run', run_id='seed-42', budget_bytes=10_000)


def active(store):
    return json.loads((store.root / MANIFEST).read_text())['entries']


def test_long_run_has_bounded_peak_and_two_resume_generations(tmp_path):
    store = CheckpointStore.create(tmp_path / 'run', run_id='300k-steps', budget_bytes=512)
    peaks = []
    for step in range(500, 300_001, 500):
        payload = json.dumps({'step': step, 'state': 'x' * 96}).encode()

        def writer(path):
            (path / 'state.json').write_bytes(payload)
            peaks.append(store.status()['bytes_used'])

        store.publish(step=step, kind='resume', expected_bytes=len(payload),
                      writer=writer, validator=lambda p: json.loads((p / 'state.json').read_text()),
                      validation_label='JSON state loader')
        assert sorted(e['step'] for e in active(store)) == ([step] if step == 500 else [step - 500, step])
        assert store.status()['latest_step'] == step
        assert not store.status()['unregistered']
    assert max(peaks) <= 512
    assert len(active(store)) == 2


@pytest.mark.parametrize('failure', ['writer', 'disk_full', 'validator', 'changed_by_validator', 'too_large'])
def test_failed_save_preserves_previous_valid_recovery_points(store, failure):
    save(store, 10)
    save(store, 20)
    previous = (store.root / MANIFEST).read_bytes()
    latest = store.latest()

    def writer(path):
        (path / 'state.json').write_bytes(b'x' * (20_000 if failure == 'too_large' else 100))
        if failure == 'writer':
            raise RuntimeError('interrupted save')
        if failure == 'disk_full':
            raise OSError(errno.ENOSPC, 'simulated exhausted disk')

    def validator(path):
        (path / 'state.json').read_bytes()
        if failure == 'validator':
            raise ValueError('missing optimizer state')
        if failure == 'changed_by_validator':
            (path / 'state.json').write_bytes(b'changed')

    with pytest.raises((RuntimeError, ValueError, OSError)):
        store.publish(step=30, kind='resume', expected_bytes=100,
                      writer=writer, validator=validator, validation_label='load state')
    assert (store.root / MANIFEST).read_bytes() == previous
    assert store.latest() == latest
    assert sorted(e['step'] for e in active(store)) == [10, 20]
    assert not store.status()['unregistered']


def test_peak_preflight_includes_existing_artifacts_and_does_not_prune_first(tmp_path):
    store = CheckpointStore.create(tmp_path / 'run', run_id='tight', budget_bytes=250)
    save(store, 10, payload=b'a' * 100)
    save(store, 20, payload=b'b' * 100)
    called = []
    with pytest.raises(RetentionError, match='peak'):
        store.publish(step=30, kind='resume', expected_bytes=100,
                      writer=lambda p: called.append(p), validator=lambda p: None,
                      validation_label='loader')
    assert not called
    assert sorted(e['step'] for e in active(store)) == [10, 20]


def test_filesystem_reserve_is_checked_before_writer(store, monkeypatch):
    monkeypatch.setattr('tools.checkpoint_retention.shutil.disk_usage', lambda p: SimpleNamespace(free=50))
    with pytest.raises(RetentionError, match='filesystem space'):
        save(store, 10, payload=b'x' * 100)
    assert not active(store)


def test_actual_save_cannot_consume_reserved_space(store, monkeypatch):
    free = [10_000]
    monkeypatch.setattr('tools.checkpoint_retention.shutil.disk_usage', lambda p: SimpleNamespace(free=free[0]))
    data = json.loads((store.root / MANIFEST).read_text())
    data['policy']['reserve_bytes'] = 100
    (store.root / MANIFEST).write_text(json.dumps(data))

    def writer(path):
        (path / 'state.json').write_bytes(b'valid but too little reserve')
        free[0] = 50

    with pytest.raises(RetentionError, match='reserve'):
        store.publish(step=1, kind='resume', expected_bytes=100,
                      writer=writer, validator=lambda p: None, validation_label='loader')
    assert not active(store)


def test_best_final_and_dependency_roles_are_not_confused_with_latest_resume(store):
    teacher = save(store, 10, pins=('teacher for phase two',))
    best = save(store, 11, kind='weights', roles=('best', 'final'))
    save(store, 20)
    save(store, 30)
    assert {e['id'] for e in active(store)} == {teacher['id'], best['id']} | set(store.status()['keep'])
    assert sorted(e['step'] for e in active(store)) == [10, 11, 20, 30]
    assert store.status()['latest_step'] == 30
    assert store.status()['roles'] == {'best': best['id'], 'final': best['id']}
    newer_best = save(store, 31, kind='weights', roles=('best',))
    assert best['id'] in {e['id'] for e in active(store)}  # still final
    assert store.status()['roles']['best'] == newer_best['id']
    store.pin(teacher['id'], 'teacher for phase two', remove=True)
    assert teacher['id'] in store.prune()['status']['remove']
    assert (store.root / teacher['id']).exists()  # preview has no side effect
    store.prune(apply=True)
    assert not (store.root / teacher['id']).exists()


def test_pinned_storage_is_included_in_peak_budget(tmp_path):
    store = CheckpointStore.create(tmp_path / 'run', run_id='pins', budget_bytes=350)
    save(store, 1, payload=b'a' * 100, pins=('dependency',))
    save(store, 2, payload=b'b' * 100)
    save(store, 3, payload=b'c' * 100)
    with pytest.raises(RetentionError, match='peak'):
        save(store, 4, payload=b'd' * 100)
    assert len(active(store)) == 3


def test_corrupt_latest_falls_back_and_is_reported_without_deletion(store):
    fallback = save(store, 100)
    latest = save(store, 200)
    (store.root / latest['id'] / 'state.json').write_text('truncated')
    assert store.latest() == store.root / fallback['id']
    assert store.status()['corrupt_or_missing'] == [latest['id']]
    assert latest['id'] in store.prune(apply=True)['status']['keep']
    save(store, 150)  # continuation from the valid 100-step fallback
    assert store.status()['latest_step'] == 150


def test_progress_is_numeric_and_weights_do_not_become_resume_checkpoints(store):
    save(store, 9)
    save(store, 100)
    save(store, 100_000, kind='weights', roles=('best',))
    assert store.status()['latest_step'] == 100
    with pytest.raises(RetentionError, match='fork'):
        save(store, 50)


def test_incomplete_shard_group_never_replaces_resume_point(store):
    fallback = save(store, 1)

    def writer(path):
        (path / 'rank0').mkdir()
        (path / 'rank0' / 'state.json').write_text('{}')

    def validator(path):
        for rank in (0, 1):
            json.loads((path / f'rank{rank}' / 'state.json').read_text())

    with pytest.raises(FileNotFoundError):
        store.publish(step=2, kind='resume', expected_bytes=10, writer=writer,
                      validator=validator, validation_label='all-rank loader')
    assert store.latest() == store.root / fallback['id']


def test_complete_shard_groups_rotate_as_whole_artifacts(store):
    for step in (1, 2, 3):
        def writer(path):
            for rank in (0, 1):
                (path / f'rank{rank}').mkdir()
                (path / f'rank{rank}' / 'state.json').write_text(json.dumps({'step': step, 'rank': rank}))

        def validator(path):
            states = [json.loads((path / f'rank{rank}' / 'state.json').read_text()) for rank in (0, 1)]
            assert all(s['step'] == step for s in states)
            return {'ranks_loaded': 2}

        store.publish(step=step, kind='resume', expected_bytes=100,
                      writer=writer, validator=validator, validation_label='all-rank loader')
    assert sorted(e['step'] for e in active(store)) == [2, 3]
    assert all(len(e['files']) == 2 for e in active(store))


def test_unregistered_files_are_preserved_and_count_toward_budget(tmp_path):
    root = tmp_path / 'legacy'
    root.mkdir()
    evidence = root / 'results.csv'
    evidence.write_bytes(b'x' * 500)
    store = CheckpointStore.create(root, run_id='migration', budget_bytes=550)
    assert store.status()['unregistered'] == ['results.csv']
    with pytest.raises(RetentionError, match='peak'):
        save(store, 1, payload=b'x' * 100)
    store.prune(apply=True)
    assert evidence.read_bytes() == b'x' * 500


@pytest.mark.skipif(sys.platform == 'win32', reason='Symlink privileges vary on Windows')
def test_symlink_inside_save_does_not_touch_outside_files(store, tmp_path):
    outside = tmp_path / 'raw-evidence.csv'
    outside.write_text('preserve me')

    def writer(path):
        (path / 'state.json').symlink_to(outside)

    with pytest.raises(RetentionError, match='Unsupported'):
        store.publish(step=1, kind='resume', expected_bytes=100, writer=writer,
                      validator=lambda p: None, validation_label='loader')
    assert outside.read_text() == 'preserve me'
    assert not active(store)


@pytest.mark.parametrize('escape', ['../another-run', '/tmp/outside', 'ckpt-invalid'])
def test_manifest_cannot_redirect_artifact_deletion_outside_store(store, escape):
    save(store, 1)
    data = json.loads((store.root / MANIFEST).read_text())
    data['entries'][0]['id'] = escape
    (store.root / MANIFEST).write_text(json.dumps(data))
    with pytest.raises(RetentionError, match='artifact id'):
        store.prune(apply=True)


@pytest.mark.parametrize('mutation', ['replace', 'extra'])
def test_changed_candidate_is_preserved_instead_of_deleted(store, mutation):
    old = save(store, 1, kind='weights', roles=('best',))
    path = store.root / old['id'] / 'state.json'
    if mutation == 'replace':
        path.write_text('changed by someone else')
    else:
        (path.parent / 'extra-evidence.txt').write_text('preserve')
    save(store, 2, kind='weights', roles=('best',))
    assert old['id'] in store.status()['corrupt_or_missing']
    store.prune(apply=True)
    assert path.exists()


def test_publication_manifest_failure_leaves_previous_latest_and_a_reported_orphan(store, monkeypatch):
    old = save(store, 1)
    previous = (store.root / MANIFEST).read_bytes()
    monkeypatch.setattr(store, '_write', lambda data: (_ for _ in ()).throw(OSError('manifest write failed')))
    with pytest.raises(OSError):
        save(store, 2)
    assert (store.root / MANIFEST).read_bytes() == previous
    assert store.latest() == store.root / old['id']
    assert len(store.status()['unregistered']) == 1
    store.prune(apply=True)
    assert len(store.status()['unregistered']) == 1


def test_interrupted_deletion_is_journaled_and_can_finish_safely(store, monkeypatch):
    import tools.checkpoint_retention as module
    first = save(store, 1)
    save(store, 2)
    real_rmtree = module.shutil.rmtree

    def interrupted(path):
        (path / 'state.json').unlink()
        raise OSError('interrupted deletion')

    monkeypatch.setattr(module.shutil, 'rmtree', interrupted)
    with pytest.raises(OSError):
        save(store, 3)
    assert store.status()['latest_step'] == 3
    assert first['id'] in store.status()['garbage_remove']
    monkeypatch.setattr(module.shutil, 'rmtree', real_rmtree)
    store.prune(apply=True)
    assert not (store.root / first['id']).exists()
    assert not store.status()['garbage_remove']
    assert sorted(e['step'] for e in active(store)) == [2, 3]


def test_cooperating_writer_lock_prevents_nested_publication(store):
    other = CheckpointStore(store.root)

    def writer(path):
        (path / 'state.json').write_text('{}')
        with pytest.raises(RetentionError, match='Another writer'):
            save(other, 2)

    store.publish(step=1, kind='resume', expected_bytes=100, writer=writer,
                  validator=lambda p: None, validation_label='loader')
    assert len(active(store)) == 1


def test_killed_writer_releases_lock_and_keeps_previous_recovery(store, tmp_path):
    save(store, 1)
    save(store, 2)
    ready = tmp_path / 'ready'
    program = '''
from pathlib import Path
import sys, time
from tools.checkpoint_retention import CheckpointStore
def writer(path):
    (path / 'partial.json').write_text('{}')
    Path(sys.argv[2]).write_text('ready')
    time.sleep(30)
CheckpointStore(sys.argv[1]).publish(step=3, kind='resume', expected_bytes=100,
    writer=writer, validator=lambda p: None, validation_label='loader')
'''
    child = subprocess.Popen([sys.executable, '-c', program, str(store.root), str(ready)],
                             cwd=Path(__file__).resolve().parents[1], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 5
        while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert ready.exists()
        with pytest.raises(RetentionError, match='Another writer'):
            save(store, 3)
    finally:
        child.kill()
        child.communicate(timeout=5)
    assert store.status()['latest_step'] == 2
    orphan = store.status()['unregistered']
    assert len(orphan) == 1 and orphan[0].startswith('.pending-')
    save(store, 3)
    assert store.status()['latest_step'] == 3
    assert store.status()['unregistered'] == orphan


def test_cpu_training_resume_matches_uninterrupted_optimizer_rng_and_data_progress(store):
    """A real standard-library SGD/momentum loop, not a PyTorch integration test."""
    def initial():
        return {'step': 0, 'weight': 0.1, 'momentum': 0.0, 'lr': 0.05,
                'data_cursor': 0, 'rng': random.Random(42).getstate()}

    def train(state, until):
        generator = random.Random()
        rng = state['rng']
        generator.setstate((rng[0], tuple(rng[1]), rng[2]))
        while state['step'] < until:
            x = generator.uniform(-1, 1)
            target = 2 * x + generator.gauss(0, 0.01)
            gradient = 2 * (state['weight'] * x - target) * x
            state['momentum'] = 0.8 * state['momentum'] + gradient
            state['weight'] -= state['lr'] * state['momentum']
            state['step'] += 1
            state['data_cursor'] += 1
            if state['step'] == 20:
                state['lr'] *= 0.5
        state['rng'] = generator.getstate()
        return state

    continuous = train(initial(), 40)
    interrupted = train(initial(), 15)

    def writer(path):
        (path / 'state.json').write_text(json.dumps(interrupted))

    def validator(path):
        loaded = json.loads((path / 'state.json').read_text())
        assert set(loaded) == {'step', 'weight', 'momentum', 'lr', 'data_cursor', 'rng'}
        assert loaded['step'] == 15 and loaded['data_cursor'] == 15
        return {'required_state_loaded': sorted(loaded)}

    store.publish(step=15, kind='resume', expected_bytes=8_000, writer=writer,
                  validator=validator, validation_label='SGD/momentum full-state load')
    train(interrupted, 18)  # work after the save is deliberately lost on interruption
    resumed = json.loads((store.latest() / 'state.json').read_text())
    resumed = train(resumed, 40)
    assert resumed == continuous


def test_cli_defaults_to_preview_and_reports_invalid_policy(tmp_path):
    script = Path(__file__).resolve().parents[1] / 'tools/checkpoint_retention.py'
    root = tmp_path / 'with spaces'
    result = subprocess.run([sys.executable, str(script), 'init', str(root), '--run-id', 'one',
                             '--budget-bytes', '1000'], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout
    preview = subprocess.run([sys.executable, str(script), 'prune', str(root)],
                             capture_output=True, text=True)
    assert preview.returncode == 0
    assert json.loads(preview.stdout)['applied'] is False
    invalid = subprocess.run([sys.executable, str(script), 'init', str(tmp_path / 'bad'),
                              '--run-id', 'two', '--budget-bytes', '1000', '--keep-last', '1'],
                             capture_output=True, text=True)
    assert invalid.returncode == 1
    assert not (tmp_path / 'bad').exists()


def test_optional_pytorch_cpu_resume_matches_continuous_training(store):
    """Exercise real model/Adam/scheduler/global and data RNG state on CPU only."""
    torch = pytest.importorskip('torch')
    torch.set_num_threads(2)

    def initialize():
        torch.manual_seed(2026)
        model = torch.nn.Sequential(torch.nn.Linear(2, 4), torch.nn.Dropout(0.2),
                                    torch.nn.Linear(4, 1)).to('cpu')
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.8)
        generator = torch.Generator(device='cpu').manual_seed(42)
        return model, optimizer, scheduler, generator

    def train(parts, start, until):
        model, optimizer, scheduler, generator = parts
        model.train()
        for step in range(start, until):
            inputs = torch.randn(8, 2, generator=generator, device='cpu')
            targets = inputs[:, :1] * 2 + inputs[:, 1:] * 0.5
            optimizer.zero_grad()
            loss = torch.nn.functional.mse_loss(model(inputs), targets)
            loss.backward()
            optimizer.step()
            scheduler.step()

    continuous = initialize()
    train(continuous, 0, 20)
    expected = {name: tensor.detach().clone() for name, tensor in continuous[0].state_dict().items()}
    expected_rng = torch.get_rng_state().clone()
    expected_data_rng = continuous[3].get_state().clone()
    interrupted = initialize()
    train(interrupted, 0, 8)

    def writer(path):
        model, optimizer, scheduler, generator = interrupted
        torch.save({'model': model.state_dict(), 'optimizer': optimizer.state_dict(),
                    'scheduler': scheduler.state_dict(), 'rng': torch.get_rng_state(),
                    'data_rng': generator.get_state(), 'step': 8, 'data_cursor': 8}, path / 'state.pt')

    def validator(path):
        state = torch.load(path / 'state.pt', map_location='cpu', weights_only=True)
        assert state['step'] == state['data_cursor'] == 8
        assert len(state['optimizer']['state']) > 0
        return {'loaded_state': sorted(state)}

    # A full PyTorch checkpoint includes two RNG tensors and is larger than the
    # tiny payload store. Create a separate explicit budget for this witness.
    torch_store = CheckpointStore.create(store.root / 'torch', run_id='torch-cpu', budget_bytes=100_000)
    torch_store.publish(step=8, kind='resume', expected_bytes=25_000,
                        writer=writer, validator=validator, validation_label='PyTorch full-state loader')
    train(interrupted, 8, 11)
    recovered = initialize()
    state = torch.load(torch_store.latest() / 'state.pt', map_location='cpu', weights_only=True)
    recovered[0].load_state_dict(state['model'])
    recovered[1].load_state_dict(state['optimizer'])
    recovered[2].load_state_dict(state['scheduler'])
    torch.set_rng_state(state['rng'])
    recovered[3].set_state(state['data_rng'])
    train(recovered, state['step'], 20)
    assert all(torch.equal(tensor, recovered[0].state_dict()[name]) for name, tensor in expected.items())
    assert recovered[1].state_dict()['param_groups'] == continuous[1].state_dict()['param_groups']
    for identifier, expected_state in continuous[1].state_dict()['state'].items():
        restored_state = recovered[1].state_dict()['state'][identifier]
        for name, value in expected_state.items():
            assert torch.equal(value, restored_state[name]) if isinstance(value, torch.Tensor) else value == restored_state[name]
    assert recovered[2].state_dict() == continuous[2].state_dict()
    assert torch.equal(torch.get_rng_state(), expected_rng)
    assert torch.equal(recovered[3].get_state(), expected_data_rng)


def test_monitoring_can_inspect_a_cooperating_publisher_without_raw_filesystem_errors(store):
    program = '''
from tools.checkpoint_retention import CheckpointStore
from pathlib import Path
import json, sys, time
store = CheckpointStore(sys.argv[1])
for step in range(1, 81):
    def writer(path):
        (path / 'state.json').write_text(json.dumps({'step':step}))
    store.publish(step=step, kind='resume', expected_bytes=100, writer=writer,
        validator=lambda p: json.loads((p/'state.json').read_text()), validation_label='loader')
    time.sleep(0.002)
'''
    child = subprocess.Popen([sys.executable, '-c', program, str(store.root)],
                             cwd=Path(__file__).resolve().parents[1], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    observed = []
    try:
        deadline = time.monotonic() + 15
        while child.poll() is None and time.monotonic() < deadline:
            try:
                snapshot = store.status()
                if snapshot['latest_step'] is not None:
                    observed.append(snapshot['latest_step'])
            except RetentionError as error:
                assert 'state changed during inspection' in str(error)
        stdout, stderr = child.communicate(timeout=2)
        assert child.returncode == 0, stderr.decode()
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=5)
    assert observed and observed == sorted(observed)
    assert store.status()['latest_step'] == 80


@pytest.mark.skipif(not hasattr(__import__('os'), 'O_DIRECTORY'), reason='Directory fsync is POSIX-specific')
def test_nested_artifact_directory_entries_are_flushed_before_manifest_commit(store, monkeypatch):
    import os
    import stat
    import tools.checkpoint_retention as module
    flushed = []
    directories = []
    real_fsync = os.fsync
    real_write = store._write

    def tracked_fsync(descriptor):
        info = os.fstat(descriptor)
        if stat.S_ISDIR(info.st_mode):
            flushed.append(info.st_ino)
        real_fsync(descriptor)

    def writer(path):
        (path / 'rank0').mkdir()
        (path / 'rank0/state.json').write_text('{}')
        directories.extend([(path / 'rank0').stat().st_ino, path.stat().st_ino])

    def before_commit(data):
        assert all(inode in flushed for inode in directories)
        assert flushed.index(directories[0]) < flushed.index(directories[1])
        real_write(data)

    monkeypatch.setattr(module.os, 'fsync', tracked_fsync)
    monkeypatch.setattr(store, '_write', before_commit)
    store.publish(step=1, kind='resume', expected_bytes=100, writer=writer,
                  validator=lambda p: json.loads((p / 'rank0/state.json').read_text()),
                  validation_label='nested loader')
