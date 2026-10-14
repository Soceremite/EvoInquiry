"""Small file-backed comparison fixtures; numbers are synthetic test data."""
from __future__ import annotations

import json
from pathlib import Path

from tools.comparison_evidence import file_reference


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def make_evidence(root, *, source_run_id='loser', winner_run_id='winner', retry=False,
                  extra_runs=()):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    slots = [{'run_id': source_run_id, 'method_id': 'method-a', 'seed': 42},
             {'run_id': winner_run_id, 'method_id': 'method-b', 'seed': 42}]
    slots.extend({'run_id': name, 'method_id': 'method-a', 'seed': seed}
                 for seed, name in enumerate(extra_runs))
    rule = {'partition': 'validation', 'metric': 'accuracy', 'direction': 'maximize',
            'aggregation': 'mean across all independent seed slots per method',
            'tie_break': 'lower measured training cost; then declared representative seed'}
    protocol = {'schema_version': 1, 'comparison_id': 'fixture-comparison',
                'comparison_type': 'tuned', 'planned_runs': slots, 'selection': rule,
                'failure_policy': 'all attempts retained; first successful attempt fills each seed slot',
                'common_settings': {'dataset': 'synthetic fixture', 'split': 'fixed sample IDs'}}
    write_json(root / 'protocol.json', protocol)
    (root / 'COMPARISON.md').write_text(
        'Synthetic fixture: all declared runs included; validation selects method-b.\n'
        'Different optimizers are allowed under the declared tuned-system question.\n', encoding='utf-8')
    ledger, runs = [], []
    for i, slot in enumerate(slots):
        config = root / f'configuration-{i}.json'
        write_json(config, {'method_id': slot['method_id'], 'seed': slot['seed'],
                            'optimizer': 'adam' if slot['method_id'] == 'method-b' else 'sgd'})
        attempts = []
        statuses = ['failed', 'completed'] if retry and i == 0 else ['completed']
        for j, status in enumerate(statuses):
            attempt_id = f'attempt-{j}'
            result = root / f'result-{i}-{j}.json'
            write_json(result, {'status': status, 'validation_accuracy': 0.8 if i == 1 else 0.7,
                                'note': 'synthetic fixture, not measured model performance'})
            ledger.append({'run_id': slot['run_id'], 'attempt_id': attempt_id, 'status': status})
            attempts.append({'attempt_id': attempt_id, 'status': status,
                             'evidence_ref': file_reference(root, result)})
        runs.append({**slot, 'status': 'completed', 'included': True,
                     'disposition': 'first successful attempt; any prior failure is retained',
                     'configuration_ref': file_reference(root, config), 'attempts': attempts})
    write_json(root / 'executions.json', {'schema_version': 1, 'attempts': ledger})
    index = {'schema_version': 1, 'protocol_ref': file_reference(root, root / 'protocol.json'),
             'comparison_log_ref': file_reference(root, root / 'COMPARISON.md'),
             'execution_log_ref': file_reference(root, root / 'executions.json'),
             'runs': runs, 'selection': {'winner_run_id': winner_run_id, 'rule': rule}}
    path = root / 'evidence.json'
    write_json(path, index)
    return path
