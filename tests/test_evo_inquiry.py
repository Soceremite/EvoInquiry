"""Portable packaging and publication checks for EvoInquiry."""
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
    for rel in inventory_publication_references():
        target = package / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)
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


def inventory_publication_references():
    from tools.publication_policy import load_policy
    return load_policy(ROOT)['required_reference_files']


def test_publication_rejects_retired_promotional_material(tmp_path):
    from tools.publication_policy import publication_errors
    shutil.copytree(ROOT / 'tools', tmp_path / 'tools')
    (tmp_path / 'xhs_post.md').write_text('An accidentally restored promotional draft.\n')
    assert any('xhs_post.md' in error for error in publication_errors(tmp_path))


def test_publication_requires_the_style_example_used_by_interview_cheatsheet(tmp_path):
    from tools.publication_policy import publication_errors
    shutil.copytree(ROOT / 'tools', tmp_path / 'tools')
    for rel in inventory_publication_references():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)
    # A present but untracked exemplar would also be missing from a release.
    tracked = set(inventory_publication_references()) - {'docs/tutorials/attention_tutorial.md'}
    assert publication_errors(tmp_path, tracked) == [
        'Missing required workflow document: docs/tutorials/attention_tutorial.md'
    ]
    (tmp_path / 'docs/tutorials/attention_tutorial.md').unlink()
    errors = publication_errors(tmp_path)
    assert errors == ['Missing required workflow document: docs/tutorials/attention_tutorial.md']
