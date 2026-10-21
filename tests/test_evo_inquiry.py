"""Portable packaging and publication checks for EvoInquiry."""
from pathlib import Path
import shutil

import pytest

from tools.verify_evo_inquiry import (
    REQUIRED_COMPARISON_RESOURCES, REQUIRED_RESEARCH_RESOURCES,
    REQUIRED_REFLECTION_RESOURCES, verify,
)
from tools import check_skills_inventory as inventory
from tools.skill_contracts import contract_errors, load_contract, normalize_namespace

ROOT = Path(__file__).resolve().parents[1]


def test_package_preserves_skill_inventory_and_resolves_shared_reference():
    report = verify(ROOT)
    assert report['status'] == 'PASS', report['errors']
    assert report['skill_entrypoints'] == 89


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


@pytest.fixture(scope='module')
def frozen_package(tmp_path_factory):
    """One real package, restored after each mutation; no mock checker outputs."""
    package = tmp_path_factory.mktemp('contract-package')
    contract = load_contract(ROOT)
    paths = set(contract['protected_files']) | {
        'tools/skill-contracts.json', '.codex-plugin/plugin.json', 'VERSION', 'LICENSE',
        'tools/check_skills_inventory.py', 'tools/run_state.py', 'tools/research_wiki.py',
        'skills/skills-codex/shared-references/evo-inquiry.md',
    } | set(REQUIRED_COMPARISON_RESOURCES) | set(REQUIRED_RESEARCH_RESOURCES) | set(REQUIRED_REFLECTION_RESOURCES)
    paths.update(inventory_publication_references())
    records = list(contract.get('workflow_adaptations', {}).values()) + list(contract.get('approved_upgrade_files', {}).values())
    for record in records:
        paths.update(ref.split('#', 1)[0] for ref in [record.get('review_ref')] + record.get('test_refs', []) if ref)
    paths |= {str(p.relative_to(ROOT)) for tree in ('skills', 'skills/skills-codex') for p in (ROOT / tree).glob('*/SKILL.md')}
    for rel in paths:
        destination = package / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, destination)
    assert not contract_errors(package)
    return package


@pytest.fixture(scope='module')
def namespace_baseline(tmp_path_factory, frozen_package):
    baseline = tmp_path_factory.mktemp('namespace-baseline')
    # A local baseline may use either historical namespace. It must not need
    # network access or a Git object database for the comparison to work.
    for path in (frozen_package / 'skills/skills-codex').glob('*/SKILL.md'):
        target = baseline / path.relative_to(frozen_package)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(normalize_namespace(path.read_text()), encoding='utf-8')
    relative = 'skills/skills-codex/shared-references/assurance-contract.md'
    target = baseline / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(normalize_namespace((frozen_package / relative).read_text()), encoding='utf-8')
    return baseline


def test_baseline_comparison_accepts_registered_namespace_migration(frozen_package, namespace_baseline):
    report = verify(frozen_package, namespace_baseline)
    assert report['status'] == 'PASS', report['errors']


@pytest.mark.parametrize('mutation', ['original', 'current', 'unregistered'])
def test_baseline_comparison_still_rejects_unknown_changes(frozen_package, namespace_baseline, mutation):
    relative = 'skills/skills-codex/shared-references/assurance-contract.md'
    path = (frozen_package if mutation == 'current' else namespace_baseline) / relative
    if mutation == 'unregistered':
        path = namespace_baseline / 'unregistered-baseline.txt'
    original = path.read_bytes() if path.exists() else None
    try:
        path.write_bytes((original or b'') + b'\nUnregistered semantic change.\n')
        report = verify(frozen_package, namespace_baseline)
        assert report['status'] == 'FAIL'
        expected = 'protected baseline file changed' if mutation == 'current' else 'unrelated upstream content changed'
        assert any(expected in error for error in report['errors']), report['errors']
    finally:
        if original is None:
            path.unlink()
        else:
            path.write_bytes(original)


