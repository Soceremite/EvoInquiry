<!-- EI-WORKFLOW-REFERENCE -->

# Overview

Read this file when the workflow reaches Overview through Phase 1: Paper Plan. In commands and examples, interpret relative skill paths from the entrypoint directory.








# Workflow 3: Paper Writing Pipeline

Orchestrate a complete paper writing workflow for: **$ARGUMENTS**

## Overview

This skill chains five sub-skills into a single automated pipeline:

```
/paper-plan → /paper-figure → /paper-write → /paper-compile → /auto-paper-improvement-loop
  (outline)     (plots)        (LaTeX)        (build PDF)       (review & polish ×2)
```

Each phase builds on the previous one's output. The final deliverable is a polished, reviewed `paper/` directory with LaTeX source and compiled PDF.

In this hybrid pack, the pipeline itself is unchanged, but `paper-plan` and `paper-write` use Orchestra-adapted shared references for stronger story framing and prose guidance.

## Constants

- **VENUE = `ICLR`** — Target venue. Options: `ICLR`, `NeurIPS`, `ICML`, `CVPR`, `ACL`, `AAAI`, `ACM`, `IEEE_JOURNAL` (IEEE Transactions / Letters), `IEEE_CONF` (IEEE conferences). Affects style file, page limit, citation format.
- **MAX_IMPROVEMENT_ROUNDS = 2** — Number of review→fix→recompile rounds in the improvement loop.
- **REVIEWER_MODEL = `gpt-6-astra`** — Model used via Codex MCP for plan review, figure review, writing review, and improvement loop.
- **AUTO_PROCEED = true** — Auto-continue between phases. Set `false` to pause and wait for user approval after each phase.
- **HUMAN_CHECKPOINT = false** — When `true`, the improvement loop (Phase 5) pauses after each round's review to let you see the score and provide custom modification instructions. When `false` (default), the loop runs fully autonomously. Passed through to `/auto-paper-improvement-loop`.
- **ILLUSTRATION = `figurespec`** — Architecture/illustration generator for Phase 2b: `figurespec` (default, deterministic JSON→SVG via `/figure-spec`, best for architecture/workflow/topology), `gemini` (AI-generated via `/paper-illustration`, best for qualitative method illustrations; needs `GEMINI_API_KEY`), `codex-image2` (AI-generated via `/paper-illustration-image2` through the local Codex native image bridge — no external API key, uses your ChatGPT Plus/Pro quota; experimental), `mermaid` (Mermaid syntax via `/mermaid-diagram`, free, best for flowcharts), or `false` (skip Phase 2b, manual only).

> Override inline: `/paper-writing "NARRATIVE_REPORT.md" — venue: NeurIPS, illustration: gemini, human checkpoint: true`
> IEEE example: `/paper-writing "NARRATIVE_REPORT.md" — venue: IEEE_JOURNAL`

## Inputs

This pipeline accepts one of:

