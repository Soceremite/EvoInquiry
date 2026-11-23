<!-- EI-WORKFLOW-REFERENCE -->

# Phase 6: Speaker Notes

Read this file when the workflow reaches Phase 6: Speaker Notes through Final Output Summary. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 6: Speaker Notes

For each slide, ensure a `\note{}` block exists with:

1. **What to say** (2-3 complete sentences, conversational tone)
2. **Timing hint** (e.g., "spend 1 minute here", "quick — 20 seconds")
3. **Transition phrase** to the next slide (e.g., "So how do we actually implement this? Let me show you...")

Also generate `slides/speaker_notes.md` as a standalone backup:

```markdown
# Speaker Notes

## Slide 1: Title
[No speaking — wait for introduction]

## Slide 2: Motivation
"Thank you. So let me start with the problem we're trying to solve..."
[Time: 1.5 min]

## Slide 3: Problem Statement
"Specifically, the challenge is..."
→ Transition: "To address this, our key insight is..."
[Time: 1 min]

...
```

**State**: Write `SLIDES_STATE.json` with `phase: 6`.

### Phase 7: PowerPoint Export

Generate an editable PPTX using `python-pptx`:

```bash
python3 -c "import pptx" 2>/dev/null || pip install python-pptx
```

Write `slides/generate_pptx.py` that:

1. Creates a PPTX with correct aspect ratio (16:9 → 13.33" x 7.5"; 4:3 → 10" x 7.5")
2. For each beamer frame:
   - Creates a slide with matching layout
   - Title in venue primary color, bold
   - Bullet points with venue accent color markers
   - Figures embedded as images (from slides/figures/)
   - Speaker notes transferred to PPTX notes field
3. Title slide with special formatting (centered, larger title)
4. Thank You slide with centered text
5. Applies venue color scheme throughout

```bash
cd slides && python3 generate_pptx.py
# Output: slides/presentation.pptx
```

> ⚠️ If `python-pptx` is not installed, skip with a note: "Install `pip install python-pptx` to enable PowerPoint export."

**State**: Write `SLIDES_STATE.json` with `phase: 7`.

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