@pytest.mark.parametrize('mutation', ['unregistered_body', 'original_digest', 'missing_review', 'missing_tests', 'bad_field'])
def test_directed_workflow_adaptations_keep_frozen_baseline_and_review_refs(frozen_package, mutation):
    import json
    contract_path = frozen_package / 'tools/skill-contracts.json'
    original = contract_path.read_bytes()
    data = json.loads(original)
    name = 'experiment-plan'
    record = data['workflow_adaptations'][name]
    if mutation == 'unregistered_body':
        del data['workflow_adaptations'][name]
    elif mutation == 'original_digest':
        data['retained_skills'][name]['body_without_hook_sha256'] = '0' * 64
        record['baseline_body_sha256'] = '0' * 64
    elif mutation == 'missing_review':
        record['review_ref'] = '../outside.md'
    elif mutation == 'missing_tests':
        record['test_refs'] = []
    else:
        record['reason'] = []
    try:
        contract_path.write_text(json.dumps(data), encoding='utf-8')
        assert contract_errors(frozen_package)
    finally:
        contract_path.write_bytes(original)


@pytest.mark.parametrize('mutation,expected', [
    ('delete', 'Missing registered Codex skill: result-to-claim'),
    ('body', 'protected workflow body changed'),
    ('tools', 'protected frontmatter changed'),
    ('extra', 'Unregistered Codex skill: unregistered'),
    ('helper', 'protected baseline file changed'),
    ('reference', 'protected baseline file changed'),
])
def test_contract_detects_destructive_changes(frozen_package, mutation, expected):
    rel = {'helper': 'tools/run_state.py',
           'reference': 'skills/skills-codex/shared-references/resumable-runs.md',
           'extra': 'skills/skills-codex/unregistered/SKILL.md'}.get(
               mutation, 'skills/skills-codex/result-to-claim/SKILL.md')
    path = frozen_package / rel
    original = path.read_bytes() if path.exists() else None
    try:
        if mutation == 'delete':
            path.unlink()
        elif mutation == 'extra':
            path.parent.mkdir()
            path.write_text('---\nname: unregistered\ndescription: "Unexpected workflow"\n---\n')
        elif mutation == 'tools':
            path.write_text(path.read_text().replace('allowed-tools: Bash(*)', 'allowed-tools: Agent, Bash(*)', 1))
        else:
            path.write_text(path.read_text() + '\nUnauthorized baseline change.\n')
        assert any(expected in error for error in contract_errors(frozen_package))
    finally:
        if original is None:
            path.unlink()
            path.parent.rmdir()
        else:
            path.write_bytes(original)


def test_description_edit_and_registered_extension_preserve_contract(frozen_package):
    import re
    path = frozen_package / 'skills/skills-codex/result-to-claim/SKILL.md'
    original = path.read_bytes()
    try:
        path.write_text(re.sub(r'^description: .*$', 'description: "Assess supported claims from completed experiments."',
                               path.read_text(), count=1, flags=re.M))
        assert not contract_errors(frozen_package)
        assert (frozen_package / 'skills/skills-codex/research-guide/SKILL.md').is_file()
    finally:
        path.write_bytes(original)


def test_broken_hook_link_is_detected(tmp_path):
    package = tmp_path / 'package'
    shutil.copytree(ROOT / 'skills', package / 'skills')
    shutil.copytree(ROOT / '.codex-plugin', package / '.codex-plugin')
    shutil.copytree(ROOT / 'tools', package / 'tools')
    shutil.copyfile(ROOT / 'LICENSE', package / 'LICENSE')
    path = package / 'skills/skills-codex/analyze-results/SKILL.md'
    path.write_text(path.read_text().replace('../shared-references/evo-inquiry.md', '../shared-references/missing.md'))
    report = verify(package)
    assert not report['shared_reference_resolves']
    assert any('reference does not resolve' in error for error in report['errors'])


@pytest.mark.parametrize('relative', REQUIRED_REFLECTION_RESOURCES)
def test_package_requires_the_executable_reflection_contract(frozen_package, relative):
    path = frozen_package / relative
    original = path.read_bytes()
    try:
        path.unlink()
        report = verify(frozen_package)
        assert report['status'] == 'FAIL'
        assert any('Missing required reflection resource ' + relative == error for error in report['errors'])
    finally:
        path.write_bytes(original)


def test_contract_loader_keeps_schema_three_extensions_backward_compatible(frozen_package):
    import json
    path = frozen_package / 'tools/skill-contracts.json'
    original = path.read_bytes()
    contract = json.loads(original)
    contract['schema_version'] = 3
    contract['added_skills'].remove('problem-synthesis')
    contract['mainline_added_skills'].remove('problem-synthesis')
    try:
        path.write_text(json.dumps(contract), encoding='utf-8')
        assert load_contract(frozen_package)['schema_version'] == 3
    finally:
        path.write_bytes(original)
