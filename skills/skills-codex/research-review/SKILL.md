---
name: "research-review"
description: "Obtain one fresh critical review of a research proposal, paper, or results. Use for review feedback; auto-review-loop handles repeated revision and re-review."
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
<!-- EVO-INQUIRY:END -->


# Research Review via a secondary Codex agent (ultra reasoning)

> **Codex assurance:** the fresh base reviewer is same-family. Record
> `review_independence: same-family` and `acceptance_status: provisional` in
> traces and deliverables. A Claude/Gemini overlay may record cross-family
> accepted; an unavailable reviewer is BLOCKED, never a fabricated PASS.

Get a multi-round critical review of research work from an external LLM with maximum reasoning depth.

## Constants

- REVIEWER_MODEL = `gpt-6-astra` — Model used via a secondary Codex agent, reasoning effort `ultra` (deep-audit tier). Must be an OpenAI model (e.g., `gpt-6-astra`, `gpt-5.5`, `o3`)
- **REVIEWER_BACKEND = `codex`** — Default: Codex ultra reviewer (deep-audit tier). Use `--reviewer: oracle-pro` only when explicitly requested; if Oracle is unavailable, warn and fall back to Codex at this skill's declared tier (`ultra`). **Same-family note:** this default reviewer is a second Codex/GPT agent — valid for Type-A completeness/drive review, but not a cross-family Type-B verdict; install a `skills-codex-claude-review` / `skills-codex-gemini-review` overlay for a cross-family acquittal (see `shared-references/reviewer-routing.md`).

## Context: $ARGUMENTS

## Prerequisites

- Use `spawn_agent` and `send_input` when the user has explicitly allowed delegation or subagents.
- If delegation is not allowed, run the same review loop locally and preserve the same deliverable structure.

## Workflow

### Step 1: Gather Research Context
Before calling the external reviewer, compile a comprehensive briefing:
1. Read project narrative documents (e.g., STORY.md, README.md, paper drafts)
2. Read any memory/notes files for key findings and experiment history
3. Identify: core claims, methodology, key results, known weaknesses

### Step 2: Initial Review (Round 1)
Send a detailed prompt with ultra reasoning:

```
spawn_agent:
  model: gpt-6-astra
  reasoning_effort: ultra
  message: |
    [Full research context + specific questions]
    Please review the work against its question, evidence and intended use.
    Verify consequential claims against actual artifacts. Identify supported
    strengths, material weaknesses, alternative explanations and missing evidence.
    Apply the same evidential standard to favorable and unfavorable conclusions. Identify:
    1. Logical gaps or unjustified claims
    2. Missing experiments that would strengthen the story
    3. Narrative weaknesses
    4. Whether the contribution is sufficient for a top venue

    === REVIEW SCOPE ===
    Evaluate the actual research question, requested deliverable and applicable
    disciplinary standards. Locate strengths and defects in the supplied evidence;
    do not presume acceptance, rejection or a particular threat model. Distinguish
    observed errors, unsupported claims and optional extensions. Propose the smallest
    adequate correction, citing its failing path, evidence or preserved invariant.
    Keep hypotheses, speculation and unperformed checks explicit. A real boundary
    or reproducibility defect is in scope when it affects this work; unrelated
    infrastructure and speculative redesign are not automatically required.
    Say plainly when something is correct. Do not manufacture findings.
    Be brutally honest. If, after genuinely trying to break it, the work
    holds up and is ready, say so clearly.
```

### Step 3: Iterative Dialogue (Rounds 2-N)
Use `send_input` with the returned agent id to continue the conversation:

```text
send_input:
  target: [saved reviewer id from Step 2]
  message: |
    Please continue the review using the revised materials below.

    Revised files:
    - /absolute/path/to/file1
    - /absolute/path/to/file2

    Focus on unresolved weaknesses and whether the revision actually fixed them.
```

For each round:
1. **Respond** to criticisms with evidence/counterarguments
2. **Ask targeted follow-ups** on the most actionable points
3. **Request specific deliverables**: experiment designs, paper outlines, claims matrices

Key follow-up patterns:
- "If we reframe X as Y, does that change your assessment?"
- "What's the minimum experiment to satisfy concern Z?"
- "Please design the minimal additional experiment package (highest decision-relevant information per unit cost)"
- "Please write a mock NeurIPS/ICML review with scores"
- "Give me a results-to-claims matrix for possible experimental outcomes"

### Step 4: Convergence
Stop when the requested review is complete, its bounded review rounds are exhausted, or further investigation needs unavailable evidence. Judge each material issue as resolved, unresolved or not substantiated, with evidence. Agreement and narrative consensus do not establish correctness. Unresolved issues remain in the final assessment; stopping is not acceptance.

### Step 5: Document Everything
Save the full interaction and conclusions to a review document in the project root:
- Round-by-round summary of criticisms and responses
- Evidence-grounded conclusions, remaining disagreement and unresolved checks
- Claims matrix (what claims are allowed under each possible outcome)
- Prioritized TODO list with estimated compute costs
- Paper outline if discussed

Update project memory/notes with key review conclusions.

If `— composed: <canonical-report-path>` is explicitly present, fold consensus,
claims matrix, TODOs, and trace links into that report instead of writing a
standalone review document. Without the directive, write the standalone review
as documented; never infer composed mode from an existing file. `— standalone`
always wins. See
[`output-composition.md`](../shared-references/output-composition.md).

### Step 6: Review Tracing

Save a trace for every `spawn_agent`, `send_input`, or `oracle-pro` review call following `../shared-references/review-tracing.md`. Record the reviewer route, saved agent id, prompt summary, raw response path, decisions, and action items. This preserves the Claude mainline Review Tracing semantics while using Codex-native reviewer calls.

## Key Rules

- ALWAYS use `model: gpt-6-astra` + `reasoning_effort: ultra` for reviews (deep-audit tier; capability fallback per `reviewer-routing.md`, never below `xhigh`)
- Send comprehensive context in Round 1 — the external model cannot read your files
- Be honest about weaknesses — hiding them leads to worse feedback
- Push back on criticisms you disagree with, but accept valid ones
- Focus on ACTIONABLE feedback — "what experiment would fix this?"
- Document the agent id for potential future resumption
- The review document should be self-contained (readable without the conversation)

## Prompt Templates

### For initial review:
"I'm going to present a complete ML research project for your critical review. Please act as a senior ML reviewer (NeurIPS/ICML level)..."

### For experiment design:
"Please design the minimal additional experiment package that gives the highest decision-relevant information per unit cost. Our compute: [describe]. Be very specific about configurations."

### For paper structure:
"Please turn this into a concrete paper outline with section-by-section claims and figure plan."

### For claims matrix:
"Please give me a results-to-claims matrix: what claim is allowed under each possible outcome of experiments X and Y?"

### For mock review:
"Please write a mock NeurIPS review with: Summary, Strengths, Weaknesses, Questions for Authors, Score, Confidence, and What Would Move Toward Accept."
