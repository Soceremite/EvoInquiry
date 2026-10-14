"""Comparison evidence is a precondition for destructive weight consolidation."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from tests.comparison_helpers import make_evidence, write_json
from tests.test_checkpoint_retention import active, save
from tools.checkpoint_retention import CheckpointStore, MANIFEST, RetentionError
from tools.comparison_evidence import file_reference


@pytest.fixture
def campaign(tmp_path):
    loser = CheckpointStore.create(tmp_path / 'loser', run_id='loser', budget_bytes=10_000)
    winner = CheckpointStore.create(tmp_path / 'winner', run_id='winner', budget_bytes=10_000)
    winning_weights = save(winner, 20, kind='weights', roles=('best', 'final'))
    winner.finish(outcome='completed', step=20, reason='all steps complete', apply=True)
    resume = save(loser, 10)
    final = save(loser, 20, kind='weights', roles=('best', 'final'))
    evidence = make_evidence(tmp_path / 'comparison', retry=True)
    return loser, winner, evidence, resume, final, winning_weights


def finish(loser, winner, evidence, *, apply=True):
    return loser.finish(outcome='completed', step=20, reason='validation comparison selects winner',
                        archive_to=winner.root, comparison_evidence=evidence, apply=apply)


def test_preview_and_apply_refuse_missing_evidence_without_pinning_or_deleting(campaign):
    loser, winner, _, resume, final, _ = campaign
    before = {s.root: (s.root / MANIFEST).read_bytes() for s in (loser, winner)}
    for apply in (False, True):
        with pytest.raises(RetentionError, match='Comparison evidence is required'):
            finish(loser, winner, None, apply=apply)
        assert all((s.root / MANIFEST).read_bytes() == before[s.root] for s in (loser, winner))
    assert all((loser.root / entry['id']).exists() for entry in (resume, final))
    assert not active(winner)[0]['pins']


@pytest.mark.parametrize('problem', ['missing-seed', 'missing-failure', 'changed-log', 'different-winner'])
def test_incomplete_comparison_retains_all_models_and_original_receipts(campaign, problem):
    loser, winner, evidence, _, _, _ = campaign
    index = json.loads(evidence.read_text())
    if problem == 'missing-seed':
        index['runs'].pop(0)
    elif problem == 'missing-failure':
        index['runs'][0]['attempts'].pop(0)
    elif problem == 'different-winner':
        index['selection']['winner_run_id'] = 'loser'
    else:
        (evidence.parent / 'COMPARISON.md').write_text('changed comparison\n')
    write_json(evidence, index)
    before = {s.root: (s.root / MANIFEST).read_bytes() for s in (loser, winner)}
    with pytest.raises(RetentionError, match='Comparison evidence verification failed'):
        finish(loser, winner, evidence)
    assert all((s.root / MANIFEST).read_bytes() == before[s.root] for s in (loser, winner))
    assert len(active(loser)) == 2 and not active(winner)[0]['pins']


def test_evidence_in_an_owned_checkpoint_is_not_a_surviving_archive(campaign):
    loser, winner, _, resume, _, _ = campaign
    evidence = make_evidence(loser.root / resume['id'] / 'comparison')
    before = (loser.root / MANIFEST).read_bytes()
    with pytest.raises(RetentionError, match='outside managed checkpoint'):
        finish(loser, winner, evidence)
    assert (loser.root / MANIFEST).read_bytes() == before and evidence.exists()


@pytest.mark.parametrize('changed_file', ['evidence.json', 'COMPARISON.md', 'result-0-0.json'])
def test_interrupted_cleanup_rechecks_bound_evidence_before_resuming(campaign, monkeypatch, changed_file):
    loser, winner, evidence, resume, final, _ = campaign
    original_clean = loser._clean_garbage
    monkeypatch.setattr(loser, '_clean_garbage', lambda data: (_ for _ in ()).throw(OSError('interrupted cleanup')))
    with pytest.raises(OSError, match='interrupted cleanup'):
        finish(loser, winner, evidence)
    monkeypatch.setattr(loser, '_clean_garbage', original_clean)
    assert {resume['id'], final['id']} == set(loser.status()['garbage_remove'])
    target = evidence.parent / changed_file
    original = target.read_bytes()
    target.write_bytes(original + b'\n')
    before = (loser.root / MANIFEST).read_bytes()
    reopened = CheckpointStore(loser.root)
    with pytest.raises(RetentionError, match='Comparison evidence verification failed'):
        reopened.prune(apply=True)
    assert (loser.root / MANIFEST).read_bytes() == before
    assert all((loser.root / entry['id']).exists() for entry in (resume, final))
    target.write_bytes(original)
    reopened.prune(apply=True)
    assert not any((loser.root / entry['id']).exists() for entry in (resume, final))
    assert evidence.exists() and active(winner)[0]['pins']


def test_legacy_comparison_receipt_remains_readable_and_requires_binding_before_cleanup(campaign, monkeypatch):
    loser, winner, evidence, resume, _, _ = campaign
    original_prune = loser._prune
    monkeypatch.setattr(loser, '_prune', lambda data: (_ for _ in ()).throw(OSError('before cleanup')))
    with pytest.raises(OSError):
        finish(loser, winner, evidence)
    monkeypatch.setattr(loser, '_prune', original_prune)
    manifest_path = loser.root / MANIFEST
    manifest = json.loads(manifest_path.read_text())
    del manifest['lifecycle']['archive']['comparison_evidence']
    write_json(manifest_path, manifest)
    legacy = CheckpointStore(loser.root)
    assert legacy.status()['lifecycle']['state'] == 'completed'
    before = manifest_path.read_bytes()
    with pytest.raises(RetentionError, match='Comparison evidence is required'):
        legacy.prune(apply=True)
    assert manifest_path.read_bytes() == before and (loser.root / resume['id']).exists()
    finish(legacy, winner, evidence)
    assert not (loser.root / resume['id']).exists()
    assert legacy.status()['lifecycle']['archive']['comparison_evidence']['sha256']


def test_cpu_file_integration_retains_logs_failed_attempts_and_dependencies(campaign):
    loser, winner, evidence, resume, final, winning_weights = campaign
    dependent = save(loser, 20, kind='weights', pins=('required teacher for planned follow-up',))
    preserved = {p: p.read_bytes() for p in evidence.parent.iterdir() if p.is_file()}
    winning_path = winner.root / winning_weights['id'] / 'state.json'
    winning_bytes = winning_path.read_bytes()
    preview = finish(loser, winner, evidence, apply=False)
    assert preview['applied'] is False and set(preview['status']['remove']) == {resume['id'], final['id']}
    assert not active(winner)[0]['pins']
    result = finish(loser, winner, evidence)
    assert set(result['deleted']) == {resume['id'], final['id']}
    assert all(p.read_bytes() == raw for p, raw in preserved.items())
    assert winning_path.read_bytes() == winning_bytes and (loser.root / dependent['id']).exists()
    assert [e['id'] for e in active(loser)] == [dependent['id']]
    assert len(active(winner)[0]['pins']) == 1
    # The bound receipt supports idempotent reuse without inventing new evidence.
    finish(loser, winner, None)
    assert len(active(winner)[0]['pins']) == 1


def test_permanently_stopped_winner_can_survive_with_validated_weights_and_recorded_results(campaign, tmp_path):
    loser, _, evidence, resume, final, _ = campaign
    winner = CheckpointStore.create(tmp_path / 'stopped-winner', run_id='winner', budget_bytes=10_000)
    save(winner, 20, kind='weights', roles=('best', 'final'))
    winner.finish(outcome='stopped', step=20, reason='user permanently ends further training', apply=True)
    index = json.loads(evidence.read_text())
    ledger_path = evidence.parent / 'executions.json'
    ledger = json.loads(ledger_path.read_text())
    for entry in ledger['attempts']:
        if entry['run_id'] == 'winner':
            entry['status'] = 'stopped'
    write_json(ledger_path, ledger)
    index['execution_log_ref'] = file_reference(evidence.parent, ledger_path)
    index['runs'][1]['status'] = index['runs'][1]['attempts'][0]['status'] = 'stopped'
    index['runs'][1]['disposition'] = 'user permanently stopped training; validation evaluation retained'
    write_json(evidence, index)
    result = finish(loser, winner, evidence)
    assert set(result['deleted']) == {resume['id'], final['id']}
    assert active(winner)[0]['pins'] and winner.status()['lifecycle']['state'] == 'stopped'


def test_cli_requires_evidence_and_preserves_preview_semantics(campaign):
    loser, winner, evidence, resume, final, _ = campaign
    script = Path(__file__).resolve().parents[1] / 'tools/checkpoint_retention.py'
    command = [sys.executable, str(script), 'finish', str(loser.root), '--outcome', 'completed',
               '--step', '20', '--reason', 'validation selection', '--archive-to', str(winner.root)]
    missing = subprocess.run(command, capture_output=True, text=True)
    assert missing.returncode == 1 and 'Comparison evidence is required' in json.loads(missing.stdout)['error']
    command += ['--comparison-evidence', str(evidence)]
    preview = subprocess.run(command, capture_output=True, text=True)
    assert preview.returncode == 0 and json.loads(preview.stdout)['applied'] is False
    assert all((loser.root / entry['id']).exists() for entry in (resume, final))
    applied = subprocess.run(command + ['--apply'], capture_output=True, text=True)
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert not any((loser.root / entry['id']).exists() for entry in (resume, final))


def test_standalone_checkpoint_cli_preserves_single_file_installation(campaign, tmp_path):
    loser, winner, evidence, _, _, _ = campaign
    standalone = tmp_path / 'standalone'
    standalone.mkdir()
    script = standalone / 'checkpoint_retention.py'
    shutil.copyfile(Path(__file__).resolve().parents[1] / 'tools/checkpoint_retention.py', script)
    # Isolated import has no repo, tools package or companion on its module path.
    result = subprocess.run([sys.executable, '-I', str(script), 'status', str(loser.root)],
                            cwd=standalone, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    before = {s.root: (s.root / MANIFEST).read_bytes() for s in (loser, winner)}
    archive = subprocess.run([sys.executable, '-I', str(script), 'finish', str(loser.root),
        '--outcome', 'completed', '--step', '20', '--reason', 'validation selection',
        '--archive-to', str(winner.root), '--comparison-evidence', str(evidence), '--apply'],
        cwd=standalone, capture_output=True, text=True)
    assert archive.returncode == 1 and 'companion comparison_evidence.py' in json.loads(archive.stdout)['error']
    assert all((s.root / MANIFEST).read_bytes() == before[s.root] for s in (loser, winner))
    shutil.copyfile(Path(__file__).resolve().parents[1] / 'tools/comparison_evidence.py',
                    standalone / 'comparison_evidence.py')
    applied = subprocess.run([sys.executable, str(script), 'finish', str(loser.root),
        '--outcome', 'completed', '--step', '20', '--reason', 'validation selection',
        '--archive-to', str(winner.root), '--comparison-evidence', str(evidence), '--apply'],
        cwd=standalone, capture_output=True, text=True)
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert not active(loser) and active(winner)[0]['pins']
