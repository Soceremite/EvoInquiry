# Fair comparative experiments

Read for designing, implementing, running, analysing or reviewing empirical
comparisons. Reuse an existing protocol when it remains valid. Apply only the
parts needed for the requested task: advice and a small analysis do not require
new experiments, a formal claim review or a machine-readable archive index.

## State the question before equalising settings

Fairness means comparable evidence for the stated question. First choose the
comparison question and the conclusion it can support.

| Question | Control or disclose | Permitted conclusion |
| --- | --- | --- |
| Controlled contribution | Hold unrelated conditions fixed; identify the changed mechanism and unavoidable coupled changes | Contribution under those conditions |
| Equal resource budget | Declare the resource cap, accounting boundary and allocation rule; measure actual consumption | Performance under that cap |
| Reasonably tuned performance | Use credible method-specific recipes; disclose search spaces, validation access, trials and total search cost | Performance of those tuned systems |

Identical epochs, learning rates or optimisers are not a universal fairness
rule. Equal steps can expose different amounts of data; equal epochs can consume
different compute. Equal time needs hardware and implementation context. Extra
data, pretraining, teacher/API access and evaluation-time compute can change the
question. A tuned-system advantage alone does not isolate a mechanism.

For a plan, write **common settings once**, followed by a short per-method table
of differences, justification, resource cost and affected claims. Record unknown
baseline details as unknown. Do not invent missing information or expand the
benchmark list to compensate for weak controls.

## Data, baselines and evaluation

Fix dataset identity/version, eligibility, sample identifiers, split construction
and the unit being generalised to. Prevent leakage through duplicates, related
subjects, overlapping time windows, labels and train-fitted preprocessing. Fit
statistics and transformations using the permitted training data, then apply
them to held-out data. Grouped or temporal tasks need suitable splits, rather
than automatically shuffling examples.

Use strong relevant baselines, preferably authoritative runnable recipes, and
record source/configuration versions. Sanity-check the reproduction and explain
material gaps from reported performance. Literature numbers are useful context
but are direct controlled comparisons only when data, evaluation, input access
and resources are comparable. If reproduction is unavailable, report that limit.
Method-specific tokenisation, augmentation or sampling may be appropriate;
record their information access and cost instead of forcing identical code.

Freeze metric definitions, direction, label mapping, evaluator version, precision,
decoding/postprocessing and evaluation inputs. Select hyperparameters, checkpoints,
thresholds and winner weights using a declared validation rule. Hold test data
apart from those choices. After test-informed changes, treat the test as exposed
and establish a defensible new evaluation or label the resulting limitation.
Missing outputs, failed cases and denominators must follow declared handling.

## Training and tuning resources

Choose only the budget measures that answer the question: examples/tokens,
updates, parameters, FLOPs, hardware time, memory, external queries, money or
inference cost. Define whether preprocessing, pretraining, tuning, failed trials,
validation, compilation and retries count. Report end-to-end and narrowly scoped
costs separately when both are useful; name the boundary of each number.

Separate a method's recipe from its hyperparameter search. Declare each search
space, trial budget, stopping/selection rules and validation access. For an
equal-budget claim, enforce the declared cap including relevant search cost;
allow method-specific allocations under the same stated accounting rule. For a
tuned-performance claim, unequal search costs must be visible and cannot justify
a resource-efficiency claim without additional evidence. A baseline should not
receive an obviously unsuitable recipe simply to match the proposed method.

For ablations, distinguish a controlled removal using the parent configuration
from a retuned alternative. Report both when necessary to distinguish a mechanism
effect from dependence on a poor alternative configuration. Reuse baseline and
evaluator evidence only when their fixed identities still match.

## Repetitions, failures and statistics

Declare independent units and planned method/run/seed slots. Choose replication
from pilot variability, the effect or precision that matters, and available
resources. The existing three-seed default is a starting estimate, not a proof
of adequate power. A deterministic computation may need no training seed;
stochastic training and a fixed-model evaluation answer different uncertainty
questions. Under a small budget, show the actual sample count and limit the
strength of the conclusion instead of manufacturing repetitions.

