<!-- EI-WORKFLOW-REFERENCE -->

# Phase 1 addendum — `--deep-fix` opt-in

Read this file when the workflow reaches Phase 1 addendum — `--deep-fix` opt-in through Regression proof-audit. In commands and examples, interpret relative skill paths from the entrypoint directory.

#### Phase 1 addendum — `--deep-fix` opt-in

If the user passed `--deep-fix` on invocation, append the following block to the reviewer prompt **after** the OUTPUT FORMAT block above (do **not** modify the original block; the new fields are additive). Default invocations skip this block entirely and emit the original output schema unchanged.

```
    ## DEEP-FIX OUTPUT (opt-in, only when --deep-fix is set)

    For EACH issue listed above, additionally provide a `deep_fix_plan`
    that is repair-grade — sufficient for an executor to apply the fix
    in one Edit pass without spawning a follow-up review thread:

    - issue_id: same as the issue id above
    - corrected_statement: the theorem/lemma statement as it should
      read after the fix, with explicit quantifiers, regime conditions,
      and uniformity scope (LaTeX, paste-ready)
    - changed_equations: list of {before: <LaTeX>, after: <LaTeX>}
      pairs for each equation that needs replacement
    - downstream_labels: list of \label{...} keys whose statements or
      proofs depend on this fix and must be re-checked or rewritten
    - minimal_tex_patch_plan: ordered list of concrete edits, each as
      {file: <path>, anchor_old: <unique LaTeX snippet to find>,
       replacement_new: <LaTeX to insert>}; the executor will pass
      these directly to its file-editing tool
    - closure_tests: 2-5 sanity checks the executor must run after
      applying the fix (e.g., "verify constant_dependence_diff matches
      computed value", "limit case γ→0 reduces to identity",
      "dimension count matches before/after")

    ## ALGEBRA / TYPE SANITY PASS (opt-in, only when --deep-fix is set)

    If any issue invokes Schur test, Young's inequality, Cauchy-Schwarz,
    Hölder, quadratic form, operator norm, or power counting, the
    deep_fix_plan for that issue MUST also include an `algebra_sanity`
    object:

    - dimension_table: map of {symbol: type_signature}, e.g.
      {"K(i,α)": "scalar ≥ 0",
       "‖K‖_{2→2}": "scalar ≥ 0",
       "Σ_i V_i^rem": "scalar quadratic in w"}
    - power_count: number of times each operator-norm or Schur factor
      appears on each side; flag mismatch as INVALID
    - zero_coupling_check: evaluate the expression at γ=0 (or the
      analogous degenerate point); confirm it reduces to the expected
      identity / vanishing case
    - constant_dependence_diff: list of constants whose dependence on
      (d, K, n, ...) changes between BEFORE and AFTER, with the new
      explicit dependence written out

    Be precise. The executor will apply this plan literally; vague
    prose ("strengthen the bound", "redo the Schur step") is not
    acceptable in deep-fix mode. If you cannot produce a precise plan
    for an issue, omit that issue's deep-fix block and signal the
    deep-fix path is unavailable — do NOT emit a vague plan, and do
    NOT add a deep-fix-only category (e.g. UNCLEAR_DEEP_FIX) into the
    standard issue list, since that contaminates default-call output.
```
  A verdict-bearing manual response MUST begin with
  `Reviewer-Model: <exact-model-id>` — pass the model THIS session is actually
  running as in `executor_model`. Missing, unknown, or same-family identity
  cannot acquit; emit `REVIEW_UNAVAILABLE` rather than guessing. If the executor
  model cannot be named, manual review's cross-family claim is unprovable — say
  so in the report instead of asserting it.


**Save the threadId.** Parse into structured issue list. Write to `PROOF_AUDIT.md`.

### Phase 1.5: Counterexample Red Team

For each CRITICAL or MAJOR issue, and for every key lemma that introduces:
- a new inequality bound
- an identifiability/uniqueness claim
- a curvature/PSD/strong convexity assertion
- a uniform-in-parameter claim
- a convergence mode upgrade (pointwise → uniform, in prob → w.h.p.)

Systematically attempt to construct counterexamples using:

| Strategy | Description |
|----------|-------------|
| **Dimensional collapse** | Set d=1 or 2, K=2, n small |
| **Degeneracy** | Singular covariance, tiny weight, overlapping means, identical components |
| **Extremal distributions** | Two-point ±a, bounded non-subGaussian, heavy tails |
| **Adversarial parameter scaling** | Pick parameters making neglected terms dominate |
| **Numeric falsification** | Translate lemma to a function, brute-force optimize over small domain |

