<!-- EI-WORKFLOW-REFERENCE -->

# Poster-talk (5-8 slides)

Read this file when the workflow reaches Poster-talk (5-8 slides) through Phase 4: Compile Slides. In commands and examples, interpret relative skill paths from the entrypoint directory.

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

