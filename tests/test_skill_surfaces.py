"""Verify generated skill surfaces and deferred instructions from real files."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from tools.generate_skill_surfaces import projection
from tools.skill_text import workflow_paths

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'tools/generate_skill_surfaces.py'
SPLIT = ('auto-review-loop', 'paper-writing', 'proof-checker', 'research-lit', 'paper-illustration',
         'grant-proposal', 'auto-paper-improvement-loop', 'paper-write', 'paper-slides', 'idea-creator')
SURFACES = ('skills', 'skills/skills-codex', 'skills/skills-codex-claude-review',
            'skills/skills-codex-gemini-review')


def test_all_committed_surfaces_match_sources():
    result = subprocess.run([sys.executable, str(TOOL), '--check'], text=True,
                            capture_output=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    sources = ROOT/'skills'
    assert (sources/'research-guide/SKILL.source.md').is_file()
    assert not (sources/'research-guide/SKILL.md').exists()
    assert 'research-guide/SKILL.md' in projection(ROOT, 'codex')


def test_each_shortened_entry_can_load_workflow_stages():
    for surface in SURFACES:
        for name in SPLIT:
            entry = ROOT / surface / name / 'SKILL.md'
            if entry.is_file():
                assert len(entry.read_text(encoding='utf-8').splitlines()) <= 200, entry
                documents = workflow_paths(entry)
                assert len(documents) >= 2, entry
                assert all(path.is_file() and path.stat().st_size > 100 for path in documents)


def test_changes_in_shared_source_are_detected_then_regenerated(tmp_path):
    def write(path, content):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
        return target

    rule = {'codex': {'destination':'skills/skills-codex', 'remove_frontmatter':['allowed-tools'], 'omit':[]},
            'claude': {'destination':'skills/skills-codex-claude-review', 'skills':[], 'omit':[]},
            'gemini': {'destination':'skills/skills-codex-gemini-review', 'from_codex':{'example/SKILL.md':'example/SKILL.md'}}}
    write('tools/surface_rules.json', json.dumps({'surfaces':rule}))
    for name in rule:
        write(f'tools/skill-surfaces/{name}/patches.json','{}')
    entry = write('skills/example/SKILL.md',
                  '---\nname: example\ndescription: Example task.\nallowed-tools: Read\n---\n\nWorkflow.\n')
    command = [sys.executable, str(TOOL), '--root', str(tmp_path)]
    subprocess.run(command, check=True, capture_output=True, timeout=20)
    codex = tmp_path/'skills/skills-codex/example/SKILL.md'
    gemini = tmp_path/'skills/skills-codex-gemini-review/example/SKILL.md'
    assert 'allowed-tools' not in codex.read_text()
    with entry.open('a', encoding='utf-8') as stream:
        stream.write('Additional workflow detail.\n')
    result = subprocess.run(command+['--check'], text=True, capture_output=True, timeout=20)
    assert result.returncode == 1
    assert all(str(path.relative_to(tmp_path)) in result.stdout for path in (codex,gemini))
    assert 'Additional workflow detail' not in codex.read_text()
    subprocess.run(command, check=True, capture_output=True, timeout=20)
    assert all('Additional workflow detail' in path.read_text() for path in (codex,gemini))
