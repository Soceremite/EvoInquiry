<!-- EI-WORKFLOW-REFERENCE -->

# Context

Read this file when the workflow reaches Context through Poster-talk (5-8 slides). In commands and examples, interpret relative skill paths from the entrypoint directory.





# Paper Slides: From Paper to Conference Talk

Generate conference presentation slides from: **$ARGUMENTS**

## Context

This skill runs **after** Workflow 3 (`/paper-writing`). It takes a compiled paper and generates a presentation slide deck for conference oral talks, spotlight presentations, or poster lightning talks.

Unlike posters (single page, visual-first), slides tell a **temporal story**: each slide builds on the previous one, with progressive revelation of the research narrative. A good talk makes the audience understand *why this matters* before showing *what was done*.

## Constants

- **VENUE = `NeurIPS`** — Target venue, determines color scheme. Supported: `NeurIPS`, `ICML`, `ICLR`, `AAAI`, `ACL`, `EMNLP`, `CVPR`, `ECCV`, `GENERIC`. Override via argument.
- **TALK_TYPE = `spotlight`** — Talk format. Options: `oral` (15-20 min), `spotlight` (5-8 min), `poster-talk` (3-5 min), `invited` (30-45 min). Determines slide count and content depth.
- **TALK_MINUTES = 15** — Talk duration in minutes. Auto-adjusts slide count (~1 slide/minute for oral, ~1.5 slides/minute for spotlight). Override explicitly if needed.
- **ASPECT_RATIO = `16:9`** — Slide aspect ratio. Options: `16:9` (default, modern projectors), `4:3` (legacy).
- **SPEAKER_NOTES = true** — Generate `\note{}` blocks in beamer and corresponding PPTX notes. Set `false` for clean slides without notes.
- **PAPER_DIR = `paper/`** — Directory containing the compiled paper.
- **OUTPUT_DIR = `slides/`** — Output directory for all slide files.
- **REVIEWER_MODEL = `gpt-6-astra`** — Model used via Codex MCP for slide review.
- **AUTO_PROCEED = false** — At each checkpoint, **always wait for explicit user confirmation**.
- **COMPILER = `latexmk`** — LaTeX build tool.
- **ENGINE = `pdflatex`** — LaTeX engine. Use `xelatex` for CJK text.

> 💡 Override: `/paper-slides "paper/" — talk_type: oral, venue: ICML, minutes: 20, aspect: 4:3`

## Talk Type → Slide Count

| Talk Type | Duration | Slides | Content Depth |
|-----------|----------|:------:|---------------|
| `poster-talk` | 3-5 min | 5-8 | Problem + 1 method slide + 1 result + conclusion |
| `spotlight` | 5-8 min | 8-12 | Problem + 2 method + 2 results + conclusion |
| `oral` | 15-20 min | 15-22 | Full story with motivation, method detail, experiments, analysis |
| `invited` | 30-45 min | 25-40 | Comprehensive: background, related work, deep method, extensive results, discussion |

## Venue Color Schemes

Same as `/paper-poster-html`:

| Venue | Primary | Accent | Background | Text |
|-------|---------|--------|------------|------|
| NeurIPS | `#8B5CF6` | `#2563EB` | `#FFFFFF` | `#1E1E1E` |
| ICML | `#DC2626` | `#1D4ED8` | `#FFFFFF` | `#1E1E1E` |
| ICLR | `#059669` | `#0284C7` | `#FFFFFF` | `#1E1E1E` |
| CVPR | `#2563EB` | `#7C3AED` | `#FFFFFF` | `#1E1E1E` |
| GENERIC | `#334155` | `#2563EB` | `#FFFFFF` | `#1E1E1E` |

## State Persistence (Compact Recovery)

Persist state to `slides/SLIDES_STATE.json` after each phase:

```json
{
  "phase": 3,
  "venue": "NeurIPS",
  "talk_type": "spotlight",
  "slide_count": 10,
  "codex_thread_id": "019cfcf4-...",
  "status": "in_progress",
  "timestamp": "2026-03-18T15:00:00"
}
```

