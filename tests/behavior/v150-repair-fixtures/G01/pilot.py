"""Small synthetic CPU studies for integration verification, not research claims.

Runs real fits and held-out predictions with only Python's standard library.
The scenarios validate artifact/decision plumbing; no LLM selects the method here.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import random
import statistics


def dataset(seed, count):
    rng = random.Random(seed)
    rows = []
    for index in range(count):
        signal, nuisance = rng.uniform(-2, 2), rng.uniform(-2, 2)
        rows.append({'id': index, 'signal': signal, 'nuisance': nuisance,
                     'target': 2 * signal + 1 + rng.gauss(0, 0.1)})
    return rows


def evaluate(feature):
    outputs, metrics = [], []
    for seed in (11, 29, 47):
        rows = dataset(seed, 512)
        train, test = rows[:256], rows[256:]
        xbar = statistics.mean(row[feature] for row in train)
        ybar = statistics.mean(row['target'] for row in train)
        slope = sum((row[feature] - xbar) * (row['target'] - ybar) for row in train) / sum(
                    (row[feature] - xbar) ** 2 for row in train)
        paired = [{'seed': seed, 'sample_id': row['id'], 'feature': feature, 'target': row['target'],
                   'baseline': ybar, 'prediction': ybar + slope * (row[feature] - xbar)} for row in test]
        baseline = statistics.mean((row['baseline'] - row['target']) ** 2 for row in paired)
        method = statistics.mean((row['prediction'] - row['target']) ** 2 for row in paired)
        metrics.append({'seed': seed, 'train_count': len(train), 'test_count': len(test),
                        'baseline_mse': baseline, 'method_mse': method, 'delta_mse': method - baseline})
        outputs.extend(paired)
    return {'feature': feature, 'seeds': metrics,
            'mean_delta_mse': statistics.mean(row['delta_mse'] for row in metrics)}, outputs


def run(output, scenario):
    output.mkdir(parents=True, exist_ok=False)
    first, predictions = evaluate('signal' if scenario == 'positive' else 'nuisance')
    studies = [first]
    original_supported = first['mean_delta_mse'] < -0.1
    if scenario == 'pivot' and not original_supported:
        second, more = evaluate('signal')
        studies.append(second)
        predictions.extend(more)
    decision = ('supported-in-synthetic-setting' if original_supported else
                'pivot-with-original-not-supported' if len(studies) > 1 else 'negative-in-synthetic-setting')
    summary = {'scenario': scenario, 'decision': decision, 'original_claim_supported': original_supported,
        'studies': studies, 'setting': 'synthetic-linear-regression', 'primary_metric': 'test MSE; lower is better',
        'minimum_practical_delta_predeclared': -0.1,
        'limitations': ['Three seed groups, one synthetic data generator.',
                       'Deterministic integration exercise; not autonomous LLM research or general causal evidence.'],
        'review_status': 'not-reviewed'}
    (output / 'results.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    with (output / 'predictions.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(predictions[0]))
        writer.writeheader()
        writer.writerows(predictions)
    # Stable outcome-independent sample, plus paired diagnostic extrema.
    representative = predictions[:3]
    changed = sorted(predictions, key=lambda row: (row['prediction'] - row['target']) ** 2
                      - (row['baseline'] - row['target']) ** 2)
    cases = {'selection': 'First three preordered samples, largest gain and largest regression in squared error.',
             'population': len(predictions), 'typical': representative,
             'largest_gain': changed[0], 'largest_regression': changed[-1]}
    (output / 'cases.json').write_text(json.dumps(cases, indent=2) + '\n', encoding='utf-8')
    (output / 'DECISIONS.md').write_text(
        '# Synthetic pilot decision\n\n' + decision + '\n\n'
        + 'Original claim supported in this test: ' + str(original_supported) + '.\n'
        + 'Sources: results.json, predictions.csv, cases.json.\n'
        + 'Revisit with another data generator and more independent seeds.\n'
        + 'A successful pivot does not retroactively support the original nuisance-feature claim.\n', encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scenario', choices=('positive', 'negative', 'pivot'), required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.scenario)))
