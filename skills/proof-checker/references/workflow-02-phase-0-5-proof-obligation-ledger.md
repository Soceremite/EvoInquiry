<!-- EI-WORKFLOW-REFERENCE -->

# Phase 0.5: Proof-Obligation Ledger

Read this file when the workflow reaches Phase 0.5: Proof-Obligation Ledger through Phase 1: First Review (reviewer backend, ultra reasoning). In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 0.5: Proof-Obligation Ledger

> **Fan-out (Tier-aware) — build the ledger in parallel; never judge in
> parallel.** For a large multi-theorem paper, ledger *construction* is breadth
> over independent sections. **Tier 1** (Workflow): spawn one Claude subagent
> per section/theorem to extract that unit's symbols, assumptions, micro-claims,
> and local quantified statements, each returning a structured ledger fragment.
> **Tier 2**: the same subagents via the Agent tool. **Tier 3**: walk the
> sections sequentially. This follows
> [`shared-references/fan-out-pattern.md`](../../shared-references/fan-out-pattern.md).
>
> Two hard rules:
> 1. **The shards EXTRACT, they do not ADJUDICATE.** Building the ledger
>    (inventorying obligations, typing symbols, restating with explicit
>    quantifiers) is structural extraction. Whether a proof step is *valid* —
>    whether an obligation is actually discharged — is a Type-B correctness
>    verdict reserved for the cross-model jury in Phase 1 / Phase 3 (codex or
>    manual, `ultra`). A Claude shard MUST NOT mark a micro-claim "proved" or
>    "sound"; it only records the obligation and where the paper claims to
>    discharge it. See [`acceptance-gate.md`](../../shared-references/acceptance-gate.md)
>    — the loop may self-verify *that the ledger is complete*, never *that the
>    proofs are correct*.
>    - **This governs the ledger spec wording below.** Where the artifacts say
>      "WHERE each is verified", "or mark UNVERIFIED", or "where conditions are
>      proven", a shard records a **location pointer** (`file:line` the paper
>      claims discharge) — never its own judgment that the discharge is
>      mathematically valid. A shard's `UNVERIFIED` means *"the paper cites no
>      discharge location"*, NOT *"the shard checked the math and it fails"*.
>      Soundness is the jury's verdict, not the shard's.
>
> **Shard output** (extraction schema, per
> [`fan-out-pattern.md`](../../shared-references/fan-out-pattern.md)): each shard
> returns `{shard_id: "<section/theorem id>", entries: [...]}` — the typed
> ledger items (symbols, assumptions, micro-claims, canonical statements,
> limit-order facts) for that unit, each carrying its canonical id (e.g.
> `MC-17`, the symbol name) as `dedup_key`. Never prose-only; never a validity
> verdict field.
> 2. **Global artifacts are a barrier, computed on the merged ledger, not
>    per-shard.** The Dependency DAG and its cycle detection (incl. semantic
>    circularity), and cross-section symbol-type consistency, require the whole
>    paper in view. Merge all shard fragments first, then compute these on the
>    union — a per-shard DAG would miss exactly the cross-section cycles this
>    phase exists to catch.

Build formal accounting artifacts. Save to `PROOF_SKELETON.md`:

#### 1. Dependency DAG
Nodes = Definitions / Assumptions / Lemmas / Theorems. Edges = "uses". **Detect cycles** (including semantic circularity where Lemma A uses a corollary that quietly depends on A).

#### 2. Assumption Ledger
For each theorem/lemma, list every hypothesis with WHERE each is verified — i.e. the **location pointer** the paper claims discharges it (`file:line`), not a judgment that the discharge is valid; mark "UNVERIFIED" when the paper cites no discharge location (not when you believe the math fails — that is the jury's call). Track **usage-minimal assumption sets** — which assumptions were actually used vs merely stated.

#### 3. Typed Symbol Table
Each symbol must have a **type signature**:
```
κ : scalar ∈ (0,1), depends on (d, α_t, Σ, μ)
u* : vector ∈ ℝ^d, u* = C^{-1}m
B^even : matrix ∈ ℝ^{(L+1)×(L+1)}, symmetric PSD
Ψ_v : function ℝ → ℝ, analytic in (ζ,κ), parity determined by v
```
Flag any symbol whose meaning changes or whose type is inconsistent across uses.

#### 4. Canonical Quantified Statements
For each theorem/lemma, rewrite the statement with **explicit quantifiers, domains, and limit order**:
```
∀K ≥ 3, ∀π ∈ Π_K^{ms,∘} \ E_K, ∃κ_0 > 0 such that ∀κ ∈ (0, κ_0):
  h_act^{(K,π)} = Θ(κ^{α_K^act})  [uniform in π on compact subsets]
```
If you cannot restate a theorem this precisely, mark it **UNCLEAR — needs disambiguation**.

#### 5. Micro-Claim Inventory
Every nontrivial step becomes a numbered micro-claim in **sequent form**:
```
MC-17: Context: [Lemma 3.1, κ < κ_0, Z_κ has bounded moments up to order 2m+2]
       ⊢ Goal: P̂_0 is positive definite
       Rule: monomials linearly independent on support of continuous distribution
       Side-conditions: positive density near origin — claimed discharge: §B.2 (paper argues via GMM weak convergence; validity is the jury's call, not the shard's)
```
Each micro-claim has: justification rule name + required conditions + where conditions are proven (a location pointer to where the paper claims to discharge them, not a validity judgment).

#### 6. Limit-Order Map
Track every asymptotic statement's **limit order and uniformity scope**:
```
h_act = Θ(κ^α)  [as κ→0, uniform in π on compact subsets of Π_K, for fixed K]
τ_act ~ (b/a)n   [as n→∞, for fixed κ,K,π with x_K ≪ 1]
```
Flag any statement where limit order is ambiguous or uniformity is unclear.

### Phase 1: First Review (reviewer backend, ultra reasoning)

Submit the **complete proof content** with the checklist below, using the selected backend.

For `codex`, call `mcp__codex__codex` and always pin `model: gpt-6-astra` + `config: {"model_reasoning_effort": "ultra"}` (deep-audit tier). For `manual`, call `mcp__manual_review__review` with the identity-bearing config from the Reviewer Calling Convention above — `model`, `sandbox` and `cwd` are Codex-only.

Use this exact prompt for both backends:

```
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

