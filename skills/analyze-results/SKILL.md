---
name: analyze-results
description: "Analyse experiment metrics and sample-level behavior, compare methods fairly, and diagnose successes, regressions and failures. Use for result interpretation, error analysis or case studies."
argument-hint: "[results-path-or-description]"
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.

Match the work to the question. For a narrow numerical query, verify the relevant
values and metric definition, then answer directly; do not load case-study,
comparison-design or governance references solely to expand that query. For a
full analysis, lead with the observed comparison and use one concise report:
metric evidence, a case/selection section and the necessary limits or next
checks. Explain each finding once instead of repeating it as observations,
insights and another summary; reference the raw table from the case section
instead of duplicating it. Finish and verify this core, including source
calculations and output paths, before optional expansion and the final response.

When a Codex plugin session is active, use its exact discovered
`skills/skills-codex/analyze-results/SKILL.md` entrypoint and references; do not
switch between the Codex mirror and this mainline tree within one session. A
different integration should follow the path it discovered and keep its own
reference tree consistent. Keep a bounded report compact and single-pass: one
raw table, one case/selection table and concise findings, normally within about
1,000 words unless detail is requested. After the requested artifact is written,
verify it once and stop. Repeated reconnect, overload or stream errors require a
short incomplete-status record or an explicit infrastructure report, not more
expensive reads or invented findings.
<!-- EVO-INQUIRY:END -->


<!-- EI-GOVERNANCE:BEGIN -->
Resolve runtime state through tools/state_paths.py before .ei operations. For
governed execution records or supplied fixed evidence references, use
[project-governance](../shared-references/project-governance.md) for fixed evidence,
profiles and controlled migration; missing profiles retain compat-v1. A standalone
result table needs its existing paths, protocol and coverage, not a new profile.
Resolve fixed execution/spec/environment/evaluator refs once. List included and excluded attempts and apply the predeclared slot aggregation; show failed/missing seeds and protocol/environment differences. current is navigation only.
For substantive result comparisons, load [comparative-experiments](../shared-references/comparative-experiments.md). Reconstruct all declared seed slots and attempts; show counts, exclusions, failures and protocol differences. Separate run variability from effect uncertainty and name independent/paired units. Use absolute metric differences; compute relative gains only for meaningful scales with a valid nonzero baseline, otherwise report them undefined or inappropriate. This qualification governs the workflow's "always compute relative improvement" default. Do not invent confidence from best seeds or tiny samples.

Apply its objective result interpretation section before writing insights: answer the requested comparison with the observed ranking and named-comparator differences, then distinguish uncertainty and practical criteria. Verify metric direction, population, denominator and aggregation before combining results. Preserve supported gains and regressions; do not substitute an unsupported favourable or unfavourable judgment for either. Recheck evidence when challenged and state the precise correction or disagreement. These rules qualify the workflow's generic insight and significance wording; short result queries need only a proportionate answer.
<!-- EI-GOVERNANCE:END -->


# Analyze Experiment Results

Analyze: $ARGUMENTS

## Workflow

### Step 1: Locate Results
Find all relevant JSON/CSV result files:
- Check `figures/`, `results/`, or project-specific output directories
- Parse JSON results into structured data

### Step 2: Build Comparison Table
Organize results by:
- **Independent variables**: model type, hyperparameters, data config
- **Dependent variables**: primary metric (e.g., perplexity, accuracy, loss), secondary metrics
- **Delta vs baseline**: always compute relative improvement

### Step 3: Statistical Analysis
- If multiple seeds: report mean +/- std, check reproducibility
- If sweeping a parameter: identify trends (monotonic, U-shaped, plateau)
- Flag outliers or suspicious results

### Step 4: Proactive Case Studies
For a substantive analysis, use [case-study-analysis](../shared-references/case-study-analysis.md):
- Inspect existing per-example predictions, inputs/targets and output assets without waiting for a separate request for samples.
- Add a compact, reproducible selection covering typical cases and available improvements, regressions and shared failures. Match methods on the same inputs and disclose missing outputs and selection coverage.
- Adapt the evidence to the task: confusion examples, residuals, paired images or timestamped video evidence. Show actual predictions/assets and distinguish observations from explanations.
- Relate case patterns to aggregate or clearly defined slice counts; selected examples alone do not establish population rates or a mechanism.
- Put the cases and selection record in the existing report, using small derived panels or references instead of copying large datasets.
If evidence is unavailable, state the gap and smallest useful export while finishing the supported analysis. A narrow numerical/status question or explicit metrics-only request can skip case collection; do not launch new inference just to populate this step.

### Step 5: Generate Insights
For each finding, structure as:
1. **Observation**: what the data shows (with numbers)
2. **Interpretation**: why this might be happening
3. **Implication**: what this means for the research question
4. **Next step**: what experiment would test the interpretation

### Step 6: Update Documentation
If findings are significant:
- Propose updates to project notes or experiment reports
- Draft a concise finding statement (1-2 sentences)

## Carry findings into the next decision

When analysis changes a substantial research choice, preserve the supported gains,
regressions, null findings, case-study evidence and unresolved alternatives in the
existing decision record through [research-manager](../research-manager/SKILL.md).
Record the condition for revisiting it. A completed analysis can justify stopping
or a new investigation without making the original hypothesis successful. For a
requested sustained cycle, use [bounded-inquiry](../shared-references/bounded-inquiry.md);
ordinary metric questions still end with the requested analysis.

## Output Format
Always include:
1. Raw data table
2. Key findings (numbered, concise)
3. Case findings and selection/source references for a substantive analysis, or the specific evidence gap
4. Suggested next experiments (if any)
