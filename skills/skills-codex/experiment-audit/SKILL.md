---
name: experiment-audit
description: "Assess experiment integrity and comparative fairness from supplied records, or obtain an independent execution audit. Use for evaluation design checks, completed-run integrity review and evidence-based audit findings."
argument-hint: "[experiment-dir-or-results-path]"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.

For a formal execution audit or existing governed run, read [project-governance](../shared-references/project-governance.md). Audit fixed input/content/review digests, declared execution inclusion and relevant interface freshness. Registry/schema PASS is integrity only and never upgrades scientific review or accepted/provisional.
For comparative integrity, use the applicable checks in [comparative-experiments](../shared-references/comparative-experiments.md). A formal fresh-review brief includes the protocol, comparison log, configurations, complete attempt ledger and raw outputs. A bounded review of supplied records stays within those records. Check relevant data, budget, selection, seed and evaluation issues; hash/coverage PASS is not a scientific fairness verdict.
<!-- EVO-INQUIRY:END -->


# Experiment Audit: Fresh-Agent Integrity Verification

> **Codex assurance:** base semantic audit results record
> `review_independence: same-family` and `acceptance_status: provisional`.
> Deterministic evidence checks may be accepted; unavailable reviewer calls emit
> BLOCKED/ERROR rather than a provisional PASS.

Keep the audit's status separate from what the supplied records support. Report
an unavailable review or unauditable execution as that specific limitation;
neither establishes a failed method or false result. A bounded assessment can
state a reported outcome without certifying execution or granting acceptance.

Audit experiment integrity for: **$ARGUMENTS**

## Choose the requested assessment

- **Local evidence assessment:** when asked to inspect a supplied protocol,
  results or evaluation description, answer that question from the available
  material. Read the relevant contents directly and save the requested report.
  State documented safeguards and their purpose, demonstrated defects, and
  decision-relevant unknowns. A protocol description can support a design
  assessment without proving that every execution followed it. Keep that
  boundary explicit; do not discard its documented strengths as worthless.
- **Independent execution audit:** when the user requests independent
  verification, or an active workflow requires a verdict-bearing audit, follow
  the full workflow below. Its fresh reviewer, provenance, tracing, output
  fields and acceptance requirements remain required.

For the local assessment, a request to be harsh does not supply evidence of a
defect. An unavailable record or unreported reliability statistic is an unknown
within the inspected scope; call it a failure only when it violates an actual
requirement or contradicts the evidence. Identify the affected claim and the
smallest useful check. Do not turn a protocol review into a certification,
create an exhaustive prerequisite inventory, or deny claims nobody made.
Finish the requested artifact and response once the material question is
answered. No independent audit verdict or acceptance is granted in this mode.

If an independent audit is required but its reviewer or essential execution
evidence is unavailable, record the specific BLOCKED condition and any useful
bounded findings. Keep the formal gate open; never relabel the bounded
assessment as a completed independent audit.

The remaining workflow and templates apply to the independent execution audit.

## Why This Exists

LLM agents can produce fraudulent experimental results through:
1. **Fake ground truth** — creating synthetic "reference" from model outputs, then reporting high agreement as performance
2. **Score normalization** — dividing metrics by the model's own max to get 0.99+
3. **Phantom results** — claiming numbers from files that don't exist or functions never called
4. **Insufficient scope** — reporting 2-scene pilots as "comprehensive evaluation"

These are NOT intentional deception — they are failure modes of optimizing agents that lack integrity constraints. This skill adds that constraint.

## Core Principle for Independent Audits

**The executor (Codex) collects file paths. A fresh Codex reviewer reads code and judges integrity. The executor does NOT participate in integrity judgment; this base route is same-family/provisional.**

This follows `shared-references/reviewer-independence.md` and `shared-references/experiment-integrity.md`.

## Constants

- **REVIEWER_BACKEND = `codex`** — Default: Codex reviewer agent (`spawn_agent`, ultra — deep-audit tier). Override with `— reviewer: oracle-pro` for GPT-5.5 Pro via Oracle MCP. See `shared-references/reviewer-routing.md`.

## Independent execution audit workflow

### Step 1: Collect Artifacts (Executor — Codex)

Locate and list these files WITHOUT reading or summarizing their content:

```
Scan project directory for:
1. Evaluation scripts:    *eval*.py, *metric*.py, *test*.py, *benchmark*.py
2. Result files:          *.json, *.csv in results/, outputs/, logs/
3. Ground truth paths:    look in eval scripts for data loading (dataset paths, GT references)
4. Experiment tracker:    EXPERIMENT_TRACKER.md, EXPERIMENT_LOG.md
5. Paper claims:          NARRATIVE_REPORT.md, paper/sections/*.tex, PAPER_PLAN.md
6. Config files:          *.yaml, *.toml, *.json configs with metric definitions
7. Case evidence, if used: selection records, sample IDs, paired predictions/assets and panel scripts
```

