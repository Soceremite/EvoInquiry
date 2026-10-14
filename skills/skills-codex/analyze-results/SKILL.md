---
name: "analyze-results"
description: "Analyse existing experiment results and fair comparisons: seed coverage, failures, variability, effect uncertainty and appropriate gains. Use for numerical result interpretation or comparison logs."
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.

Ordinary interpretation, confounds, and missing-metric caveats belong in the analysis. For authorized analysis followed by planning, apply [task-scope](../shared-references/task-scope.md) and complete those outputs without an incidental formal claim workflow.

For this stage, read [project-governance](../shared-references/project-governance.md). Resolve fixed execution/spec/environment/evaluator refs once. List included and excluded attempts and apply the predeclared slot aggregation; show failed/missing seeds and protocol/environment differences. current is navigation only.
For result comparisons, load [comparative-experiments](../shared-references/comparative-experiments.md). Reconstruct all declared seed slots and attempts; show counts, exclusions, failures and protocol differences. Separate run variability from effect uncertainty and name independent/paired units. Use absolute metric differences; compute relative gains only for meaningful scales with a valid nonzero baseline, otherwise report them undefined or inappropriate. This qualification governs the workflow's "always compute relative improvement" default. Do not invent confidence from best seeds or tiny samples.
<!-- EVO-INQUIRY:END -->


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

### Step 4: Generate Insights
For each finding, structure as:
1. **Observation**: what the data shows (with numbers)
2. **Interpretation**: why this might be happening
3. **Implication**: what this means for the research question
4. **Next step**: what experiment would test the interpretation

### Step 5: Update Documentation
If findings are significant:
- Propose updates to project notes or experiment reports
- Draft a concise finding statement (1-2 sentences)

## Output Format
Always include:
1. Raw data table
2. Key findings (numbered, concise)
3. Suggested next experiments (if any)

