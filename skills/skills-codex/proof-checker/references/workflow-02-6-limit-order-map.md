<!-- EI-WORKFLOW-REFERENCE -->

# 6. Limit-Order Map

Read this file when the workflow reaches 6. Limit-Order Map through Phase 4: Audit Report Generation. In commands and examples, interpret relative skill paths from the entrypoint directory.

#### 6. Limit-Order Map
Track every asymptotic statement's **limit order and uniformity scope**:
```
h_act = Θ(κ^α)  [as κ→0, uniform in π on compact subsets of Π_K, for fixed K]
τ_act ~ (b/a)n   [as n→∞, for fixed κ,K,π with x_K ≪ 1]
```
Flag any statement where limit order is ambiguous or uniformity is unclear.

### Phase 1: First Review (Codex GPT-6-Astra ultra)

Submit the **complete proof content** with the following **mandatory reviewer checklist** in the prompt:

```text
spawn_agent:
  model: gpt-6-astra
  reasoning_effort: ultra
  message: |
    You are performing a rigorous mathematical proof review. For EVERY theorem,
    lemma, and proposition, check ALL of the following:

    ## MANDATORY CHECKS

    A. DEFINITIONS: List any symbol whose meaning is ambiguous or changes.
    B. HYPOTHESIS DISCHARGE: For each lemma/theorem APPLICATION (not statement),
       list each hypothesis and whether it was verified, with location.
    C. INEQUALITY AUDIT: For each inequality chain, verify direction, missing
       absolute values, missing conditions (convexity, PSD, integrability).
    D. INTERCHANGE AUDIT: Flag every limit/derivative/expectation/integral
       interchange. State which theorem justifies it (DCT/MCT/Fubini/Leibniz)
       and which conditions are verified/missing.
    E. PROBABILITY MODE: Track whether claims are a.s./in prob./in expectation/
       w.h.p. Ensure transitions are justified.
    F. UNIFORMITY & CONSTANTS: For every O(·), o(·), Θ(·), ≲, state whether
       it is uniform over all parameters. List hidden parameter dependence.
    G. EDGE/DEGENERATE CASES: Attempt to break each key lemma with a 1D,
       low-rank, or extreme-parameter construction.
    H. DEPENDENCY CONSISTENCY: Detect cycles or forward references to unproven
       results.

    ## OUTPUT FORMAT (per issue)
    For each issue found, provide:
    - id: sequential number
    - status: INVALID / UNJUSTIFIED / UNDERSTATED / OVERSTATED / UNCLEAR
    - impact: GLOBAL / LOCAL / COSMETIC
    - category: [from taxonomy]
    - location: section/equation/line
    - statement: what the proof claims
    - why_invalid: why this is wrong or unjustified
    - counterexample: YES (describe) / NO / CANDIDATE (describe attempt)
    - affects: which downstream results break if this is wrong
    - minimal_fix: how to fix it

    [FULL PROOF CONTENT HERE]
```

**Save the reviewer `agent_id`.** Parse into structured issue list. Write to `PROOF_AUDIT.md`.

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

### Phase 3: Re-Review (Codex GPT-6-Astra ultra)

Launch a fresh reviewer agent for the next review round. Do not use `send_input` here; proof-checker keeps each round independent. Request the same mandatory checklist.

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
For any fix that resolved a FATAL or CRITICAL issue, submit the **fixed section alone** (without showing the previous critique) to a **fresh Codex thread**:

```text
spawn_agent:
  model: gpt-6-astra
  reasoning_effort: ultra
  message: |
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

### Phase 3.9: Unrecoverable Proof Protocol

If acceptance gate is not met after MAX_REVIEW_ROUNDS, output a **Proof Unrecoverable Report**:
1. Minimal set of blocking FATAL/CRITICAL issues that could not be resolved
2. Salvage options ranked: (a) weaken claim, (b) strengthen assumptions, (c) add missing lemmas, (d) restructure argument
3. Which parts of the proof are likely still reusable
4. Recommended next steps for the author

Do NOT silently declare success. The report must be honest.

### Phase 4: Audit Report Generation

Generate `proof_audit_report.tex` with:

1. **Overview table**: All issues with two-axis severity, category, fix strategy, status
2. **Before/After logic chain**: Red (BEFORE) → Green (AFTER) comparison
3. **For each fix**: original proof → why wrong → counterexample (if any) → complete derivation → remaining subtleties
4. **Proof-obligation diff**: What was unverified before, what is verified now
5. **Summary**: Now proven / still assumed / open problems
6. **Colored boxes**: BEFORE (red), AFTER (green), WHY WRONG (orange), KEY INSIGHT (blue), WARNING (yellow)

Compile: `pdflatex proof_audit_report.tex && pdflatex proof_audit_report.tex`

