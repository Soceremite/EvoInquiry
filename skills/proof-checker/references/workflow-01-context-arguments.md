<!-- EI-WORKFLOW-REFERENCE -->

# Context: $ARGUMENTS

Read this file when the workflow reaches Context: $ARGUMENTS through Phase 0: Preparation. In commands and examples, interpret relative skill paths from the entrypoint directory.








# Proof Checker: Rigorous Mathematical Verification & Fixing

> 🔒 **Do not wrap this skill in `/loop`, `/schedule`, or `CronCreate`.** It is
> verdict-bearing — it judges proof validity across rounds, threading the
> reviewer's memory from Phase 1 → Phase 3 via `codex-reply` so the reviewer can
> check whether a fix actually closed the gap it flagged. An external timer
> re-enters from the top each tick, starting a fresh thread and losing that
> memory. Schedule the *external wait that precedes it*, not the verdict. See
> [`shared-references/external-cadence.md`](../../shared-references/external-cadence.md).

Systematically verify a mathematical proof via cross-model adversarial review, fix identified gaps, re-review until convergence, and generate a detailed audit report with proof-obligation accounting.

## Context: $ARGUMENTS

## Constants

- MAX_REVIEW_ROUNDS = 3
- REVIEWER_MODEL = `gpt-6-astra` — Default model for the Codex backend, reasoning effort `ultra` (deep-audit tier; capability fallback `gpt-6-astra`+`xhigh` → `gpt-5.5`+`xhigh` per `shared-references/reviewer-routing.md`, capability errors only — never below `xhigh`). Manual backend uses a model the user chooses, **but it must be a non-Claude model ARIS can classify** (OpenAI, Google, DeepSeek, Moonshot/Kimi, Qwen) — the executor is Claude, so routing the proof review into any Claude product makes Claude judge Claude and voids the cross-model invariant (see `shared-references/reviewer-routing.md`).
- **REVIEWER_BACKEND = `codex`** — Default: Codex MCP (ultra). Override with `— reviewer: oracle-pro` for Oracle MCP, or `— reviewer: manual` for Manual Review MCP. If manual-review MCP is unavailable, stop and print the install command; do not fall back to Codex. See `shared-references/reviewer-routing.md`.

## Reviewer Calling Convention

When calling the reviewer, branch on REVIEWER_BACKEND:

**If REVIEWER_BACKEND = `codex`:**
  Use `mcp__codex__codex` for new review threads
  (`model: gpt-6-astra`, `config: {"model_reasoning_effort": "ultra"}`).
  Use `mcp__codex__codex-reply` for follow-up rounds (reuse threadId).

**If REVIEWER_BACKEND = `manual`:**
  Use `mcp__manual_review__review` for new review threads with:
    prompt: [exact same prompt that would go to Codex]
    config: {"model_reasoning_effort": "xhigh", "executor_model": "<actual executor model>", "require_reviewer_model": true}
  Save the returned `threadId`.
  Use `mcp__manual_review__review_reply` for follow-up rounds with:
    threadId: [saved manual-review threadId]
    prompt: [follow-up prompt]
    config: {"model_reasoning_effort": "xhigh", "executor_model": "<actual executor model>", "require_reviewer_model": true}

Prompt fidelity: the manual prompt must be exactly the same text that Codex would receive.
Review tracing applies equally to both backends.

- AUDIT_DOC: `PROOF_AUDIT.md` at the paper directory root, alongside `main.tex` (cumulative log; when invoked via `/paper-writing`, this is `paper/PROOF_AUDIT.md`)
- REPORT_TEX: `proof_audit_report.tex` (formal before/after PDF)
- STATE_FILE: `PROOF_CHECK_STATE.json` (for recovery)
- SKELETON_DOC: `PROOF_SKELETON.md` (micro-claim inventory)
- **RENDER_HTML = true** — When `true` (default), auto-render `PROOF_AUDIT.md` to HTML at workflow end via `/render-html`. Uses **full Codex review gate** (audit-class artifact — math-heavy content; render-fidelity check protects against MathJax breakage and matches the skill's cross-model audit invariant). Set `false` to skip, or pass `— render html: false`.

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

### Phase 0: Preparation

1. **Locate the proof**: Find the main `.tex` file(s).
2. **Read the entire proof**: Extract list of all theorems/lemmas/propositions/corollaries/definitions/assumptions.
3. **Read reference materials**: Reference papers, prior results.
4. **Build a section map**: Structured list with line numbers and key claims.
5. **Identify the main theorem**: Central result, assumptions, claims.

