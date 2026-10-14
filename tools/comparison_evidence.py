#!/usr/bin/env python3
"""Verify comparison archive coverage and fixed file references, not scientific validity.

References use portable paths relative to the evidence index directory. Keep
that index above the protocol, configurations and execution logs it references.
This local cooperating-writer check does not certify preregistration, numerical
aggregation, semantic fairness, or filesystem transactions with other writers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat

SHA256 = re.compile(r'[a-f0-9]{64}\Z')
TERMINAL = {'completed', 'failed', 'stopped'}
RUN_STATUSES = TERMINAL | {'not-run'}
MAX_RECORD_BYTES = 16 * 1024 * 1024


class ComparisonEvidenceError(ValueError):
    """Comparison evidence is incomplete, changed or unsafe to archive."""


def _require(condition, message):
    if not condition:
        raise ComparisonEvidenceError(message)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _choice(value, choices):
    return isinstance(value, str) and value in choices


def _is_link(path):
    """Include NTFS directory junctions, including Python without is_junction."""
    if path.is_symlink():
        return True
    junction = getattr(path, 'is_junction', None)
    if callable(junction) and junction():
        return True
    try:
        attributes = getattr(path.lstat(), 'st_file_attributes', 0)
    except OSError:
        return False
    return bool(attributes & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)
                and attributes & getattr(stat, 'FILE_ATTRIBUTE_DIRECTORY', 0))


def _object_pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def _reject_constant(value):
    raise ComparisonEvidenceError(f'Non-finite JSON number: {value}')


def _json(path):
    try:
        with path.open('rb') as source:
            raw = source.read(MAX_RECORD_BYTES + 1)
        _require(len(raw) <= MAX_RECORD_BYTES, 'Comparison JSON records must not exceed 16 MiB')
        document = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=_object_pairs,
                              parse_constant=_reject_constant)
        _require(isinstance(document, dict), f'Expected a JSON object: {path.name}')
        _require(type(document.get('schema_version')) is int and document['schema_version'] == 1,
                 f'Unsupported comparison schema: {path.name}')
        return document, hashlib.sha256(raw).hexdigest()
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ComparisonEvidenceError(f'Cannot read comparison record {path.name}: {error}') from error


def file_reference(root, path):
    """Create a content reference; callers must persist the returned record."""
    root, path = Path(root).resolve(), Path(path)
    path = path if path.is_absolute() else root / path
    _require(not _is_link(path), 'Evidence references cannot be symlinks or junctions')
    try:
        relative = path.resolve().relative_to(root).as_posix()
    except ValueError as error:
        raise ComparisonEvidenceError('Evidence reference is outside its index directory') from error
    reference = {'path': relative, 'sha256': _digest(path)}
    _reference(root, reference, {})
    return reference


def _digest(path):
    _require(path.is_file() and not _is_link(path), f'Evidence file is missing or not regular: {path.name}')
    _require(path.stat().st_size > 0, f'Evidence file is empty: {path.name}')
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _reference(root, reference, verified):
    _require(isinstance(reference, dict) and _text(reference.get('path'))
             and isinstance(reference.get('sha256'), str) and SHA256.fullmatch(reference['sha256']),
             'A fixed path/SHA-256 evidence reference is required')
    name = reference['path']
    relative = PurePosixPath(name)
    _require(not relative.is_absolute() and '\\' not in name and ':' not in name
             and '..' not in relative.parts and relative.parts,
             'Evidence paths must be portable relative paths inside the index directory')
    path = root
    for part in relative.parts:
        path = path / part
        _require(not _is_link(path), 'Evidence references cannot traverse symlinks or junctions')
    path = path.resolve()
    _require(path.is_relative_to(root), 'Evidence reference resolves outside the index directory')
    _require(_digest(path) == reference['sha256'], f'Evidence changed: {name}')
    verified[path] = reference['sha256']
    return path


def _selection(rule):
    _require(isinstance(rule, dict), 'A declared validation selection rule is required')
    _require(rule.get('partition') == 'validation', 'Winner selection must use validation, never test results')
    _require(_choice(rule.get('direction'), ('maximize', 'minimize')), 'Selection direction must be declared')
    for key in ('metric', 'aggregation', 'tie_break'):
        _require(_text(rule.get(key)), f'Selection {key} must be declared')


def validate_evidence(path, *, source_run_id=None, winner_run_id=None,
                      forbidden_roots=(), expected_sha256=None):
    """Check every declared slot and recorded attempt before discarding weights.

    A changed index cannot silently replace a previously bound archive receipt.
    The execution ledger is independent of the per-run evidence table; every
    recorded failure/retry must appear. Unrecorded jobs still require review.
    """
    path = Path(path)
    _require(not _is_link(path), 'The comparison evidence index cannot be a symlink or junction')
    path = path.resolve()
    root = path.parent
    index, digest = _json(path)
    if expected_sha256 is not None:
        _require(digest == expected_sha256, 'The bound comparison evidence index changed')
    verified = {path: digest}
    protocol_path = _reference(root, index.get('protocol_ref'), verified)
    protocol, protocol_digest = _json(protocol_path)
    _require(protocol_digest == index['protocol_ref']['sha256'], 'Comparison protocol changed while reading')
    _require(_text(protocol.get('comparison_id')), 'A comparison identity is required')
    _require(_choice(protocol.get('comparison_type'), ('controlled', 'equal-budget', 'tuned')),
             'Declare controlled, equal-budget or tuned comparison')
    _selection(protocol.get('selection'))
    _require(_text(protocol.get('failure_policy')), 'Declare failure and retry accounting')
    planned = protocol.get('planned_runs')
    _require(isinstance(planned, list) and bool(planned), 'Declare method/run/seed slots before execution')
    slots = {}
    for slot in planned:
        _require(isinstance(slot, dict) and _text(slot.get('run_id')) and _text(slot.get('method_id')),
                 'Each declared slot needs a run and method identity')
        _require('seed' in slot and (slot['seed'] is None or type(slot['seed']) is int),
                 'A seed must be an integer or null for a deterministic run')
        _require(slot['run_id'] not in slots, 'Duplicate declared run identity')
        slots[slot['run_id']] = slot
    _reference(root, index.get('comparison_log_ref'), verified)
    ledger_path = _reference(root, index.get('execution_log_ref'), verified)
    ledger, ledger_digest = _json(ledger_path)
    _require(ledger_digest == index['execution_log_ref']['sha256'], 'Execution ledger changed while reading')
    recorded = ledger.get('attempts')
    _require(isinstance(recorded, list) and bool(recorded), 'A terminal execution ledger is required')
    attempts = {}
    for entry in recorded:
        _require(isinstance(entry, dict) and _text(entry.get('run_id')) and entry['run_id'] in slots
                 and _text(entry.get('attempt_id')) and _choice(entry.get('status'), TERMINAL),
                 'Execution ledger has an undeclared run or nonterminal attempt')
        key = (entry['run_id'], entry['attempt_id'])
        _require(key not in attempts, 'Duplicate recorded execution attempt')
        attempts[key] = entry['status']
    runs = index.get('runs')
    _require(isinstance(runs, list) and bool(runs), 'Per-run comparison evidence is required')
    covered, covered_attempts = {}, set()
    for run in runs:
        _require(isinstance(run, dict) and _text(run.get('run_id')) and run['run_id'] in slots,
                 'Evidence contains an undeclared run')
        run_id = run['run_id']
        _require(run_id not in covered, 'Duplicate run evidence')
        slot = slots[run_id]
        _require(run.get('method_id') == slot['method_id'] and 'seed' in run
                 and type(run['seed']) is type(slot['seed']) and run['seed'] == slot['seed'],
                 'Run method/seed differs from its declared slot')
        _require(_choice(run.get('status'), RUN_STATUSES) and type(run.get('included')) is bool
                 and _text(run.get('disposition')), 'Record terminal status and inclusion/exclusion rationale')
        _reference(root, run.get('configuration_ref'), verified)
        receipts = run.get('attempts')
        _require(isinstance(receipts, list) and (bool(receipts) or run['status'] == 'not-run'),
                 'Every executed run needs execution attempt evidence')
        if run['status'] == 'not-run':
            _require(not receipts and not run['included'],
                     'An unstarted slot cannot contain attempts or be included as a result')
            _reference(root, run.get('cancellation_ref'), verified)
        for receipt in receipts:
            _require(isinstance(receipt, dict) and _text(receipt.get('attempt_id')),
                     'An attempt identity is required')
            key = (run_id, receipt['attempt_id'])
            _require(key in attempts and receipt.get('status') == attempts[key],
                     'Attempt evidence differs from the execution ledger')
            _require(key not in covered_attempts, 'Duplicate attempt evidence')
            covered_attempts.add(key)
            _reference(root, receipt.get('evidence_ref'), verified)
        _require(run['status'] != 'completed' or any(r['status'] == 'completed' for r in receipts),
                 'A completed run requires a completed attempt')
        covered[run_id] = run
    _require(set(covered) == set(slots), 'Comparison evidence omits declared runs or seed slots')
    _require(covered_attempts == set(attempts), 'Comparison evidence omits recorded failures or retry attempts')
    selection = index.get('selection')
    _require(isinstance(selection, dict) and selection.get('rule') == protocol['selection'],
             'The selection rule differs from the fixed comparison protocol')
    winner = selection.get('winner_run_id')
    _require(isinstance(winner, str) and winner in covered
             and covered[winner]['status'] in ('completed', 'stopped') and covered[winner]['included'],
             'The selected winner must be a completed or permanently stopped included run')
    if source_run_id is not None:
        _require(source_run_id in covered, 'The archived run is missing from comparison evidence')
    if winner_run_id is not None:
        _require(winner == winner_run_id, 'The selected winner differs from the surviving checkpoint store')
    forbidden = [Path(directory).resolve() for directory in forbidden_roots]
    for file, recorded_digest in verified.items():
        _require(not any(file == directory or directory in file.parents for directory in forbidden),
                 'Comparison evidence must survive outside managed checkpoint artifact directories')
        _require(_digest(file) == recorded_digest, f'Evidence changed during verification: {file.name}')
    return {'status': 'PASS', 'scientific_verdict': 'not-assessed',
            'comparison_id': protocol['comparison_id'], 'run_count': len(covered),
            'attempt_count': len(covered_attempts), 'winner_run_id': winner,
            'reference': {'path': str(path), 'sha256': digest},
            'verified_files': [str(file) for file in verified]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    parser.add_argument('--source-run-id')
    parser.add_argument('--winner-run-id')
    args = parser.parse_args()
    try:
        result = validate_evidence(args.evidence, source_run_id=args.source_run_id,
                                   winner_run_id=args.winner_run_id)
    except (ComparisonEvidenceError, OSError) as error:
        print(json.dumps({'status': 'FAIL', 'error': str(error)}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
