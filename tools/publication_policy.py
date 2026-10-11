"""Validate the audited public package without weakening runtime preservation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


def load_policy(root: Path) -> dict:
    return json.loads((root / 'tools/publication-policy.json').read_text())


def publication_errors(root: Path, files: Iterable[str] | None = None) -> list[str]:
    policy = load_policy(root)
    retired = set(policy['retired_upstream_files'])
    present = set(files) if files is not None else {
        name for name in retired if (root / name).is_file()
    }
    errors = [f'Retired public material is present: {name}' for name in sorted(retired & present)]
    for name in policy['required_reference_files']:
        if not (root / name).is_file() or (files is not None and name not in present):
            errors.append(f'Missing required workflow document: {name}')
    return errors
