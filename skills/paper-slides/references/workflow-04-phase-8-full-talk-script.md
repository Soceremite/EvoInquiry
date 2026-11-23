<!-- EI-WORKFLOW-REFERENCE -->

# Phase 8: Full Talk Script

Read this file when the workflow reaches Phase 8: Full Talk Script through Parameter Pass-Through. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 8: Full Talk Script

Generate `slides/TALK_SCRIPT.md` — a complete, word-for-word script for the talk.

This is different from speaker notes (brief reminders). The talk script is a **full manuscript** that can be read aloud or used for practice.

```markdown
# Talk Script: [Paper Title]

**Venue**: [VENUE] [YEAR]
**Talk type**: [TALK_TYPE] ([TALK_MINUTES] min)
**Total slides**: [N]

---

## Slide 1: Title [0:00 - 0:15]

*[Wait for chair introduction]*

"Thank you [chair name]. I'm [author] from [affiliation], and today I'll be talking about [short title]."

---

## Slide 2: Motivation [0:15 - 1:30]

"Let me start with the problem. [Describe the real-world motivation in accessible terms]. This matters because [impact statement].

The current state of the art approaches this with [brief existing approach]. But there's a fundamental limitation: [gap statement]."

→ *Transition*: "So what's our key insight?"

---

## Slide 3: Key Insight [1:30 - 2:30]

"Our key observation is that [core insight in one sentence].

This leads us to propose [method name], which [one-sentence description]."

→ *Transition*: "Let me walk you through how this works."

---

## Slide 4-N: [Continue for each slide...]

...

---

## Slide [N]: Thank You [TALK_MINUTES:00]

"To summarize: we've shown that [main result]. The key takeaway is [memorable final message].

The paper and code are available at the QR code on screen. I'm happy to take questions."

---

## Time Budget Summary

| Slide | Topic | Duration | Cumulative |
|:-----:|-------|:--------:|:----------:|
| 1 | Title | 0:15 | 0:15 |
| 2 | Motivation | 1:15 | 1:30 |
| 3 | Key Insight | 1:00 | 2:30 |
| ... | ... | ... | ... |
| N | Thank You | 0:15 | [TALK_MINUTES]:00 |

**Total**: [sum] min (target: [TALK_MINUTES] min)

---

## Anticipated Q&A

### Q1: How does this compare to [strongest baseline]?
**A**: "[Specific comparison with numbers]. Our advantage is particularly clear in [specific scenario], where we see [X%] improvement."

### Q2: What are the main limitations?
**A**: "[Honest answer]. We see this as [future work direction]."

### Q3: How computationally expensive is this?
**A**: "[Training/inference cost]. Compared to [baseline], our method requires [comparison]."

### Q4: Does this generalize to [related domain]?
**A**: "[Answer based on paper's discussion section]."

### Q5: What's the most surprising finding?
**A**: "[Interesting insight from the experiments]."

### Q6: How sensitive is the method to [hyperparameter/design choice]?
**A**: "[Reference ablation study if available]."

### Q7: What's the next step for this research?
**A**: "[Future work from conclusion]."

### Q8: [Domain-specific question]
**A**: "[Answer]."
```

### Final Output Summary

```
📊 Slide generation complete:
- Talk type: [TALK_TYPE] ([TALK_MINUTES] min) for [VENUE]
- Files:
  slides/
  ├── main.tex              # Beamer LaTeX source
  ├── main.pdf              # Compiled slides (primary output)
  ├── presentation.pptx     # Editable PowerPoint
  ├── SLIDE_OUTLINE.md      # Slide-by-slide outline
  ├── SLIDES_REVIEW.md      # GPT-6-Astra review feedback
  ├── speaker_notes.md      # Per-slide speaker notes
  ├── TALK_SCRIPT.md        # Full word-for-word talk script + Q&A
  ├── SLIDES_STATE.json     # State persistence
  ├── generate_pptx.py      # PPTX generation script
  └── figures/              # Symlinked from paper/figures/

Next steps:
1. Practice with TALK_SCRIPT.md (read aloud, time yourself)
2. Edit presentation.pptx for visual tweaks (animations, custom graphics)
3. Review Anticipated Q&A section before the talk
4. Do a dry run with a colleague
```

**State**: Write `SLIDES_STATE.json` with `phase: 8, status: "completed"`.

## Recommended Follow-up: `/slides-polish`

After this skill produces the initial Beamer + PPTX, the typical drift is
**typography proportion + per-slide layout**, not content. Run
`/slides-polish` as a focused post-generation polish phase: it does
per-page Codex review against a reference visual (e.g., a prior academic
talk), bumps PPTX fonts to projector-readable sizes, fixes text-frame
overflow, and applies a fix-pattern catalog (italic style leaks, em-dash
spacing, image aspect ratio, Chinese-font hints, anonymity placeholders).

`/slides-polish` is read-only on content (no claim / number / citation
edits) and preserves speaker notes verbatim. Invocation:

```
/slides-polish slides/ — reference: <ref-pdf> [— style: generic | why-rf | <venue>]
```

Skip it for short decks (< 5 slides) or when a complete redesign is
needed (re-run `/paper-slides` instead).

## Key Rules

- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.
- **One message per slide.** If a slide has two ideas, split it into two slides.
- **Do NOT fabricate data.** All numbers must come from `paper/sections/*.tex`.
- **Bullet points only** — never full sentences on slides. Sentence fragments are fine.
- **Figure slides: figure ≥60% of slide area.** The figure IS the content.
- **Progressive disclosure**: Use `\pause` or `\onslide` for complex method slides.
- **De-AI polish**: Remove watch words from all slide text and talk script.
- **Do NOT hallucinate citations.** Reference only papers cited in the paper.
- **Opening hook matters**: Never start with "In this paper, we..." — start with the problem or a provocative question.
- **Font size minimums**: Title ≥28pt, body ≥20pt, footnotes ≥14pt.
- **Feishu notifications are optional.** If `~/.claude/feishu.json` exists, send notifications. If absent, skip.

## Parameter Pass-Through

```
/paper-slides "paper/" — talk_type: oral, venue: ICML, minutes: 20, aspect: 4:3, notes: false
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `venue` | NeurIPS | Conference for color scheme |
| `talk_type` | spotlight | oral/spotlight/poster-talk/invited |
| `minutes` | 15 | Talk duration |
| `aspect` | 16:9 | Aspect ratio (16:9 / 4:3) |
| `notes` | true | Generate speaker notes |
| `engine` | pdflatex | LaTeX engine |
| `auto proceed` | false | Skip checkpoints |