**DO NOT summarize, interpret, or explain any file content.** Only collect paths.

### Step 2: Send to Reviewer (GPT-6-Astra via Codex MCP)

Pass ONLY file paths and the audit checklist to the reviewer. The reviewer reads everything directly.

```text
spawn_agent:
  model: gpt-6-astra
  reasoning_effort: ultra
  message: |
    You are an experiment integrity auditor. Verify the comparison against the
    actual protocol, implementation and raw evidence. Identify substantiated
    strengths, defects and unresolved checks without presuming compromise or
    correctness. Distinguish missing evidence from demonstrated errors. Read
    the relevant files below and investigate these integrity patterns.

    Files to read:
    - Evaluation scripts: [list paths]
    - Result files: [list paths]
    - Experiment tracker: [list paths]
    - Paper claims: [list paths]
    - Config files: [list paths]
    - Case evidence and selection records: [paths, if used]
    - Case-study guidance when applicable: [resolved ../shared-references/case-study-analysis.md]

    ## Audit Checklist

    ### A. Ground Truth Provenance
    For each evaluation script:
    1. Where does "ground truth" / "reference" / "target" come from?
    2. Is it loaded from the DATASET, or generated/derived from MODEL OUTPUTS?
    3. If derived: is it explicitly labeled as proxy evaluation?
    4. Are official eval scripts used when available for this benchmark?
    FAIL if: GT is derived from model outputs without explicit proxy labeling.

    ### B. Score Normalization
    For each metric computation:
    1. Does the formula, normalization, aggregation and zero-denominator handling
       match the declared evaluation protocol (official where applicable)?
    2. What do the numerator, denominator and fitting population represent?
       Check whether method-specific rescaling changes the compared quantity.
    3. For additional display rescaling, are the original scores/units, formula
       and reference range available, and does the claim respect that scale?
    Prediction-dependent denominators, such as precision/F1/IoU, and declared
    per-example normalization are not failures by themselves. Neither is a
    score near 1. FAIL when evidence demonstrates an undisclosed or claim-invalid
    rescaling that inflates the reported performance or invalidates the
    comparison. A labeled display does not justify false absolute-performance
    or relative-gain claims; missing essential evidence remains unknown/BLOCKED.

    ### C. Result File Existence
    For each claim in the paper/narrative:
    1. Does the referenced result file actually exist?
    2. Does the claimed metric key exist in that file?
    3. Does the claimed NUMBER match what's in the file?
    4. Is the experiment tracker status DONE (not TODO/IN_PROGRESS)?
    FAIL if: Claimed results reference nonexistent files or mismatched numbers.

    ### D. Dead Code Detection
    For each metric function defined in eval scripts:
    1. Is it actually CALLED in any evaluation pipeline?
    2. Does its output appear in any result file?
    WARN if: Metric functions exist but are never called.

    ### E. Scope Assessment
    1. How many scenes/datasets/configurations were actually tested?
    2. How many seeds/runs per configuration?
    3. Does the paper use words like "comprehensive", "extensive", "robust"?
    4. Is the actual scope sufficient for those claims?
    When a case study or qualitative claim is supplied, inspect its actual
    selection pool/rule, sample/run/draw identities and paired outputs. Check
    omitted regressions/shared failures, missing outputs, asymmetric crops or
    timestamps, and whether a panel-only rate is presented as population-wide.
    Distinguish inspected media from annotations and hypotheses from mechanisms.
    Absence of a panel alone is not an integrity failure.
    WARN if: Scope language exceeds actual evidence.

    ### F. Evaluation Type Classification
    Classify each evaluation as:
    - real_gt: uses dataset-provided ground truth
    - synthetic_proxy: uses model-generated reference
    - self_supervised_proxy: no GT by design
    - simulation_only: simulated environment
    - human_eval: human judges

    ## Output Format

    For each check (A-F), report:
    - Status: PASS | WARN | FAIL
    - Evidence: exact file:line references
    - Details: what specifically was found

    Overall verdict: PASS | WARN | FAIL
    
    Be thorough. Read every eval script line by line.
```

### Step 3: Parse and Write Report (Executor — Codex)

Parse the reviewer's response and write `EXPERIMENT_AUDIT.md`:

```markdown
# Experiment Audit Report

**Date**: [today]
**Auditor**: GPT-6-Astra ultra (fresh same-family agent, read-only, provisional)
**Project**: [project name]

## Overall Verdict: [PASS | WARN | FAIL]

## Integrity Status: [pass | warn | fail]

## Checks

### A. Ground Truth Provenance: [PASS|WARN|FAIL]
[details + file:line evidence]

### B. Score Normalization: [PASS|WARN|FAIL]
[details]

### C. Result File Existence: [PASS|WARN|FAIL]
[details]

### D. Dead Code Detection: [PASS|WARN|FAIL]
[details]

### E. Scope Assessment: [PASS|WARN|FAIL]
[details]

### F. Evaluation Type: [real_gt | synthetic_proxy | ...]
[classification + evidence]

## Action Items
- [specific fixes if WARN or FAIL]

## Claim Impact
- Claim 1: [supported | needs qualifier | unsupported]
- Claim 2: ...
```

