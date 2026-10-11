"""Portable packaging checks for the personal Codex edition."""
from pathlib import Path
import shutil

from tools.verify_evo_inquiry import verify
from tools import check_skills_inventory as inventory

ROOT = Path(__file__).resolve().parents[1]


def test_package_preserves_skill_inventory_and_resolves_shared_reference():
    report = verify(ROOT)
    assert report['status'] == 'PASS', report['errors']
    assert report['skill_entrypoints'] == 83


def test_missing_principles_are_detected(tmp_path):
    # A real broken link must make package verification fail.
    package = tmp_path / 'package'
    shutil.copytree(ROOT / 'skills', package / 'skills')
    shutil.copytree(ROOT / '.codex-plugin', package / '.codex-plugin')
    shutil.copytree(ROOT / 'tools', package / 'tools')
    shutil.copyfile(ROOT / 'LICENSE', package / 'LICENSE')
    (package / 'skills/skills-codex/shared-references/evo-inquiry.md').unlink()
    report = verify(package)
    assert report['status'] == 'FAIL'
    assert not report['shared_reference_resolves']


def test_inventory_still_rejects_unrelated_codex_only_references(tmp_path, monkeypatch):
    mirror = tmp_path / 'skills-codex'
    shutil.copytree(ROOT / 'skills/skills-codex', mirror)
    (mirror / 'shared-references/unregistered.md').write_text('An unexpected document.\n')
    monkeypatch.setattr(inventory, 'CODEX_ROOT', mirror)
    failures = inventory.check_inventory()
    assert any('unexpected Codex-only shared references: unregistered.md' in f for f in failures)
