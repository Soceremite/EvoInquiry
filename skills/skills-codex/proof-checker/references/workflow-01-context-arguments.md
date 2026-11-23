<!-- EI-WORKFLOW-REFERENCE -->

# Context: $ARGUMENTS

Read this file when the workflow reaches Context: $ARGUMENTS through 5. Micro-Claim Inventory. In commands and examples, interpret relative skill paths from the entrypoint directory.





# Proof Checker: Rigorous Mathematical Verification & Fixing

> **Codex assurance:** base Codex proof judgments are
> `review_independence: same-family` and `acceptance_status: provisional`.
> Deterministic compilation/algebra checks may be accepted; a semantic proof
> acceptance requires a cross-family overlay. Reviewer failure emits BLOCKED.

Systematically verify a mathematical proof via fresh-agent adversarial review, fix identified gaps, re-review until convergence, and generate a detailed audit report with proof-obligation accounting.

## Context: $ARGUMENTS

## Constants

- MAX_REVIEW_ROUNDS = 3
- REVIEWER_MODEL = `gpt-6-astra` via Codex reviewer agent, reasoning effort
  `ultra` for this deep-audit skill (capability fallback never below `xhigh`)
- **REVIEWER_BACKEND = `codex`** — Default: Codex reviewer agent (`spawn_agent`, ultra — deep-audit tier). Override with `— reviewer: oracle-pro` for GPT-5.5 Pro via Oracle MCP. See `shared-references/reviewer-routing.md`.
- AUDIT_DOC: `PROOF_AUDIT.md` at the paper directory root, alongside `main.tex` (cumulative log; when invoked via `/paper-writing`, this is `paper/PROOF_AUDIT.md`)
- REPORT_TEX: `proof_audit_report.tex` (formal before/after PDF)
- STATE_FILE: `PROOF_CHECK_STATE.json` (for recovery)
- SKELETON_DOC: `PROOF_SKELETON.md` (micro-claim inventory)
- **RENDER_HTML = true** — When `true` (default), auto-render `PROOF_AUDIT.md` to HTML at workflow end via `/render-html`. Uses **full review gate** (audit-class, math-heavy — render-fidelity check protects against MathJax breakage). Set `false` to skip, or pass `— render html: false`. **Non-blocking**: failures don't invalidate the proof audit.

### Acceptance Gate (objective, replaces subjective scoring)

The proof passes when ALL of the following hold:
1. Zero open FATAL or CRITICAL issues
2. Every theorem/lemma has: (i) explicit hypotheses, (ii) proof with all interchanges justified, (iii) every application discharges hypotheses in the ledger
3. All big-O/Θ/o statements have declared parameter dependence and uniformity scope
4. Counterexample pass executed on all key lemmas (log candidates even if none found)

## Issue Taxonomy (20 categories, 4 groups)

### Group A: Logic & Proof Structure

| Category | Description | Example |
|----------|-------------|---------|
| **UNJUSTIFIED_ASSERTION** | Claim stated without proof or reference | "The Hessian splits into Gram blocks" |
| **UNPROVEN_SUBCLAIM** | "Clearly" / "it follows" hides a nontrivial lemma | "By symmetry, the cross-terms vanish" without checking |
| **QUANTIFIER_ERROR** | Wrong order ∀/∃, missing "for sufficiently small κ" | "For all π, there exists ε" vs "there exists ε for all π" |
| **IMPLICATION_REVERSAL** | Uses (A⇒B) as (B⇒A), or claims equivalence with only one direction | |
| **CASE_INCOMPLETE** | Misses boundary/degenerate cases | Singular covariance, zero weight, non-unique argmin |
| **CIRCULAR_DEPENDENCY** | Lemma uses theorem that depends on it | |
| **LOGICAL_GAP** | A step is not justified by what precedes it | B=Θ(1) → β_K=0 without analyzing W |

### Group B: Analysis & Measure Theory

| Category | Description | Example |
|----------|-------------|---------|
| **ILLEGAL_INTERCHANGE** | Swaps limit/expectation/derivative/integral without DCT/MCT/Fubini | Differentiating under E without domination |
| **NONUNIFORM_CONVERGENCE** | Pointwise convergence used as uniform | sup and limit swapped |
| **MISSING_DOMINATION** | DCT cited but no dominating function given | |
| **INTEGRABILITY_GAP** | Uses E|X|^p without proving/assuming finite moments | |
| **REGULARITY_GAP** | Differentiability/Lipschitz/convexity used but not established | |
| **STOCHASTIC_MODE_CONFUSION** | Mixes a.s./in prob./in L²/in expectation | |

### Group C: Model & Parameter Tracking

