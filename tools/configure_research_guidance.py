#!/usr/bin/env python3
"""Opt in to persistent EvoInquiry research routing without replacing other rules."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates/EVOINQUIRY_AGENTS_SNIPPET.md"
BEGIN = "<!-- EVOINQUIRY:RESEARCH-GUIDANCE:BEGIN -->"
END = "<!-- EVOINQUIRY:RESEARCH-GUIDANCE:END -->"


class GuidanceError(ValueError):
    pass


def guidance_block(newline: str = "\n") -> str:
    template = TEMPLATE.read_text(encoding="utf-8")
    blocks = re.findall(r"```markdown\n(.*?)\n```", template, re.S)
    if len(blocks) != 1 or not blocks[0].strip():
        raise GuidanceError("The research guidance template must contain one Markdown block")
    return "\n".join((BEGIN, "## EvoInquiry research guidance", "", blocks[0], END)).replace(
        "\n", newline)


def managed_span(text: str) -> tuple[int, int] | None:
    begins, ends = text.count(BEGIN), text.count(END)
    if not begins and not ends:
        return None
    if begins != 1 or ends != 1 or text.index(END) < text.index(BEGIN):
        raise GuidanceError("Research guidance markers are incomplete or duplicated; review the file")
    return text.index(BEGIN), text.index(END) + len(END)


def render_guidance(original: bytes, *, remove: bool = False) -> bytes:
    # Decode bytes directly so existing BOMs and line endings remain unchanged.
    text = original.decode("utf-8")
    span = managed_span(text)
    newline = "\r\n" if "\r\n" in text else "\n"
    if remove:
        if span is None:
            return original
        start, end = span
        if text[end:].startswith(newline):
            end += len(newline)
        return (text[:start] + text[end:]).encode("utf-8")
    block = guidance_block(newline)
    if span is not None:
        start, end = span
        return (text[:start] + block + text[end:]).encode("utf-8")
    separator = newline if text and not text.endswith(("\n", "\r")) else ""
    return (text + separator + block + newline).encode("utf-8")


def instruction_file(directory: Path) -> Path:
    override = directory / "AGENTS.override.md"
    if override.is_file() and override.read_bytes().strip():
        return override
    return directory / "AGENTS.md"


def write_guidance(target: Path, original: bytes, updated: bytes) -> None:
    """Preserve other instructions; refuse to clobber an observed concurrent edit."""
    if target.is_symlink():
        raise GuidanceError("The instruction file is a symlink; edit its source explicitly")
    existed = target.exists()
    mode = stat.S_IMODE(target.stat().st_mode) if existed else 0o644
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".ei-guidance-",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        if target.is_symlink() or target.exists() != existed or (
            target.read_bytes() if target.exists() else b""
        ) != original:
            raise GuidanceError("Instructions changed during the update; rerun against the current file")
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--project", type=Path, help="Research project directory")
    scope.add_argument("--global", dest="global_scope", action="store_true",
                       help="Codex home: CODEX_HOME, or ~/.codex when unset")
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--check", action="store_true", help="Check without writing")
    operation.add_argument("--remove", action="store_true", help="Remove only the managed block")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args(argv)
    directory = args.project if args.project is not None else Path(
        os.environ.get("CODEX_HOME") or str(Path.home() / ".codex"))
    try:
        target = instruction_file(directory.expanduser().resolve())
        original = target.read_bytes() if target.exists() else b""
        updated = render_guidance(original, remove=args.remove)
        if args.check:
            present = managed_span(original.decode("utf-8")) is not None
            current = present and updated == original
            print(f"{'CURRENT' if current else 'MISSING_OR_OUTDATED'}: {target}")
            return 0 if current else 1
        if args.dry_run:
            print(f"{'Would update' if updated != original else 'Unchanged'}: {target}")
            if not args.remove:
                print(guidance_block())
            return 0
        if updated != original:
            write_guidance(target, original, updated)
        print(f"{'UPDATED' if updated != original else 'UNCHANGED'}: {target}")
        print("Start a new Codex session to load changed instructions.")
        return 0
    except (GuidanceError, OSError, UnicodeError) as exc:
        print(f"Research guidance: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
