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


@pytest.mark.parametrize('outcome', ['completed', 'stopped'])
def test_finished_training_removes_recovery_state_after_verified_final_export(store, outcome):
    first = save(store, 10)
    second = save(store, 20)
    final = save(store, 20, kind='weights', roles=('best', 'final'))
    original = (store.root / final['id'] / 'state.json').read_bytes()
    result = store.finish(outcome=outcome, step=20, reason='all steps complete or explicit permanent stop', apply=True)
    assert set(result['deleted']) == {first['id'], second['id']}
    assert [e['id'] for e in active(store)] == [final['id']]
    assert (store.root / final['id'] / 'state.json').read_bytes() == original
    reopened = CheckpointStore(store.root)
    assert reopened.status()['lifecycle']['state'] == outcome
    assert reopened.latest() is None
    assert not reopened.finish(outcome=outcome, step=20, reason='all steps complete or explicit permanent stop', apply=True)['deleted']


@pytest.mark.parametrize('problem', ['missing', 'resume_only', 'corrupt'])
def test_finish_requires_loaded_and_intact_inference_export_before_deletion(store, problem):
    save(store, 10)
    save(store, 20)
    if problem == 'resume_only':
        save(store, 20, roles=('final',))
    elif problem == 'corrupt':
        exported = save(store, 20, kind='weights', roles=('final',))
        (store.root / exported['id'] / 'state.json').write_text('changed')
    before = {p.relative_to(store.root): p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    with pytest.raises(RetentionError, match='inference weights'):
        store.finish(outcome='completed', step=20, reason='training complete', apply=True)
    after = {p.relative_to(store.root): p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    assert after == before
    assert store.status()['lifecycle']['state'] == 'active'


def test_finish_preview_preserves_all_artifacts_and_resume_policy(store):
    saved = save(store, 10)
    save(store, 20)
    save(store, 20, kind='weights', roles=('final',))
    before = (store.root / MANIFEST).read_bytes()
    result = store.finish(outcome='stopped', step=20, reason='user ends training')
    assert result['applied'] is False
    assert saved['id'] in result['status']['remove']
    assert result['proposed_lifecycle']['state'] == 'stopped'
    assert (store.root / MANIFEST).read_bytes() == before
    assert len(active(store)) == 3
    assert store.status()['lifecycle']['state'] == 'active'


def test_finish_preserves_dependencies_changed_files_and_unregistered_evidence(store):
    teacher = save(store, 1, pins=('needed by the student experiment',))
    changed = save(store, 2)
    (store.root / changed['id'] / 'state.json').write_text('failed-save diagnostic')
    save(store, 3)
    final = save(store, 3, kind='weights', roles=('best', 'final'))
    evidence = store.root / 'metrics.csv'
    evidence.write_text('seed,accuracy\n42,0.81\n')
    store.finish(outcome='completed', step=3, reason='completed with a teacher dependency', apply=True)
    assert {e['id'] for e in active(store)} == {teacher['id'], changed['id'], final['id']}
    assert evidence.read_text() == 'seed,accuracy\n42,0.81\n'
    store.pin(teacher['id'], 'needed by the student experiment', remove=True)
    store.prune(apply=True)
    assert {e['id'] for e in active(store)} == {changed['id'], final['id']}


def test_finished_run_rejects_new_publication_before_invoking_writer(store):
    save(store, 20, kind='weights', roles=('final',))
    store.finish(outcome='stopped', step=20, reason='user ends training', apply=True)
    calls = []
    with pytest.raises(RetentionError, match='Training has finished'):
        store.publish(step=21, kind='resume', expected_bytes=100, writer=lambda p: calls.append(p),
                      validator=lambda p: None, validation_label='loader')
    assert calls == []
    with pytest.raises(RetentionError, match='outcome cannot change'):
        store.finish(outcome='completed', step=20, reason='another outcome', apply=True)


def test_finish_refuses_claimed_terminal_progress_before_saved_steps(store):
    save(store, 20)
    save(store, 20, kind='weights', roles=('final',))
    with pytest.raises(RetentionError, match='precedes registered'):
        store.finish(outcome='completed', step=10, reason='incorrect progress', apply=True)
    assert store.status()['lifecycle']['state'] == 'active'
    assert len(active(store)) == 2


def test_comparison_archives_nonwinner_weights_only_after_preserving_finished_winner(store, tmp_path):
    winner = CheckpointStore.create(tmp_path / 'winner', run_id='best-by-validation', budget_bytes=10_000)
    best = save(winner, 15, kind='weights', roles=('best', 'final'))
    winner.finish(outcome='completed', step=20, reason='all training steps completed', apply=True)
    save(store, 10)
    loser_best = save(store, 20, kind='weights', roles=('best', 'final'))
    evidence = store.root / 'results.csv'
    evidence.write_text('model,validation_score\nloser,0.76\n')
    survivor = (winner.root / best['id'] / 'state.json').read_bytes()
    before = {root: (root / MANIFEST).read_bytes() for root in (store.root, winner.root)}
    preview = store.finish(outcome='completed', step=20, reason='shared validation metric selects the winner', archive_to=winner.root)
    assert preview['status']['remove'] and preview['released_roles']
    assert all((root / MANIFEST).read_bytes() == raw for root, raw in before.items())
    result = store.finish(outcome='completed', step=20, reason='shared validation metric selects the winner', archive_to=winner.root, apply=True)
    assert loser_best['id'] in result['deleted']
    assert not active(store) and store.latest() is None
    assert evidence.read_text() == 'model,validation_score\nloser,0.76\n'
    assert (winner.root / best['id'] / 'state.json').read_bytes() == survivor
    assert len(active(winner)[0]['pins']) == 1
    assert store.status()['lifecycle']['archive']['root'] == str(winner.root)
    assert store.status()['lifecycle']['archive']['files'] == best['files']
    store.finish(outcome='completed', step=20, reason='shared validation metric selects the winner', archive_to=winner.root, apply=True)
    assert len(active(winner)[0]['pins']) == 1


@pytest.mark.parametrize('problem', ['active', 'missing_best', 'corrupt_best'])
def test_comparison_cannot_delete_loser_with_an_unavailable_survivor(store, tmp_path, problem):
    winner = CheckpointStore.create(tmp_path / 'winner', run_id='winner', budget_bytes=10_000)
    best = save(winner, 20, kind='weights', roles=('best', 'final'))
    if problem != 'active':
        winner.finish(outcome='completed', step=20, reason='done', apply=True)
    if problem == 'missing_best':
        data = json.loads((winner.root / MANIFEST).read_text())
        del data['roles']['best']
        (winner.root / MANIFEST).write_text(json.dumps(data))
    if problem == 'corrupt_best':
        (winner.root / best['id'] / 'state.json').write_text('corrupt')
    save(store, 20)
    save(store, 20, kind='weights', roles=('final',))
    before = (store.root / MANIFEST).read_bytes()
    with pytest.raises(RetentionError):
        store.finish(outcome='completed', step=20, reason='winner selected', archive_to=winner.root, apply=True)
    assert (store.root / MANIFEST).read_bytes() == before
    assert len(active(store)) == 2


def test_completed_runs_can_later_consolidate_without_releasing_dependency_models(store, tmp_path):
    winner = CheckpointStore.create(tmp_path / 'winner', run_id='winner', budget_bytes=10_000)
    save(winner, 20, kind='weights', roles=('best', 'final'))
    winner.finish(outcome='completed', step=20, reason='done', apply=True)
    dependent = save(store, 10, kind='weights', pins=('required by an approved ablation',))
    final = save(store, 20, kind='weights', roles=('best', 'final'))
    store.finish(outcome='completed', step=20, reason='done', apply=True)
    store.finish(outcome='completed', step=20, reason='campaign keeps validation winner', archive_to=winner.root, apply=True)
    assert [e['id'] for e in active(store)] == [dependent['id']]
    assert not (store.root / final['id']).exists()


def test_finish_pins_survivor_before_any_local_deletion_even_if_local_commit_fails(store, tmp_path, monkeypatch):
    winner = CheckpointStore.create(tmp_path / 'winner', run_id='winner', budget_bytes=10_000)
    save(winner, 20, kind='weights', roles=('best', 'final'))
    winner.finish(outcome='completed', step=20, reason='done', apply=True)
    saved = save(store, 20)
    before = (store.root / MANIFEST).read_bytes()
    monkeypatch.setattr(store, '_write', lambda data: (_ for _ in ()).throw(OSError('local manifest failed')))
    with pytest.raises(OSError, match='manifest failed'):
        store.finish(outcome='completed', step=20, reason='winner selected', archive_to=winner.root, apply=True)
    assert (store.root / MANIFEST).read_bytes() == before
    assert (store.root / saved['id']).exists()
    assert len(active(winner)[0]['pins']) == 1


def test_finish_interrupted_deletion_is_recoverable_and_preserves_archived_weights(store, monkeypatch):
    import tools.checkpoint_retention as module
    saved = save(store, 10)
    final = save(store, 20, kind='weights', roles=('final',))
    real_rmtree = module.shutil.rmtree

    def interrupted(path):
        (path / 'state.json').unlink()
        raise OSError('interrupted retirement')

    monkeypatch.setattr(module.shutil, 'rmtree', interrupted)
    with pytest.raises(OSError, match='interrupted retirement'):
        store.finish(outcome='completed', step=20, reason='done', apply=True)
    assert store.status()['lifecycle']['state'] == 'completed'
    assert saved['id'] in store.status()['garbage_remove']
    monkeypatch.setattr(module.shutil, 'rmtree', real_rmtree)
    reopened = CheckpointStore(store.root)
    reopened.prune(apply=True)
    assert [e['id'] for e in active(reopened)] == [final['id']]
    assert not reopened.status()['garbage_remove']


@pytest.mark.parametrize('external', [False, True])
def test_prune_retry_refuses_further_deletion_if_archived_survivor_is_damaged(store, tmp_path, monkeypatch, external):
    survivor_store = (CheckpointStore.create(tmp_path / 'winner', run_id='winner', budget_bytes=10_000)
                      if external else store)
    survivor = save(survivor_store, 20, kind='weights', roles=('best', 'final'))
    if external:
        survivor_store.finish(outcome='completed', step=20, reason='done', apply=True)
    recoverable = save(store, 20)
    if external:
        save(store, 20, kind='weights', roles=('final',))
    original_prune = store._prune
    monkeypatch.setattr(store, '_prune', lambda data: (_ for _ in ()).throw(OSError('interrupted before cleanup')))
    with pytest.raises(OSError, match='interrupted before cleanup'):
        store.finish(outcome='completed', step=20, reason='done',
                     archive_to=survivor_store.root if external else None, apply=True)
    monkeypatch.setattr(store, '_prune', original_prune)
    path = survivor_store.root / survivor['id'] / 'state.json'
    original_bytes = path.read_bytes()
    path.write_text('now corrupt')
    before = (store.root / MANIFEST).read_bytes()
    reopened = CheckpointStore(store.root)
    with pytest.raises(RetentionError, match='Archived inference weights'):
        reopened.prune(apply=True)
    assert (store.root / MANIFEST).read_bytes() == before
    assert (store.root / recoverable['id']).exists()
    path.write_bytes(original_bytes)
    reopened.prune(apply=True)
    assert not (store.root / recoverable['id']).exists()
    assert path.read_bytes() == original_bytes


def test_journaled_retirement_requires_surviving_archive_on_retry(store, tmp_path, monkeypatch):
    import tools.checkpoint_retention as module
    winner = CheckpointStore.create(tmp_path / 'winner', run_id='winner', budget_bytes=10_000)
    best = save(winner, 20, kind='weights', roles=('best', 'final'))
    winner.finish(outcome='completed', step=20, reason='done', apply=True)
    source = save(store, 20)
    real_rmtree = module.shutil.rmtree
    monkeypatch.setattr(module.shutil, 'rmtree', lambda p: (_ for _ in ()).throw(OSError('before deletion')))
    with pytest.raises(OSError, match='before deletion'):
        store.finish(outcome='completed', step=20, reason='winner chosen', archive_to=winner.root, apply=True)
    monkeypatch.setattr(module.shutil, 'rmtree', real_rmtree)
    assert source['id'] in store.status()['garbage_remove']
    (winner.root / best['id'] / 'state.json').write_text('corrupt winner')
    with pytest.raises(RetentionError, match='Archived inference weights'):
        store.prune(apply=True)
    assert (store.root / source['id'] / 'state.json').is_file()


def test_finish_cannot_race_another_cooperating_publisher(store):
    save(store, 10, kind='weights', roles=('final',))
    other = CheckpointStore(store.root)

    def writer(path):
        (path / 'state.json').write_text('{}')
        with pytest.raises(RetentionError, match='Another writer'):
            other.finish(outcome='completed', step=20, reason='done', apply=True)

    store.publish(step=20, kind='resume', expected_bytes=100, writer=writer,
                  validator=lambda p: None, validation_label='loader')
    assert store.status()['lifecycle']['state'] == 'active'


def test_finished_store_can_be_relocated_before_comparison_archiving(store, tmp_path):
    saved = save(store, 20, kind='weights', roles=('best', 'final'))
    store.finish(outcome='completed', step=20, reason='done', apply=True)
    moved = tmp_path / 'relocated run'
    store.root.rename(moved)
    winner = CheckpointStore.create(tmp_path / 'winner', run_id='winner', budget_bytes=10_000)
    save(winner, 20, kind='weights', roles=('best', 'final'))
    winner.finish(outcome='completed', step=20, reason='done', apply=True)
    reopened = CheckpointStore(moved)
    reopened.finish(outcome='completed', step=20, reason='validation winner', archive_to=winner.root, apply=True)
    assert not (moved / saved['id']).exists()
    assert reopened.status()['lifecycle']['archive']['scope'] == 'comparison'


def test_comparison_lock_failure_releases_other_store_lock_without_mutation(store, tmp_path):
    from tools.checkpoint_retention import _lock
    winner = CheckpointStore.create(tmp_path / 'winner', run_id='winner', budget_bytes=10_000)
    save(winner, 20, kind='weights', roles=('best', 'final'))
    winner.finish(outcome='completed', step=20, reason='done', apply=True)
    save(store, 20, kind='weights', roles=('final',))
    before = (store.root / MANIFEST).read_bytes()
    with _lock(winner.root):
        with pytest.raises(RetentionError, match='Another writer'):
            store.finish(outcome='completed', step=20, reason='validation winner', archive_to=winner.root, apply=True)
    assert (store.root / MANIFEST).read_bytes() == before
    # If the second ordered lock failed, the first lock must not leak.
    save(store, 21)
    assert store.status()['latest_step'] == 21


def test_cli_finish_is_preview_until_explicit_application(store):
    save(store, 10)
    final = save(store, 20, kind='weights', roles=('final',))
    script = Path(__file__).resolve().parents[1] / 'tools/checkpoint_retention.py'
    command = [sys.executable, str(script), 'finish', str(store.root),
               '--outcome', 'stopped', '--step', '20', '--reason', 'user ends training']
    preview = subprocess.run(command, capture_output=True, text=True)
    assert preview.returncode == 0, preview.stdout
    assert json.loads(preview.stdout)['applied'] is False
    assert len(active(store)) == 2
    applied = subprocess.run(command + ['--apply'], capture_output=True, text=True)
    assert applied.returncode == 0, applied.stdout
    assert json.loads(applied.stdout)['applied'] is True
    assert [e['id'] for e in active(store)] == [final['id']]


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
