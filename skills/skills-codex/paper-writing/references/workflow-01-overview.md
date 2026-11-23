<!-- EI-WORKFLOW-REFERENCE -->

# Overview

Read this file when the workflow reaches Overview through Phase 1.5: Negotiated Acceptance Contract (before any writing). In commands and examples, interpret relative skill paths from the entrypoint directory.





# Workflow 3: Paper Writing Pipeline

> **Codex assurance:** every base semantic audit is same-family provisional.
> The pipeline still completes when all mandatory audits are green, but the
> Final Report must say `Submission-ready: provisional`; only cross-family or
> deterministic accepted audit coverage may say `yes`.

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
- **ILLUSTRATION = `figurespec`** — Architecture/illustration generator for Phase 2b: `figurespec` (default, deterministic JSON→SVG via `/figure-spec`, best for architecture/workflow/topology), `gemini` (AI-generated via `/paper-illustration`, best for qualitative method illustrations; needs `GEMINI_API_KEY`), `mermaid` (Mermaid syntax via `/mermaid-diagram`, free, best for flowcharts), or `false` (skip Phase 2b, manual only).

> Override inline: `/paper-writing "NARRATIVE_REPORT.md" — venue: NeurIPS, illustration: gemini, human checkpoint: true`
> IEEE example: `/paper-writing "NARRATIVE_REPORT.md" — venue: IEEE_JOURNAL`

## Inputs

This pipeline accepts one of:

1. **`NARRATIVE_REPORT.md`** (best) — structured research narrative with claims, experiments, results, figures
2. **Research direction + experiment results** — the skill will help draft the narrative first
3. **Existing `PAPER_PLAN.md`** — skip Phase 1, start from **Phase 1.5** (the contract negotiation still runs; only resuming a genuine pre-1.5 legacy run may skip it, and then Phase 6.0's row 0 records "no contract")

The more detailed the input (especially figure descriptions and quantitative results), the better the output.

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
  `shared-references/integration-contract.md` §2); a non-zero exit blocks the Final Report.

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

### Phase 1.5: Negotiated Acceptance Contract (before any writing)

The plan says what the paper will contain; the CONTRACT says what "done" means
— a checklist of testable assertions, negotiated ADVERSARIALLY before the first
section is written, and graded at the end. (The plan is the boundary; the
contract is what gets graded.)

1. **Executor proposes.** From `PAPER_PLAN.md` + `NARRATIVE_REPORT.md`, draft
   `PAPER_ACCEPTANCE_CONTRACT.md`: **10–20 testable assertions** — every
   headline claim has a named evidence source; every abstract number traces to
   a results file; scope qualifiers the title/abstract must carry; figures
   that must exist and what each must show; section-level completeness; venue
   constraints. Each assertion must be CHECKABLE by reading the final PDF +
   results files — no vibes ("writing is clear" is not an assertion; "every
   acronym is defined at first use" is). Fewer than ~10 rubber-stamps; beyond
   ~20 stalls on trivia.

2. **Reviewer pushes back.** Spawn a FRESH reviewer agent (xhigh reasoning)
   pointed at `PAPER_PLAN.md`, `PAPER_ACCEPTANCE_CONTRACT.md`, and the evidence
   inventory (`NARRATIVE_REPORT.md` + results paths). Its brief: push back on
   the contract, not the plan — (a) untestable/vibes assertions → demand a
   checkable rewrite; (b) missing assertions (uncovered claims, untraced
   numbers, foreseeable overclaims with no scope assertion); (c) assertions
   the evidence cannot possibly satisfy — flag now, not after writing. It must
   end with exactly one line: `CONTRACT_ACCEPTED: yes` or
   `CONTRACT_ACCEPTED: no` plus numbered revision demands. A reply with a
   missing or malformed verdict line is treated as `no`; request a corrected
   verdict as a follow-up — the correction exchange does not consume a round.
   Include the scope-limits block from
   [`review-scope-limits.md`](../../shared-references/review-scope-limits.md) in the
   brief.

3. **Iterate.** On `no`, revise per the demands and resubmit as a follow-up in
   the SAME reviewer thread (the negotiation is one conversation). **Max 3
   rounds.**

4. **Fallback — never stall the pipeline.** Round 3 still `no` → record the
   unresolved demands verbatim in a "## Disputed" section and mark
   `status: contested`. A contested contract is precisely the "insert a human
   when the CONTRACT is wrong" trigger, so it OVERRIDES `AUTO_PROCEED` for this
   one decision: pause and present the dispute for a human tie-break. If no
   human responds (unattended run), proceed — but a contested contract caps the
   outcome: Phase 6 gates on the UNDISPUTED assertions and the Final Report
   must set `Submission-ready: no` with the dispute reproduced verbatim; the
   tie-break happens when the human returns.

**Output:** `PAPER_ACCEPTANCE_CONTRACT.md` (`status: accepted | contested`,
round count, reviewer thread/agent id). FROZEN once accepted — Phases 2–5
implement against it, never edit it; a genuinely-wrong assertion is a contract
question for a checkpoint, not a silent rewrite.

**Boundary:** the claim audit (Phases 4.7 / 5.5) stays zero-context — the
contract is a WRITER-side gate, never passed to the claim auditor (two
different nets by design).

