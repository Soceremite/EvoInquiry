<!-- EI-WORKFLOW-REFERENCE -->

# Context

Read this file when the workflow reaches Context through Spotlight (8-12 slides). In commands and examples, interpret relative skill paths from the entrypoint directory.








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

## Optional: Style reference (`— style-ref: <source>`, opt-in)

Lets the user steer the talk's **structural** rhythm (story beats, theorem density, figure density inherited from the source paper) toward a reference paper. **Default OFF — when the user does not pass `— style-ref`, do nothing differently from before.**

Only when `— style-ref: <source>` appears in `$ARGUMENTS`, run the helper FIRST:

```bash
# Resolve $STYLE_HELPER via the canonical strict-safe chain (see
# shared-references/integration-contract.md §2). Policy A — gate:
# unresolved helper means --style-ref cannot be satisfied, so abort.
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.ei/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.ei/repo" 2>/dev/null) || true
fi
STYLE_HELPER=".ei/tools/extract_paper_style.py"
[ -f "$STYLE_HELPER" ] || STYLE_HELPER="tools/extract_paper_style.py"
[ -f "$STYLE_HELPER" ] || { [ -n "${ARIS_REPO:-}" ] && STYLE_HELPER="$ARIS_REPO/tools/extract_paper_style.py"; }
[ -f "$STYLE_HELPER" ] || {
  echo "ERROR: extract_paper_style.py not resolved at .ei/tools/, tools/, \$ARIS_REPO/tools/, or via ~/.ei/repo." >&2
  echo "       Fix: rerun bash tools/install_aris.sh or smart_update.sh (refreshes ~/.ei/repo), export ARIS_REPO, or copy the helper to tools/." >&2
  echo "       --style-ref cannot be satisfied; aborting." >&2
  exit 1
}
STYLE_STATUS=0
CACHE=$(python3 "$STYLE_HELPER" --source "<source>") || STYLE_STATUS=$?
case "$STYLE_STATUS" in
  0) ;;                                       # use $CACHE/style_profile.md as structural guidance
  2) echo "warning: style-ref skipped (missing optional dep)" >&2 ;;
  3) echo "error: --style-ref source failed; aborting slides" >&2 ; exit 1 ;;
  *) echo "error: helper failed unexpectedly; aborting slides" >&2 ; exit 1 ;;
esac
```

Sources accepted: local TeX dir / file, local PDF, arXiv id, http(s) URL. Overleaf URLs/IDs are rejected — clone via `/overleaf-sync setup <id>` first and pass the local clone path.

**Strict rules** (full contract in `tools/extract_paper_style.py` docstring):

- Use `style_profile.md` to align section-budget tendency and theorem-environment density. Talk-type slide count above still takes precedence.
- **Never copy speaker-note prose, slide titles, or examples** from anything reachable through the cache. The talk content is from the user's paper, not the reference.
- **Never pass `— style-ref` (or the cache contents) to the GPT-6-Astra reviewer sub-agent** — the reviewer must judge the talk's clarity on its own merits.

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

