---
name: "paper-figure"
description: "Create publication-quality data plots, tables and qualitative case panels from real experiment outputs. Use for paper result figures, visual comparisons or statistical displays."
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.

For this stage, read [project-governance](../shared-references/project-governance.md). Pin the included result files, execution list and aggregation protocol. Do not redraw historical evidence by resolving current or selecting the best retry.
<!-- EVO-INQUIRY:END -->

> Override for Codex users who want **Gemini**, not a second Codex agent, to act as the reviewer. Install this package **after** `skills/skills-codex/*`.

# Paper Figure: Publication-Quality Plots from Experiment Data

> **Gemini overlay assurance:** verify the actual different-family reviewer before recording `review_independence: cross-family`; `acceptance_status: accepted` requires a positive disposition and the workflow's evidence closure. Negative, unavailable and budget-stop outcomes grant no phase acceptance; same-family responses retain the base provisional contract.

Generate all figures and tables for a paper based on: **$ARGUMENTS**

## Scope and routing

Use this skill directly for a requested data plot or table, including a single
figure without a paper outline. Choose a chart that answers the question.

| Input | Route and deliverable |
| --- | --- |
| Numerical observations, curves or comparisons | This skill: traceable data, editable script, requested vector/raster exports and caption |
| Exact architecture or workflow | `figure-spec`: structured definition and editable SVG |
| Small flow, sequence or relationship diagram | `mermaid-diagram`: editable Mermaid source |
| Conceptual illustration | An available illustration tool; label it as schematic |
| Actual generated samples, photographs or screenshots | Arrange supplied or genuinely produced assets; retain their source |

Read supplied data before choosing the layout. If evidence is missing, provide
an editable plotting script or clearly labeled empty template, and state what
is needed to populate it. Example numbers below are synthetic demonstrations;
never reuse them as project results. Preserve existing figures.

## Evidence and statistical display

- Identify the comparison, metric direction, units, denominator, data subset and
  independent experimental unit. Keep relevant baselines, regressions, failed
  runs and missing observations visible. Missing is not zero.
- Calculate uncertainty from actual independent units and name it in the
  caption (SD, SEM, interval, or range). Means alone cannot supply error bars;
  do not treat tokens or correlated samples as independent training repeats.
- Preserve the planned primary metric. A favorable secondary plot does not
  rescue a failed primary claim. Trace exploratory selections and transforms.
- Mark truncated axes and smoothing; retain raw curves when smoothing could
  affect the interpretation. Use facets or resource/quality trade-offs when
  one ranking would hide a relevant exception.
- Save a standalone script and the exact input selection. A finalized figure
  can use `tools/figure_evidence.py create recipe.json --root PROJECT --output
  figure.manifest.json` to bind inputs, editable source, outputs, transforms and
  caption; `check` detects changed files. This is an identity receipt, not a
  statistical or semantic certificate. Reuse `evidence_check.py` for supported
  literal numeric checks; assess the actual scientific conclusion separately.
- Inspect the rendered artifact at its intended column width for font support,
  clipping, overlaps, distinguishable series, grayscale and accessible colors.
  Record unverified visual checks honestly. Missing fonts/backends call for a
  bounded alternative (SVG, source plus table), not repeated blind generation.

## Case-study panels

For qualitative result figures, read [case-study-analysis](../shared-references/case-study-analysis.md) and reuse the analysis report's selection record. If selection is missing, establish and disclose a reproducible rule before arranging actual assets. Show relevant successes, regressions and shared failures when available; label an explicitly selected illustrative panel and keep its claims within that scope. Do not replace an unfavorable aggregate with favorable examples.

Keep the same sample, conditioning, scale, crop and temporal window across methods, or disclose necessary differences. Include targets/references when they exist, plus sample/run/draw IDs or timestamps. Use genuine outputs; conceptual illustrations cannot stand in for experimental samples. A storyboard supports only its inspected frames and annotations. Save the small panel, editable layout script and selection/source references; reuse the existing figure receipt when binding these files.

## Constants

- **STYLE = `publication`** — Visual style preset. Options: `publication` (default, clean for print), `poster` (larger fonts), `slide` (bold colors)
- **DPI = 300** — Output resolution
- **FORMAT = `pdf`** — Output format. Options: `pdf` or `svg` (vector), `png` (raster fallback)
- **COLOR_PALETTE = `tab10`** — Default matplotlib color cycle. Options: `tab10`, `Set2`, `colorblind` (deuteranopia-safe)
- **FONT_SIZE = 10** — Base font size (matches typical conference body text)
- **FIG_DIR = `figures/`** — Output directory for generated figures
- **REVIEWER_MODEL = `gemini-review`** — Gemini reviewer invoked through the local `gemini-review` MCP bridge. Set `GEMINI_REVIEW_MODEL` if you need a specific Gemini model override.

## Inputs

1. **Requested figure or PAPER_PLAN.md** — use the actual request; an existing outline can supply its figure plan
2. **Experiment data** — JSON files, CSV files, or screen logs in `figures/` or project root
3. **Existing figures** — any manually created figures to preserve

