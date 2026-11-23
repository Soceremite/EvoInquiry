<!-- EI-WORKFLOW-REFERENCE -->

# Key Rules

Read this file when the workflow reaches Key Rules through Parameter Pass-Through. In commands and examples, interpret relative skill paths from the entrypoint directory.

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
- **Feishu notifications are optional.** If `~/.codex/feishu.json` exists, send notifications. If absent, skip.

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
