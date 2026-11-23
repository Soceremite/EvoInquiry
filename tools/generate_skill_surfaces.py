#!/usr/bin/env python3
"""Render the checked-in skill trees from the maintainable sources and host diffs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys

if __package__:
    from .generate_codex_claude_review_overrides import render_text, transform_body
    from .registry_common import atomic_write
else:
    from generate_codex_claude_review_overrides import render_text, transform_body
    from registry_common import atomic_write


ROOT = Path(__file__).resolve().parents[1]
DESTINATIONS = {'codex': 'skills/skills-codex', 'claude': 'skills/skills-codex-claude-review',
                'gemini': 'skills/skills-codex-gemini-review'}
SURFACES = tuple(DESTINATIONS)
FRONT = re.compile(rb'\A---\n(.*?)\n---\n', re.S)


def _files(directory):
    """Return portable relative files, excluding Python build caches."""
    return {path.relative_to(directory).as_posix(): path.read_bytes()
            for path in sorted(directory.rglob('*')) if path.is_file()
            and '__pycache__' not in path.parts and path.suffix not in ('.pyc', '.pyo')}


def _strip_fields(entry, fields):
    match = FRONT.match(entry)
    if match is None:
        raise ValueError('A skill source must have frontmatter')
    keys = {field.encode()+b':' for field in fields}
    header = b'\n'.join(line for line in match[1].splitlines() if not any(line.startswith(key) for key in keys))
    return b'---\n'+header+b'\n---\n'+entry[match.end():]


def _declared(entry):
    match = FRONT.match(entry)
    if match is None:
        raise ValueError('A skill source must have frontmatter')
    field = re.search(rb'^surfaces: \[([^\n]+)\]$', match[1], re.M)
    return {item.strip().decode() for item in field[1].split(b',')} if field else {'mainline', 'codex'}


def _sources(root):
    """Read the canonical directories and project Codex-only source entrypoints."""
    skills = root/'skills'
    output = {'shared-references/'+path:data for path,data in _files(skills/'shared-references').items()}
    for folder in sorted(skills.iterdir()):
        if not folder.is_dir() or folder.name.startswith('skills-codex'):
            continue
        source = folder/'SKILL.md'
        if not source.is_file():
            source = folder/'SKILL.source.md'
        if not source.is_file():
            continue
        if 'codex' not in _declared(source.read_bytes().replace(b'\r\n', b'\n')):
            continue
        for relative,data in _files(folder).items():
            target = 'SKILL.md' if relative == 'SKILL.source.md' else relative
            if target == 'SKILL.md':
                # Keep generated entrypoints stable across editor line endings.
                data = _strip_fields(data.replace(b'\r\n', b'\n'), ['surfaces'])
            output[folder.name+'/'+target] = data
    return output


def _surface_base(root, name, codex, rules):
    config = rules[name]
    if name == 'codex':
        output = _sources(root)
        for path in output:
            if path.endswith('/SKILL.md'):
                output[path] = _strip_fields(output[path], config['remove_frontmatter'])
        return {path:data for path,data in output.items() if path not in config['omit']}
    if name == 'claude':
        output = {}
        for path,data in codex.items():
            owner, _, rest = path.partition('/')
            if owner not in config['skills']:
                continue
            if rest == 'SKILL.md':
                output[path] = render_text(owner, data.decode('utf-8')).encode('utf-8')
            elif rest.startswith('references/'):
                output[path] = transform_body(data.decode('utf-8')).encode('utf-8') if path.endswith('.md') else data
        return {path:data for path,data in output.items() if path not in config['omit']}
    return {path:codex[source] for path,source in config['from_codex'].items() if source in codex}


def _apply_hunks(data, hunks, label):
    """Apply line hunks at their original context or its unique moved location."""
    lines = data.decode('utf-8').splitlines(keepends=True)
    result, cursor = [], 0
    for offset, before, after in hunks:
        width = len(before)
        if offset >= cursor and lines[offset:offset+width] == before and (width or not lines):
            position = offset
        else:
            found = [i for i in range(cursor,len(lines)-width+1) if lines[i:i+width] == before]
            if len(found) != 1:
                raise ValueError(f'{label}: source changed in a host-specific section. Reconcile the host diff.')
            position = found[0]
        result.extend(lines[cursor:position])
        result.extend(after)
        cursor = position+width
    return ''.join(result+lines[cursor:]).encode('utf-8')


def projection(root, name, *, rules=None, codex=None, mark=True):
    """Return expected relative filenames and bytes for one installed surface."""
    root = Path(root)
    rules = rules or json.loads((root/'tools/surface_rules.json').read_text(encoding='utf-8'))['surfaces']
    if name != 'codex' and codex is None:
        codex = projection(root, 'codex', rules=rules, mark=False)
    base = _surface_base(root,name,codex or {},rules)
    variants = root/'tools/skill-surfaces'/name
    overrides = json.loads((variants/'patches.json').read_text(encoding='utf-8'))
    for path,hunks in overrides.items():
        if path not in base:
            raise ValueError(f'{name}/{path}: missing source for host diff')
        base[path] = _apply_hunks(base[path],hunks,f'{name}/{path}')
    for path,data in _files(variants/'extras').items():
        if path in base:
            raise ValueError(f'{name}/{path}: both a source and a host-only file exist')
        base[path] = data
    if mark:
        for path,data in base.items():
            if path.endswith('/SKILL.md'):
                owner = path.split('/')[0]
                source = f'skills/{path}'
                if (root/'skills'/owner/'SKILL.source.md').is_file():
                    source = f'skills/{owner}/SKILL.source.md'
                stamp = f'<!-- GENERATED from {source} — do not edit directly -->\n'.encode()
                header = FRONT.match(data)
                if header is None:
                    raise ValueError(f'{name}/{path}: missing generated frontmatter')
                position = header.end()
                base[path] = data[:position]+stamp+data[position:]
    return base


def rendered_skills(root, name):
    """Return installed entrypoint names for an actual declaration projection."""
    return {path.split('/')[0] for path in projection(root,name) if path.endswith('/SKILL.md')}


def surface_changes(directory, expected, skill=None):
    """Compare a generated surface to disk, optionally limiting it to one skill."""
    actual = _files(directory)
    for path in sorted(expected.keys() | actual.keys()):
        if skill and path.partition('/')[0] != skill:
            continue
        if expected.get(path) == actual.get(path):
            continue
        relative = PurePosixPath(path)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError(f'Invalid generated path {path}')
        yield directory / relative, expected.get(path)


def write_changes(changes):
    for path, content in changes:
        if content is None:
            path.unlink()
        else:
            permissions = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
            atomic_write(path, content)
            path.chmod(permissions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--surface',choices=('all',*SURFACES),default='all')
    parser.add_argument('--skill')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check',action='store_true')
    mode.add_argument('--dry-run',action='store_true')
    args = parser.parse_args()
    try:
        root=args.root.resolve()
        rules=json.loads((root/'tools/surface_rules.json').read_text(encoding='utf-8'))['surfaces']
        names=SURFACES if args.surface=='all' else (args.surface,)
        codex=projection(root,'codex',rules=rules,mark=False)
        changes=[]
        for name in names:
            expected=projection(root,name,rules=rules,codex=codex)
            if rules[name]['destination'] != DESTINATIONS[name]:
                raise ValueError(f'{name}: generated files must stay in {DESTINATIONS[name]}')
            changes.extend(surface_changes(root / DESTINATIONS[name], expected, args.skill))
        if not (args.check or args.dry_run):
            write_changes(changes)
        if changes and (args.check or args.dry_run):
            for path,_ in changes:
                print(path.relative_to(root))
        print(f'{len(changes)} differing files across {", ".join(names)}')
        return int(bool(changes) and args.check)
    except (OSError,ValueError,KeyError) as error:
        print(error,file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
