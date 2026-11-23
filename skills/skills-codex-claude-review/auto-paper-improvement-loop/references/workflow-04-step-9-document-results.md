<!-- EI-WORKFLOW-REFERENCE -->

# Step 9: Document Results

Read this file when the workflow reaches Step 9: Document Results through Review Tracing. In commands and examples, interpret relative skill paths from the entrypoint directory.

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
<summary>Claude Review (Round 1)</summary>

[Full raw review text, verbatim]

</details>

### Fixes Implemented
1. [Fix description]
2. [Fix description]
...

## Round 2 Review & Fixes

<details>
<summary>Claude Review (Round 2)</summary>

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

## Key Rules

- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.

- **Preserve all PDF versions** — user needs to compare progression
- **Save FULL raw review text** — do not summarize or truncate Claude responses
- **Reviewer independence (Round 2+)**: when `REVIEWER_BIAS_GUARD = true` (default), use a **fresh** `mcp__claude-review__review_start` reviewer for every review round; never use stale reviewer continuation and never include "since last round" / fix summaries in the prompt. See the Reviewer Independence Protocol section above.
- **Always recompile after fixes** — verify 0 errors before proceeding
- **Do not fabricate experimental results** — synthetic validation must describe methodology, not invent numbers
- **Respect the paper's claims** — narrow genuine overclaims rather than adding unsupported new claims, and state supported claims directly rather than wrapping them in fresh hedges
- **Global consistency** — when renaming notation or changing a claim's scope, keep every restatement semantically consistent across ALL files (abstract, intro, method, experiments, theory sections, conclusion, tables, figure captions); consistency means matching scope, not copying disclaimer sentences everywhere
- **Edit-whitelist rejections are LOGGED, not silently dropped** — when `EDIT_WHITELIST` is set and an edit is rejected for a path or forbidden-operation violation, the rejection MUST be appended to `PAPER_IMPROVEMENT_LOG.md` with file, reason, offending pattern, and the original reviewer concern. The loop reports a rejection summary at the end of every round (and in the checkpoint, if `HUMAN_CHECKPOINT = true`). Never silently swallow a whitelist rejection — the audit trail is the whole point of the parameter.

## Typical Score Progression

Based on end-to-end testing on a real theory-paper run:

| Round | Score | Key Improvements |
|-------|-------|-----------------|
| Round 0 | 4/10 (content) | Baseline: assumption-model mismatch, overclaims, notation issues |
| Round 1 | 6/10 (content) | Fixed assumptions, softened claims, added interpretation, renamed notation |
| Round 2 | 7/10 (content) | Added synthetic validation, formal truncation proposition, stronger limitations |
| Round 3 | 5→8.5/10 (format) | Removed hero fig, appendix, compressed conclusion, fixed overfull hbox |

**+4.5 points across 3 rounds** (2 content + 1 format) is typical for a well-structured but rough first draft. Final state at submission: clean overfull-hbox count and venue-format-compliant length.

## Review Tracing

After each `mcp__claude-review__review_start`, `mcp__claude-review__review_reply_start`, or adversarial reviewer call, save the trace following `../shared-references/review-tracing.md`. Write files directly to `.ei/traces/auto-paper-improvement-loop/<date>_run<NN>/`. Respect the `--- trace:` parameter when present (default: `full`).