**On startup**: if `SLIDES_STATE.json` exists with `"status": "in_progress"` and within 24h → resume. Otherwise → fresh start.

## Workflow

### Phase 0: Input Validation & Setup

1. **Check prerequisites**:
   ```bash
   which pdflatex && which latexmk
   ```

2. **Verify paper exists**:
   ```bash
   ls $PAPER_DIR/main.tex || ls $PAPER_DIR/main.pdf
   ls $PAPER_DIR/sections/*.tex
   ls $PAPER_DIR/figures/
   ```

3. **Backup existing slides**: if `slides/` exists, copy to `slides-backup-{timestamp}/`

4. **Create output directory**: `mkdir -p slides/figures`

5. **Detect CJK**: if paper contains Chinese/Japanese/Korean, set ENGINE to `xelatex`

6. **Determine slide count**: from TALK_TYPE and TALK_MINUTES using the table above

7. **Check for resume**: read `slides/SLIDES_STATE.json` if it exists

**State**: Write `SLIDES_STATE.json` with `phase: 0`.

### Phase 1: Content Extraction & Slide Outline

Read `paper/sections/*.tex` and build a slide-by-slide outline.

**Slide template by talk type**:

#### Oral (15-22 slides)

| Slide | Purpose | Content Source | Figure? |
|:-----:|---------|----------------|:-------:|
| 1 | Title | Paper metadata | No |
| 2 | Outline | Section headers | No |
| 3-4 | Motivation & Problem | Introduction | Optional |
| 5 | Key Insight | Introduction (contribution) | No |
| 6-9 | Method | Method section | Yes (hero figure) |
| 10-14 | Results | Experiments | Yes (per slide) |
| 15-16 | Analysis / Ablations | Experiments | Yes |
| 17 | Limitations | Conclusion | No |
| 18 | Conclusion / Takeaway | Conclusion | No |
| 19 | Thank You + QR | — | QR code |

#### Spotlight (8-12 slides)

| Slide | Purpose | Content Source | Figure? |
|:-----:|---------|----------------|:-------:|
| 1 | Title | Paper metadata | No |
| 2-3 | Problem + Why It Matters | Introduction | Optional |
| 4 | Key Insight | Contribution | No |
| 5-6 | Method | Method (condensed) | Yes (hero) |
| 7-9 | Results | Key results only | Yes |
| 10 | Takeaway | Conclusion | No |
| 11 | Thank You + QR | — | QR code |

#### Poster-talk (5-8 slides)

| Slide | Purpose | Content Source | Figure? |
|:-----:|---------|----------------|:-------:|
| 1 | Title | Paper metadata | No |
| 2 | Problem | Introduction (1 slide) | No |
| 3 | Method | Method (1 slide) | Yes |
| 4-5 | Results | Key result only | Yes |
| 6 | Takeaway + QR | Conclusion | QR |

**For each slide, specify**:
- Title (max 8 words)
- 3-5 bullet points (max 8 words each)
- Figure reference (if any) from paper/figures/
- Speaker note (2-3 sentences of what to say)
- Time allocation (in seconds)

**Output**: `slides/SLIDE_OUTLINE.md`

**🚦 Checkpoint:**

```
📊 Slide outline ready:
- Talk type: [TALK_TYPE] ([TALK_MINUTES] min)
- Slide count: [N] slides
- Figures used: [N] from paper/figures/
- Time budget: [breakdown]

Slide-by-slide outline:
1. [Title slide]
2. [Motivation — 1.5 min]
3. [Problem statement — 1 min]
...

Proceed to drafting? Or adjust the outline?
```

**⛔ STOP HERE and wait for user response.** This is the most critical checkpoint — the outline determines the entire talk flow.

Options:
- **"go"** → proceed to Phase 2
- **adjustments** (e.g., "merge slides 3-4", "add a demo slide", "cut the ablation") → revise
- **"stop"** → save to `slides/SLIDE_OUTLINE.md`

**State**: Write `SLIDES_STATE.json` with `phase: 1`.

