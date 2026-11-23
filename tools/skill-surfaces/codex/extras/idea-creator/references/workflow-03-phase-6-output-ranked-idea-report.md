<!-- EI-WORKFLOW-REFERENCE -->

# Phase 6: Output — Ranked Idea Report

Read this file when the workflow reaches Phase 6: Output — Ranked Idea Report through Review Tracing. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 6: Output — Ranked Idea Report

Write a structured report to `idea-stage/IDEA_REPORT.md`:

**Lead every recommended idea with its method, in plain language.** Before any hypothesis, novelty score, or claim, state in 2–4 concrete steps what we actually build / train / run — no jargon, no claim-IDs. The reader must understand *what we do* before *what we claim*; claims (hypothesis, validation, expected outcome) come after and read as the method's acceptance criteria.

```markdown
# Research Idea Report

**Direction**: [user's research direction]
**Generated**: [date]
**Ideas evaluated**: X generated → Y survived filtering → Z piloted → W recommended

## Landscape Summary
[3-5 paragraphs on the current state of the field]

## Recommended Ideas (ranked)

### Idea 1: [title]
- **Method (what we actually do)**: [2–4 concrete steps in plain language — what we build / train / run. No jargon, no claim-IDs, no hypothesis yet. Lead with this so the reader grasps the approach first.]
- **Hypothesis**: [one sentence]
- **Minimum experiment**: [concrete description]
- **Expected outcome**: [what success/failure looks like]
- **Novelty**: X/10 — closest work: [paper]
- **Feasibility**: [compute, data, implementation estimates]
- **Risk**: LOW/MEDIUM/HIGH
- **Contribution type**: empirical / method / theory / diagnostic
- **Pilot result**: [POSITIVE: metric +X% / NEGATIVE: no signal / SKIPPED: needs GPU]
- **Reviewer's likely objection**: [strongest counterargument]
- **Why we should do this**: [1-2 sentences]

### Idea 2: [title]
...

## Eliminated Ideas (for reference)
| Idea | Reason eliminated |
|------|-------------------|
| ... | Already done by [paper] |
| ... | Requires > 1 week GPU time |
| ... | Result wouldn't be interesting either way |

## Pilot Experiment Results
| Idea | GPU | Time | Key Metric | Signal |
|------|-----|------|------------|--------|
| Idea 1 | GPU 0 | 45 min | +2.3% CE | POSITIVE |
| Idea 2 | GPU 1 | 30 min | -0.1% CE | NEGATIVE |
| Idea 3 | GPU 2 | 1.5 hr | +0.8% CE | WEAK POSITIVE |

## Suggested Execution Order
1. Start with Idea 1 (highest decision value after the pilot)
2. Idea 3 as backup (weak signal, may need larger scale to confirm)
3. Idea 2 eliminated by pilot — negative result documented

## Next Steps
- [ ] Scale up Idea 1 to full experiment (multi-seed, full dataset)
- [ ] If confirmed, invoke /auto-review-loop for full iteration
```

## Phase 7: Write Ideas to Research Wiki (if active)

Skip this phase entirely if `research-wiki/` does not exist.

This is critical for spiral learning: without it, `ideas/` stays empty and re-ideation has no memory.

The idea page is written by the **deterministic `upsert_idea` helper** — NOT freehand
markdown — so **every generation, including a re-run with updated constraints, records
reliably** (one helper call per idea, not a prose step the model can skip). `upsert_idea`
writes the page, wires the `inspired_by`/`addresses_gap` edges, and rebuilds index +
query_pack in a single call. Default **skip-on-exist**: a re-ideation run records NEW
ideas without clobbering an existing idea whose `outcome` `/result-to-claim` may already
have enriched. `--outcome` stays `pending` at creation (the experiment verdict is set
later by `/result-to-claim`, never guessed here). If `WIKI_SCRIPT` is unavailable, the
ideas are NOT recorded and a single WARN is reported (fix: install ARIS `research_wiki.py`).

```text
if research-wiki/ exists AND WIKI_SCRIPT is available:
    for each recommended (stage proposed) and eliminated (stage archived) idea:
        python3 "$WIKI_SCRIPT" upsert_idea research-wiki/ --slug "<stable-idea-id>" \
             --title "<idea title>" --stage "<proposed|archived>" --outcome pending \
             --thesis "<core hypothesis / direction>" \
             --risks "<novelty / feasibility risks; why killed if eliminated>" \
             --based-on "<paper:slug,paper:slug2>" --target-gaps "<G2,G10>"
    log: "idea-creator wrote N ideas (M recommended, K eliminated)"
else if research-wiki/ exists AND WIKI_SCRIPT unavailable:
    report: ideas NOT recorded — ARIS research_wiki.py unreachable
```

Edge semantics (wired by `upsert_idea` itself): `idea:<id> --inspired_by--> paper:<slug>`
and `idea:<id> --addresses_gap--> gap:<id>`.

## Output Protocols

**Composition:** default is standalone and writes the normal ranked report. If
and only if `— composed: <canonical-report-path>` is present, fold unique idea,
pilot, and reviewer findings into that report and do not emit overlapping
standalone summaries. `— standalone` always wins; never infer composition from
an old report already existing. Traces and reusable pilot artifacts remain.
See [`output-composition.md`](../../shared-references/output-composition.md).

> Follow these shared protocols for all output files:
> - **[Output Versioning Protocol](../../shared-references/output-versioning.md)** — write timestamped file first, then copy to fixed name
> - **[Output Manifest Protocol](../../shared-references/output-manifest.md)** — log outputs only above the manifest threshold
> - **[Output Language Protocol](../../shared-references/output-language.md)** — respect the project's language setting

## Key Rules

- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.

- The user provides a DIRECTION, not an idea. Your job is to generate the ideas.
- Quantity first, quality second: brainstorm broadly, then narrow only to allocate pilot budget — annotate the rest, don't paper-kill them.
- A good negative result is just as publishable as a positive one. Prioritize ideas where the answer matters regardless of direction.
- Don't fall in love with any idea before validating it — but let evidence do the killing, not anticipated objections.
- Always estimate compute cost. An idea that needs 1000 GPU-hours is not actionable for most researchers.
- "Apply X to Y" is legitimate when Y can reveal a non-obvious interaction, failure mode, or finding — judge the revelation, not the template.
- Include eliminated ideas in the report — they save future time by documenting dead ends.
- **If the user's direction is broad (e.g., "NLP"), use Phase 1 to derive 2-3 concrete frames and generate across them — ask the user only when a missing constraint would materially change the pilot slate.** A good direction is 1-2 sentences specifying the problem, domain, and constraint — e.g., "factorized gap in discrete diffusion LMs" or "sample efficiency of offline RL with image observations". Without sufficient specificity, generated ideas will be too vague to run experiments on.

## Composing with Other Skills

After this skill produces the ranked report:
```
/idea-creator "direction"     → ranked ideas
/novelty-check "top idea"     → deep novelty verification (already done in Phase 4, but user can re-run)
/research-review "top idea"   → external critical feedback
implement                     → write code
/run-experiment               → deploy to GPU
/auto-review-loop             → iterate until submission-ready
```

## Review Tracing

After each `spawn_agent` or `send_input` reviewer call, save the trace following `../shared-references/review-tracing.md`. Include the reviewer route, saved agent id, prompt summary, raw output path, selected ideas, and rejected ideas.
