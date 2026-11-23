<!-- EI-WORKFLOW-REFERENCE -->

# Step 4.5: Restatement Regression Test

Read this file when the workflow reaches Step 4.5: Restatement Regression Test through Step 7: Recompile Round 2. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Step 4.5: Restatement Regression Test

After every recompilation, rerun a theorem-statement consistency check so fix rounds cannot reintroduce appendix drift. **Run this after Step 4 and again after Step 7 before the final format check.**

**Scope**
- Compare only theorem/lemma/proposition/corollary statements, not proof bodies.
- Classify files by `main.tex` input order: files before `\appendix` are main body; files after `\appendix` are appendix.

**Normalized comparison logic**
- Strip comments, `\label{...}`, `\ref{...}`, `\eqref{...}`, `\cite...{...}`, and whitespace-only differences.
- Collapse formatting-only macros such as `\emph{}`, `\textbf{}`, `\textit{}`, `\mathrm{}`, `\mathbf{}`, `\mathcal{}`, and `\operatorname{}` to their contents.
- Preserve quantifiers, case splits, assumptions, and the literal names of defined objects.
- Compare by theorem label when available; otherwise compare by theorem type and order.
- Flag any change in hypotheses, case splits, quantifier order, or terminology (`stationary` vs `terminal`) as regression drift.

```bash
python3 - <<'PY'
import re
def normalize(s):
    s = re.sub(r'%.*', '', s)
    s = re.sub(r'\\label\{[^}]*\}', '', s)
    s = re.sub(r'\\(?:ref|eqref|cref|Cref|cite[a-zA-Z]*)\{[^}]*\}', '', s)
    s = re.sub(r'\\(?:emph|textbf|textit|mathrm|mathbf|mathsf|mathcal|operatorname)\{([^{}]*)\}', r'\1', s)
    s = re.sub(r'\\begin\{[^}]+\}|\\end\{[^}]+\}', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip().lower()
# Compare normalized theorem blocks from the current main-body files
# against their appendix restatements. Any mismatch blocks completion.
PY
```

**Empirical motivation:** in a real submission run, a key theorem had a multi-case split in the main text but a single-case statement in the appendix; a key variable was named one way in main and another in appendix. These drifted multiple times across fix rounds because no automated check caught regression.

**Optional deeper check: `/proof-checker --restatement-check`**

The inline Python check above is the default and is sufficient for routine main-vs-appendix consistency. For broader coverage, you may additionally invoke `/proof-checker --restatement-check` (added in PR #189), which extends the comparison to:

- Restatements in summary tables, abstract, "Key Contributions" lists, and discussion sections (not just main vs appendix).
- Six named drift signatures classified by reviewer: `conditional_loss`, `scope_change`, `quantifier_loss`, `regime_envelope_change`, `constant_change`, `variable_rename`.
- Structured findings emitted as `details.restatement_drift[]` in `PROOF_AUDIT.json`, suitable for downstream tooling or audit trails.

This is advisory only — the inline Step 4.5 check remains the default and continues to run on every loop round. Consider invoking `/proof-checker --restatement-check` when (a) you suspect cross-location drift outside the main↔appendix axis (e.g., abstract overclaim relative to theorem statement), or (b) you want reviewer-graded drift signatures rather than raw string mismatches. Running both is supported and they are independent: the inline check fails fast on string drift, the proof-checker pass surfaces semantic-class drift.

### Step 5: Round 2 Review

If `REVIEWER_BIAS_GUARD = true` (default), use a **fresh** `mcp__codex__codex` thread for Round 2. Do not reuse the Round 1 threadId for prompting. Save the returned threadId only for recovery bookkeeping.

```
mcp__codex__codex:
  model: gpt-6-astra
  config: {"model_reasoning_effort": "xhigh"}
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

If `REVIEWER_BIAS_GUARD = false` (legacy debugging only), use `mcp__codex__codex-reply` with the saved threadId; this is **not** the recommended path.

### Step 5.5: Kill Argument Exercise (theory / scope-heavy papers only)

Run this only if the paper is theory-heavy (≥5 `\begin{theorem}|\begin{lemma}|\begin{proposition}|\begin{corollary}` environments in the source) or has explicit scope/generality claims in title/abstract, and only on the final scheduled round (`current_round == MAX_ROUNDS`).

**Delegate to `/kill-argument`** — the canonical implementation lives at `skills/kill-argument/SKILL.md` (extracted in May 2026). This step does NOT re-implement the Attack-and-Adjudication prompt template; instead, invoke the skill and read its output:

```bash
# Invoke the canonical adversarial-review primitive on the current paper.
# /kill-argument runs two fresh-thread codex gpt-6-astra ultra calls and writes
# KILL_ARGUMENT.{md,json} into the paper directory. It is detect-only —
# it never edits the paper itself.
/kill-argument "$PAPER_DIR"

# Read the structured verdict.
KILL_VERDICT=$(jq -r '.verdict' "$PAPER_DIR/KILL_ARGUMENT.json")
KILL_REASON=$(jq -r '.reason_code' "$PAPER_DIR/KILL_ARGUMENT.json")
```

**Merge rule** (auto-loop's responsibility — `/kill-argument` itself is detect-only):

- Read `details.decomposed_points` from `KILL_ARGUMENT.json`.
- For each point with `verdict == "still_unresolved"` or `verdict == "partially_answered"` at `severity_if_unresolved == "critical"`:
  - Dedupe against the Round 2 weakness list by semantic overlap (~85% similarity threshold).
  - If novel, append it to the Step 6 fix list with the recommended_fix as the action description.
- If the adjudication shows the issue is `answered_by_current_text`, only downgrade an existing weakness item after verifying the cited file:line evidence yourself.
- Record both `KILL_ARGUMENT.md` and the merge decision in `PAPER_IMPROVEMENT_LOG.md`.
- If `HUMAN_CHECKPOINT = true`, include the merged findings in the checkpoint summary before asking the user to proceed.

This phase feeds directly into Step 6. The merged findings must land before the final recompile.

If `/kill-argument` returns `verdict: NOT_APPLICABLE` (paper isn't theory- or scope-heavy enough to need this check), skip Step 5.5 entirely and proceed to Step 6. If it returns `BLOCKED` or `ERROR`, log the reason in `PAPER_IMPROVEMENT_LOG.md` and proceed without merging — the loop should not stall on an adversarial check that cannot run.

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