| Category | Description | Example |
|----------|-------------|---------|
| **MISSING_DERIVATION** | A quantity is used but never derived from the model | Risk functional with undefined B, W |
| **HIDDEN_ASSUMPTION** | Proof silently uses a condition not in the theorem | Gaussianity assumed but not stated |
| **INSUFFICIENT_ASSUMPTION** | Hypotheses too weak for proof (counterexample exists) | Moment conditions admitting 2-point distributions |
| **DIMENSION_TRACKING** | Parameter dependence (d, n, K, ...) not explicit | d enters only through κ |
| **NORMALIZATION_MISMATCH** | Coordinate/scaling conventions inconsistent | Rescaled vs raw coordinates |
| **CONSTANT_DEPENDENCE_HIDDEN** | "C" depends on d,n,K but treated as universal | |

### Group D: Scope & Claims

| Category | Description | Example |
|----------|-------------|---------|
| **SCOPE_OVERCLAIM** | Conclusion stated more broadly than proof supports | "β_K=0" with only generic overlap |
| **REFERENCE_MISMATCH** | Cited theorem's hypotheses not verified at point of use | |

## Two-Axis Severity System

### Axis A — Proof Status (what is wrong)

| Status | Meaning |
|--------|---------|
| **INVALID** | Statement false as written (counterexample exists or contradiction) |
| **UNJUSTIFIED** | Could be true, but current proof does not establish it |
| **UNDERSTATED** | True only after strengthening assumptions |
| **OVERSTATED** | True only after weakening conclusion / adding qualifiers |
| **UNCLEAR** | Ambiguous notation / definition drift (not wrong per se) |

### Axis B — Impact (how much breaks)

| Impact | Meaning |
|--------|---------|
| **GLOBAL** | Breaks main theorem or core dependency chain |
| **LOCAL** | Affects a side result but not the main theorem |
| **COSMETIC** | Exposition only |

### Severity Labels (derived)

| Label | Definition |
|-------|------------|
| **FATAL** | INVALID + GLOBAL |
| **CRITICAL** | (INVALID + LOCAL) or (UNJUSTIFIED + GLOBAL) |
| **MAJOR** | (UNJUSTIFIED + LOCAL) or (UNDERSTATED/OVERSTATED + GLOBAL) |
| **MINOR** | Clarity / notation / dimension bookkeeping that doesn't change claims |

## Side-Condition Checklists for Common Theorems

When the proof invokes any of the following, require explicit verification of ALL listed conditions:

| Theorem | Required Conditions |
|---------|-------------------|
| **DCT** (Dominated Convergence) | Pointwise a.e. convergence + integrable dominating function |
| **MCT** (Monotone Convergence) | Monotone increasing + non-negative |
| **Fubini/Tonelli** | Product measurability + integrability (Fubini) or non-negative (Tonelli) |
| **Leibniz integral rule** | Continuity of integrand + dominating function for derivative |
| **Implicit Function Theorem** | Continuous differentiability + non-singular Jacobian |
| **Taylor with remainder** | Sufficient differentiability + remainder form (Lagrange/integral) |
| **Jensen's inequality** | Convexity of function + integrability |
| **Cauchy-Schwarz** | Correct inner product space + integrability of both factors |
| **Weyl/Davis-Kahan** | Symmetry/Hermiticity + perturbation bound conditions |
| **Analytic continuation** | Domain connectivity + identity theorem conditions |
| **WLOG reduction** | Invariance under claimed symmetry + reduction is reversible |

## Workflow

### Proof-obligation fan-out

Independent sections/theorems may be extracted by fresh read-only
`spawn_agent` shards, with a sequential fresh-context fallback. Each shard
returns `{"shard_id": ..., "entries": [{"payload": ..., "dedup_key":
"<theorem-or-obligation-id>"}]}` and must not declare the proof valid. The
parent mechanically merges obligations; the fresh Codex review that evaluates
them records `review_independence: same-family` and
`acceptance_status: provisional`. See
[`fan-out-pattern.md`](../../shared-references/fan-out-pattern.md).

### Phase 0: Preparation

1. **Locate the proof**: Find the main `.tex` file(s).
2. **Read the entire proof**: Extract list of all theorems/lemmas/propositions/corollaries/definitions/assumptions.
3. **Read reference materials**: Reference papers, prior results.
4. **Build a section map**: Structured list with line numbers and key claims.
5. **Identify the main theorem**: Central result, assumptions, claims.

### Phase 0.5: Proof-Obligation Ledger

Build formal accounting artifacts. Save to `PROOF_SKELETON.md`:

#### 1. Dependency DAG
Nodes = Definitions / Assumptions / Lemmas / Theorems. Edges = "uses". **Detect cycles** (including semantic circularity where Lemma A uses a corollary that quietly depends on A).

#### 2. Assumption Ledger
For each theorem/lemma, list every hypothesis with WHERE each is verified (or mark "UNVERIFIED"). Track **usage-minimal assumption sets** — which assumptions were actually used vs merely stated.

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
       Side-conditions: positive density near origin ✓ (by GMM weak convergence)
```
Each micro-claim has: justification rule name + required conditions + where conditions are proven.

