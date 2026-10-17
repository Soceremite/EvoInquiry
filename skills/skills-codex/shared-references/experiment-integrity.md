# Experiment Integrity Protocol

## Core Principle

**The model that writes experiment code must NOT be the model that judges experiment integrity.** This is the same principle as reviewer-independence, applied to experiments.

## Prohibited Patterns

### 1. Fake Ground Truth
- ❌ Creating synthetic "reference" from model outputs and comparing against it
- ❌ Using baseline model outputs as ground truth
- ❌ Generating pseudo-GT that is structurally similar to predictions
- ✅ Using dataset-provided ground truth
- ✅ Using official evaluation scripts when available
- ✅ Proxy evaluation is allowed IF explicitly labeled as `synthetic_proxy`

### 2. Score Normalization Fraud
- ❌ Undisclosed or claim-invalid rescaling that inflates reported performance or hides material differences
- ✅ Check the formula, units, aggregation and reference population against the declared metric and claim. Precision/F1/IoU denominators and defined per-example normalization are not failures merely because they depend on predictions
- ✅ A common min-max transform can be a labeled display when its fitting range and original scores are available. Including every method alone does not validate it: it does not preserve absolute calibration, thresholds or relative gains, and a tied range needs a declared convention
- ✅ Keep original and transformed scores traceable when additional rescaling is used. Disclosure does not excuse a false claim; a score near 1 alone is not evidence of wrongdoing

### 3. Phantom Results
- ❌ Claiming results from files that don't exist
- ❌ Referencing metrics from functions that are never called
- ❌ Reporting TRACKER status as DONE when it's still TODO
- ✅ Every claimed number must trace to an actual output file

### 4. Insufficient Scope
- ❌ Reporting 2-scene pilot as "comprehensive evaluation"
- ❌ Using words like "robust", "extensive", "across settings" for tiny experiments
- ✅ Honestly label scope: "pilot (N=2)", "preliminary", "limited evaluation"
- ✅ State exact scope: N scenes, N seeds, N configurations

## Evaluation Types (must be declared)

| Type | Label | What it means | Claim ceiling |
|------|-------|---------------|---------------|
| Real GT | `real_gt` | Dataset-provided ground truth | Full performance claims |
| Synthetic proxy | `synthetic_proxy` | Model-generated reference | "Proxy consistency" only |
| Self-supervised | `self_supervised_proxy` | No GT by design | Relative improvement only |
| Simulation | `simulation_only` | Simulated environment | "In simulation" qualifier |
| Human eval | `human_eval` | Human judges | Subject to inter-rater stats |

## Who Checks

The **reviewer model** (different family from executor) performs integrity checks via `/experiment-audit`. The executor collects file paths; the reviewer reads code and results directly.

**Never let the executor judge its own experiment integrity.**
