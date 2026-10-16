---
name: research-review
description: Get a deep critical review of research from an external reviewer backend (Codex or manual). Use when user says "review my research", "help me review", "get external review", or wants critical feedback on research ideas, papers, or experimental results.
argument-hint: "[topic-or-scope]"
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit, mcp__codex__codex, mcp__codex__codex-reply, mcp__manual_review__review, mcp__manual_review__review_reply
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
<!-- EVO-INQUIRY:END -->


<!-- EI-GOVERNANCE:BEGIN -->
Resolve runtime state through tools/state_paths.py before .ei operations. Use
[project-governance](../shared-references/project-governance.md) for fixed evidence,
profiles and controlled migration; missing profiles retain compat-v1.
<!-- EI-GOVERNANCE:END -->


# Research Review via External Reviewer Backend (ultra reasoning)

> 🔒 **Do not wrap this skill in `/loop`, `/schedule`, or `CronCreate`.** It is
> verdict-bearing — it produces a cross-model review verdict, multi-round with
> reviewer thread continuity. An external timer re-fires the verdict on
> wall-clock time and breaks the reviewer's round-to-round memory: zero new
> signal, full token cost. Schedule the *external wait that precedes it* (work
> ready → then review once), not the verdict. See
> [`shared-references/external-cadence.md`](../shared-references/external-cadence.md).

Get a multi-round critical review of research work from the selected external reviewer backend with maximum reasoning depth.

## Constants

- REVIEWER_MODEL = `gpt-6-astra` — Default model for the Codex backend, reasoning effort `ultra` (deep-audit tier). Must be an OpenAI model (e.g., `gpt-6-astra`, `gpt-5.5`, `o3`). Manual backend uses a model the user chooses — it must be a recognized model from a different family (OpenAI, Anthropic, Google, DeepSeek, Moonshot/Kimi, Qwen).
- **REVIEWER_BACKEND = `codex`** — Default: Codex MCP (ultra). Override with `— reviewer: oracle-pro` for Oracle MCP, or `— reviewer: manual` for Manual Review MCP. If manual-review MCP is unavailable, stop and print the install command; do not fall back to Codex. See `shared-references/reviewer-routing.md`.

## Reviewer Calling Convention

When calling the reviewer, branch on REVIEWER_BACKEND:

**If REVIEWER_BACKEND = `codex`:**
  Use `mcp__codex__codex` for new review threads.
  Use `mcp__codex__codex-reply` for follow-up rounds (reuse threadId).

**If REVIEWER_BACKEND = `manual`:**
  Use `mcp__manual_review__review` for new review threads with:
    prompt: [exact same prompt that would go to Codex]
    config: {"model_reasoning_effort": "xhigh", "executor_model": "<actual executor model>", "require_reviewer_model": true}
  Save the returned `threadId`.
  Use `mcp__manual_review__review_reply` for follow-up rounds with:
    threadId: [saved manual-review threadId]
    prompt: [follow-up prompt]
    config: {"model_reasoning_effort": "xhigh", "executor_model": "<actual executor model>", "require_reviewer_model": true}

Content fidelity: the manual reviewer should see the same substantive review
brief Codex would read. If the manual UI supports file upload / attachment,
reuse the same brief file; otherwise paste the brief contents inline because
remote web UIs cannot read your local filesystem paths. Review tracing applies
equally to both backends.

## Context: $ARGUMENTS

## Prerequisites

- **Codex MCP Server** configured in Claude Code:
  ```bash
  claude mcp add codex -s user -- python3 "$HOME/aris_repo/mcp-servers/codex-exec/server.py"   # your ARIS clone's path
  ```
- This gives Claude Code access to `mcp__codex__codex` and `mcp__codex__codex-reply` tools

## Workflow

### Step 1: Gather Research Context
Before calling the external reviewer, compile a comprehensive briefing:
1. Read project narrative documents (e.g., STORY.md, README.md, paper drafts)
2. Read any memory/notes files for key findings and experiment history
3. Identify: core claims, methodology, key results, known weaknesses

