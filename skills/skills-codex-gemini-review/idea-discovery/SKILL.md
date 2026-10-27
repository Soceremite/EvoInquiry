---
name: "idea-discovery"
description: "Workflow 1: Full idea discovery pipeline. Orchestrates research-lit \u2192 idea-creator \u2192 novelty-check \u2192 research-review to go from a broad research direction to validated, pilot-tested ideas. Use when user says \\\"\u627eidea\u5168\u6d41\u7a0b\\\", \\\"idea discovery pipeline\\\", \\\"\u4ece\u96f6\u5f00\u59cb\u627e\u65b9\u5411\\\", or wants the complete idea exploration workflow."
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
<!-- EVO-INQUIRY:END -->

> Override for Codex users who want **Gemini**, not a second Codex agent, to act as the reviewer. Install this package **after** `skills/skills-codex/*`.

# Workflow 1: Idea Discovery Pipeline

> **Gemini overlay assurance:** verify the actual different-family reviewer before recording `review_independence: cross-family`; `acceptance_status: accepted` requires a positive disposition and the workflow's evidence closure. Negative, unavailable and budget-stop outcomes grant no phase acceptance; same-family responses retain the base provisional contract.

Orchestrate a complete idea discovery workflow for: **$ARGUMENTS**

## Overview

This skill chains sub-skills into a single automated pipeline:

```
problem-framing → /research-lit → /idea-creator → /novelty-check → /research-review → /research-refine-pipeline
  (survey)      (brainstorm)    (verify novel)    (critical feedback)  (refine method + plan experiments)
```

Each phase builds on the previous one's output. The final deliverables are a validated `idea-stage/IDEA_REPORT.md` with ranked ideas, plus a refined proposal (`refine-logs/FINAL_PROPOSAL.md`) and experiment plan (`refine-logs/EXPERIMENT_PLAN.md`) for the top idea.

## Constants

Pilot duration, reminders, compute and concurrency follow the
[session resource table](../shared-references/resource-budget.md) and current plan.
Prefer the smallest informative pilot; ideas or planning alone do not launch one.

- **MAX_PILOT_IDEAS = 3** — Run pilots for at most 3 top ideas in parallel. Additional ideas are validated on paper only.
- **AUTO_PROCEED = true** — When `true`, checkpoints are informational: report the selected option and continue in the same turn. Set to `false` to ask for explicit user confirmation and end the turn at each selection checkpoint.
- **RESUMABLE = true** — Use the existing versioned run state and final evidence gate below.
- **OUTPUT_DIR = `idea-stage/`** — All idea-stage outputs go here. Create the directory if it doesn't exist.
- **REVIEWER_MODEL = `gemini-review`** — Gemini reviewer invoked through the local `gemini-review` MCP bridge. Passed to the reviewer-aware sub-skills installed by this overlay.
- **ARXIV_DOWNLOAD = false** — When `true`, `/research-lit` downloads the top relevant arXiv PDFs during Phase 1. When `false` (default), only fetches metadata. Passed through to `/research-lit`.

> 💡 These are defaults. Override by telling the skill, e.g., `/idea-discovery "topic" — arxiv download: true`.

## Checkpoint execution rule

Resolve `AUTO_PROCEED` once from `$ARGUMENTS` before Phase 1 and keep that mode
for the entire workflow.

- **`AUTO_PROCEED=true` is non-blocking.** A checkpoint is a progress update,
  not a question. State the result and the automatically selected next action,
  then continue executing in the **same turn**. Do not ask for confirmation,
  request user input, sleep, wait for silence, or end the turn at a checkpoint.
- **`AUTO_PROCEED=false` is blocking.** Present the options, ask the user, and
  end the turn. Resume only after an explicit reply.

Never implement auto-proceed as “ask, then continue if there is no response.”
Once a turn ends, silence cannot resume the workflow. The user can still
interrupt a non-blocking run at any time.

This rule governs only `AUTO_PROCEED`-controlled selection checkpoints. If the
user explicitly enables a Feishu **interactive** gate, that external approval
or reply is an intentional blocking exception; wait for that user-controlled
gate rather than treating it as a silence timeout. Feishu off/push-only modes
remain non-blocking under `AUTO_PROCEED=true`.

## Per-stage evidence gate (`RESUMABLE = true`)


