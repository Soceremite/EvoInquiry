<!-- EI-WORKFLOW-REFERENCE -->

# Context

Read this file when the workflow reaches Context through Step 4: Recompile Round 1. In commands and examples, interpret relative skill paths from the entrypoint directory.




> Override for Codex users who want **Gemini**, not a second Codex agent, to act as the reviewer. Install this package **after** `skills/skills-codex/*`.

# Auto Paper Improvement Loop: Review → Fix → Recompile

> **Gemini overlay assurance:** verify the actual different-family reviewer before recording `review_independence: cross-family`; `acceptance_status: accepted` requires a positive disposition and the workflow's evidence closure. Negative, unavailable and budget-stop outcomes grant no phase acceptance; same-family responses retain the base provisional contract.

Autonomously improve the paper at: **$ARGUMENTS**

## Context

This skill is designed to run **after** Workflow 3 (`/paper-plan` → `/paper-figure` → `/paper-write` → `/paper-compile`). It takes a compiled paper and iteratively improves it through external LLM review.

Unlike `/auto-review-loop` (which iterates on **research** — running experiments, collecting data, rewriting narrative), this skill iterates on **paper writing quality** — fixing theoretical inconsistencies, softening overclaims, adding missing content, and improving presentation.

## Constants

- **MAX_ROUNDS = 2** — Two rounds of review→fix→recompile. Empirically, Round 1 catches structural issues (4→6/10), Round 2 catches remaining presentation issues (6→7/10). Diminishing returns beyond 2 rounds for writing-only improvements.
- **REVIEWER_MODEL = `gemini-review`** — Gemini reviewer invoked through the local `gemini-review` MCP bridge. Set `GEMINI_REVIEW_MODEL` if you need a specific Gemini model override.
- **REVIEW_LOG = `PAPER_IMPROVEMENT_LOG.md`** — Cumulative log of all rounds, stored in paper directory.
- **HUMAN_CHECKPOINT = false** — When `true`, pause after each round's review and present score + weaknesses to the user. The user can approve fixes, provide custom modification instructions, skip specific fixes, or stop early. When `false` (default), runs fully autonomously.

> 💡 Override: `/auto-paper-improvement-loop "paper/" — human checkpoint: true`

## Inputs

1. **Compiled paper** — `paper/main.pdf` + LaTeX source files
2. **All section `.tex` files** — concatenated for review prompt

## State Persistence (Compact Recovery)

If the context window fills up mid-loop, Codex auto-compacts. To recover, this skill writes `PAPER_IMPROVEMENT_STATE.json` after each round:

```json
{
  "current_round": 1,
  "thread_id": "019ce736-...",
  "last_score": 6,
  "status": "in_progress",
  "timestamp": "2026-03-13T21:00:00"
}
```

**On startup**: if `PAPER_IMPROVEMENT_STATE.json` exists with `"status": "in_progress"` AND `timestamp` is within 24 hours, read it + `PAPER_IMPROVEMENT_LOG.md` to recover context, then resume from the next round. Otherwise (file absent, `"status": "completed"`, or older than 24 hours), start fresh.

**After each round**: overwrite the state file. **On completion**: set `"status": "completed"`.

## Workflow

### Step 0: Preserve Original

```bash
cp paper/main.pdf paper/main_round0_original.pdf
```

### Step 1: Collect Paper Text

Concatenate all section files into a single text block for the review prompt:

```bash
# Collect all sections in order
for f in paper/sections/*.tex; do
    echo "% === $(basename $f) ==="
    cat "$f"
done > /tmp/paper_full_text.txt
```

### Step 2: Round 1 Review

Send the full paper text to Gemini review:

