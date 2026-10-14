"""Persistent routing must preserve existing user rules and actual discovery scope."""
from pathlib import Path
import os

import pytest

from tools.configure_research_guidance import (
    BEGIN, END, GuidanceError, guidance_block, instruction_file, main,
    render_guidance, write_guidance,
)


@pytest.mark.parametrize("original", [
    b"", b"# Existing rules\nUse the project budget.\n",
    "\ufeff# 项目规范\r\n保留原始证据。\r\n".encode("utf-8"),
    b"<!-- ARIS:BEGIN -->\nOther installer rules\n<!-- ARIS:END -->",
])
def test_install_preserves_prior_bytes_and_repeated_install_is_unchanged(original):
    updated = render_guidance(original)
    assert updated.startswith(original)
    assert render_guidance(updated) == updated
    assert updated.decode("utf-8").count(BEGIN) == 1


def test_upgrade_and_removal_preserve_unmanaged_prefix_suffix_and_crlf():
    prefix = "\ufeff# Existing\r\n用户已有规则。\r\n".encode("utf-8")
    suffix = b"# Later rules\r\nKeep this instruction too.\r\n"
    original = prefix + (BEGIN + "\r\nOld rules\r\n" + END + "\r\n").encode() + suffix
    updated = render_guidance(original)
    assert updated.startswith(prefix) and updated.endswith(suffix)
    assert b"Old rules" not in updated
    assert b"\n" not in updated.replace(b"\r\n", b"")
    assert render_guidance(updated, remove=True) == prefix + suffix


@pytest.mark.parametrize("text", [BEGIN, END, END + BEGIN, BEGIN + BEGIN + END,
                                         BEGIN + END + END])
def test_malformed_or_duplicate_blocks_cannot_overwrite_instructions(tmp_path, text):
    target = tmp_path / "AGENTS.md"
    original = text.encode()
    target.write_bytes(original)
    assert main(["--project", str(tmp_path)]) == 2
    assert target.read_bytes() == original


@pytest.mark.parametrize("override", [b"", b"  \n", b"# Override\nFollow local limits.\n"])
def test_update_targets_the_instruction_file_codex_will_discover(tmp_path, override):
    base = tmp_path / "AGENTS.md"
    base.write_bytes(b"# Base rules\n")
    other = tmp_path / "AGENTS.override.md"
    other.write_bytes(override)
    target = other if override.strip() else base
    assert instruction_file(tmp_path) == target
    assert main(["--project", str(tmp_path)]) == 0
    assert BEGIN.encode() in target.read_bytes()
    untouched = base if target == other else other
    assert untouched.read_bytes() == (b"# Base rules\n" if target == other else override)


def test_global_respects_codex_home_and_leaves_runtime_configuration_unchanged(tmp_path, monkeypatch):
    codex_root = tmp_path / "Codex 设置"
    codex_root.mkdir()
    config = codex_root / "config.toml"
    original_config = b'model = "existing-model"\n[plugins."evo-inquiry@evo-inquiry"]\nenabled = true\n'
    config.write_bytes(original_config)
    monkeypatch.setenv("CODEX_HOME", str(codex_root))
    assert main(["--global"]) == 0
    target = codex_root / "AGENTS.md"
    first = target.read_bytes()
    modified = target.stat().st_mtime_ns
    assert main(["--global", "--check"]) == 0
    assert main(["--global"]) == 0
    assert target.read_bytes() == first and target.stat().st_mtime_ns == modified
    assert config.read_bytes() == original_config


def test_preview_and_check_never_create_a_missing_project(tmp_path):
    project = tmp_path / "新项目 with spaces"
    assert main(["--project", str(project), "--dry-run"]) == 0
    assert main(["--project", str(project), "--check"]) == 1
    assert not project.exists()


def test_check_detects_obsolete_guidance_and_remove_only_removes_our_block(tmp_path):
    target = tmp_path / "AGENTS.md"
    prefix, suffix = b"# Other rules\n", b"# Final rules\n"
    old = prefix + (BEGIN + "\nOld rules\n" + END + "\n").encode() + suffix
    target.write_bytes(old)
    assert main(["--project", str(tmp_path), "--check"]) == 1
    assert target.read_bytes() == old
    assert main(["--project", str(tmp_path)]) == 0
    assert main(["--project", str(tmp_path), "--remove"]) == 0
    assert target.read_bytes() == prefix + suffix
    assert main(["--project", str(tmp_path), "--remove"]) == 0
    assert target.read_bytes() == prefix + suffix


def test_observed_concurrent_edit_is_preserved_and_temporary_file_is_removed(tmp_path):
    target = tmp_path / "AGENTS.md"
    original = b"# Before\n"
    current = b"# Edited by another writer\n"
    target.write_bytes(current)
    with pytest.raises(GuidanceError, match="changed during"):
        write_guidance(target, original, render_guidance(original))
    assert target.read_bytes() == current
    assert list(tmp_path.glob(".ei-guidance-*")) == []


def test_instruction_symlink_is_preserved(tmp_path):
    source = tmp_path / "shared-rules.md"
    original = b"# Shared rules\n"
    source.write_bytes(original)
    link = tmp_path / "AGENTS.md"
    try:
        link.symlink_to(source)
    except (OSError, NotImplementedError):
        pytest.skip("Creating symlinks is unavailable on this runner")
    assert main(["--project", str(tmp_path)]) == 2
    assert link.is_symlink() and source.read_bytes() == original


@pytest.mark.skipif(os.name != "posix", reason="POSIX file permission preservation")
def test_existing_instruction_permissions_survive_update(tmp_path):
    target = tmp_path / "AGENTS.md"
    original = b"# Other preferences\n"
    target.write_bytes(original)
    target.chmod(0o640)
    write_guidance(target, original, render_guidance(original))
    assert target.stat().st_mode & 0o777 == 0o640
