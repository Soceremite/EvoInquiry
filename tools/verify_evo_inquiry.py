#!/usr/bin/env python3
"""Check the EvoInquiry package and optional preservation of an ARIS baseline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

try:
    from tools.publication_policy import load_policy, publication_errors
    from tools.skill_contracts import HOOK, contract_errors, load_contract, normalize_namespace, skill_parts
except ModuleNotFoundError:
    from publication_policy import load_policy, publication_errors
    from skill_contracts import HOOK, contract_errors, load_contract, normalize_namespace, skill_parts

BLOCK = HOOK


def verify(root: Path, baseline: Path | None = None) -> dict:
    errors: list[str] = []
    errors.extend(publication_errors(root))
    errors.extend(contract_errors(root))
    skills_root = root / 'skills/skills-codex'
    skills = sorted(skills_root.glob('*/SKILL.md'))
    reference = skills_root / 'shared-references/evo-inquiry.md'
    if not reference.is_file():
        errors.append('Missing common principles reference')
    else:
        principles = reference.read_text()
        if len(re.findall(r'^## [1-6]\. ', principles, re.M)) != 6:
            errors.append('Expected six named principles')
    try:
        retained = set(load_contract(root)['retained_skills'])
    except (OSError, ValueError, TypeError):
        retained = set()
    for skill in skills:
        rel = skill.relative_to(root)
        body = skill.read_text()
        if len(BLOCK.findall(body)) != 1:
            errors.append(f'{rel}: expected one EvoInquiry entry block')
        target = skill.parent / '../shared-references/evo-inquiry.md'
        if ('[EvoInquiry](../shared-references/evo-inquiry.md)' not in body
                or not target.is_file() or target.resolve() != reference.resolve()):
            errors.append(f'{rel}: reference does not resolve to the common principles')
        if baseline is not None and skill.parent.name in retained:
            old = baseline / rel
            try:
                current_parts = skill_parts(body)[:2]
                current_parts = (current_parts[0], normalize_namespace(current_parts[1]))
                old_parts = skill_parts(old.read_text())[:2] if old.is_file() else None
                equal = old.is_file() and current_parts == old_parts
            except (ValueError, TypeError):
                equal = False
            if not equal:
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
        # Retire only individually audited public materials. All retained skill
        # contracts and runtime helpers still receive byte-for-byte checks.
        policy = load_policy(root)
        retired = set(policy['retired_upstream_files'])
        permitted = {
            '.codex-plugin/plugin.json', 'README.md', 'README_CN.md',
            'tests/test_plugin_manifest.py', 'tests/test_codex_skill_mirror.py',
            'tests/test_web_debug_search.py',
            'tests/test_claude_review_artifact_tools.py',
            'tests/test_evo_inquiry.py',
            'tools/check_skills_inventory.py',
            'tools/generate_codex_claude_review_overrides.py',
            '.gitignore', 'CONTRIBUTING.md', 'CONTRIBUTING_CN.md',
            '.github/workflows/test-suite.yml',
            '.github/workflows/check-skills-inventory.yml',
            'VERSION', 'AGENT_GUIDE.md', 'CHANGELOG.md', 'RELEASE_NOTES.md',
            'release-validation.json', 'docs/BETA_VALIDATION.md',
            'skills/skills-codex/shared-references/evo-inquiry.md',
            '.github/workflows/release-beta.yml',
            'tools/verify_evo_inquiry.py',
        } | set(policy['adapted_upstream_documents']) | {str(p.relative_to(root)) for p in skills}
        permitted |= set(load_contract(root).get('approved_upgrade_files', {}))
        for original in baseline.rglob('*'):
            rel = original.relative_to(baseline)
            if '.git' in rel.parts or '__pycache__' in rel.parts or '.pytest_cache' in rel.parts or original.suffix == '.pyc':
                continue
            if str(rel) in retired:
                if (root / rel).exists():
                    errors.append(f'{rel}: audited retirement was not applied')
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
        'frozen_contract_checked': True,
        'retained_skill_contracts': len(retained),
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
