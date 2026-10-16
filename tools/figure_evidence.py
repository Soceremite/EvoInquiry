#!/usr/bin/env python3
"""Bind a figure, its editable source and caption to unchanged local inputs.

This receipt verifies file identity and optional literal number checks. It does
not judge scientific support, uncertainty calculations or visual readability.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .registry_common import configure_utf8_output, fixed_ref, verify_ref
    from .evidence_check import check_batch
except ImportError:
    from registry_common import configure_utf8_output, fixed_ref, verify_ref
    from evidence_check import check_batch

DATA_FIELDS = ('selection', 'aggregation', 'unit', 'uncertainty', 'axis', 'smoothing', 'missing')


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be nonempty')
    return value


def _paths(values, name):
    if not isinstance(values, list) or not values:
        raise ValueError(f'{name} must be a nonempty list')
    for value in values:
        _text(value, name)
    if len(set(values)) != len(values):
        raise ValueError(f'{name} contains duplicate paths')
    return values


def build_manifest(root, recipe):
    root = Path(root).resolve()
    if not isinstance(recipe, dict) or recipe.get('schema_version') != 1:
        raise ValueError('Expected figure recipe schema_version 1')
    if recipe.get('kind') not in ('data', 'structure', 'illustration'):
        raise ValueError('Unknown figure kind')
    transforms = recipe.get('transforms', {})
    if not isinstance(transforms, dict):
        raise ValueError('transforms must be an object')
    if recipe['kind'] == 'data':
        for field in DATA_FIELDS:
            _text(transforms.get(field), 'transforms.' + field)
    inputs = _paths(recipe.get('inputs'), 'inputs')
    outputs = _paths(recipe.get('outputs'), 'outputs')
    source = _text(recipe.get('source'), 'source')
    input_refs = [fixed_ref(root, path) for path in inputs]
    source_ref = fixed_ref(root, source)
    output_refs = [fixed_ref(root, path) for path in outputs]
    input_paths = {ref['path'] for ref in input_refs}
    output_paths = {ref['path'] for ref in output_refs}
    if len(input_paths) != len(input_refs) or len(output_paths) != len(output_refs):
        raise ValueError('Duplicate normalized file paths')
    if output_paths & (input_paths | {source_ref['path']}):
        raise ValueError('Output must not overwrite an input or editable source')
    claims = recipe.get('numeric_claims', [])
    if not isinstance(claims, list):
        raise ValueError('numeric_claims must be a list')
    for claim in claims:
        if not isinstance(claim, dict) or claim.get('source') not in inputs:
            raise ValueError('Numeric claim source must be an exact input path')
        _text(claim.get('value'), 'numeric claim value')
    checks = check_batch(claims, str(root)) if claims else None
    return {
        'schema_version': 1, 'kind': recipe['kind'],
        'caption': _text(recipe.get('caption'), 'caption'),
        'inputs': input_refs, 'source': source_ref, 'outputs': output_refs,
        'transforms': dict(transforms), 'numeric_checks': checks,
        'scope': 'File identity and literal number checks; scientific and visual review remain separate.',
    }


def check_manifest(root, record):
    if not isinstance(record, dict) or record.get('schema_version') != 1:
        raise ValueError('Expected figure manifest schema_version 1')
    if record.get('kind') not in ('data', 'structure', 'illustration'):
        raise ValueError('Unknown figure kind')
    _text(record.get('caption'), 'caption')
    if not isinstance(record.get('transforms'), dict):
        raise ValueError('transforms must be an object')
    if record['kind'] == 'data':
        for field in DATA_FIELDS:
            _text(record['transforms'].get(field), 'transforms.' + field)
    paths = {}
    for key in ('inputs', 'outputs'):
        if not isinstance(record.get(key), list) or not record[key]:
            raise ValueError(f'Missing {key} references')
        paths[key] = [verify_ref(Path(root), reference) for reference in record[key]]
        if len(set(paths[key])) != len(paths[key]):
            raise ValueError('Duplicate normalized file paths')
    source = verify_ref(Path(root), record.get('source'))
    if set(paths['outputs']) & (set(paths['inputs']) | {source}):
        raise ValueError('Output overlaps an input or editable source')
    return {'status': 'PASS', 'scope': 'Referenced file identity only'}


def main():
    configure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('create')
    create.add_argument('recipe', type=Path)
    create.add_argument('--root', type=Path, default=Path.cwd())
    create.add_argument('--output', type=Path, required=True)
    check = sub.add_parser('check')
    check.add_argument('manifest', type=Path)
    check.add_argument('--root', type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        if args.command == 'create':
            record = build_manifest(args.root, json.loads(args.recipe.read_text(encoding='utf-8')))
            rendered = json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
            with args.output.open('x', encoding='utf-8') as handle:
                handle.write(rendered)
            print(args.output)
        else:
            print(json.dumps(check_manifest(args.root, json.loads(args.manifest.read_text(encoding='utf-8')))))
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(2, f'Figure evidence error: {error}\n')


if __name__ == '__main__':
    main()
