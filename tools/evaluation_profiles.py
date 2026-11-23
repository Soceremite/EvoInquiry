"""Validate interchangeable batch sizes and device counts on a fixed evaluation cohort."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

if __package__:
    from .registry_common import RegistryError, atomic_write, configure_utf8_output, identifier, local_path, read_record, verify_ref
else:
    from registry_common import RegistryError, atomic_write, configure_utf8_output, identifier, local_path, read_record, verify_ref


def _number(value, label, *, positive=False):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise RegistryError(f'Invalid {label}')
    return value


def _values_match(left, right, tolerance):
    """Compare JSON predictions by label or by declared numeric tolerance."""
    if type(left) in (float, int) and type(right) in (float, int):
        return math.isfinite(left) and math.isfinite(right) and math.isclose(left, right, rel_tol=0, abs_tol=tolerance)
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(_values_match(a, b, tolerance) for a, b in zip(left, right))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_values_match(left[k], right[k], tolerance) for k in left)
    return left == right


def _collect(root, profile, expected, metrics):
    """Join disjoint shard outputs by sample ID and reduce original contributions."""
    rows = {}
    refs = profile['shards']
    if not isinstance(refs, list) or not refs:
        raise RegistryError('Every profile requires at least one output shard')
    for ref in refs:
        shard = read_record(verify_ref(root, ref))
        for row in shard['samples']:
            sample_id = row['id']
            if sample_id not in expected or sample_id in rows:
                raise RegistryError(f'Unexpected or repeated sample ID: {sample_id}')
            if row['metrics'].keys() != metrics.keys() or any(
                    type(value) not in (int, float) or not math.isfinite(value)
                    for value in row['metrics'].values()):
                raise RegistryError(f'Invalid metric contributions for sample {sample_id}')
            if not _values_match(row['prediction'], row['prediction'], 0):
                raise RegistryError(f'Nonfinite prediction for sample {sample_id}')
            rows[sample_id] = row
    missing = expected - rows.keys()
    if missing:
        raise RegistryError(f'Shards omit {len(missing)} expected samples')
    aggregates = {}
    for name, rule in metrics.items():
        values = [rows[sample_id]['metrics'][name] for sample_id in sorted(expected)]
        reducer = rule['reducer']
        if reducer == 'max':
            aggregates[name] = max(values)
        else:
            total = math.fsum(values)
            aggregates[name] = total / len(values) if reducer == 'mean' else total
    return rows, aggregates


def _cohort(root, reference):
    ids = read_record(verify_ref(root, reference))['sample_ids']
    if (not isinstance(ids, list) or not ids or any(not isinstance(value, str) or not value for value in ids)
            or len(ids) != len(set(ids))):
        raise RegistryError('Declare unique, nonempty evaluation sample IDs')
    return set(ids)


def _metric_rules(metrics):
    if not isinstance(metrics, dict) or not metrics:
        raise RegistryError('Declare metric reducers and tolerances')
    for rule in metrics.values():
        if rule['reducer'] not in ('mean', 'sum', 'max'):
            raise RegistryError('Use a mean, sum or max reducer over per-sample contributions')
        _number(rule.get('atol', 0), 'metric atol')


def collect_results(root, request):
    """Combine full evaluation shards using the applicable frozen cohort and metric definitions."""
    expected = _cohort(root, request['sample_ids_ref'])
    metrics = request['metrics']
    _metric_rules(metrics)
    _, aggregate = _collect(root, request, expected, metrics)
    return {'schema_version': 1, 'status': 'COMPLETE', 'sample_count': len(expected),
            'sample_ids_ref': request['sample_ids_ref'], 'shards': request['shards'],
            'metric_rules': metrics, 'metrics': aggregate}


def validate(root, request):
    """Return a placement receipt only for profiles that preserve the fixed result."""
    spec = read_record(verify_ref(root, request['spec_ref']))
    verify_ref(root, request['env_revision'])
    for key in ('data_ref', 'split_ref', 'evaluator_ref', 'protocol_ref'):
        verify_ref(root, spec[key])
    if (request['variant_id'] not in {row['variant_id'] for row in spec['variants']}
            or request['seed'] not in spec['seeds']):
        raise RegistryError('Profile validation differs from the declared variant and seed')
    for ref in request.get('input_refs', []):
        verify_ref(root, ref)
    expected = _cohort(root, request['sample_ids_ref'])
    metrics = request['metrics']
    tolerance = _number(request.get('prediction_atol', 0), 'prediction_atol')
    _metric_rules(metrics)
    results, names, baseline = [], set(), None
    host, precision = request['host'], request['precision']
    if any(not isinstance(value, str) or not value for value in (host, precision)):
        raise RegistryError('Declare the evaluation host and common precision')
    for profile in (request['baseline'], *request['alternatives']):
        name = identifier(profile['id'])
        uuids = profile['gpu_uuids']
        batch_size = profile['batch_size']
        if (name in names or type(batch_size) is not int or batch_size < 1 or not isinstance(uuids, list)
                or any(not isinstance(uuid, str) or not uuid.startswith('GPU-') for uuid in uuids)
                or len(uuids) != len(set(uuids))):
            raise RegistryError(f'Invalid or repeated configuration for {name}')
        if profile.get('precision', precision) != precision:
            raise RegistryError('Compare profiles at the same precision')
        measurement = read_record(verify_ref(root, profile['measurement_ref']))
        controls = {'host': host, 'precision': precision, 'batch_size': batch_size, 'gpu_uuids': uuids,
                    'shards': profile['shards'], 'isolated': True}
        if any(measurement.get(key) != value for key, value in controls.items()):
            raise RegistryError(f'Measurement for {name} differs from the declared inputs or isolation')
        names.add(name)
        peak = _number(measurement['peak_bytes_per_gpu'], 'per-GPU peak', positive=bool(uuids))
        if not uuids and peak:
            raise RegistryError('CPU profiles have zero GPU memory peak')
        elapsed = _number(measurement['elapsed_seconds'], 'elapsed seconds', positive=True)
        rows, aggregate = _collect(root, profile, expected, metrics)
        if baseline is None:
            baseline, baseline_metrics = rows, aggregate
        else:
            for sample_id, reference in baseline.items():
                candidate = rows[sample_id]
                if not _values_match(reference['prediction'], candidate['prediction'], tolerance):
                    raise RegistryError(f'Profile {name} differs on sample {sample_id}')
                for metric, rule in metrics.items():
                    if not _values_match(reference['metrics'][metric], candidate['metrics'][metric], rule.get('atol', 0)):
                        raise RegistryError(f'Profile {name} differs on {metric} for sample {sample_id}')
            for metric, total in baseline_metrics.items():
                if not _values_match(total, aggregate[metric], metrics[metric].get('atol', 0)):
                    raise RegistryError(f'Profile {name} differs on aggregate {metric}')
        results.append({'id': name, 'batch_size': batch_size, 'gpu_uuids': uuids,
                        'precision': precision, 'peak_bytes_per_gpu': peak, 'elapsed_seconds': elapsed,
                        'samples_per_second': len(expected) / elapsed,
                        'gpu_seconds': len(uuids) * elapsed, 'metrics': aggregate,
                        'shards': profile['shards'], 'measurement_ref': profile['measurement_ref']})
    return {'schema_version': 1, 'status': 'EQUIVALENT', 'host': host, 'precision': precision,
            'spec_ref': request['spec_ref'], 'env_revision': request['env_revision'],
            'variant_id': request['variant_id'], 'seed': request['seed'],
            'input_refs': request.get('input_refs', []), 'sample_ids_ref': request['sample_ids_ref'],
            'sample_count': len(expected), 'profiles': results, 'prediction_atol': tolerance, 'metrics': metrics}


def read_profiles(root, reference, *, execution=None, revalidate=False):
    """Resolve reserved profiles and, for real dispatch, verify the execution identity."""
    receipt = read_record(verify_ref(root, reference))
    if receipt.get('schema_version') != 1 or receipt.get('status') != 'EQUIVALENT' or not receipt.get('profiles'):
        raise RegistryError('Use a verified evaluation profile receipt')
    if execution is not None:
        for key in ('spec_ref', 'env_revision', 'variant_id', 'seed'):
            if receipt[key] != execution[key]:
                raise RegistryError(f'Evaluation profile receipt differs from the frozen {key}')
        if receipt['input_refs'] != execution.get('evaluation_input_refs', []):
            raise RegistryError('Evaluation profile receipt differs from frozen model or input artifacts')
        for ref in (receipt['sample_ids_ref'], *receipt['input_refs']):
            verify_ref(root, ref)
    if revalidate:
        baseline, *alternatives = receipt['profiles']
        if validate(root, dict(receipt, baseline=baseline, alternatives=alternatives)) != receipt:
            raise RegistryError('Evaluation profile receipt does not reproduce from its evidence')
    return receipt


def main():
    configure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--request', type=Path, help='Validate interchangeable execution profiles')
    source.add_argument('--collect', type=Path, help='Verify full sample coverage and reduce evaluation shards')
    parser.add_argument('--output', type=Path, help='Project-relative receipt path')
    args = parser.parse_args()
    try:
        root = Path(args.root).resolve()
        receipt = (validate(root, read_record(args.request)) if args.request
                   else collect_results(root, read_record(args.collect)))
        if args.output is not None:
            atomic_write(local_path(root, args.output), receipt)
        print(json.dumps(receipt, indent=2, ensure_ascii=False))
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(2, f'ERROR: {error}\n')


if __name__ == '__main__':
    main()
