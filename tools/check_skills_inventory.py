#!/usr/bin/env python3
"""Check EvoInquiry skill inventory and retained workflow contracts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    from tools.skill_contracts import contract_errors, load_contract
except ModuleNotFoundError:
    from skill_contracts import contract_errors, load_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"
CODEX_ROOT = SKILLS_ROOT / "skills-codex"
CATALOG = REPO_ROOT / "docs" / "SKILLS_CATALOG.md"
README = REPO_ROOT / "README.md"
README_CN = REPO_ROOT / "README_CN.md"
AGENT_GUIDE = REPO_ROOT / "AGENT_GUIDE.md"
BOM = b"\xef\xbb\xbf"

FORBIDDEN_CODEX_REVIEWER_STRINGS = (
    "mcp__codex__codex",
    "codex-reply",
    "reviewer-continuation",
    "threadId",
)

# Stable anchors shared by the English and Chinese public guides.
REQUIRED_README_ANCHORS = (
    "capabilities", "installation", "usage", "setup", "contributing", "license",
)


def skill_names(root: Path) -> set[str]:
    return {path.parent.name for path in root.glob("*/SKILL.md")}


def allowed_tools(text: str) -> list[str]:
    """Tokens on the frontmatter `allowed-tools:` line (empty if absent)."""
    match = re.search(r"^allowed-tools:\s*(.+)$", text, flags=re.MULTILINE)
    if not match:
        return []
    return [tok.strip() for tok in match.group(1).split(",") if tok.strip()]


def frontmatter_split(text: str) -> str:
    """Return the body after a leading YAML frontmatter block (whole text if
    no frontmatter). Anchors on the opening `---` fence and the first closing
    `---` fence, so `---` horizontal rules later in the body are not mistaken
    for the frontmatter boundary."""
    match = re.match(r"^---\n.*?\n---\n", text, flags=re.DOTALL)
    return text[match.end():] if match else text


def readme_anchors(text: str) -> set[str]:
    return set(re.findall(r'<a id="([^"]+)"></a>', text))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def catalog_names() -> set[str]:
    text = read(CATALOG)
    return set(re.findall(r"\[`/([^`]+)`\]\(\.\./skills/[^)]+/SKILL\.md\)", text))


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def require_count(path: Path, text: str, pattern: str, expected_count: int, failures: list[str]) -> None:
    match = re.search(pattern, text)
    rel = path.relative_to(REPO_ROOT)
    if match is None:
        failures.append(f"{rel} is missing live count pattern: {pattern}")
        return
    actual = int(match.group("count"))
    if actual != expected_count:
        failures.append(f"{rel} reports {actual} skills; expected {expected_count}")


def check_inventory() -> list[str]:
    failures: list[str] = []
    failures.extend(contract_errors(REPO_ROOT))
    try:
        extensions = set(load_contract(REPO_ROOT)['added_skills'])
    except (OSError, ValueError, TypeError):
        extensions = set()
    main = skill_names(SKILLS_ROOT)
    codex = skill_names(CODEX_ROOT)
    catalog = catalog_names()
    main_refs = {path.name for path in (SKILLS_ROOT / "shared-references").glob("*.md")}
    codex_refs = {path.name for path in (CODEX_ROOT / "shared-references").glob("*.md")}
    # Register the Codex extension references explicitly; all
    # retained workflow inventory and contract checks continue to apply.
    manifest = json.loads(read(REPO_ROOT / ".codex-plugin" / "plugin.json"))
    evo_refs = {"evo-inquiry.md", "task-scope.md", "experiment-storage.md"} if manifest.get("name") == "evo-inquiry" else set()
    require(
        evo_refs <= codex_refs,
        "missing EvoInquiry shared reference",
        failures,
    )

    missing_codex = sorted(main - codex)
    extra_codex = sorted(codex - main - extensions)
    missing_extensions = sorted(extensions - codex)
    missing_catalog = sorted(codex - catalog)
    extra_catalog = sorted(catalog - codex)

    require(not missing_codex, f"missing Codex mirrors: {', '.join(missing_codex)}", failures)
    require(not extra_codex, f"unexpected Codex-only skills: {', '.join(extra_codex)}", failures)
    require(not missing_extensions, f"missing registered extensions: {', '.join(missing_extensions)}", failures)
    require(
        not (main_refs - codex_refs),
        f"missing Codex shared references: {', '.join(sorted(main_refs - codex_refs))}",
        failures,
    )
    require(
        not (codex_refs - main_refs - evo_refs),
        f"unexpected Codex-only shared references: {', '.join(sorted(codex_refs - main_refs - evo_refs))}",
        failures,
    )
    require(not missing_catalog, f"missing catalog entries: {', '.join(missing_catalog)}", failures)
    require(not extra_catalog, f"catalog entries without installed skills: {', '.join(extra_catalog)}", failures)

    catalog_text = read(CATALOG)
    readme = read(README)
    readme_cn = read(README_CN)
    expected_count = len(codex)
    count_checks = [
        (CATALOG, catalog_text, r"\*\*(?P<count>\d+) skills\*\*"),
        (README, readme, r"\*\*(?P<count>\d+) Codex skills\*\*"),
        (README_CN, readme_cn, r"\*\*(?P<count>\d+) 个 Codex skill\*\*"),
        (AGENT_GUIDE, read(AGENT_GUIDE), r"Full catalog.*?\*\*(?P<count>\d+) skills\*\*"),
    ]
    for path, text, pattern in count_checks:
        require_count(path, text, pattern, expected_count, failures)

    for skill_file in sorted(CODEX_ROOT.glob("*/SKILL.md")):
        if skill_file.read_bytes().startswith(BOM):
            failures.append(f"{skill_file.relative_to(REPO_ROOT)} starts with UTF-8 BOM before frontmatter")
        text = read(skill_file)
        for forbidden in FORBIDDEN_CODEX_REVIEWER_STRINGS:
            if forbidden in text:
                failures.append(f"{skill_file.relative_to(REPO_ROOT)} contains forbidden reviewer string: {forbidden}")

    # Public guide parity: links use the same explicit anchors in both languages.
    en_anchors = readme_anchors(readme)
    cn_anchors = readme_anchors(readme_cn)
    for required in REQUIRED_README_ANCHORS:
        if required not in en_anchors:
            failures.append(f"README.md missing required anchor: <a id=\"{required}\"></a>")
        if required not in cn_anchors:
            failures.append(f"README_CN.md missing required anchor: <a id=\"{required}\"></a>")

    require(en_anchors == cn_anchors, "English/Chinese README anchors differ", failures)

    # Agent-grant hygiene (WB2): `Agent` in allowed-tools is the Tier-2
    # fan-out capability gate. Per shared-references/fan-out-pattern.md it is
    # granted ONLY to skills that actually fan out, and such skills MUST cite
    # the convention doc in their body. A grant without that citation is a
    # vestigial/boilerplate grant and fails the drift check.
    for skill_file in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
        text = read(skill_file)
        if "Agent" not in allowed_tools(text):
            continue
        if "fan-out-pattern.md" not in frontmatter_split(text):
            rel = skill_file.relative_to(REPO_ROOT)
            failures.append(
                f"{rel} grants `Agent` in allowed-tools but its body does not "
                f"cite fan-out-pattern.md — vestigial grant or undocumented "
                f"fan-out (see shared-references/fan-out-pattern.md)"
            )

    # Watchdog 'loop' task type ⇔ its documented trigger (A2). Mirrors the Agent-grant⇒cite
    # rule above: a feature with no documented trigger is dead weight, a documented trigger
    # for a missing feature is a broken pointer. The loop type is a shipped feature, so BOTH
    # must be present.
    watchdog_py = read(REPO_ROOT / "tools" / "watchdog.py")
    ext_cadence = read(SKILLS_ROOT / "shared-references" / "external-cadence.md")
    tool_loop = bool(re.search(r"def check_loop\b", watchdog_py)) and bool(re.search(r'==\s*"loop"', watchdog_py))
    doc_loop = bool(re.search(r'"type"\s*:\s*"loop"', ext_cadence))
    require(tool_loop, "tools/watchdog.py must implement the loop-liveness check_loop (A2)", failures)
    require(doc_loop, "external-cadence.md must document registering a watchdog 'loop' task — its trigger (A2)", failures)

    # iteration_log.py (stall→pivot, B) must exist AND be both documented (the ladder with
    # both thresholds) and actually wired into a heartbeat consumer — else it is dead code.
    # Same dead-code guard as the Agent-grant⇒cite rule above.
    extc = read(SKILLS_ROOT / "shared-references" / "external-cadence.md")
    rp = read(SKILLS_ROOT / "research-pipeline" / "SKILL.md")
    tool_stall = (REPO_ROOT / "tools" / "iteration_log.py").is_file()
    doc_ladder = bool(re.search(r"forced structural pivot", extc, re.IGNORECASE)) and \
        bool(re.search(r"stale_count`?\s*>=\s*2", extc)) and bool(re.search(r"stale_count`?\s*>=\s*4", extc))
    # Prove the wiring is real (not a prose mention): resolver chain + note invocation +
    # both pivot branches handled in research-pipeline.
    wired = ('iteration_log.py' in rp and 'ITER_LOG' in rp
             and re.search(r'"\$ITER_LOG"\s+note', rp) is not None
             and 'pivot' in rp and 'structural' in rp and 'human' in rp)
    require(tool_stall, "tools/iteration_log.py (stall→pivot, B) must exist", failures)
    require(doc_ladder, "external-cadence.md must document the stall ladder with both thresholds (>=2 structural, >=4 human) (B)", failures)
    require(wired, "research-pipeline/SKILL.md must actually wire iteration_log.py (resolver + `$ITER_LOG note` + pivot handling) — not just mention it (B)", failures)

    # Check reachable packaged resources; CLI behavior is exercised in tests.
    resources = [REPO_ROOT / 'tools/problem_synthesis.py',
                 REPO_ROOT / 'tools/research_control.py',
                 CODEX_ROOT / 'problem-synthesis/SKILL.md',
                 CODEX_ROOT / 'problem-synthesis/references/record-format.md']
    for resource in resources:
        require(resource.is_file(), f'Missing problem-synthesis resource: {resource}', failures)
    if all(resource.is_file() for resource in resources):
        skill = read(resources[2])
        pipeline = read(CODEX_ROOT / 'research-pipeline/SKILL.md')
        require('references/record-format.md' in skill and '/problem-synthesis' in pipeline,
                'problem-synthesis must be reachable from the workflow and link its recorder contract', failures)

    # research_wiki.py add_claim (claim layer) ⇔ its documented birth trigger in
    # /proof-checker. add_claim is a writer; without a skill that calls it, the claim
    # layer is dead code (the exact orphan-writer trap). Same dead-code guard as above:
    # the writer and its single birth point must BOTH be present.
    rwiki = read(REPO_ROOT / "tools" / "research_wiki.py")
    pchk = read(SKILLS_ROOT / "proof-checker" / "SKILL.md")
    tool_claim = bool(re.search(r"def add_claim\b", rwiki)) and bool(re.search(r'add_parser\("add_claim"', rwiki))
    # Prove the trigger is real (anchored to the actual command line, not a prose
    # mention or comment): proof-checker must literally invoke the resolved helper.
    born = re.search(r'python3\s+"\$WIKI_SCRIPT"\s+add_claim\b', pchk) is not None
    require(tool_claim, "tools/research_wiki.py must implement the add_claim claim-layer writer + its CLI", failures)
    require(born, "proof-checker/SKILL.md must invoke `add_claim` as the claim birth point — not just mention it (else add_claim is an orphan writer)", failures)

    # research_wiki.py upsert_idea (idea layer) ⇔ its documented write-back in
    # /idea-creator Phase 7. Same orphan-writer guard: the deterministic idea writer
    # and the skill that calls it must BOTH be present, anchored to the real command.
    icreator = read(SKILLS_ROOT / "idea-creator" / "SKILL.md")
    tool_idea = bool(re.search(r"def upsert_idea\b", rwiki)) and bool(re.search(r'add_parser\("upsert_idea"', rwiki))
    idea_written = re.search(r'python3\s+"\$WIKI_SCRIPT"\s+upsert_idea\b', icreator) is not None
    require(tool_idea, "tools/research_wiki.py must implement the upsert_idea idea-layer writer + its CLI", failures)
    require(idea_written, "idea-creator/SKILL.md must invoke `upsert_idea` to record ideas (Phase 7) — not just mention it (else ideas are written freehand and skipped on re-gen)", failures)

    # research_wiki.py add_experiment (experiment layer) ⇔ its write-back in
    # /result-to-claim Step 5. Same orphan-writer guard; closes the last freehand
    # wiki layer so the supports/invalidates edges never dangle off a missing exp node.
    r2c = read(SKILLS_ROOT / "result-to-claim" / "SKILL.md")
    tool_exp = bool(re.search(r"def add_experiment\b", rwiki)) and bool(re.search(r'add_parser\("add_experiment"', rwiki))
    exp_written = re.search(r'python3\s+"\$WIKI_SCRIPT"\s+add_experiment\b', r2c) is not None
    require(tool_exp, "tools/research_wiki.py must implement the add_experiment experiment-layer writer + its CLI", failures)
    require(exp_written, "result-to-claim/SKILL.md must invoke `add_experiment` to create the experiment node (Step 5) — not just mention it (else exp pages are freehand and supports/invalidates edges dangle)", failures)

    return failures


def main() -> int:
    failures = check_inventory()
    if failures:
        print("EvoInquiry skill inventory drift detected:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("EvoInquiry skill inventory is consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
