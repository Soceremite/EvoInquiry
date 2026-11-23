<!-- EI-WORKFLOW-REFERENCE -->

# Step 2: Round 1 Review

Read this file when the workflow reaches Step 2: Round 1 Review through Step 4.5: Restatement Regression Test. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Step 2: Round 1 Review

Send the full paper text AND compiled PDF to GPT-6-Astra xhigh:

```text
spawn_agent:
  model: gpt-6-astra
  reasoning_effort: xhigh
  message: |
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
    self-containedness, notation consistency, AND visual presentation quality.
```

Save the agent_id for Round 2.

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

**Edit-whitelist gate (if set):** If `EDIT_WHITELIST` is set, before applying each proposed edit, check the target path against `allowed_paths` / `forbidden_paths` and the new-lines diff against `forbidden_operations` per the "Optional: Edit Whitelist" section. Rejections are logged to `PAPER_IMPROVEMENT_LOG.md` under `## Rejected by edit_whitelist (Round 1)` with file, reason (`path` or `operation`), the offending pattern, and the original reviewer concern. The loop continues with remaining edits — a rejection never aborts the round. Surface a rejection summary at the end of the round.

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
| Proof gap (theory papers) | Run `/proof-checker` if PROOF_AUDIT.md doesn't exist yet; fix FATAL/CRITICAL issues |
| Writing clutter / passive voice | Apply sciwrite 5-pass audit: clutter extraction → active voice → sentence architecture → keyword consistency → numerical integrity. See `paper-write` Step 5 |
| Number mismatch (paper vs results) | Run `/paper-claim-audit` if PAPER_CLAIM_AUDIT.md doesn't exist; fix any `number_mismatch` or `aggregation_mismatch` claims |
| Keyword inconsistency | The "Banana Rule": if Methods says "obese group", Results must not say "heavier group". Extract key terms, verify consistency across all sections |

### Step 4: Recompile Round 1

```bash
cd paper && latexmk -C && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
cp main.pdf main_round1.pdf
```

Verify: 0 undefined references, 0 undefined citations.

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

