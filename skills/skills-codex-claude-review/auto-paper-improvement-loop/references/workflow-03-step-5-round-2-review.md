<!-- EI-WORKFLOW-REFERENCE -->

# Step 5: Round 2 Review

Read this file when the workflow reaches Step 5: Round 2 Review through Step 8: Format Check. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Step 5: Round 2 Review

If `REVIEWER_BIAS_GUARD = true` (default), use a **fresh** `mcp__claude-review__review_start` reviewer for Round 2. Do not ask the reviewer to reward the Round 1 fix summary for prompting. Save the returned threadId only for recovery bookkeeping.

```
mcp__claude-review__review_start:
  # the bridge grants the reviewer no tools by default; this prompt passes
  # artifact paths, so it has to ask for read-only access explicitly
  tools: "Read,Grep,Glob"
  prompt: |
    You are reviewing a [VENUE] paper. This is a fresh, zero-context review.

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
    Ignore any prior review rounds, prior fix lists, or executor explanations.
    Judge the paper only from the current LaTeX source and compiled PDF.

    ## Paper Files:
    - LaTeX source: [list all section .tex files]
    - Compiled PDF: paper/main.pdf
    - Figures: [list figure files]

    Read BOTH the LaTeX source (for content/logic) AND the compiled PDF (for visual presentation).

    ## Review Instructions
    Please act as a senior ML reviewer ([VENUE] level). Provide:
    1. **Overall Score** (1-10, where 6 = weak accept, 7 = accept)
    2. **Summary** (2-3 sentences)
    3. **Strengths** (bullet list, ranked)
    4. **Weaknesses** (bullet list, ranked: CRITICAL > MAJOR > MINOR)
    5. **For each CRITICAL/MAJOR weakness**: A specific, actionable fix
    6. **Missing References** (if any)
    7. **Visual Review** (from the PDF):
       - Figure quality: readable? labels legible? colors distinguishable in grayscale?
       - Figure-caption alignment: does each caption match its figure?
       - Layout: orphaned headers, awkward page breaks, figures far from references?
       - Table formatting: aligned columns, consistent decimals, bold for best results?
       - Visual consistency: same color scheme across all figures?
    8. **Verdict**: Ready for submission? Yes / Almost / No

    Focus on: theoretical rigor, claims vs evidence alignment, writing clarity,
    self-containedness, notation consistency, and visual presentation quality.
```

After this start call, immediately save the returned `jobId` and poll `mcp__claude-review__review_status` with a bounded `waitSeconds` until `done=true`. Treat the completed status payload's `response` as the reviewer output, and save the completed `threadId` for any follow-up round.

If `REVIEWER_BIAS_GUARD = false` (legacy debugging only), use `mcp__claude-review__review_reply_start` with the saved reviewer id; this is **not** the recommended path.

### Step 5.5: Kill Argument Exercise (theory / scope-heavy papers only)

Run this only if the paper is theory-heavy (≥5 `\begin{theorem}|\begin{lemma}|\begin{proposition}|\begin{corollary}` environments in the source) or has explicit scope/generality claims in title/abstract, and only on the final scheduled round (`current_round == MAX_ROUNDS`).

**Delegate to the `kill-argument` skill** (extracted in May 2026 as a standalone primitive). This step does NOT re-implement the Attack-and-Adjudication prompt template; instead, invoke the skill and read its output. The Codex-CLI form is to call the installed skill the same way you would call any other ARIS skill from the agent's tool list, then parse `KILL_ARGUMENT.json` from the paper directory.

**Merge rule** (auto-loop's responsibility — `kill-argument` itself is detect-only):

- Read `details.decomposed_points` from `KILL_ARGUMENT.json`.
- For each point with `verdict == "still_unresolved"` or `verdict == "partially_answered"` at `severity_if_unresolved == "critical"`:
  - Dedupe against the Round 2 weakness list by semantic overlap (~85% similarity threshold).
  - If novel, append it to the Step 6 fix list with the recommended_fix as the action description.
- If the adjudication shows the issue is `answered_by_current_text`, only downgrade an existing weakness item after verifying the cited file:line evidence yourself.
- Record both `KILL_ARGUMENT.md` and the merge decision in `PAPER_IMPROVEMENT_LOG.md`.
- If `HUMAN_CHECKPOINT = true`, include the merged findings in the checkpoint summary before asking the user to proceed.

This phase feeds directly into Step 6. The merged findings must land before the final recompile.

If kill-argument returns `verdict: NOT_APPLICABLE`, skip Step 5.5 entirely and proceed to Step 6. If it returns `BLOCKED` or `ERROR`, log the reason in `PAPER_IMPROVEMENT_LOG.md` and proceed without merging — the loop should not stall on an adversarial check that cannot run.

**Empirical motivation:** in a real submission run, after several rounds of standard improvement (score 7-8/10), the kill-argument exercise surfaced framing weaknesses that no prior review caught (e.g., a setting being mostly conditional rather than truly general, or a baseline being irrelevant to real systems). Author rebuttal forced explicit scope qualifications in abstract and discussion.

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

**Edit-whitelist gate (if set):** Same as Step 3 — if `EDIT_WHITELIST` is set, run the path + forbidden-operation checks before applying each proposed edit. Rejections are logged to `PAPER_IMPROVEMENT_LOG.md` under `## Rejected by edit_whitelist (Round 2)` and the loop continues. Surface a rejection summary at the end of the round.

### Step 7: Recompile Round 2

```bash
cd paper && latexmk -C && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
cp main.pdf main_round2.pdf
```

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