Resolve `run_state.py` and `idea_discovery_gate.py` from the Codex manifest
using the same resolver pattern as `/research-pipeline`. If either helper is
unavailable, the final report is `BLOCKED`; do not silently continue without a
state record.

For a new run, derive `<run_id>` from the direction slug and date, then start
this ordered state record with `--executor <actual-Codex-model>
--provisional-advances` (for example, `codex-gpt-6-astra`):

```text
problem-framing,research-lit,idea-creator,novelty-check,research-review,research-refine-pipeline
```

New runs use `--workflow-contract idea-discovery/v2` on `run_state.py start`.
Retain the contract and phase list on resume: old runs without this field use
the v1 five-phase gate. Never restart an old run under v2 to bypass its state.
The additional `problem-framing` artifact is the canonical report section
`idea-stage/IDEA_REPORT.md#problem-framing`; reuse a suitable existing proposal
by reference. Its completion records framing, not scientific acceptance. After
marking this artifact `done` in Phase 0, run:

```text
python3 <resolved-idea_discovery_gate.py> . <run_id> --framing-only
```

Only a passing content/artifact check records this mechanical phase as complete
with a deterministic receipt. It does not certify the question or accept any
research/review phase. If blocked, fix the actual missing artifact before moving
on. The final report gate still grants no semantic phase acceptance.

For each phase, mark `running` on entry and `done --artifact <path>` only after
its artifact is present. Use these artifact locators so the final gate can
check the canonical report rather than scattered scratch files:

| Phase | Artifact locator |
|---|---|
| `problem-framing` (v2) | `idea-stage/IDEA_REPORT.md#problem-framing` |
| `research-lit` | `idea-stage/IDEA_REPORT.md#literature-landscape` |
| `idea-creator` | `idea-stage/IDEA_REPORT.md#ranked-ideas` |
| `novelty-check` | `idea-stage/IDEA_REPORT.md#novelty-verification` |
| `research-review` | `idea-stage/IDEA_REPORT.md#external-critical-review` |
| `research-refine-pipeline` | `refine-logs/FINAL_PROPOSAL.md` |

`novelty-check` and `research-review` are reviewer-bearing phases. After
folding the actual findings into the report, record `done`, then use
`run_state.py accept` only after a positive identity-bearing response from the
actual different-family Gemini reviewer, with its real model and durable trace
or completed thread ID. Use the same actual executor identity as the run record.
Do not invent a response or identity. Same-family reviews remain provisional
under the base contract; this overlay cannot relabel them as cross-family.
A negative or unavailable review leaves the phase unaccepted and the final gate
blocked. PROCEED WITH CAUTION permits further investigation, not novelty proof.

At the end of Phase 5, run:

```text
python3 <resolved-idea_discovery_gate.py> . <run_id> --report idea-stage/IDEA_REPORT.md
```

The gate writes its result to `gates.idea-discovery-evidence` in the run state.
On `PASS`, it has validated (but never created) the two review receipts, all
required artifacts, and non-empty anchored report sections. Per-phase
acceptance or provisional status stays with the reviewer route that produced
the receipt. On a non-zero exit, the gate writes explicit
`BLOCKED: <stage> evidence missing` lines to the report; do not present the
workflow as complete. On `— resume <run_id>`, start from the first non-terminal
phase and re-run the gate before finalizing.

## Pipeline

### Phase 0: Problem framing and existing brief

For v2, establish the question, assumptions, constraints and what the next evidence
would change. Use [scientific-brainstorming](../scientific-brainstorming/SKILL.md)
when the direction is vague; a fixed existing question can be reused. Write the
`Problem Framing` section of the canonical idea report with its evidence links.
Do not automatically launch pilots or require a venue to complete framing.

#### Load Research Brief (if available)


### Phase 1: Literature Survey

Invoke `/research-lit` to map the research landscape:

```
/research-lit "$ARGUMENTS"
```

**What this does:**
- Search arXiv, Google Scholar, Semantic Scholar for recent papers
- Build a landscape map: sub-directions, approaches, open problems
- Identify structural gaps and recurring limitations
- Output a literature summary (saved to working notes)

**🚦 Checkpoint:** Present the landscape summary to the user.

**When `AUTO_PROCEED=true` (non-blocking):** report the selected direction and
continue immediately in the same turn, without a question:

```
📚 Literature survey complete. Here's what I found:
- [key findings, gaps, open problems]

AUTO_PROCEED: selected [top-ranked direction]. Continuing to Phase 2.
```