If the figure request is clear, proceed with its relevant data. Ask only for missing information that materially changes the output; do not require a paper outline for a standalone plot.

## Workflow

### Step 1: Read Figure Plan

Use the requested figure, or parse an existing Figure Plan table from PAPER_PLAN.md:

```markdown
| ID | Type | Description | Data Source | Priority |
|----|------|-------------|-------------|----------|
| Fig 1 | Architecture | ... | manual | HIGH |
| Fig 2 | Line plot | ... | figures/exp.json | HIGH |
```

Identify:
- Which figures can be auto-generated from data
- Which need `figure-spec`, Mermaid or supplied qualitative assets
- Which are comparison tables (generate as LaTeX)

### Step 2: Set Up Plotting Environment

Create a shared style configuration script:

```python
# paper_plot_style.py — shared across all figure scripts
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams.update({
    'font.size': FONT_SIZE,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
    'axes.labelsize': FONT_SIZE,
    'axes.titlesize': FONT_SIZE + 1,
    'xtick.labelsize': FONT_SIZE - 1,
    'ytick.labelsize': FONT_SIZE - 1,
    'legend.fontsize': FONT_SIZE - 1,
    'figure.dpi': DPI,
    'savefig.dpi': DPI,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'axes.grid': False,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'text.usetex': False,  # set True if LaTeX is available
    'mathtext.fontset': 'stix',
})

# Color palette
COLORS = plt.cm.tab10.colors  # or Set2, or colorblind-safe

def save_fig(fig, name, fmt=FORMAT):
    """Save figure to FIG_DIR with consistent naming."""
    fig.savefig(f'{FIG_DIR}/{name}.{fmt}')
    print(f'Saved: {FIG_DIR}/{name}.{fmt}')
```

### Step 3: Auto-Select Figure Type

Use this decision tree for data-driven figures (inspired by Imbad0202/academic-research-skills):

| Data Pattern | Recommended Type | Size |
|-------------|-----------------|------|
| X=time/steps, Y=metric | Line plot | 0.48\textwidth |
| Methods × 1 metric | Bar chart | 0.48\textwidth |
| Methods × multiple metrics | Facets / aligned dot plots with explicit units | 0.95\textwidth |
| Two continuous variables | Scatter plot | 0.48\textwidth |
| Matrix / grid values | Heatmap | 0.48\textwidth |
| Distribution comparison | Box/violin plot | 0.48\textwidth |
| Multi-dataset results | Multi-panel (subfigure) | 0.95\textwidth |
| Prior work comparison | LaTeX table | — |

### Step 4: Generate Each Figure

For each figure in the plan, create a standalone Python script:

**Line plots** (training curves, scaling):
```python
# gen_fig2_training_curves.py
from paper_plot_style import *
import json

with open('figures/exp_results.json') as f:
    data = json.load(f)

fig, ax = plt.subplots(1, 1, figsize=(5, 3.5))
ax.plot(data['steps'], data['fac_loss'], label='Factorized', color=COLORS[0])
ax.plot(data['steps'], data['crf_loss'], label='CRF-LR', color=COLORS[1])
ax.set_xlabel('Training Steps')
ax.set_ylabel('Cross-Entropy Loss')
ax.legend(frameon=False)
save_fig(fig, 'fig2_training_curves')
```

**Bar charts** (comparison, ablation):
```python
fig, ax = plt.subplots(1, 1, figsize=(5, 3))
methods = ['Baseline', 'Method A', 'Method B', 'Ours']
values = [82.3, 85.1, 86.7, 89.2]
bars = ax.bar(methods, values, color=[COLORS[i] for i in range(len(methods))])
ax.set_ylabel('Accuracy (%)')
# Add value labels on bars
for bar, val in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{val:.1f}', ha='center', va='bottom', fontsize=FONT_SIZE-1)
save_fig(fig, 'fig3_comparison')
```

**Comparison tables** (LaTeX, for theory papers):
```latex
\begin{table}[t]
\centering
\caption{Comparison of estimation error bounds. $n$: sample size, $D$: ambient dim, $d$: latent dim, $K$: subspaces, $n_k$: modes.}
\label{tab:bounds}
\begin{tabular}{lccc}
\toprule
Method & Rate & Depends on $D$? & Multi-modal? \\
\midrule
\citet{MinimaxOkoAS23} & $n^{-s'/D}$ & Yes (curse) & No \\
\citet{ScoreMatchingdistributionrecovery} & $n^{-2/d}$ & No & No \\
\textbf{Ours} & $\sqrt{\sum n_k d_k / n}$ & No & Yes \\
\bottomrule
\end{tabular}
\end{table}
```

**Architecture/pipeline diagrams**:
- Use `figure-spec` for precise editable component/edge diagrams, or
  `mermaid-diagram` for small flows. Keep their source and actual rendered output.
