# Case studies and sample-level diagnosis

Read for a substantive experiment analysis, error analysis or qualitative result
panel. Use existing evaluation artifacts and the project's own analysis tools.
Case studies complement aggregate results by showing what changed and where;
they do not by themselves establish prevalence, generalisation or a mechanism.

## Act without waiting for a separate request

For a full result analysis, inspect the available per-example predictions,
targets, inputs and generated assets. When usable evidence exists, include a
small, traceable case study in the analysis itself. A compact panel, often four
to eight cases, is a starting point rather than a quota. Use fewer or more when
the question, evidence and budget justify it. A single-method analysis can
contrast successes and failures without inventing a baseline.

A narrow arithmetic, ranking or training-status question does not need a new
case report. Honor an explicit metrics-only request. If only aggregate scores
exist, state that cases cannot be reconstructed from those scores, finish the
supported analysis and identify the smallest useful export: stable sample IDs,
input/target references, per-method predictions or output paths, evaluation
settings and relevant run/seed identities. Do not invent examples or launch new
inference, annotation or external services merely to fill this gap. Existing
authorization and resource limits still apply to any proposed collection.

## Choose cases before building the story

1. Identify the question, eligible population, split, exclusions and available
   outputs. Count missing or unpaired outputs rather than treating a complete
   subset as the whole evaluation. Reuse a predeclared selection rule if valid.
2. Match methods by sample ID and relevant input/conditioning settings. Preserve
   targets, preprocessing, masks/crops, temporal windows and output limits. Use
   the validation-selected or predeclared representative runs; do not pick a
   favorable training seed per example. Record repeated outputs explicitly.
3. Include an outcome-independent sample of the eligible pool, using sorted IDs
   and a recorded sampling seed or another reproducible rule. Add diagnostic
   contrasts where present: improved cases, regressions and shared failures.
   Report empty strata honestly; do not fabricate a regression for balance.
   A large positive delta can still be a failure for both methods.
4. Select across relevant, recorded slices such as classes, target ranges or
   task conditions when they answer the question. Label extreme, hand-picked or
   user-selected examples as such. Log candidate counts, selected IDs, the rule,
   exclusions and any replacements. Limited space may leave strata uncovered;
   disclose that instead of presenting the panel as representative.

Use the same rule for baseline and candidate. Never search only the candidate's
best outputs, replace inconvenient failures or tune thresholds after seeing the
test cases without labeling the change exploratory. A post-hoc slice or error
taxonomy is hypothesis-generating. If it motivates changes, treat the inspected
test material as exposed when planning a new confirmatory evaluation.

## Adapt the evidence to the task

| Task | Inspect and show | Keep the interpretation bounded |
| --- | --- | --- |
| Classification | True label, each prediction and available confidence; confusion pairs, class support and relevant conditions | Check label mapping and class imbalance. A wrong high-confidence prediction is not a calibration estimate; use population-level calibration analysis when warranted. |
| Regression / forecasting | Target and predictions in original units; signed and absolute residuals, target/time ranges and provided intervals | Inspect typical errors and tail regressions. Distinguish an outlier, systematic bias and scale effects; never choose a percentage error with an unsuitable denominator. Preserve temporal order and forecast horizon. |
| Image generation / reconstruction | Same prompt/input and conditioning, real per-method outputs and any actual target; identical display scale and disclosed crops | Record model, sampler, steps and generation seed/noise when available. Inspect adherence, content/detail failures and artifacts; an aesthetic preference or one per-image score does not establish distributional quality. Do not invent per-image FID or use an AI illustration as an experimental output. |
| Video understanding | Same clip/window, question or event, ground-truth annotation, prediction and timestamped frames or accessible clip evidence | Check temporal order, event localisation, duration and available modalities. Sparse frames cannot establish unseen motion or audio; distinguish annotation-based findings from actually inspected media. Frames from one video are not independent videos. |

Other tasks can use the same structure with their actual unit: a document,
sequence, patient, episode or structured output. For stochastic generation,
preserve the planned draw count and pairing protocol. Equal integer seeds do
not guarantee matched noise or comparable draws across different implementations.
If only one draw is available, describe that draw rather than sampling stability.

When adding qualitative judgments, state the task criteria and who made the judgment. Hide method identity or randomise display order when useful and feasible. An agent's exploratory visual assessment is not a fabricated human study or a validated perceptual score; new annotation work still needs the applicable authorization and budget.

## Connect individual evidence to aggregate findings

For each selected case, show the input/target reference, paired outputs or
predictions, relevant score or error if defined, and the concrete observed
difference. Separate that observation from a possible explanation and a proposed
test. Do not infer attention, reasoning or causal mechanisms from an attractive
output alone. If the media cannot be opened, report only what the supplied
annotations or values support; do not claim a visual inspection occurred.

Relate patterns to full-pool or clearly identified slice counts where available.
If a rate is computed only on the selected panel, label its denominator and do
not report it as a population rate. Preserve the declared primary outcome:
compelling cases do not reverse an unfavorable aggregate result, and an improved
aggregate does not erase a genuine local regression. Distinguish an illustrative
counterexample to an absolute claim from the frequency of that failure.

## Keep the result reviewable and small

Lead with the observed aggregate result, then use one case table or panel to
explain the useful contrasts. A census of a small eligible pool is a valid
outcome-independent choice; it needs no additional random sample. Combine the
selection rule, coverage and provenance into a brief note and discuss each
finding once. Reserve time to verify the report and finish the response before
adding optional plots, repeated summaries or additional diagnostic branches.

Put the case section in the existing analysis report; reuse its artifact and
versioning conventions instead of creating a second registry. Include a compact
selection record with the source paths/revisions, population and coverage,
sample/run/draw IDs, rule and sampling seed, missing items and transformations.
Actual case rows can be a table, paired text, residual plot, contact sheet or
timestamped storyboard. Reference immutable originals when possible; save only
the small derived panel/crops needed for review and avoid copying whole datasets
or videos. Do not delete original evidence to make room for a panel.

For a publication panel, use `paper-figure` to arrange actual assets, retain an
editable script and disclose selection and transforms in the caption. Its
existing figure identity receipt can bind the selection record and source
assets. Any readability or visual inspection not performed remains unverified;
file hashes do not judge the scientific interpretation. Preserve the selection
record and necessary compact evidence before a separately authorized cleanup,
so the analysis does not silently depend on disposable checkpoints.
