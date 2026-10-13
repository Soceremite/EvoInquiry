"""Python symbol navigation and source/doc freshness checks, without executing code.

Static callers are hints: reflection, configuration entrypoints and dynamic
registrations need explicit annotations. Freshness is not semantic correctness.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import subprocess
import sys
import tokenize

try:
    from .registry_common import RegistryError, atomic_write, digest, file_digest, local_path, now, read_record
except ImportError:
    from registry_common import RegistryError, atomic_write, digest, file_digest, local_path, now, read_record


def _symbols(root, relative):
    path = local_path(root, relative)
    with tokenize.open(path) as source:
        tree = ast.parse(source.read(), filename=str(relative))
    parts = list(Path(relative).with_suffix('').parts)
    if 'src' in parts:
        parts = parts[parts.index('src') + 1:]
    module = '.'.join(parts)
    if module.endswith('.__init__'):
        module = module[:-9]
    result = []

    def visit(nodes, parent=''):
        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            name = parent + node.name
            documentation = ast.get_docstring(node) or ''
            signature = ast.dump(node.args, include_attributes=False) if hasattr(node, 'args') else 'class'
            if getattr(node, 'returns', None):
                signature += '->' + ast.dump(node.returns, include_attributes=False)
            body = ast.Module(body=node.body, type_ignores=[])
            if documentation:
                body.body = node.body[1:]
            result.append({'qualified_symbol': module + '.' + name, 'path': Path(relative).as_posix(),
                           'purpose': documentation.split('\n')[0], 'signature': signature,
                           'public': not any(part.startswith('_') for part in name.split('.')),
                           'source_hash': file_digest(path), 'symbol_hash': digest(ast.dump(body, include_attributes=False)),
                           'documentation_hash': digest(documentation.encode()),
                           'calls': sorted({ast.unparse(call.func) for call in ast.walk(node) if isinstance(call, ast.Call)})})
            if isinstance(node, ast.ClassDef):
                visit(node.body, name + '.')

    visit(tree.body)
    return result


def build_map(root, paths=None, annotations=None):
    """Build a symbol map with explicit reuse examples, tests and dynamic caller hints."""
    root = Path(root).resolve()
    if paths is None:
        paths = [p.relative_to(root).as_posix() for prefix in ('src', 'families')
                 for p in (root / prefix).rglob('*.py') if not p.is_symlink()]
    rows = [row for path in sorted(paths) for row in _symbols(root, path)]
    names = [row['qualified_symbol'] for row in rows]
    if len(set(names)) != len(names):
        raise RegistryError('Duplicate module/symbol identity; supply separate family maps')
    annotations = annotations or {}
    try:
        commit = subprocess.check_output(['git', '--git-dir=' + str(root / '.git'),
                                          '--work-tree=' + str(root), 'rev-parse', 'HEAD'],
                                         stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    for row in rows:
        annotation = annotations.get(row['qualified_symbol'], {})
        row.update(reuse_example=annotation.get('reuse_example', ''),
                   callers=sorted(set(annotation.get('callers', [])) | {
                       candidate['qualified_symbol'] for candidate in rows
                       if row['qualified_symbol'] in candidate['calls']}),
                   tests=annotation.get('tests', []), dynamic_callers=annotation.get('dynamic_callers', []),
                   source_commit=commit, verified_at=now())
        for test in row['tests']:
            local_path(root, test.split('::')[0])
    return {'schema_version': 1, 'symbols': rows, 'limitations':
            ['Static calls do not cover dynamic dispatch or configuration.',
             'Code/doc hashes detect drift; contract tests and review establish semantics.']}


def check_freshness(root, mapping):
    """Flag code/signature/doc drift and missing public docs or consumer test entrypoints."""
    issues = []
    cache = {}
    for row in mapping['symbols']:
        path = row['path']
        try:
            if path not in cache:
                cache[path] = {item['qualified_symbol']: item for item in _symbols(root, path)}
            current = cache[path].get(row['qualified_symbol'])
            if not current:
                issues.append({'symbol': row['qualified_symbol'], 'reason': 'symbol-missing'})
                continue
            if current['source_hash'] != row['source_hash']:
                issues.append({'symbol': row['qualified_symbol'], 'reason': 'source-stale'})
            if current['signature'] != row['signature']:
                issues.append({'symbol': row['qualified_symbol'], 'reason': 'public-interface-changed'})
            if (current['symbol_hash'] != row['symbol_hash']
                    and current['documentation_hash'] == row['documentation_hash'] and row['public']):
                issues.append({'symbol': row['qualified_symbol'], 'reason': 'documentation-review-needed'})
            if current['public'] and (not current['purpose'] or not row.get('reuse_example') or not row.get('tests')):
                issues.append({'symbol': row['qualified_symbol'], 'reason': 'public-contract-incomplete'})
            for test in row.get('tests', []):
                if not local_path(root, test.split('::')[0]).is_file():
                    issues.append({'symbol': row['qualified_symbol'], 'reason': 'consumer-test-missing'})
        except (OSError, SyntaxError, RegistryError) as error:
            issues.append({'symbol': row['qualified_symbol'], 'reason': str(error)})
    return {'status': 'STALE' if issues else 'PASS', 'issues': issues}


def resolve_symbol(mapping, qualified_symbol):
    """Return one exact symbol; callers should read its real implementation and tests."""
    matches = [row for row in mapping['symbols'] if row['qualified_symbol'] == qualified_symbol]
    if len(matches) != 1:
        raise RegistryError('Symbol is missing or ambiguous: ' + qualified_symbol)
    return matches[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    sub = parser.add_subparsers(dest='command', required=True)
    build = sub.add_parser('build')
    build.add_argument('--paths', nargs='*')
    build.add_argument('--annotations')
    build.add_argument('--output', default='docs/code-map.yaml')
    check = sub.add_parser('check')
    check.add_argument('--map', default='docs/code-map.yaml')
    resolve = sub.add_parser('resolve')
    resolve.add_argument('symbol')
    resolve.add_argument('--map', default='docs/code-map.yaml')
    args = parser.parse_args()
    try:
        if args.command == 'build':
            result = build_map(args.root, args.paths, read_record(args.annotations) if args.annotations else None)
            atomic_write(local_path(args.root, args.output), result)
        else:
            mapping = read_record(local_path(args.root, args.map))
            result = check_freshness(args.root, mapping) if args.command == 'check' else resolve_symbol(mapping, args.symbol)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get('status') != 'STALE' else 2
    except (RegistryError, OSError, SyntaxError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
