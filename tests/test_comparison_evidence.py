"""Coverage, identity and evidence survival, without a scientific PASS claim."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from tests.comparison_helpers import make_evidence, write_json
from tools.comparison_evidence import ComparisonEvidenceError, MAX_RECORD_BYTES, file_reference, validate_evidence


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def test_complete_comparison_allows_method_specific_recipes_and_preserves_retries(tmp_path):
    path = make_evidence(tmp_path, retry=True, extra_runs=('second-seed',))
    result = validate_evidence(path, source_run_id='loser', winner_run_id='winner')
    assert result['status'] == 'PASS' and result['scientific_verdict'] == 'not-assessed'
    assert result['run_count'] == 3 and result['attempt_count'] == 4
    assert read(tmp_path / 'configuration-0.json')['optimizer'] != read(tmp_path / 'configuration-1.json')['optimizer']


@pytest.mark.parametrize('problem', ['seed-slot', 'failed-attempt', 'duplicate-run', 'wrong-seed',
                                    'wrong-method', 'running-attempt', 'excluded-winner', 'unknown-winner'])
def test_missing_or_misrepresented_execution_evidence_is_rejected(tmp_path, problem):
    path = make_evidence(tmp_path, retry=True, extra_runs=('second-seed',))
    index = read(path)
    if problem == 'seed-slot':
        index['runs'].pop()
    elif problem == 'failed-attempt':
        index['runs'][0]['attempts'].pop(0)
    elif problem == 'duplicate-run':
        index['runs'].append(index['runs'][0])
    elif problem == 'wrong-seed':
        index['runs'][0]['seed'] = 7
    elif problem == 'wrong-method':
        index['runs'][0]['method_id'] = 'method-c'
    elif problem == 'running-attempt':
        index['runs'][0]['attempts'][0]['status'] = 'running'
    elif problem == 'excluded-winner':
        index['runs'][1]['included'] = False
    else:
        index['selection']['winner_run_id'] = 'not-declared'
    write_json(path, index)
    with pytest.raises(ComparisonEvidenceError):
        validate_evidence(path)


def test_failure_only_run_can_be_recorded_without_fabricating_metrics(tmp_path):
    path = make_evidence(tmp_path)
    index = read(path)
    ledger = read(tmp_path / 'executions.json')
    ledger['attempts'][0]['status'] = 'failed'
    write_json(tmp_path / 'executions.json', ledger)
    index['execution_log_ref'] = file_reference(tmp_path, tmp_path / 'executions.json')
    index['runs'][0].update(status='failed', included=False, disposition='OOM; no successful result')
    index['runs'][0]['attempts'][0]['status'] = 'failed'
    failure_path = tmp_path / 'failure.log'
    failure_path.write_text('OOM before evaluation\n')
    index['runs'][0]['attempts'][0]['evidence_ref'] = file_reference(tmp_path, failure_path)
    write_json(path, index)
    assert validate_evidence(path)['attempt_count'] == 2


def test_unstarted_seed_has_a_cancellation_record_instead_of_a_fabricated_attempt(tmp_path):
    path = make_evidence(tmp_path, extra_runs=('cancelled-seed',))
    index = read(path)
    ledger = read(tmp_path / 'executions.json')
    ledger['attempts'] = [e for e in ledger['attempts'] if e['run_id'] != 'cancelled-seed']
    write_json(tmp_path / 'executions.json', ledger)
    index['execution_log_ref'] = file_reference(tmp_path, tmp_path / 'executions.json')
    (tmp_path / 'cancellation.log').write_text('User permanently ends campaign before this slot launches.\n')
    index['runs'][2].update(status='not-run', included=False, disposition='not started; user ended campaign',
                            attempts=[], cancellation_ref=file_reference(tmp_path, tmp_path / 'cancellation.log'))
    write_json(path, index)
    report = validate_evidence(path)
    assert report['run_count'] == 3 and report['attempt_count'] == 2
    index['runs'][2]['included'] = True
    write_json(path, index)
    with pytest.raises(ComparisonEvidenceError, match='unstarted slot'):
        validate_evidence(path)


def test_unstarted_seed_requires_cancellation_evidence(tmp_path):
    path = make_evidence(tmp_path)
    index = read(path)
    index['runs'][0].update(status='not-run', included=False, attempts=[], disposition='cancelled')
    write_json(path, index)
    with pytest.raises(ComparisonEvidenceError, match='fixed path/SHA-256'):
        validate_evidence(path)


@pytest.mark.parametrize('problem', ['test-selection', 'changed-rule', 'wrong-store', 'missing-run'])
def test_selection_and_checkpoint_store_identity_are_bound(tmp_path, problem):
    path = make_evidence(tmp_path)
    index = read(path)
    kwargs = {}
    if problem == 'test-selection':
        protocol = read(tmp_path / 'protocol.json')
        protocol['selection']['partition'] = 'test'
        write_json(tmp_path / 'protocol.json', protocol)
        index['protocol_ref'] = file_reference(tmp_path, tmp_path / 'protocol.json')
        index['selection']['rule'] = protocol['selection']
    elif problem == 'changed-rule':
        index['selection']['rule']['aggregation'] = 'best seed after observing results'
    elif problem == 'wrong-store':
        kwargs['winner_run_id'] = 'loser'
    else:
        kwargs['source_run_id'] = 'unrecorded-run'
    write_json(path, index)
    with pytest.raises(ComparisonEvidenceError):
        validate_evidence(path, **kwargs)


@pytest.mark.parametrize('file', ['COMPARISON.md', 'protocol.json', 'executions.json',
                                 'configuration-0.json', 'result-0-0.json'])
@pytest.mark.parametrize('operation', ['change', 'remove', 'empty'])
def test_all_required_files_are_verified(tmp_path, file, operation):
    path = make_evidence(tmp_path)
    target = tmp_path / file
    if operation == 'remove':
        target.unlink()
    else:
        target.write_text('changed' if operation == 'change' else '')
    with pytest.raises(ComparisonEvidenceError):
        validate_evidence(path)


def test_bound_index_cannot_be_silently_replaced(tmp_path):
    path = make_evidence(tmp_path)
    bound = validate_evidence(path)['reference']
    index = read(path)
    index['runs'][0]['disposition'] = 'a changed exclusion explanation'
    write_json(path, index)
    with pytest.raises(ComparisonEvidenceError, match='bound comparison evidence index changed'):
        validate_evidence(path, expected_sha256=bound['sha256'])


def test_evidence_inside_a_checkpoint_candidate_is_rejected(tmp_path):
    path = make_evidence(tmp_path / 'checkpoint-artifact')
    with pytest.raises(ComparisonEvidenceError, match='outside managed checkpoint'):
        validate_evidence(path, forbidden_roots=(path.parent,))


@pytest.mark.parametrize('name', ['../outside.json', '/outside.json', 'C:/outside.json', 'logs\\result.json'])
def test_nonportable_or_escaping_paths_are_rejected(tmp_path, name):
    path = make_evidence(tmp_path)
    index = read(path)
    index['comparison_log_ref']['path'] = name
    write_json(path, index)
    with pytest.raises(ComparisonEvidenceError, match='portable relative paths'):
        validate_evidence(path)


@pytest.mark.parametrize('location', ['index', 'file', 'directory'])
def test_symlink_evidence_is_rejected(tmp_path, location):
    path = make_evidence(tmp_path / 'evidence')
    index = read(path)
    try:
        if location == 'index':
            link = tmp_path / 'linked-index.json'
            link.symlink_to(path)
            path = link
        elif location == 'file':
            target = path.parent / 'COMPARISON.md'
            link = path.parent / 'linked-log.md'
            link.symlink_to(target)
            index['comparison_log_ref']['path'] = link.name
            write_json(path, index)
        else:
            directory = path.parent / 'logs'
            directory.mkdir()
            target = directory / 'summary.md'
            target.write_text('summary\n')
            index['comparison_log_ref'] = file_reference(path.parent, target)
            directory.rename(path.parent / 'actual-logs')
            directory.symlink_to(path.parent / 'actual-logs', target_is_directory=True)
            write_json(path, index)
    except OSError:
        pytest.skip('Symlink creation is unavailable on this filesystem')
    with pytest.raises(ComparisonEvidenceError, match='symlink'):
        validate_evidence(path)


@pytest.mark.parametrize('field', ['comparison_type', 'ledger-run', 'run-id', 'status', 'winner'])
def test_malformed_structured_fields_fail_with_an_actionable_error(tmp_path, field):
    path = make_evidence(tmp_path)
    index = read(path)
    if field == 'comparison_type':
        protocol = read(tmp_path / 'protocol.json')
        protocol[field] = []
        write_json(tmp_path / 'protocol.json', protocol)
        index['protocol_ref'] = file_reference(tmp_path, tmp_path / 'protocol.json')
    elif field == 'ledger-run':
        ledger = read(tmp_path / 'executions.json')
        ledger['attempts'][0]['run_id'] = []
        write_json(tmp_path / 'executions.json', ledger)
        index['execution_log_ref'] = file_reference(tmp_path, tmp_path / 'executions.json')
    elif field == 'run-id':
        index['runs'][0]['run_id'] = {}
    elif field == 'status':
        index['runs'][0]['status'] = []
    else:
        index['selection']['winner_run_id'] = []
    write_json(path, index)
    with pytest.raises(ComparisonEvidenceError):
        validate_evidence(path)


def test_deterministic_slots_do_not_require_training_seeds(tmp_path):
    path = make_evidence(tmp_path)
    protocol, index = read(tmp_path / 'protocol.json'), read(path)
    for slot, run in zip(protocol['planned_runs'], index['runs']):
        slot['seed'] = run['seed'] = None
    write_json(tmp_path / 'protocol.json', protocol)
    index['protocol_ref'] = file_reference(tmp_path, tmp_path / 'protocol.json')
    write_json(path, index)
    assert validate_evidence(path)['run_count'] == 2


def test_duplicate_json_keys_and_nonfinite_numbers_are_rejected(tmp_path):
    path = tmp_path / 'evidence.json'
    for raw in ('{"schema_version":1,"schema_version":1}', '{"schema_version":1,"value":NaN}'):
        path.write_text(raw)
        with pytest.raises(ComparisonEvidenceError):
            validate_evidence(path)


def test_large_json_index_is_bounded_without_loading_model_sized_files(tmp_path):
    path = tmp_path / 'evidence.json'
    with path.open('wb') as source:
        source.truncate(MAX_RECORD_BYTES + 1)
    with pytest.raises(ComparisonEvidenceError, match='16 MiB'):
        validate_evidence(path)


@pytest.mark.skipif(sys.platform != 'win32', reason='NTFS Junction requires a native Windows runner')
@pytest.mark.parametrize('fallback', [False, True])
def test_native_windows_junction_cannot_redirect_comparison_evidence(tmp_path, monkeypatch, fallback):
    path = make_evidence(tmp_path / 'comparison')
    index = read(path)
    outside = tmp_path / 'outside'
    outside.mkdir()
    raw = (path.parent / 'COMPARISON.md').read_bytes()
    (outside / 'summary.md').write_bytes(raw)
    link = path.parent / 'redirected'
    created = subprocess.run(['cmd.exe', '/c', 'mklink', '/J', str(link), str(outside)], capture_output=True)
    assert created.returncode == 0, created.stdout + created.stderr
    if fallback:
        monkeypatch.setattr(Path, 'is_junction', None)
    index['comparison_log_ref']['path'] = 'redirected/summary.md'
    write_json(path, index)
    with pytest.raises(ComparisonEvidenceError, match='junction'):
        validate_evidence(path)


def test_cli_checks_real_files_and_reports_coverage_without_a_scientific_verdict(tmp_path):
    path = make_evidence(tmp_path / 'comparison with spaces', retry=True)
    script = Path(__file__).resolve().parents[1] / 'tools/comparison_evidence.py'
    command = [sys.executable, str(script), str(path), '--winner-run-id', 'winner']
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)['scientific_verdict'] == 'not-assessed'
    (path.parent / 'COMPARISON.md').unlink()
    rejected = subprocess.run(command, capture_output=True, text=True)
    assert rejected.returncode == 1 and json.loads(rejected.stdout)['status'] == 'FAIL'