- Preserve supplied figures and include them in LaTeX when they already satisfy
  the request. Missing external illustration services do not block local SVG.
- Inspect labels and relationships; method structure alone is not empirical
  evidence. Record unavailable rendering checks instead of marking them passed.

### Step 5: Run All Scripts

```bash
# Run all figure generation scripts
for script in gen_fig*.py; do
    python "$script"
done
```

Verify all output files exist and are non-empty.

### Step 6: Generate LaTeX Include Snippets

For each figure, output the LaTeX code to include it:

```latex
% === Fig 2: Training Curves ===
\begin{figure}[t]
    \centering
    \includegraphics[width=0.48\textwidth]{figures/fig2_training_curves.pdf}
    \caption{Training curves comparing factorized and CRF-LR denoising.}
    \label{fig:training_curves}
\end{figure}
```

Save all snippets to `figures/latex_includes.tex` for easy copy-paste into the paper.

### Step 7: Figure Quality Review with REVIEWER_MODEL

Send figure descriptions and captions to Gemini for review:

```
mcp__gemini-review__review_start:
  prompt: |
    Review these figure/table plans for a [VENUE] submission.

    For each figure:
    1. Is the caption informative and self-contained?
    2. Does the figure type match the data being shown?
    3. Is the comparison fair and clear?
    4. Any missing baselines or ablations?
    5. Would a different visualization be more effective?

    [list all figures with captions and descriptions]
```

After this start call, immediately save the returned `jobId` and poll `mcp__gemini-review__review_status` with a bounded `waitSeconds` until `done=true`. Treat the completed status payload's `response` as the reviewer output, and save the completed `threadId` for any follow-up round.

### Step 8: Quality Checklist

Before finishing, verify each figure (from pedrohcgs/claude-code-my-workflow):

- [ ] Font size readable at printed paper size (not too small)
- [ ] Colors distinguishable in grayscale (print-friendly)
- [ ] **No title inside figures** — titles go only in LaTeX `\caption{}` (from pedrohcgs)
- [ ] Legend does not overlap data
- [ ] Axis labels have units where applicable
- [ ] Axis labels are publication-quality (not variable names like `emp_rate`)
- [ ] Figure width fits single column (0.48\textwidth) or full width (0.95\textwidth)
- [ ] PDF output is vector (not rasterized text)
- [ ] No matplotlib default title (remove `plt.title` for publications)
- [ ] Serif font matches paper body text (Times / Computer Modern)
- [ ] Colorblind-accessible (if using colorblind palette)

## Output

```
figures/
├── paper_plot_style.py          # shared style config
├── gen_fig1_architecture.py     # per-figure scripts
├── gen_fig2_training_curves.py
├── gen_fig3_comparison.py
├── fig1_architecture.pdf        # generated figures
├── fig2_training_curves.pdf
├── fig3_comparison.pdf
├── latex_includes.tex           # LaTeX snippets for all figures
└── TABLE_*.tex                  # standalone table LaTeX files
```

## Output Protocols

> Follow these shared protocols for all output files:
> - **[Output Versioning Protocol](../shared-references/output-versioning.md)** — write timestamped file first, then copy to fixed name
> - **[Output Manifest Protocol](../shared-references/output-manifest.md)** — log every output to MANIFEST.md
> - **[Output Language Protocol](../shared-references/output-language.md)** — respect the project's language setting

## Key Rules

- **Every figure must be reproducible** — save the generation script alongside the output
- **Do NOT hardcode data** — always read from JSON/CSV files
- **Use vector format (PDF)** for all plots — PNG only as fallback
- **No decorative elements** — no background colors, no 3D effects, no chart junk
- **Consistent style across all figures** — same fonts, colors, line widths
- **Colorblind-safe** — verify with https://davidmathlogic.com/colorblind/ if needed
- **One script per figure** — easy to re-run individual figures when data changes
- **No titles inside figures** — captions are in LaTeX only
- **Comparison tables count as figures** — generate them as standalone .tex files

## Figure Type Reference

| Type | When to Use | Typical Size |
|------|------------|--------------|
| Line plot | Training curves, scaling trends | 0.48\textwidth |
| Bar chart | Method comparison, ablation | 0.48\textwidth |
| Grouped bar | Multi-metric comparison | 0.95\textwidth |
| Scatter plot | Correlation analysis | 0.48\textwidth |
| Heatmap | Attention, confusion matrix | 0.48\textwidth |
| Box/violin | Distribution comparison | 0.48\textwidth |
| Architecture | System overview | 0.95\textwidth |
| Multi-panel | Combined results (subfigures) | 0.95\textwidth |
| Comparison table | Prior bounds vs. ours (theory) | full width |

## Acknowledgements

Design pattern (type × style matrix) inspired by [baoyu-skills](https://github.com/jimliu/baoyu-skills). Publication style defaults and figure rules from [pedrohcgs/claude-code-my-workflow](https://github.com/pedrohcgs/claude-code-my-workflow). Visualization decision tree from [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills).
