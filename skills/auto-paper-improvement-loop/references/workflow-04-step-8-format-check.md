<!-- EI-WORKFLOW-REFERENCE -->

# Step 8: Format Check

Read this file when the workflow reaches Step 8: Format Check through Review Tracing. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Step 8: Format Check

After the final recompilation, run a **location-aware** format compliance check.

```bash
# If the log lacks file/line data, rerun the final compile once with -file-line-error.
cd paper && latexmk -pdf -file-line-error -interaction=nonstopmode -halt-on-error main.tex
```

```bash
# 1. Page count vs venue limit
PAGES=$(pdfinfo paper/main.pdf | grep Pages | awk '{print $2}')
echo "Pages: $PAGES (limit: 9 main body for ICLR/NeurIPS)"

# 2. Duplicate labels: HARD BLOCK
DUP_LABELS=$(grep -Rho "\\\\label{[^}]*}" paper/main.tex paper/sections 2>/dev/null | sort | uniq -d || true)
if [ -n "$DUP_LABELS" ]; then
    echo "Duplicate labels found (BLOCKING):"
    echo "$DUP_LABELS"
fi

# 3. Overfull warnings with location classification
OVERFULLS=$(grep -n "Overfull \\\\hbox" paper/main.log 2>/dev/null || true)

# Main body = source files before \appendix in main.tex.
# Appendix = source files after \appendix, or files whose path contains "appendix".
# Bibliography = paper.bbl, references.bib, or bibliography-generated output.
MAIN_BODY_OVERFULL=$(echo "$OVERFULLS" | grep -v -E 'appendix|paper\.bbl|references\.bib' || true)
APPENDIX_OVERFULL=$(echo "$OVERFULLS" | grep -E 'appendix' || true)
BIB_OVERFULL=$(echo "$OVERFULLS" | grep -E 'paper\.bbl|references\.bib' || true)

echo "Main-body overfulls (any size BLOCKS):"
echo "$MAIN_BODY_OVERFULL"
echo "Appendix overfulls (>10pt blocks):"
echo "$APPENDIX_OVERFULL"
echo "Bibliography overfulls (>20pt blocks):"
echo "$BIB_OVERFULL"
```

**Stop criteria:**
- Any duplicate label blocks completion.
- Any overfull in the main body blocks completion, regardless of size.
- Appendix overfulls block completion only if they exceed 10pt or are visibly clipping.
- Bibliography overfulls block completion only if they exceed 20pt or are visibly clipping.
- Underfull hboxes remain warnings unless they create obvious layout damage.

**Auto-fix patterns (location-aware):**

| Issue | Fix |
|-------|-----|
| Main-body overfull in equation | Split with `aligned` / `split` / `multline`, or shorten notation |
| Main-body overfull in table | Reduce font, resize table, or break table across rows |
| Main-body overfull in text | Rephrase; do not hide it with global `\sloppy` |
| Appendix overfull ≤ 10pt | Warn only unless visibly clipping |
| Appendix overfull > 10pt | Apply the same fix if the spill is visible |
| Bibliography overfull ≤ 20pt | Warn only unless caused by malformed entry or clipping |
| Bibliography overfull > 20pt | Fix malformed entry, URL, or DOI formatting |
| Over page limit | Move content to appendix, compress tables, reduce figure sizes |

**Location-aware interpretation:**
- Classify by the source file reported in the `-file-line-error` log.
- If a warning cannot be classified, treat it as main body and fix it.

**Empirical motivation:** in a real submission run, dozens of overfull hbox warnings (the largest well over 100pt in an appendix proof) survived multiple improvement rounds because the previous blanket "overfull > 10pt blocks" rule was too lax and treated all locations equally.

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
<summary>GPT-6-Astra xhigh Review (Round 1)</summary>

[Full raw review text, verbatim]

</details>

### Fixes Implemented
1. [Fix description]
2. [Fix description]
...

## Round 2 Review & Fixes

<details>
<summary>GPT-6-Astra xhigh Review (Round 2)</summary>

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

After each round's review AND at final completion, check `~/.claude/feishu.json`:
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
- **Save FULL raw review text** — do not summarize or truncate GPT-6-Astra responses
- **Reviewer independence (Round 2+)**: when `REVIEWER_BIAS_GUARD = true` (default), use a **fresh** `mcp__codex__codex` thread for every review round; never use `mcp__codex__codex-reply` and never include "since last round" / fix summaries in the prompt. See the Reviewer Independence Protocol section above.
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

After each `mcp__codex__codex` or `mcp__codex__codex-reply` reviewer call, save the trace following `shared-references/review-tracing.md` (Policy C — forensic; never silently skip). Use `save_trace.sh` (resolved per the chain in `shared-references/integration-contract.md` §2) or write files directly to `.ei/traces/<skill>/<date>_run<NN>/`. Respect the `--- trace:` parameter (default: `full`).
