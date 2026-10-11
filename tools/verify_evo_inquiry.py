#!/usr/bin/env python3
"""Check the EvoInquiry package and optional preservation of an ARIS baseline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

BLOCK = re.compile(r"\n<!-- EVO-INQUIRY:BEGIN -->\n.*?<!-- EVO-INQUIRY:END -->\n\n", re.S)


def verify(root: Path, baseline: Path | None = None) -> dict:
    errors: list[str] = []
    skills_root = root / 'skills/skills-codex'
    skills = sorted(skills_root.glob('*/SKILL.md'))
    reference = skills_root / 'shared-references/evo-inquiry.md'
    if not reference.is_file():
        errors.append('Missing common principles reference')
    else:
        principles = reference.read_text()
        if len(re.findall(r'^## [1-6]\. ', principles, re.M)) != 6:
            errors.append('Expected six named principles')
    upstream_skills = sorted((root / 'skills').glob('*/SKILL.md'))
    if {p.parent.name for p in skills} != {p.parent.name for p in upstream_skills}:
        errors.append('Codex skill inventory differs from retained upstream inventory')
    for skill in skills:
        rel = skill.relative_to(root)
        body = skill.read_text()
        if len(BLOCK.findall(body)) != 1:
            errors.append(f'{rel}: expected one compass entry block')
        target = skill.parent / '../shared-references/evo-inquiry.md'
        if not target.is_file() or target.resolve() != reference.resolve():
            errors.append(f'{rel}: reference does not resolve to the common principles')
        if baseline is not None:
            old = baseline / rel
            if not old.is_file() or BLOCK.sub('', body) != old.read_text():
                errors.append(f'{rel}: original skill body or frontmatter changed')
    manifest = json.loads((root / '.codex-plugin/plugin.json').read_text())
    if manifest.get('name') != 'evo-inquiry':
        errors.append('Wrong Codex plugin name')
    if manifest.get('interface', {}).get('displayName') != "EvoInquiry":
        errors.append('Wrong display name')
    if manifest.get('skills') != './skills/skills-codex/':
        errors.append('Wrong skill discovery directory')
    if 'version' in manifest:
        version_path = root / 'VERSION'
        if not version_path.is_file() or manifest['version'] != version_path.read_text().strip():
            errors.append('Plugin version differs from VERSION or VERSION is missing')
    if not (root / 'LICENSE').is_file():
        errors.append('Missing upstream license')
    for required in ['tools/check_skills_inventory.py', 'tools/run_state.py', 'tools/research_wiki.py']:
        if not (root / required).is_file():
            errors.append(f'Missing upstream helper {required}')
    if baseline is not None:
        # Only Codex entry blocks, presentation, and explicit test adaptations
        # may alter inherited files. Everything else is preserved byte-for-byte.
        permitted = {
            '.codex-plugin/plugin.json', 'README.md', 'README_CN.md',
            'tests/test_plugin_manifest.py', 'tests/test_codex_skill_mirror.py',
            'tests/test_web_debug_search.py',
            'tools/check_skills_inventory.py',
            'tools/generate_codex_claude_review_overrides.py',
            '.gitignore', 'CONTRIBUTING.md', 'CONTRIBUTING_CN.md',
            '.github/workflows/test-suite.yml',
        } | {str(p.relative_to(root)) for p in skills}
        for original in baseline.rglob('*'):
            rel = original.relative_to(baseline)
            if '.git' in rel.parts or '__pycache__' in rel.parts or '.pytest_cache' in rel.parts or original.suffix == '.pyc':
                continue
            if original.is_file() and str(rel) not in permitted:
                current = root / rel
                if not current.is_file() or current.read_bytes() != original.read_bytes():
                    errors.append(f'{rel}: unrelated upstream content changed')
    return {
        'package': str(root.resolve()),
        'skill_entrypoints': len(skills),
        'shared_reference_resolves': not any('reference' in e.lower() for e in errors),
        'baseline_compared': baseline is not None,
        'errors': errors,
        'status': 'PASS' if not errors else 'FAIL',
        'limitation': 'Packaging and preservation checks do not establish future model behavior.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = verify(args.package, args.baseline)
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered)
    sys.stdout.write(rendered)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