Also write `EXPERIMENT_AUDIT.json` for machine consumption:

```json
{
  "audit_skill": "experiment-audit",
  "verdict": "WARN",
  "reason_code": "scope_exceeds_evidence",
  "summary": "Two-scene evaluation supports a qualified claim only.",
  "audited_input_hashes": {"results/eval.json": "sha256:<hash>"},
  "trace_path": ".ei/traces/experiment-audit/2026-04-10_run01/",
  "agent_id": "agent_019f...",
  "verdict_id": "agent_019f...",
  "executor_model": "codex-gpt-6-astra",
  "executor_family": "openai",
  "reviewer_model": "gpt-6-astra",
  "reviewer_family": "openai",
  "reviewer_reasoning": "ultra",
  "review_independence": "same-family",
  "acceptance_status": "provisional",
  "generated_at": "2026-04-10T00:00:00Z",
  "date": "2026-04-10",
  "auditor": "gpt-6-astra-ultra",
  "overall_verdict": "warn",
  "integrity_status": "warn",
  "checks": {
    "gt_provenance": {"status": "pass", "details": "..."},
    "score_normalization": {"status": "warn", "details": "..."},
    "result_existence": {"status": "pass", "details": "..."},
    "dead_code": {"status": "pass", "details": "..."},
    "scope": {"status": "warn", "details": "..."},
    "eval_type": "real_gt"
  },
  "claims": [
    {"id": "C1", "impact": "supported"},
    {"id": "C2", "impact": "needs_qualifier"}
  ]
}
```

### Step 4: Print Summary

```
🔬 Experiment Audit Complete

  GT Provenance:      ✅ PASS — real dataset GT used
  Score Normalization: ⚠️ WARN — boundary metric uses self-reference
  Result Existence:    ✅ PASS — all files exist, numbers match
  Dead Code:           ✅ PASS — all metric functions called
  Scope:               ⚠️ WARN — 2 scenes, paper says "comprehensive"

  Overall: ⚠️ WARN
  
  See EXPERIMENT_AUDIT.md for details.
```

## Integration with Other Skills

### Automatic in /research-pipeline (advisory, never blocks)

When integrated into the pipeline, this skill runs automatically after `/experiment-bridge` and before `/auto-review-loop`:

```
/experiment-bridge → results ready
    ↓
/experiment-audit (automatic, advisory)
    ├── PASS  → continue normally
    ├── WARN  → print ⚠️ warning, continue, tag claims as [INTEGRITY: WARN]
    └── FAIL  → print 🔴 alert, continue, tag claims as [INTEGRITY CONCERN]
    ↓
/auto-review-loop → proceeds with integrity tags visible to reviewer
```

**Never blocks the pipeline.** Even on FAIL, the pipeline continues — but claims carry visible integrity tags.

### Read by /result-to-claim (if exists)

```
if EXPERIMENT_AUDIT.json exists:
    read integrity_status
    attach to verdict: {claim_supported: "yes", integrity_status: "warn"}
    if integrity_status == "fail":
        downgrade verdict display: "yes [INTEGRITY CONCERN]"
else:
    verdict as normal, integrity_status = "unavailable"
    mark as "provisional — no integrity audit"
```

### Read by /paper-write (if exists)

```
if EXPERIMENT_AUDIT.json exists AND integrity_status == "fail":
    add footnote to affected claims: "Note: integrity audit flagged concerns with this evaluation"
```

## Key Rules

- **Reviewer independence**: executor collects paths, reviewer judges. Period.
- **Never block**: warn loudly, never halt the pipeline.
- **File-as-switch**: no EXPERIMENT_AUDIT.md = skill was never run = zero impact on existing behavior.
- **Review class**: base Codex is same-family provisional; only an overlay may claim cross-family accepted.
- **Honest about limits**: the audit catches common patterns, not all possible fraud. It is a safety net, not a guarantee.

## Acknowledgements

Motivated by community-reported integrity issues (#57, #131) where executor agents created fake ground truth and self-normalized scores.

## Review Tracing

After each reviewer agent call, save the trace following `shared-references/review-tracing.md` (Policy C — forensic; never silently skip). Use `save_trace.sh` (resolved per the chain in `shared-references/integration-contract.md` §2) or write files directly to `.ei/traces/<skill>/<date>_run<NN>/`. Respect the `--- trace:` parameter (default: `full`).
