#!/usr/bin/env python3
"""Preservation checks with explicit, digest-pinned governance upgrade adaptations."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

SOURCE_COMMIT = "b9c7861fd22cd2f5471765d583c593f083fa12cc"
UPGRADE_SOURCE_COMMIT = '69cfbc5dc5fc34c4d7e6146fe66f5520866f7dfe'
FROZEN_RETAINED_SHA256 = '547ce394cd26d88642e890edffa7fb9ed941d14e21902859441da3a2439e5271'
FROZEN_PROTECTED_SHA256 = 'a1a2d20192f2dd5fab167c07f435d42a96a2d4308c0d0cbbf3954dae66dbf1b3'
HOOK = re.compile(r"\n<!-- EVO-INQUIRY:BEGIN -->\n.*?<!-- EVO-INQUIRY:END -->\n\n", re.S)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
GOVERNANCE_HOOK = re.compile(r'\n<!-- EI-GOVERNANCE:BEGIN -->\n.*?<!-- EI-GOVERNANCE:END -->\n\n', re.S)


def normalize_namespace(text: str) -> str:
    """Reverse only namespace tokens, not scientific symbols such as torch.einsum."""
    text = GOVERNANCE_HOOK.sub('', text)
    text = text.replace('.ei/queue', '.aris_queue')
    return re.sub(r'\.ei(?=[/\\\s"\x27`._-]|$)', '.aris', text)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def skill_parts(text: str) -> tuple[str, str, str]:
    """Separate one scalar description without ignoring any other YAML fields.

    Retained frontmatter uses single-line scalar descriptions. Reject multiline
    values rather than accidentally allowing a description edit to absorb tools
    or metadata. All other frontmatter bytes and body bytes stay significant.
    """
    match = FRONTMATTER.match(text)
    if not match:
        raise ValueError("missing leading YAML frontmatter")
    lines = match[1].splitlines(keepends=True)
    indices = [i for i, line in enumerate(lines) if line.startswith("description:")]
    if len(indices) != 1:
        raise ValueError("expected one single-line description")
    i = indices[0]
    value = lines[i].partition(":")[2].strip()
    if not value or value.startswith(("|", ">")) or (i + 1 < len(lines) and lines[i + 1][:1].isspace()):
        raise ValueError("description must be a nonempty single-line scalar")
    # New descriptions are JSON-quoted, a subset of YAML. Older unquoted or
    # single-quoted scalars remain valid when comparing a frozen source.
    if value.startswith('"'):
        description = json.loads(value)
        if not isinstance(description, str) or not description.strip():
            raise ValueError("description must be a nonempty string")
    else:
        description = value.strip("'")
    stable_frontmatter = "".join(lines[:i] + lines[i + 1:]).rstrip("\n")
    return stable_frontmatter, HOOK.sub("", text[match.end():]), description


def load_contract(root: Path) -> dict:
    data = json.loads((root / "tools/skill-contracts.json").read_text(encoding="utf-8"))
    version = data.get('schema_version')
    if data.get("source_commit") != SOURCE_COMMIT or version not in (2, 3):
        raise ValueError("contract source or schema differs from the frozen beta.3 baseline")
    retained = data.get("retained_skills", {})
    for records, expected in ((retained, FROZEN_RETAINED_SHA256),
                              (data.get('protected_files'), FROZEN_PROTECTED_SHA256)):
        if digest(json.dumps(records, sort_keys=True, separators=(',', ':')).encode()) != expected:
            raise ValueError('Frozen original digests changed; adaptations must not replace the baseline')
    additions = ['research-guide', 'project-governance', 'environment-maintenance']
    mainline_additions = ['project-governance', 'environment-maintenance']
    if version == 3:
        additions += ['scientific-brainstorming', 'research-manager']
        mainline_additions += ['scientific-brainstorming', 'research-manager']
    if (len(retained) != 83 or data.get('added_skills') != additions
            or data.get('mainline_added_skills') != mainline_additions
            or data.get('upgrade_source_commit') != UPGRADE_SOURCE_COMMIT):
        raise ValueError('expected the frozen 83 retained skills and registered extensions')
    adaptations = data.get('workflow_adaptations', {})
    if not isinstance(adaptations, dict) or set(adaptations) - set(retained):
        raise ValueError('workflow adaptation refers to an unretained skill')
    for name, record in adaptations.items():
        if version != 3 or not isinstance(record, dict):
            raise ValueError(f'{name}: invalid workflow adaptation')
        if record.get('baseline_body_sha256') != retained[name]['body_without_hook_sha256']:
            raise ValueError(f'{name}: adaptation baseline differs from the frozen body')
        candidate_hash, reason = record.get('body_sha256'), record.get('reason')
        if (not isinstance(candidate_hash, str) or not re.fullmatch(r'[a-f0-9]{64}', candidate_hash)
                or not isinstance(reason, str) or not reason.strip()):
            raise ValueError(f'{name}: adaptation needs an exact digest and reason')
        tests = record.get('test_refs')
        if not isinstance(tests, list) or not tests:
            raise ValueError(f'{name}: adaptation needs test references')
        references = [record.get('review_ref', '')] + tests
        if not all(_local_reference(root, ref) for ref in references):
            raise ValueError(f'{name}: adaptation review/test references missing or outside package')
    for relative, record in data.get('approved_upgrade_files', {}).items():
        if not isinstance(record, dict) or relative not in data['protected_files']:
            raise ValueError(f'{relative}: invalid protected-file adaptation')
        if record.get('baseline_sha256') != data['protected_files'][relative]:
            raise ValueError(f'{relative}: protected-file baseline mismatch')
        if record.get('adaptation_version') in ('1.4.0', '1.5.0'):
            refs = record.get('test_refs')
            if (not isinstance(refs, list) or not refs
                    or not all(_local_reference(root, ref) for ref in [record.get('review_ref')] + refs)):
                raise ValueError(f'{relative}: protected-file review/test references missing')
    return data


def _local_reference(root: Path, reference: str) -> bool:
    if not isinstance(reference, str) or not reference:
        return False
    relative = Path(reference.split('#', 1)[0])
    target = (root / relative).resolve()
    return not relative.is_absolute() and target.is_relative_to(root.resolve()) and target.is_file()


def contract_errors(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        contract = load_contract(root)
    except (OSError, ValueError, TypeError) as exc:
        return [f"Skill contract unavailable: {exc}"]
    base = root / "skills/skills-codex"
    retained = set(contract["retained_skills"])
    expected = retained | set(contract["added_skills"])
    actual = {p.parent.name for p in base.glob("*/SKILL.md")}
    for name in sorted(expected - actual):
        errors.append(f"Missing registered Codex skill: {name}")
    for name in sorted(actual - expected):
        errors.append(f"Unregistered Codex skill: {name}")
    mainline = {p.parent.name for p in (root / "skills").glob("*/SKILL.md")}
    if mainline != retained | set(contract['mainline_added_skills']):
        errors.append("Retained upstream inventory differs from frozen skill contract")
    for name in sorted(actual & expected):
        path = base / name / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        try:
            frontmatter, body, _ = skill_parts(text)
        except (ValueError, TypeError) as exc:
            errors.append(f"{name}: invalid frontmatter: {exc}")
            continue
        name_match = re.search(r'^name:\s*[\"\']?([a-z0-9-]+)[\"\']?\s*$', frontmatter, re.M)
        if not name_match or name_match[1] != name:
            errors.append(f"{name}: frontmatter name differs from skill directory")
        if name in retained:
            frozen = contract["retained_skills"][name]
            if digest(frontmatter.encode()) != frozen["frontmatter_except_description_sha256"]:
                errors.append(f"{name}: protected frontmatter changed")
            normalized = normalize_namespace(body)
            adapted = contract.get('workflow_adaptations', {}).get(name, {})
            expected_body = adapted.get('body_sha256', frozen['body_without_hook_sha256'])
            if digest(normalized.encode()) != expected_body:
                errors.append(f"{name}: protected workflow body changed")
    for rel, expected_hash in contract["protected_files"].items():
        path = root / rel
        adaptation = contract.get('approved_upgrade_files', {}).get(rel)
        if adaptation:
            expected_hash = adaptation['sha256']
        valid = path.is_file() and digest(path.read_bytes()) == expected_hash
        if not valid and path.is_file() and not adaptation:
            try:
                valid = digest(normalize_namespace(path.read_text()).encode()) == expected_hash
            except UnicodeError:
                pass
        if not valid:
            errors.append(f"{rel}: protected baseline file changed or missing")
    return errors
