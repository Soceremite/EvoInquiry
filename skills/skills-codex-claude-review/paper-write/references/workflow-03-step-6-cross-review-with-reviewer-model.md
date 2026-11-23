<!-- EI-WORKFLOW-REFERENCE -->

# Step 6: Cross-Review with REVIEWER_MODEL

Read this file when the workflow reaches Step 6: Cross-Review with REVIEWER_MODEL through Acknowledgements. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Step 6: Cross-Review with REVIEWER_MODEL

Send the complete draft to Claude review:

```
mcp__claude-review__review_start:
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

    For each issue, specify: severity (CRITICAL/MAJOR/MINOR), location, and fix.

    [paste full draft text]
```

After this start call, immediately save the returned `jobId` and poll `mcp__claude-review__review_status` with a bounded `waitSeconds` until `done=true`. Treat the completed status payload's `response` as the reviewer output, and save the completed `threadId` for any follow-up round.

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

## Key Rules

=== CONFIDENT PROSE, HONEST LIMITS (never upgrades claims) ===
1. Calibrate each claim to the evidence's actual scope and modality, then state
   that calibrated claim directly. Necessary assumptions, uncertainty, and
   scope are part of the claim; stacked hedges and defensive throat-clearing
   are not.
2. If the current claim is unsupported, narrow it to a version the evidence
   supports or cut it. Do not substitute a softer-sounding synonym for fixing
   scope, modality, comparison, or aggregation.
3. Put generic caveats and broader boundary discussion in one Limitations
   section. Outside it, remove generic disclaimers such as "further research
   is needed", "may not generalize", and "should be interpreted with caution".
   Claim-defining scope, assumptions, and statistical qualifications stay
   attached to the claims they make true.
4. Aim for 2-4 material, specific limitations (dataset scale, compute regime,
   assumption X). Real ones only — never invent one to meet a count, never
   apologize generically, never repeat the same limitation through the paper.
5. Writing instructions are not manuscript content. "Do not mention X" means
   omit X, not write "we do not address/claim/discuss X". Never expose
   drafting instructions, requested omissions, reviewer feedback, or revision
   history in manuscript prose.
6. Replace self-defence ("we do not claim", "our goal is merely") with a
   positive, evidence-matched statement of what the paper does establish. If
   the defensive sentence carries a real boundary, keep that boundary in the
   claim or Limitations; do not delete truth-conditional content.
7. Tone-only edits never alter facts, negation, modality, scope, assumptions,
   comparison direction, aggregation, numbers, formulas, or citations. Genuine
   overclaims must still be narrowed; supported claims wrapped in redundant
   caution must be stated directly.
8. One causal spine: gap -> question -> insight -> consequence -> evidence ->
   implication. Every section advances it. Explain why the design was chosen, without implying inevitability:
   the gap creates a concrete question, the key insight answers it, the method
   follows from the insight, each major experiment tests a consequence of it,
   and the conclusion states exactly what the evidence establishes.
   Front-load the contribution; never narrate the drafting or revision process.
9. Organize the paper around the research question and what its evidence
   establishes. Preserve prespecified primary questions and metrics. If new
   findings motivate a revised question, label that change and distinguish
   exploratory observations from later independent confirmation.
10. Report favorable and unfavorable primary findings where their claims are
    assessed. Tables stay complete. Explain a tradeoff only when the design
    supports it; material exceptions and truth-conditional limitations belong
    beside the affected claim, even when also discussed in Limitations.
    Do not choose a winning metric after inspecting results or move a core
    failure out of the main result to make the contribution look stronger.
11. Every experiment should inform the research question: support, weaken or
    refute a hypothesis, distinguish mechanisms, establish a boundary, or show
    a useful null result. Material negative findings stay beside affected
    claims. Remove unrelated detail only when that preserves the evidence
    needed to assess the main question; never hide a failed primary outcome.
12. State the actual contribution and its conditions directly. Abstract and
    introduction identify the problem, checked gap, method and strongest
    supported finding. The conclusion states what was learned, including a
    revised hypothesis or useful negative result when warranted. Do not force
    a success story or suppress a material limitation to create a launch.



- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.

- **Do NOT generate author names, emails, or affiliations** — use anonymous block or placeholder
- **Write complete sections, not outlines** — the output should be compilable LaTeX
- **One file per section** — modular structure for easy editing
- **Every claim must cite evidence** — cross-reference the Claims-Evidence Matrix
- **Compile-ready** — the output should compile with `latexmk` without errors (modulo missing figures)
- **Calibrate, don't hedge** — match each claim to its evidence's actual scope and modality, then state it directly; generic caveats live in Limitations only (the CONFIDENT PROSE, HONEST LIMITS block above is the contract)
- **Evidence-matched narrative** — retain the primary question and metrics, report relevant gains and regressions beside their claims, and distinguish exploratory reframing from confirmed findings (rules 9-12 above)
- **Venue style matters** — ML conferences (ICLR/NeurIPS/ICML) use `natbib` (`\citep`/`\citet`); **IEEE venues use `cite` package (`\cite{}`, numeric)**. Never mix.
- **Page limit rules differ by venue** — ML conferences: main body to Conclusion, references/appendix NOT counted. **IEEE: references ARE counted toward the page limit.**
- **Clean bib** — references.bib must only contain entries that are actually `\cite`d
- **Section count is flexible** — match PAPER_PLAN structure, don't force into 5 sections
- **Backup before overwrite** — never destroy existing `paper/` directory without backing up
- **Front-load the contribution** — do not hide the payoff until the experiments or appendix
- **Order results by argument, not by lab notebook** — present experiments in the sequence that best builds the case, never in the order they happened to run
- **Controls and ablations sit next to the claim they test** — not pooled in a distant subsection where the reader has forgotten what was at stake

## Writing Quality Reference

- `../shared-references/writing-principles.md` — story framing, abstract/introduction patterns, sentence-level clarity, reviewer reading order
- `../shared-references/venue-checklists.md` — ICLR/NeurIPS/ICML/IEEE submission requirements to check before declaring done
- `../shared-references/citation-discipline.md` — stricter fallback for ambiguous citations

Principles from [Research-Paper-Writing-Skills](https://github.com/Master-cai/Research-Paper-Writing-Skills):

1. **One message per paragraph** — each paragraph makes exactly one point
2. **Topic sentence first** — the first sentence states the paragraph's message
3. **Explicit transitions** — connect paragraphs with logical connectors
4. **Reverse outline test** — extract topic sentences; they should form a coherent narrative

De-AI patterns from [kgraph57/paper-writer-skill](https://github.com/kgraph57/paper-writer-skill):

5. **No AI watch words** — delve, pivotal, landscape, tapestry, underscore
6. **No significance inflation** — groundbreaking, revolutionary, paradigm shift
7. **No formulaic structures** — vary sentence openings and transitions

## Acknowledgements

Writing methodology adapted from [Research-Paper-Writing-Skills](https://github.com/Master-cai/Research-Paper-Writing-Skills) (CCF award-winning methodology). Citation verification from [claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) and [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills). De-AI polish from [kgraph57/paper-writer-skill](https://github.com/kgraph57/paper-writer-skill). Backup mechanism from [baoyu-skills](https://github.com/jimliu/baoyu-skills).
