<!-- EI-WORKFLOW-REFERENCE -->

# Phase 5: Codex MCP Review

Read this file when the workflow reaches Phase 5: Codex MCP Review through Phase 7: PowerPoint Export. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 5: Codex MCP Review

Send the slide outline + selected LaTeX frames to GPT-6-Astra xhigh:

```
mcp__codex__codex:
  model: gpt-6-astra
  config: {"model_reasoning_effort": "xhigh"}
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

Apply fixes. Recompile if LaTeX was changed.

> ⚠️ If `mcp__codex__codex` is not available (no OpenAI API key), skip external review and proceed to Phase 6. Note the skip in `SLIDES_STATE.json`.

Save review to `slides/SLIDES_REVIEW.md`.

**State**: Write `SLIDES_STATE.json` with `phase: 5`.

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