```
mcp__gemini-review__review_start:
  prompt: |
    You are reviewing a [VENUE] paper. Please provide a detailed, structured review.

    Judge claim calibration in BOTH directions. Recommend narrowing only when the
    current scope or modality exceeds the evidence; do not ask for extra hedges
    around a supported result. Flag stacked hedges, self-defence ("we do not
    claim"), instruction confessions ("we do not address X"), and generic caveats
    outside Limitations as writing defects to remove. Tone fixes must never alter
    facts, negation, modality, scope, comparison direction, or numbers.
    Preserve the original research question and prespecified primary outcomes.
    Report material null findings and regressions beside the claims they qualify.
    Distinguish a supported claim, an unsupported claim and evidence against it;
    no unfavorable result is a writing defect merely because of its sign.
    Retrospective reframing must be labeled exploratory and cannot redefine the
    original success criterion. Explain a tradeoff only when the evidence supports
    it. Keep generic caveats in Limitations; claim-defining exceptions remain with
    the affected claim. Never hide material unfavorable evidence or select a
    favorable secondary metric as though it had always been the primary target.

    ## Full Paper Text:
    [paste concatenated sections]

    ## Review Instructions
    Please act as a senior ML reviewer ([VENUE] level). Provide:
    1. **Overall Score** (1-10, where 6 = weak accept, 7 = accept)
    2. **Summary** (2-3 sentences)
    3. **Strengths** (bullet list, ranked)
    4. **Weaknesses** (bullet list, ranked: CRITICAL > MAJOR > MINOR)
    5. **For each CRITICAL/MAJOR weakness**: A specific, actionable fix
    6. **Missing References** (if any)
    7. **Verdict**: Ready for submission? Yes / Almost / No

    Focus on: theoretical rigor, claims vs evidence alignment, writing clarity,
    self-containedness, notation consistency.
```

After this start call, immediately save the returned `jobId` and poll `mcp__gemini-review__review_status` with a bounded `waitSeconds` until `done=true`. Treat the completed status payload's `response` as the reviewer output, and save the completed `threadId` for any follow-up round.

Save the returned `jobId`, poll `mcp__gemini-review__review_status` until `done=true`, then save the completed `threadId` for Round 2.

### Step 2b: Human Checkpoint (if enabled)

**Skip if `HUMAN_CHECKPOINT = false`.**

Present the review results and wait for user input:

```
📋 Round 1 review complete.

Score: X/10 — [verdict]
Key weaknesses (by severity):
1. [CRITICAL] ...
2. [MAJOR] ...
3. [MINOR] ...

Reply "go" to implement all fixes, give custom instructions, "skip 2" to skip specific fixes, or "stop" to end.
```

Parse user response same as `/auto-review-loop`: approve / custom instructions / skip / stop.

### Step 3: Implement Round 1 Fixes

Parse the review and implement fixes by severity:

**Priority order:**
1. CRITICAL fixes (assumption mismatches, internal contradictions)
2. MAJOR fixes (overclaims, missing content, notation issues)
3. MINOR fixes (if time permits)

**Before applying any fix:** calibrate claims to evidence and state them
directly; generic caveats belong in Limitations only; writing instructions are
never manuscript content; tone edits never change what the paper knows.

**Common fix patterns:**

| Issue | Fix Pattern |
|-------|-------------|
| Assumption-model mismatch | Rewrite assumption to match the model, add formal proposition bridging the gap |
| Genuine overclaim | Narrow the claim itself to the supported scope/modality — never substitute a softer-sounding synonym for fixing scope, comparison, or aggregation |
| Supported claim wrapped in caution | Remove the redundant hedges; keep any scope qualifier that makes the claim true |
| Scattered generic caveats | Consolidate into Limitations and delete the duplicates |
| Unsupported primary claim or material regression | Report the original primary outcome and its implications beside the claim. Keep secondary gains exploratory; narrow unsupported scope and explain only evidenced tradeoffs. Preserve all material evidence |
| Experiment whose role is unclear | Identify the question, assumption, alternative or boundary it tests. Preserve material null/negative results; shorten unrelated detail |
| Missing metrics | Add quantitative table with honest parameter counts and caveats |
| Theorem not self-contained | Add "Interpretation" paragraph listing all dependencies |
| Notation confusion | Rename conflicting symbols globally, add Notation paragraph |
| Missing references | Add to `references.bib`, cite in appropriate locations |
| Theory-practice gap | Explicitly frame theory as idealized; add synthetic validation subsection |

### Step 4: Recompile Round 1

```bash
cd paper && latexmk -C && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
cp main.pdf main_round1.pdf
```

Verify: 0 undefined references, 0 undefined citations.

