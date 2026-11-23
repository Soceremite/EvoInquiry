<!-- EI-WORKFLOW-REFERENCE -->

# Step 5: Round 2 Review

Read this file when the workflow reaches Step 5: Round 2 Review through Key Rules. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Step 5: Round 2 Review

Start a **fresh** `mcp__gemini-review__review_start` — do not reuse the Round 1
thread, do not send fix summaries. The reviewer re-reads the recompiled paper
cold; executor notes are not evidence, and "since your last review, we
implemented..." is exactly the self-report path that lets fixes be graded on
their description instead of their substance:

```
mcp__gemini-review__review_start:
  prompt: |
    You are reviewing a [VENUE] paper (Round 2 — fresh read of the current
    manuscript; judge only what is on the page).

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

    [full current paper text]

    Please provide the same structured format:
    Score, Summary, Strengths, Weaknesses, Actionable fixes, Verdict.
```

After this start call, immediately save the returned `jobId` and poll `mcp__gemini-review__review_status` with a bounded `waitSeconds` until `done=true`. Treat the completed status payload's `response` as the reviewer output, and save the completed `threadId` for any follow-up round.

### Step 5b: Human Checkpoint (if enabled)

**Skip if `HUMAN_CHECKPOINT = false`.** Same as Step 2b — present Round 2 review, wait for user input.

### Step 6: Implement Round 2 Fixes

Same process as Step 3. Typical Round 2 fixes:
- Add controlled synthetic experiments validating theory
- Re-check calibration in both directions: narrow genuine overclaims, state
  supported claims directly, consolidate scattered generic caveats into
  Limitations — and do not re-soften claims the evidence already supports
- Formalize informal arguments (e.g., truncation → formal proposition)
- Make Limitations more specific only when a material limit is missing

### Step 7: Recompile Round 2

```bash
cd paper && latexmk -C && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
cp main.pdf main_round2.pdf
```

### Step 8: Format Check

After the final recompilation, run a format compliance check:

```bash
# 1. Page count vs venue limit
PAGES=$(pdfinfo paper/main.pdf | grep Pages | awk '{print $2}')
echo "Pages: $PAGES (limit: 9 main body for ICLR/NeurIPS)"

# 2. Overfull hbox warnings (content exceeding margins)
OVERFULL=$(grep -c "Overfull" paper/main.log 2>/dev/null || echo 0)
echo "Overfull hbox warnings: $OVERFULL"
grep "Overfull" paper/main.log 2>/dev/null | head -10

# 3. Underfull hbox warnings (loose spacing)
UNDERFULL=$(grep -c "Underfull" paper/main.log 2>/dev/null || echo 0)
echo "Underfull hbox warnings: $UNDERFULL"

# 4. Bad boxes summary
grep -c "badness" paper/main.log 2>/dev/null || echo "0 badness warnings"
```

**Auto-fix patterns:**

| Issue | Fix |
|-------|-----|
| Overfull hbox in equation | Wrap in `\resizebox` or split with `\split`/`aligned` |
| Overfull hbox in table | Reduce font (`\small`/`\footnotesize`) or use `\resizebox{\linewidth}{!}{...}` |
| Overfull hbox in text | Rephrase sentence or add `\allowbreak` / `\-` hints |
| Over page limit | Move content to appendix, compress tables, reduce figure sizes |
| Underfull hbox (loose) | Rephrase for better line filling or add `\looseness=-1` |

If any overfull hbox > 10pt is found, fix it and recompile before documenting.

### Step 9: Document Results

Create `PAPER_IMPROVEMENT_LOG.md` in the paper directory:

```markdown
# Paper Improvement Log

## Score Progression

| Round | Score | Verdict | Key Changes |
|-------|-------|---------|-------------|
| Round 0 (original) | X/10 | No/Almost/Yes | Baseline |
| Round 1 | Y/10 | No/Almost/Yes | [summary of fixes] |
| Round 2 | Z/10 | No/Almost/Yes | [summary of fixes] |

## Round 1 Review & Fixes

<details>
<summary>Gemini Review (Round 1)</summary>

[Full raw review text, verbatim]

</details>

### Fixes Implemented
1. [Fix description]
2. [Fix description]
...

## Round 2 Review & Fixes

<details>
<summary>Gemini Review (Round 2)</summary>

[Full raw review text, verbatim]

</details>

### Fixes Implemented
1. [Fix description]
2. [Fix description]
...

## PDFs
- `main_round0_original.pdf` — Original generated paper
- `main_round1.pdf` — After Round 1 fixes
- `main_round2.pdf` — Final version after Round 2 fixes
```

### Step 9: Summary

Report to user:
- Score progression table
- Number of CRITICAL/MAJOR/MINOR issues fixed per round
- Final page count
- Remaining issues (if any)

### Feishu Notification (if configured)

After each round's review AND at final completion, check `~/.codex/feishu.json`:
- **After each round**: Send `review_scored` — "Round N: X/10 — [key changes]"
- **After final round**: Send `pipeline_done` — score progression table + final page count
- If config absent or mode `"off"`: skip entirely (no-op)

## Output

```
paper/
├── main_round0_original.pdf    # Original
├── main_round1.pdf             # After Round 1
├── main_round2.pdf             # After Round 2 (final)
├── main.pdf                    # = main_round2.pdf
└── PAPER_IMPROVEMENT_LOG.md    # Full review log with scores
```

## Output Protocols

> Follow these shared protocols for all output files:
> - **[Output Versioning Protocol](../../shared-references/output-versioning.md)** — write timestamped file first, then copy to fixed name
> - **[Output Manifest Protocol](../../shared-references/output-manifest.md)** — log every output to MANIFEST.md
> - **[Output Language Protocol](../../shared-references/output-language.md)** — respect the project's language setting

## Key Rules

- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.

- **Preserve all PDF versions** — user needs to compare progression
- **Save FULL raw review text** — do not summarize or truncate Gemini reviewer responses
- **Use `mcp__gemini-review__review_reply_start` plus `mcp__gemini-review__review_status`** for Round 2 to maintain conversation context
- **Always recompile after fixes** — verify 0 errors before proceeding
- **Do not fabricate experimental results** — synthetic validation must describe methodology, not invent numbers
- **Respect the paper's claims** — narrow genuine overclaims rather than adding unsupported new claims, and state supported claims directly rather than wrapping them in fresh hedges
- **Global consistency** — when renaming notation or changing a claim's scope, keep every restatement semantically consistent across ALL files (abstract, intro, method, experiments, theory sections, conclusion, tables, figure captions); consistency means matching scope, not copying disclaimer sentences everywhere

