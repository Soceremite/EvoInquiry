#!/usr/bin/env python3
"""Field-level preservation checks against the committed beta.3 contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

SOURCE_COMMIT = "b9c7861fd22cd2f5471765d583c593f083fa12cc"
HOOK = re.compile(r"\n<!-- EVO-INQUIRY:BEGIN -->\n.*?<!-- EVO-INQUIRY:END -->\n\n", re.S)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


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
    if data.get("source_commit") != SOURCE_COMMIT or data.get("schema_version") != 1:
        raise ValueError("contract source or schema differs from the frozen beta.3 baseline")
    retained = data.get("retained_skills", {})
    if len(retained) != 83 or data.get("added_skills") != ["research-guide"]:
        raise ValueError("expected 83 retained skills and the registered research-guide extension")
    return data


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
    if mainline != retained:
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
            if digest(body.encode()) != frozen["body_without_hook_sha256"]:
                errors.append(f"{name}: protected workflow body changed")
    for rel, expected_hash in contract["protected_files"].items():
        path = root / rel
        if not path.is_file() or digest(path.read_bytes()) != expected_hash:
            errors.append(f"{rel}: protected baseline file changed or missing")
    return errors