**When `AUTO_PROCEED=false` (blocking):** present the same findings, ask
`Does this match your understanding? Should I adjust the scope before generating ideas?`,
then end the turn.

- **User approves** → proceed to Phase 2 with the best direction.
- **User requests changes** (e.g., "focus more on X", "ignore Y", "too broad") → refine the search with updated queries, re-run `/research-lit` with adjusted scope, and present again. Repeat until the user is satisfied.

### Phase 2: Idea Generation + Filtering + Pilots

Invoke `/idea-creator` with the landscape context:

```
/idea-creator "$ARGUMENTS"
```

**What this does:**
- Generate a task-appropriate set of distinct concrete ideas via `/idea-creator`; avoid fixed quotas and duplicated mechanisms
- Filter by feasibility, compute cost, quick novelty search
- Deep validate top ideas (full novelty check + devil's advocate)
- Run pilots only within the established authorization, verified compute/storage budget and actual resources; planning or brainstorming alone does not launch them
- Rank by question value, valid discriminating evidence and feasible next inquiry; distinguish measurement/execution failure from a null or contradictory finding
- Output `idea-stage/IDEA_REPORT.md`

**🚦 Checkpoint:** Present `idea-stage/IDEA_REPORT.md` ranked ideas to the user.

**When `AUTO_PROCEED=true` (non-blocking):** report the automatic selection and
continue immediately in the same turn, without a question:

```
💡 Generated X ideas, filtered to Y, piloted Z. Top results:

1. [Idea 1] — Pilot: POSITIVE (+X%)
2. [Idea 2] — Pilot: WEAK POSITIVE (+Y%)
3. [Idea 3] — Pilot: NULL/NEGATIVE — assess validity, alternatives and information value

AUTO_PROCEED: selected [top-ranked idea(s)]. Continuing to Phase 3.
```

**When `AUTO_PROCEED=false` (blocking):** present the same ranking, ask
`Which ideas should I validate further? Or should I regenerate with different constraints?`,
then end the turn.

- **User picks ideas** → proceed to Phase 3 with the selected ideas.
- **User unhappy with all ideas** → collect feedback ("what's missing?", "what direction do you prefer?"), update the prompt with user's constraints, and re-run Phase 2 (idea generation). Repeat until the user selects at least 1 idea.
- **User wants to adjust scope** → go back to Phase 1 with refined direction.

### Phase 3: Deep Novelty Verification

For each shortlisted idea (including informative null or negative pilots), run a thorough novelty check:

```
/novelty-check "[top idea 1 description]"
/novelty-check "[top idea 2 description]"
```

**What this does:**
- Multi-source literature search (arXiv, Scholar, Semantic Scholar)
- Cross-verify with the Gemini-backed `/novelty-check` overlay
- Check for concurrent work (last 3-6 months)
- Identify closest existing work and differentiation points

**Update `idea-stage/IDEA_REPORT.md`** with deep novelty results. Eliminate any idea that turns out to be already published.

### Phase 4: External Critical Review

For the surviving top idea(s), get a sharp outside read — strongest case, named risks, and the cheapest discriminating next experiment; preserve the original hypothesis while checking whether evidence warrants revising it; record an explicit change rather than silently rewriting it:

```
/research-review "[top idea with hypothesis + pilot results]"
```

**What this does:**
- Gemini acts as a senior reviewer (NeurIPS/ICML level) via the local `gemini-review` MCP bridge
- Scores the idea, identifies weaknesses, suggests minimum viable improvements
- Provides concrete feedback on experimental design

**Update `idea-stage/IDEA_REPORT.md`** with reviewer feedback and revised plan.

### Phase 4.5: Method Refinement + Experiment Planning

After review, refine the top idea into a concrete proposal and plan experiments:

```
/research-refine-pipeline "[top idea description + pilot results + reviewer feedback]"
```

**What this does:**
- Freeze a **Problem Anchor** to prevent scope drift
- Refine the method via Gemini review — reviewer risks choose the next tests, they do not add components; the score is advisory, and preserving the core hypothesis outranks pleasing the reviewer
- Generate a claim-driven experiment roadmap with ablations, budgets, and run order
- Output: `refine-logs/FINAL_PROPOSAL.md`, `refine-logs/EXPERIMENT_PLAN.md`, `refine-logs/EXPERIMENT_TRACKER.md`

**🚦 Checkpoint:** Present the refined proposal summary.

**When `AUTO_PROCEED=true` (non-blocking):** report that the proposal was
selected and continue immediately in the same turn, without a question:

```
🔬 Method refined and experiment plan ready:
- Problem anchor: [anchored problem]
- Method thesis: [one sentence]
- Dominant contribution: [what's new]
- Must-run experiments: [N blocks]
- First 3 runs to launch: [list]

AUTO_PROCEED: accepted the top proposal. Continuing to Final Report.
```

**When `AUTO_PROCEED=false` (blocking):** present the same summary, ask
`Proceed to implementation? Or adjust the proposal?`, then end the turn.

- **User approves** → proceed to Final Report.
- **User requests changes** → pass feedback to `/research-refine` for another round.
- **Lite mode:** If the pilot was inconclusive, still produce the smallest discriminating next-experiment plan — a reviewer score alone never downgrades an idea.

### Phase 5: Final Report

Finalize the existing `idea-stage/IDEA_REPORT.md` with all accumulated information. Preserve the v2 `Problem Framing` section and its evidence references; do not replace it with the template placeholders:

```markdown
# Idea Discovery Report

**Direction**: $ARGUMENTS
**Date**: [today]
**Pipeline**: problem-framing (v2) → research-lit → idea-creator → novelty-check → research-review → research-refine-pipeline

## Executive Summary
[2-3 sentences: best idea, key evidence, recommended next step]

## Problem Framing
[v2: preserve the established question, constraints, alternatives and evidence links from Phase 0; old v1 runs keep their existing contract]

## Literature Landscape
[from Phase 1]

## Ranked Ideas
[from Phase 2, updated with Phase 3-4 results]

### 🏆 Idea 1: [title] — RECOMMENDED
- Pilot: [observed outcome, uncertainty and what it distinguishes; or not run]
- Novelty: [search coverage, closest checked work, verified difference or unknown]
- Reviewer score: X/10
- Next step: implement full experiment → /auto-review-loop

### Idea 2: [title] — BACKUP
...

## Eliminated Ideas
[ideas killed at each phase, with reasons]

## Refined Proposal
- Proposal: `refine-logs/FINAL_PROPOSAL.md`
- Experiment plan: `refine-logs/EXPERIMENT_PLAN.md`
- Tracker: `refine-logs/EXPERIMENT_TRACKER.md`

## Next Steps
- [ ] /run-experiment to deploy experiments from the plan
- [ ] /auto-review-loop to iterate until submission-ready
- [ ] Or invoke /research-pipeline for the complete end-to-end flow
```

## Output Protocols

> Follow these shared protocols for all output files:
> - **[Output Versioning Protocol](../shared-references/output-versioning.md)** — write timestamped file first, then copy to fixed name
> - **[Output Manifest Protocol](../shared-references/output-manifest.md)** — log every output to MANIFEST.md
> - **[Output Language Protocol](../shared-references/output-language.md)** — respect the project's language setting

## Key Rules

- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.

- **Don't skip phases.** Each phase filters and validates — skipping leads to wasted effort later.
- **Checkpoint between phases.** Briefly summarize what was found. With `AUTO_PROCEED=true`, state the selected next action and keep executing in the same turn; with `false`, ask and end the turn.
- **Let pilots kill, not vibes.** A cheap pilot that says no beats a month of implementation that says no — but the kill needs empirical signal or a named published paper, not taste. Talking yourself out of ideas on paper is how pipelines end up with nothing to run.
- **Evidence and question value guide selection.** Distinguish valid negative or null findings from broken execution and underpowered checks. A positive pilot is useful evidence, not an automatic ranking rule; retain informative boundaries and alternatives.
- **Document everything.** Dead ends are just as valuable as successes for future reference.
- **Be honest with the reviewer.** Include negative results and failed pilots in the review prompt.
- **Feishu notifications are optional.** If `~/.codex/feishu.json` exists, send `checkpoint` at each phase transition and `pipeline_done` at final report. If absent/off, skip silently.

## Composing with Workflow 2

After this pipeline produces a validated top idea:

```
/idea-discovery "direction"         ← you are here (Workflow 1, includes method refinement + experiment planning)
/run-experiment                     ← deploy experiments from the plan
/auto-review-loop "top idea"        ← Workflow 2: iterate until submission-ready

Or use /research-pipeline for the full end-to-end flow.
```
