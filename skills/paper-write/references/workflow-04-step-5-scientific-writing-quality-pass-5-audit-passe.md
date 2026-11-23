<!-- EI-WORKFLOW-REFERENCE -->

# Step 5: Scientific Writing Quality Pass (5 audit passes)

Read this file when the workflow reaches Step 5: Scientific Writing Quality Pass (5 audit passes) through Step 8: Final Checks. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Step 5: Scientific Writing Quality Pass (5 audit passes)

After drafting all sections, run five sequential audit passes. Based on Sainani's "Writing in the Sciences" methodology: every word must earn its place.

**Pass 1: Clutter Extraction** — Strip sentences to cleanest components.

| Cluttered phrase | Replace with |
|------------------|--------------|
| Due to the fact that | Because |
| In order to | To |
| A number of | Several |
| It is worth noting that | (delete — just state the point) |
| It is important to note that | (delete) |
| At the present time | Now |
| On the basis of | Based on |
| In light of the fact that | Because |
| Have an effect on | Affect |
| Give rise to | Cause |

Also remove redundancies: "completely eliminate" → "eliminate", "future plans" → "plans", "unexpected surprise" → "surprise".

Remove AI-isms: delve, pivotal, landscape, tapestry, underscore, noteworthy, intriguingly.

**Pass 2: Active Voice and Verb Vitality** — Identify who did what.

- Spot passive: "to-be" verb + past participle ("was observed", "were analyzed")
- Convert: find the actor, reconstruct as Subject–Verb–Object
- Resurrect smothered verbs (nominalizations):
  - "We made an investigation" → "We investigated"
  - "Failure of the system occurs" → "The system fails"
  - "Provides a description of" → "Describes"

Passive voice IS acceptable for: established facts, methods where agent is irrelevant, or when required by venue style.

**Pass 3: Sentence Architecture** — Structure and flow. Vary paragraph shape:
if every paragraph runs problem → method → benefit → summary, the mold numbs
the reader — break it.

- Flag sentences > 40 words for splitting
- Ensure subject and verb are close together (no long parenthetical insertions between them)
- Put familiar context first, new information later
- Place the most important point near the end of the sentence
- Let each paragraph do one job
- Don't start consecutive sentences with "This" or "We"
- Check paragraph transitions — each paragraph's first sentence should connect to the previous

**Pass 4: Keyword Consistency** — The Banana Rule.

**Do not call a "banana" an "elongated yellow fruit" to avoid repetition.** If the Methods say "obese group," the Results must not switch to "heavier group." Synonym variation for technical terms forces the reader to wonder whether a new category has been introduced.

- Extract all key terms from Method section (group names, variable names, technique names, abbreviations)
- Verify exact same terms appear in Results, Discussion, Tables, Figure captions
- Flag every synonym substitution for a defined term
- Acronym austerity: flag non-standard acronyms created only for convenience; verify every acronym is defined at first use

**Pass 5: Numerical and Citation Integrity**

- Does sample size (N) in Abstract match Table 1?
- Do percentages in Results match raw numbers in Tables?
- Are significant figures consistent and appropriate?
- Do Figure graphics match Table values?
- Flag statistics cited only through secondary sources (reviews, textbooks) — recommend verifying primary source

### Step 6: Cross-Review with REVIEWER_MODEL

Send the complete draft to GPT-6-Astra xhigh:

```
mcp__codex__codex:
  model: gpt-6-astra
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    Review this [VENUE] paper draft (main body, excluding appendix).

    Judge claim calibration in BOTH directions. Recommend narrowing only when the
    current scope or modality exceeds the evidence; do not ask for extra hedges
    around a supported result. Flag stacked hedges, self-defence ("we do not
    claim"), instruction confessions ("we do not address X"), and generic caveats
    outside Limitations as writing defects to remove. Tone fixes must never alter
    facts, negation, modality, scope, comparison direction, or numbers.

    Focus on:
    1. Does each claim from the intro have supporting evidence?
    2. Is the writing clear, concise, and free of AI-isms?
    3. Any logical gaps or unclear explanations?
    4. Does it fit within [MAX_PAGES] pages (to end of Conclusion)?
    5. Is related work sufficiently comprehensive (≥1 page)?
    6. For theory papers: are proof sketches adequate?
    7. Are figures/tables clearly described and properly referenced?
    8. Would a skim reader understand the contribution from the title, abstract, introduction, and Figure 1?

    For each issue, specify: severity (CRITICAL/MAJOR/MINOR), location, and fix.

    [paste full draft text]
```

Apply CRITICAL and MAJOR fixes. Document MINOR issues for the user.

### Step 7: Reverse Outline Test (from Research-Paper-Writing-Skills)

After drafting all sections:

1. **Extract topic sentences** — pull the first sentence of every paragraph
2. **Read them in sequence** — they should form a coherent narrative on their own
3. **Check claim coverage** — every claim from the Claims-Evidence Matrix must appear
4. **Check evidence mapping** — every experiment/figure must support a stated claim
5. **Fix gaps** — if a topic sentence doesn't advance the story, rewrite the paragraph

### Step 8: Final Checks

Before declaring done:

- [ ] All `\ref{}` and `\label{}` match (no undefined references)
- [ ] All citation commands (`\citep{}`/`\citet{}` for ML conferences, `\cite{}` for IEEE) have corresponding BibTeX entries
- [ ] No author information in anonymous mode
- [ ] Figure/table numbering is correct
- [ ] Page count within MAX_PAGES (main body to Conclusion end)
- [ ] No TODO/FIXME/XXX markers left in the text
- [ ] No `[VERIFY]` markers left unchecked
- [ ] Abstract is self-contained (understandable without reading the paper)
- [ ] Title is specific and informative (not generic)
- [ ] Related work is ≥1 full page
- [ ] references.bib contains ONLY cited entries (no bloat)
- [ ] **No stale section files** — every .tex in `sections/` is `\input`ed by `main.tex`
- [ ] **Section files match main.tex** — file numbering and `\input` paths are consistent
- [ ] Venue-specific required sections/checklists satisfied (read `../shared-references/venue-checklists.md` if needed)
- [ ] A skim reader can recover the main claim from the title, abstract, introduction, and Figure 1/captions