1. **`NARRATIVE_REPORT.md`** (best) — structured research narrative with claims, experiments, results, figures
2. **Research direction + experiment results** — the skill will help draft the narrative first
3. **Existing `PAPER_PLAN.md`** — skip Phase 1, start from **Phase 1.5** (the contract negotiation still runs; only resuming a genuine pre-1.5 legacy run may skip it, and then Phase 6.0's row 0 records "no contract")

The more detailed the input (especially figure descriptions and quantitative results), the better the output.

## Optional: Style reference (`— style-ref: <source>`, opt-in)

Lets the user steer **structural** style (section ordering, theorem density, sentence cadence, figure density, bibliography style) of the generated paper toward a reference paper they admire. **Default OFF — when the user does not pass `— style-ref`, do nothing differently from before.**

When `— style-ref: <source>` is in `$ARGUMENTS`, run the helper FIRST, before Phase 1 (paper-plan):

```bash
# Resolve $STYLE_HELPER via the canonical strict-safe chain (see
# shared-references/integration-contract.md §2). Policy A — gate:
# unresolved helper means --style-ref cannot be satisfied, so abort.
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.ei/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.ei/repo" 2>/dev/null) || true
fi
STYLE_HELPER=".ei/tools/extract_paper_style.py"
[ -f "$STYLE_HELPER" ] || STYLE_HELPER="tools/extract_paper_style.py"
[ -f "$STYLE_HELPER" ] || { [ -n "${ARIS_REPO:-}" ] && STYLE_HELPER="$ARIS_REPO/tools/extract_paper_style.py"; }
[ -f "$STYLE_HELPER" ] || {
  echo "ERROR: extract_paper_style.py not resolved at .ei/tools/, tools/, \$ARIS_REPO/tools/, or via ~/.ei/repo." >&2
  echo "       Fix: rerun bash tools/install_aris.sh or smart_update.sh (refreshes ~/.ei/repo), export ARIS_REPO, or copy the helper to tools/." >&2
  echo "       --style-ref cannot be satisfied; aborting." >&2
  exit 1
}
STYLE_STATUS=0
CACHE=$(python3 "$STYLE_HELPER" --source "<source>") || STYLE_STATUS=$?
case "$STYLE_STATUS" in
  0) ;;                                       # share $CACHE/style_profile.md with downstream WRITER phases only
  2) echo "warning: style-ref skipped (missing optional dep)" >&2 ;;
  3) echo "error: --style-ref source failed; aborting pipeline" >&2 ; exit 1 ;;
  *) echo "error: helper failed unexpectedly; aborting pipeline" >&2 ; exit 1 ;;
esac
```

Then forward `— style-ref: <source>` only to the **writer-side** sub-skills:
- `/paper-plan` (Phase 1) — outline structure
- `/paper-write` (Phase 3) — section-by-section prose
- `/paper-illustration` (Phase 2b) — figure structural matching, optional

Sources accepted: local TeX dir / file, local PDF, arXiv id, http(s) URL. Overleaf URLs/IDs are rejected — clone via `/overleaf-sync setup <id>` first and pass the local clone path.

**Strict rules** (full contract in `tools/extract_paper_style.py` docstring):

- Use `style_profile.md` as **structural** guidance only. Match section-count tendency, theorem density, caption-length distribution, sentence cadence, math display ratio, citation style.
- **Never copy prose, claims, examples, or terminology** from anything reachable through the cache.
- **Never pass `— style-ref` (or the cache contents) to reviewer / auditor sub-skills** — Phase 4.5 (`/proof-checker`), Phase 4.7 / 5.5 (`/paper-claim-audit`), Phase 5 (`/auto-paper-improvement-loop` reviewer), Phase 5.8 (`/citation-audit`) MUST run on the artifact alone. Cross-model review independence (`../shared-references/reviewer-independence.md`).

## Pipeline

### Phase 0: Assurance Setup

Resolve the active `assurance` level and persist it so Phase 6's external
verifier reads the same value. **Run once at pipeline start, before Phase 1.**

**Resolution order** (first match wins):

1. Explicit `— assurance: draft | submission` in `$ARGUMENTS`
2. Derived from `— effort:`
   - `lite` / `balanced` → `draft` (default, **zero change from current behavior**)
   - `max` / `beast` → `submission`
3. Default: `draft`

**Action:**

```bash
mkdir -p paper/.ei
echo "<resolved-level>" > paper/.ei/assurance.txt   # draft or submission
```

**What each level does downstream:**

- **`draft`** — Existing behavior. Audits run only when their content detector
  matches (Phase 4.5 / 4.7 / 5.5 / 5.8). Missing artifacts are non-blocking.
  Silent-skip allowed.
- **`submission`** — The four mandatory audits (proof-checker,
  paper-claim-audit, citation-audit, kill-argument) are treated as load-bearing gates. Each
  sub-audit must emit its JSON artifact (PASS / WARN / FAIL / NOT_APPLICABLE /
  BLOCKED / ERROR) — never silent-skip. Phase 6 runs
  `verify_paper_audits.sh` (canonical name; resolved per
  [`shared-references/integration-contract.md`](../../shared-references/integration-contract.md) §2);
  a non-zero exit blocks the Final Report.

**Escape hatch:** a user wanting the old "beast = depth-only, no audit gate"
can pass `— effort: beast, assurance: draft` explicitly. Legal but
discouraged for actual submissions. See
`shared-references/assurance-contract.md` for the full contract.

**Announce the resolved level in-line before Phase 1:**

```
📋 Assurance: <level> (derived from effort: <effort>)
   <either "current behavior, no audit gate" OR "mandatory audits gated by verify_paper_audits.sh (resolved per integration-contract §2)">
```

### Phase 1: Paper Plan

Invoke `/paper-plan` to create the structural outline:

```
/paper-plan "$ARGUMENTS"
```

If `— style-ref: <source>` was passed in `$ARGUMENTS` and the helper succeeded above, append `— style-ref: <source>` to the invocation: `/paper-plan "<topic> — style-ref: <source>"`. (Writer-side phase — forwarding is allowed; reviewer/auditor phases below must not see the style ref.)

**What this does:**
- Parse NARRATIVE_REPORT.md for claims, evidence, and figure descriptions
- Build a **Claims-Evidence Matrix** — every claim maps to evidence, every experiment supports a claim
- Design section structure (5-8 sections depending on paper type)
- Plan figure/table placement with data sources
- Scaffold citation structure
- GPT-6-Astra reviews the plan for completeness

**Output:** `PAPER_PLAN.md` with section plan, figure plan, citation scaffolding.

**Checkpoint:** Present the plan summary to the user.

```
📐 Paper plan complete:
- Title: [proposed title]
- Sections: [N] ([list])
- Figures: [N] auto-generated + [M] manual
- Target: [VENUE], [PAGE_LIMIT] pages

Shall I proceed with figure generation?
```

- **User approves** (or AUTO_PROCEED=true) → proceed to Phase 1.5.
- **User requests changes** → adjust plan and re-present.