**Rule**: Label "counterexample found" ONLY if algebraically verified. Otherwise log as "candidate counterexample — needs verification."

Record all attempts (successful or not) in `PROOF_AUDIT.md`.

### Phase 2: Fix Implementation

For each issue, ordered by severity (FATAL → CRITICAL → MAJOR → MINOR):

#### Step 2a: Choose fix strategy
For each issue, explicitly choose one of:
- **ADD_DERIVATION**: Write missing proof steps
- **STRENGTHEN_ASSUMPTION**: Add conditions to theorem statement
- **WEAKEN_CLAIM**: Reduce conclusion scope
- **ADD_REFERENCE**: Cite known result + verify its conditions apply

Log this choice — it is a scope-changing decision when it alters theorem statements.

#### Step 2b: Derive the fix mathematically
- Complete mathematical derivation, not just a claim
- If new proposition/lemma needed, write in full theorem-proof style

#### Step 2c: Implement in LaTeX
- Edit the `.tex` file
- Preserve existing `\label` references where possible

#### Step 2d: Record the fix
```markdown
### Fix N: [SHORT TITLE]
**Issue**: [id] [CATEGORY] — [description]
**Severity**: FATAL / CRITICAL / MAJOR / MINOR
**Status**: INVALID / UNJUSTIFIED / UNDERSTATED / OVERSTATED
**Impact**: GLOBAL / LOCAL / COSMETIC
**Fix strategy**: ADD_DERIVATION / STRENGTHEN_ASSUMPTION / WEAKEN_CLAIM / ADD_REFERENCE
**Location**: Section X, Lines Y-Z

**BEFORE**: [what the proof originally did]
**WHY WRONG**: [mathematical problem, with counterexample if applicable]
**AFTER**: [what the fix does]
**KEY EQUATION**: [central new equation]
**PROOF OBLIGATIONS ADDED**: [new conditions/lemmas introduced]
**DOWNSTREAM EFFECTS**: [which results now need re-checking]
```

#### Step 2e: Compile check
```bash
pdflatex -interaction=nonstopmode <file>.tex 2>&1 | grep -E "Error|Warning|undefined"
```

### Phase 3: Re-Review (reviewer backend, ultra reasoning)

Continue with the selected backend. For `codex`, use `mcp__codex__codex-reply` with the saved threadId. For `manual`, use `mcp__manual_review__review_reply` with the saved threadId. Include fix summaries. Request the same mandatory checklist.

Check acceptance gate. If not met, repeat Phases 2-3 (up to MAX_REVIEW_ROUNDS).

### Phase 3.5: Global Closure & Independent Verification

#### Global closure checks
After all fixes, verify the proof as a whole:
- **Statement–conclusion match**: Does the proof end with EXACTLY what the theorem claims (quantifiers, constants, uniformity)?
- **All obligations discharged**: Every node in the obligation DAG is proven or explicitly assumed (and the theorem statement includes it).
- **Case analysis coverage**: Cases partition the domain AND include boundary/degenerate cases.
- **Induction correctness** (if applicable): Base case, inductive step, correct use of IH, induction measure strictly decreases.
- **WLOG reductions**: Each "without loss of generality" spawns a micro-claim proving the reduction is lossless.
- **No silent assumption strengthening**: Any fix that strengthened assumptions has propagated to the main theorem statement.

#### Independent second review for FATAL/CRITICAL fixes
For any fix that resolved a FATAL or CRITICAL issue, submit the **fixed section alone** (without showing the previous critique) to a **fresh reviewer thread** using the selected backend. Do NOT use a reply tool — this step must be blind.

*For codex:* start a fresh `mcp__codex__codex` thread.
*For manual:* start a fresh `mcp__manual_review__review` thread.

The blind review prompt:

```
[Codex:]
mcp__codex__codex:
  model: gpt-6-astra
  config: {"model_reasoning_effort": "ultra"}
  prompt: |
    Blind review of the following proof section. You have NOT seen any prior
    review or discussion. Check every step for correctness, hidden assumptions,
    illegal interchanges, and counterexamples.
    [FIXED SECTION ONLY]
```

If the blind reviewer finds new issues, re-enter Phase 2.

#### Regression proof-audit
After fixes, re-run:
- DAG acyclicity check (no new cycles introduced)
- Counterexample suite on all DOWNSTREAM lemmas of modified results
- Assumption-delta report: what became stronger/weaker due to fixes?

