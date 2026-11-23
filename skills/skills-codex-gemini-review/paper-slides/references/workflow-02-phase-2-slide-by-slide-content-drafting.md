<!-- EI-WORKFLOW-REFERENCE -->

# Phase 2: Slide-by-Slide Content Drafting

Read this file when the workflow reaches Phase 2: Slide-by-Slide Content Drafting through Phase 5: Gemini Review. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 2: Slide-by-Slide Content Drafting

For each slide in the outline, draft the actual content.

**Presentation rules (enforced strictly)**:

| Rule | Rationale |
|------|-----------|
| **One message per slide** | If a slide has two ideas, split it |
| **Max 6 lines per slide** | More than 6 lines = wall of text |
| **Max 8 words per line** | Audience reads, not listens, if text is long |
| **Sentence fragments, not sentences** | "Improves F1 by 3.2%" not "Our method improves the F1 score by 3.2 percentage points" |
| **Figure slides: figure ≥60% area** | The figure IS the content; bullets are annotations |
| **Bold key numbers** | "Achieves **94.3%** accuracy" |
| **Progressive disclosure** | Use `\pause` or `\onslide` for complex slides |
| **No Related Work slide** | Unless invited talk (30+ min) |

**For each slide, produce**:
1. `\frametitle{}`
2. Content (itemize or figure + caption)
3. `\note{}` with speaker text (if SPEAKER_NOTES=true)

### Phase 3: Generate Slides LaTeX

Create `slides/main.tex` using beamer.

**Template structure**:

```latex
\documentclass[aspectratio=169]{beamer}

% Venue theme
\usepackage{xcolor}
\definecolor{primary}{HTML}{VENUE_PRIMARY}
\definecolor{accent}{HTML}{VENUE_ACCENT}

% Clean theme
\usetheme{default}
\usecolortheme{default}
\setbeamercolor{frametitle}{fg=primary}
\setbeamercolor{title}{fg=primary}
\setbeamercolor{structure}{fg=accent}
\setbeamercolor{itemize item}{fg=primary}
\setbeamercolor{itemize subitem}{fg=accent}
\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{footline}{
  \hfill\insertframenumber/\inserttotalframenumber\hspace{2mm}\vspace{2mm}
}

% Packages
\usepackage{graphicx,amsmath,booktabs}
\graphicspath{{figures/}}

% Speaker notes (if enabled)
% \setbeameroption{show notes on second screen=right}

% Metadata
\title{PAPER TITLE}
\author{Author 1 \and Author 2}
\institute{Affiliation}
\date{VENUE YEAR}

\begin{document}

\begin{frame}
\titlepage
\end{frame}

% Content slides follow...

\begin{frame}{Motivation}
\begin{itemize}
  \item Bullet point 1
  \item Bullet point 2
  \item \textbf{Key insight in bold}
\end{itemize}
\note{Speaker note: explain the motivation...}
\end{frame}

% Figure slide example
\begin{frame}{Method Overview}
\centering
\includegraphics[width=0.85\textwidth]{method_overview.pdf}
\vspace{0.5em}
\begin{itemize}
  \item Key annotation about the figure
\end{itemize}
\note{Walk through the figure left to right...}
\end{frame}

% ... more slides ...

\begin{frame}{Thank You}
\centering
{\Large Questions?}\\[2em]
Paper: [URL or QR placeholder]\\
Code: [URL or QR placeholder]
\end{frame}

\end{document}
```

**Symlink figures**:
```bash
ln -sf ../paper/figures/*.pdf slides/figures/ 2>/dev/null
ln -sf ../paper/figures/*.png slides/figures/ 2>/dev/null
```

**Key formatting rules**:
- Title font: ≥28pt, venue primary color
- Body font: ≥20pt
- Footnotes: ≥14pt
- No navigation symbols
- Frame numbers in bottom-right
- Clean white background (no gradients, no decorative elements)

### Phase 4: Compile Slides

```bash
cd slides && latexmk -$ENGINE -interaction=nonstopmode main.tex
```

**Error handling loop** (max 3 attempts):
1. Parse error log
2. Fix: missing package, undefined command, file not found, overfull boxes
3. Recompile

**Verification**:
```bash
# Check slide count matches outline
pdfinfo slides/main.pdf | grep Pages
```

If page count differs significantly from outline (>2 slides off), investigate.

**State**: Write `SLIDES_STATE.json` with `phase: 4`.

### Phase 5: Gemini Review

Send the slide outline + selected LaTeX frames to Gemini:

```
mcp__gemini-review__review_start:
  prompt: |
    Review this [TALK_TYPE] presentation ([TALK_MINUTES] min) for [VENUE].

    Evaluate using these criteria (score 1-5 each):

    1. **Story arc** — Does the talk build a compelling narrative? (Problem → insight → method → evidence → takeaway)
    2. **Slide density** — Any slides with too much text? (Max 6 lines, 8 words/line)
    3. **Time budget** — Is [N] slides realistic for [TALK_MINUTES] minutes?
    4. **Figure visibility** — Will figures be readable on a projector?
    5. **Opening hook** — Do slides 2-3 grab attention? (Not "In this paper, we...")
    6. **Takeaway** — Is the final message clear and memorable?
    7. **Progressive build** — Are complex ideas revealed gradually?

    Slide outline:
    [PASTE SLIDE_OUTLINE.md]

    Selected frames (LaTeX):
    [PASTE KEY FRAMES]

    Provide:
    - Score for each criterion
    - Top 3 actionable fixes
    - Overall: Ready to present? (Yes / Needs revision / Major issues)
```

After this start call, immediately save the returned `jobId` and poll `mcp__gemini-review__review_status` with a bounded `waitSeconds` until `done=true`. Treat the completed status payload's `response` as the slide review.

Apply fixes. Recompile if LaTeX was changed.

> ⚠️ If `gemini-review` MCP is not available or Gemini credentials are missing, skip external review and proceed to Phase 6. Note the skip in `SLIDES_STATE.json`.

Save review to `slides/SLIDES_REVIEW.md`.

**State**: Write `SLIDES_STATE.json` with `phase: 5`.