Retain all attempts, including OOMs, divergence, interruptions and retries.
Predeclare how an attempt fills a seed slot and how missing/failed slots affect
aggregation. A retry is not a new independent seed. Record changed batch size,
precision, data or resource allocation as a protocol deviation; decide whether
the affected comparison needs rerunning. Never silently discard weak seeds,
choose the best retry, or replace a multi-seed summary with its best seed.

Report individual runs, counts, inclusion/exclusion reasons, an appropriate
aggregate and variability. Distinguish standard deviation across independent
runs from uncertainty of an estimated effect. Compare **differences** with
uncertainty when the evidence supports it; name the interval method and sampling
unit. Same integer seeds do not establish matched initialisation or a paired
design. Pair only genuinely matched independent units, and preserve groups or
hierarchy in resampling. Thousands of examples from one trained model do not
become thousands of independent training runs. Tiny-sample intervals or tests
need their assumptions and limits, not a significance guarantee.

Use absolute differences in metric units, including percentage points for
accuracy. Add relative gains only when the metric scale and nonzero baseline
make the ratio meaningful. Zero, negative or arbitrary-origin metrics may make
relative improvement undefined or misleading; label it accordingly. Do not
average incompatible metrics or normalise scores in a way that hides raw results.
For many comparisons, disclose selection and multiplicity rather than reporting
only the most favourable outcome.

## Comparison log and weight archival

Before consolidation, persist the fixed protocol, per-run configurations,
raw metrics or failure evidence, complete attempt ledger, comparison summary,
selection rule and reason, deviations, uncertainty, negative results and limits.
The log should make clear which runs were included and why. Prefer the validated
winner's weights after inspecting future dependencies; preserve necessary
teachers, ensembles, ablation inputs or audit models with pins. Aggregated method
performance and the particular inference checkpoint retained are different
choices: document the representative checkpoint rule as well. Do not use test
scores or a best-seed presentation to conceal the full comparison.

When `tools/checkpoint_retention.py` performs **comparison** consolidation,
provide `--comparison-evidence INDEX.json` with `--archive-to WINNER_ROOT`.
`tools/comparison_evidence.py` checks the declared slots, recorded attempts,
validation selection identity and fixed references before any deletion. Keep
the index and all referenced logs outside managed checkpoint artifact directories.
The surviving weights and bound evidence are rechecked before interrupted cleanup
continues. Legacy comparison receipts remain readable but need evidence binding
before further destructive cleanup. Ordinary single-run completion is unchanged.
Resolve these tools from the loaded package root containing `skills/` and `tools/`;
their record format is documented in `docs/COMPARISON_EVIDENCE.md` there.

A file-integrity PASS cannot establish scientific fairness or correct numerical
interpretation. Review the actual protocol, code and raw outputs. Explain whether
the evidence supports a mechanism, a resource-bound result, a tuned-system result,
or only a preliminary observation. Formal claim verdicts retain their existing
review gates; an ordinary result query remains an ordinary analysis.

## Sources

[Bouthillier et al., Accounting for Variance in Machine Learning Benchmarks](https://proceedings.mlsys.org/paper_files/paper/2021/hash/0184b0cd3cfb185989f858a1d9f5c1eb-Abstract.html)
motivates accounting for data, initialisation and tuning variability.
[Dodge et al., Show Your Work](https://aclanthology.org/D19-1224/) supports reporting
search budgets and validation performance.
[Agarwal et al., Deep Reinforcement Learning at the Edge of the Statistical Precipice](https://proceedings.neurips.cc/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html)
examines few-run evaluation and uncertainty in reinforcement learning; its specific
estimators are not mandatory for every field.
[scikit-learn's leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage)
explains train-only fitting of learned preprocessing.
