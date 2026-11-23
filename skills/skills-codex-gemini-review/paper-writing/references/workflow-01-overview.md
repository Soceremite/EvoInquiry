<!-- EI-WORKFLOW-REFERENCE -->

# Overview

Read this file when the workflow reaches Overview through Phase 3: LaTeX Writing. In commands and examples, interpret relative skill paths from the entrypoint directory.




> Override for Codex users who want **Gemini**, not a second Codex agent, to act as the reviewer. Install this package **after** `skills/skills-codex/*`.

# Workflow 3: Paper Writing Pipeline

> **Gemini overlay assurance:** verify the actual different-family reviewer before recording `review_independence: cross-family`; `acceptance_status: accepted` requires a positive disposition and the workflow's evidence closure. Negative, unavailable and budget-stop outcomes grant no phase acceptance; same-family responses retain the base provisional contract.

Orchestrate a complete paper writing workflow for: **$ARGUMENTS**

## Overview

This skill chains five sub-skills into a single automated pipeline:

```
/paper-plan → /paper-figure → /paper-write → /paper-compile → /auto-paper-improvement-loop
  (outline)     (plots)        (LaTeX)        (build PDF)       (review & polish ×2)
```

Each phase builds on the previous one's output. The final deliverable is a polished, reviewed `paper/` directory with LaTeX source and compiled PDF.

## Constants

- **VENUE = `ICLR`** — Target venue. Options: `ICLR`, `NeurIPS`, `ICML`. Affects style file, page limit, citation format.
- **MAX_IMPROVEMENT_ROUNDS = 2** — Number of review→fix→recompile rounds in the improvement loop.
- **REVIEWER_MODEL = `gemini-review`** — Gemini reviewer invoked through the local `gemini-review` MCP bridge for plan review, figure review, writing review, and the improvement loop.
- **AUTO_PROCEED = true** — Auto-continue between phases. Set `false` to pause and wait for user approval after each phase.
- **HUMAN_CHECKPOINT = false** — When `true`, the improvement loop (Phase 5) pauses after each round's review to let you see the score and provide custom modification instructions. When `false` (default), the loop runs fully autonomously. Passed through to `/auto-paper-improvement-loop`.

> Override inline: `/paper-writing "NARRATIVE_REPORT.md" — venue: NeurIPS, human checkpoint: true`

## Inputs

This pipeline accepts one of:

1. **`NARRATIVE_REPORT.md`** (best) — structured research narrative with claims, experiments, results, figures
2. **Research direction + experiment results** — the skill will help draft the narrative first
3. **Existing `PAPER_PLAN.md`** — skip Phase 1, start from Phase 2

The more detailed the input (especially figure descriptions and quantitative results), the better the output.

## Pipeline

### Phase 1: Paper Plan

Invoke `/paper-plan` to create the structural outline:

```
/paper-plan "$ARGUMENTS"
```

**What this does:**
- Parse NARRATIVE_REPORT.md for claims, evidence, and figure descriptions
- Build a **Claims-Evidence Matrix** — every claim maps to evidence, every experiment supports a claim
- Design section structure (5-8 sections depending on paper type)
- Plan figure/table placement with data sources
- Scaffold citation structure
- Gemini reviews the plan for completeness via the `/paper-plan` overlay

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

- **User approves** (or AUTO_PROCEED=true) → proceed to Phase 2.
- **User requests changes** → adjust plan and re-present.

### Phase 2: Figure Generation

Invoke `/paper-figure` to generate data-driven plots and tables:

```
/paper-figure "PAPER_PLAN.md"
```

**What this does:**
- Read figure plan from PAPER_PLAN.md
- Generate matplotlib/seaborn plots from JSON/CSV data
- Generate LaTeX comparison tables
- Create `figures/latex_includes.tex` for easy insertion
- Gemini reviews figure quality and captions via the `/paper-figure` overlay

**Output:** `figures/` directory with PDFs, generation scripts, and LaTeX snippets.

#### Phase 2b: AI Illustration Generation (when `illustration: true`)

**Skip this step entirely if `illustration` is not set or is `false`.**

If the paper plan includes architecture diagrams, pipeline figures, or method illustrations, invoke `/paper-illustration`:

```
/paper-illustration "[method description from PAPER_PLAN.md or NARRATIVE_REPORT.md]"
```

**What this does:**
- Codex plans the layout → Gemini optimizes → Nano Banana Pro renders → Codex reviews (score ≥ 9)
- Output: `figures/ai_generated/*.png` — publication-quality method diagrams
- Requires `GEMINI_API_KEY` environment variable

> **Without `illustration: true`:** Architecture diagrams must still be created manually (draw.io, Figma, TikZ) and placed in `figures/` before proceeding — same as before.

**Checkpoint:** List generated vs manual figures.

```
📊 Figures complete:
- Data plots (auto): [list]
- AI illustrations (auto): [list, if illustration: true]
- Manual (need your input): [list]
- LaTeX snippets: figures/latex_includes.tex

[If manual figures needed]: Please add them to figures/ before I proceed.
[If all auto]: Shall I proceed with LaTeX writing?
```

> **Writing invariant (every drafting and revision step):** calibrate each
> claim to its evidence and state it directly; generic caveats live in the
> Limitations section only; writing instructions are never manuscript content
> ("do not mention X" means omit X, not "we do not address X"); tone edits
> never change what the paper knows; preserve the primary question and metrics, report favorable and unfavorable
> findings beside the affected claims, and label retrospective reframing as
> exploratory. Explain tradeoffs only when supported; generic caveats and
> claim-defining limitations are different. `/paper-write` carries the full CONFIDENT PROSE, HONEST LIMITS
> contract.

### Phase 3: LaTeX Writing

Invoke `/paper-write` to generate section-by-section LaTeX:

```
/paper-write "PAPER_PLAN.md"
```

**What this does:**
- Write each section following the plan, with proper LaTeX formatting
- Insert figure/table references from `figures/latex_includes.tex`
- Build `references.bib` from citation scaffolding
- Clean stale files from previous section structures
- Automated bib cleaning (remove uncited entries)
- De-AI polish (remove "delve", "pivotal", "landscape"...)
- Gemini reviews each section for quality via the `/paper-write` overlay

**Output:** `paper/` directory with `main.tex`, `sections/*.tex`, `references.bib`, `math_commands.tex`.

**Checkpoint:** Report section completion.

```
✍️ LaTeX writing complete:
- Sections: [N] written ([list])
- Citations: [N] unique keys in references.bib
- Stale files cleaned: [list, if any]

Shall I proceed with compilation?
```

