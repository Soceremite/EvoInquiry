"""Release verification must detect missing resources of the added workflow."""
from pathlib import Path
import shutil

import pytest

from tools.publication_policy import load_policy
from tools.skill_contracts import load_contract
from tools.verify_evo_inquiry import REQUIRED_COMPARISON_RESOURCES, verify

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def package(tmp_path_factory):
    root = tmp_path_factory.mktemp('comparison-package')
    contract = load_contract(ROOT)
    paths = set(contract['protected_files']) | set(contract['approved_upgrade_files'])
    paths |= set(load_policy(ROOT)['required_reference_files']) | set(REQUIRED_COMPARISON_RESOURCES)
    paths |= {'tools/skill-contracts.json', 'tools/publication-policy.json',
              '.codex-plugin/plugin.json', 'VERSION', 'LICENSE',
              'tools/check_skills_inventory.py', 'tools/run_state.py', 'tools/research_wiki.py',
              'skills/skills-codex/shared-references/evo-inquiry.md'}
    for tree in ('skills', 'skills/skills-codex'):
        paths.update(str(path.relative_to(ROOT)) for path in (ROOT / tree).glob('*/SKILL.md'))
    for name in paths:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    assert verify(root)['status'] == 'PASS', verify(root)['errors']
    return root


@pytest.mark.parametrize('name', REQUIRED_COMPARISON_RESOURCES)
def test_missing_new_resource_blocks_package_verification(package, name):
    target = package / name
    original = target.read_bytes()
    try:
        target.unlink()
        report = verify(package)
        assert report['status'] == 'FAIL'
        assert f'Missing required comparison/routing resource {name}' in report['errors']
    finally:
        target.write_bytes(original)
