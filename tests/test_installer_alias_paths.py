"""Exercise existing install/reconcile/delete contracts through real directory aliases."""
import importlib
import os

import pytest


@pytest.mark.skipif(os.name == 'nt', reason='Unix Bash installer acceptance runs on Linux and macOS')
@pytest.mark.parametrize('module,function', [
    ('test_codex_install_update', 'test_install_aris_codex_reconcile_and_uninstall'),
    ('test_codex_install_update', 'test_install_aris_codex_uninstall_uses_manifest_repo_root'),
    ('test_codex_install_update', 'test_install_aris_codex_reconcile_removes_stale_links_from_manifest_repo'),
    ('test_copilot_install', 'test_install_copilot_creates_github_skills_symlinks'),
    ('test_copilot_install', 'test_install_copilot_reconcile_adds_and_removes'),
    ('test_copilot_install', 'test_install_copilot_uninstall_uses_manifest_repo_root'),
    ('test_copilot_install', 'test_install_copilot_replace_link_resolves_conflict'),
    ('test_copilot_install', 'test_install_copilot_deploys_agents'),
])
def test_installer_contract_through_directory_alias(tmp_path, module, function):
    actual = tmp_path / 'actual'
    actual.mkdir()
    alias = tmp_path / 'alias'
    alias.symlink_to(actual, target_is_directory=True)
    assert alias.samefile(actual) and alias != actual
    contract = getattr(importlib.import_module('tests.' + module), function)
    contract(alias)