### Step 2: Initial Review (Round 1)
Send a detailed prompt with ultra reasoning, using the selected backend. For
the `codex` backend, keep the MCP payload short: write the full briefing to
`RESEARCH_REVIEW_REQUEST.md`, then point Codex at that file.

*For codex backend:*

```
mcp__codex__codex:
  model: gpt-6-astra
  config: {"model_reasoning_effort": "ultra"}
  prompt: |
    Read the review brief at <absolute path to RESEARCH_REVIEW_REQUEST.md>.
    Executor notes are not evidence beyond the files they cite, so verify the
    referenced artifacts before judging.
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

The review brief should contain the full research context, the specific
questions, and the primary artifact / raw-result paths the reviewer should
inspect.

*For manual backend:* use `mcp__manual_review__review` with the same brief
contents. If the manual-review UI supports attachments, attach
`RESEARCH_REVIEW_REQUEST.md`; otherwise paste the brief inline. Save the
returned `threadId`.

### Step 3: Iterative Dialogue (Rounds 2-N)
For `codex` backend: use `mcp__codex__codex-reply` with the returned `threadId`.
For `manual` backend: use `mcp__manual_review__review_reply` with the same `threadId`.
Use the appropriate tool to continue the conversation. For Codex follow-up
rounds, write an updated brief such as `RESEARCH_REVIEW_ROUND_2.md` and send
only the path:

```text
mcp__codex__codex-reply:
  threadId: [saved reviewer threadId from Step 2]
  # replies inherit the thread's model/effort (gpt-6-astra ultra)
  prompt: |
    Read the updated review brief at <absolute path to
    RESEARCH_REVIEW_ROUND_2.md>.
    Focus on unresolved weaknesses and whether the revision actually fixed them.
```

For manual follow-up rounds, attach that same updated brief if possible;
otherwise paste it inline.

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

> **Composed mode** — if invoked with `— composed: <canonical-report-path>` (an
> orchestrator like `/idea-discovery` passes this), do **not** write a standalone review
> `.md` in the project root. The raw conversation is already persisted to `.ei/traces/…`
> (see *Review Tracing* below — that audit copy is kept in every mode); fold the review
> *conclusions* (consensus, claims matrix, prioritized TODOs) into the orchestrator's
> canonical report and cite the trace path there. **Default (no `— composed:` directive):
> behave exactly as above — write the standalone review document.** Never infer composed
> mode from a report file merely existing. Full rules:
> [`shared-references/output-composition.md`](../shared-references/output-composition.md).

## Key Rules

- ALWAYS pin `model: gpt-6-astra` + `config: {"model_reasoning_effort": "ultra"}` for reviews (deep-audit tier; capability fallback per `reviewer-routing.md`, never below `xhigh`)
- That pin is the **Codex** backend's. For `manual`, use the identity-bearing config from the Reviewer Calling Convention above; `model`, `sandbox` and `cwd` are Codex-only
- Put comprehensive context in the review brief. Codex can read local files
  when you pass an absolute path; manual reviewers usually cannot, so attach or
  paste the same brief there.
- Be honest about weaknesses — hiding them leads to worse feedback
- Push back on criticisms you disagree with, but accept valid ones
- Focus on ACTIONABLE feedback — "what experiment would fix this?"
- Document the threadId for potential future resumption
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

## Review Tracing

After each reviewer call (`mcp__codex__codex`, `mcp__codex__codex-reply`, `mcp__manual_review__review`, or `mcp__manual_review__review_reply`), save the trace following `shared-references/review-tracing.md` (Policy C — forensic; never silently skip). Use `save_trace.sh` (resolved per the chain in `shared-references/integration-contract.md` §2) or write files directly to `.ei/traces/<skill>/<date>_run<NN>/`. Respect the `--- trace:` parameter (default: `full`).
  A verdict-bearing manual response MUST begin with
  `Reviewer-Model: <exact-model-id>` — pass the model THIS session is actually
  running as in `executor_model`. Missing, unknown, or same-family identity
  cannot acquit; emit `REVIEW_UNAVAILABLE` rather than guessing. If the executor
  model cannot be named, manual review's cross-family claim is unprovable — say
  so in the report instead of asserting it.
