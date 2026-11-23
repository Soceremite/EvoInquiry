<!-- EI-WORKFLOW-REFERENCE -->

# Phase 4: Deep Validation (the cross-model jury)

Read this file when the workflow reaches Phase 4: Deep Validation (the cross-model jury) through Output Protocols. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 4: Deep Validation (the cross-model jury)

**This is the jury.** It receives the FULL annotated candidate set from
Phase 3 (Phase 3 no longer pre-narrows on quality), and the **cross-model
reviewer — not the executor — does the quality/novelty narrowing.** Run the
steps in this order so the cheap cross-model triage gates the expensive
per-idea novelty search:

1. **Cross-model triage (devil's advocate) — ranks ALL candidates first.**
   Use the selected reviewer backend (see Reviewer Calling Convention). For
   `codex`, use `mcp__codex__codex-reply` on the **default-model thread**
   from Phase 2 (the triage bundle carries the full union, so no context is
   lost from the second model's thread). For `manual`, use
   `mcp__manual_review__review_reply` with the saved threadId. For the
   `codex` backend, write the full annotated candidate set to
   `idea-stage/codex_triage_bundle.md` and send only a path-based follow-up:
   ```
   Read the idea-triage bundle at <absolute path to
   idea-stage/codex_triage_bundle.md> and follow all instructions in it.
   ```
   For the `manual` backend, attach that same bundle if possible; otherwise
   paste its contents inline. Bundle contents:
   ```
   Here is the full annotated candidate set (deduped, budget-feasible):
   [write all candidates with their prior_work / so_what / effort_note notes]

   For each, make the strongest case both ways:
   - What is the best case FOR it — what would make this the paper people cite?
   - What's the strongest objection a reviewer would raise?
   - What's the most likely failure mode?
   - Is the prior_work note a real novelty problem, or differentiable?
   - Rank by expected information and upside within the pilot budget — which results would matter most, whichever way they come out?
   - Which 2-3 would you actually work on, and why?

   Keep the original candidate traceable; revise a hypothesis explicitly when evidence warrants it. An objection is answered or recorded as a named
   risk on the idea — never absorbed by adding a module, a gate, or a
   qualifier. A bold idea with a named risk outranks a hedged idea with
   none, and complexity added since the brainstorm is a red flag, not
   progress. And do not let your picks be uniformly the safest — if the
   top set is all LOW-risk, name the high-upside idea that most deserves a
   pilot slot and what result would convince you.
   ```
   The reviewer's ranking allocates the scarce pilot slots; it is not an elimination verdict — feasible ideas not selected remain candidates. The executor
   does not eliminate candidates on its own taste before or instead of this.

2. **Novelty check — on the reviewer's top picks only.** Run the
   `/novelty-check` workflow (multi-source search + cross-model verification)
   on the ideas the triage ranked worth pursuing. This bounds the expensive
   multi-source search to the survivors instead of every candidate, while
   keeping the novelty verdict cross-model.

3. **Select for pilots**: take the top 2-3 ideas that survive both the
   cross-model triage and the novelty check forward to Phase 5.

### Phase 5: Parallel Pilot Experiments (for top 2-3 ideas)

Before committing to a full research effort, run cheap pilot experiments to get empirical signal. This is the key differentiator from paper-only validation.

1. **Design pilots**: For each top idea, define the minimal experiment that would give a positive or negative signal:
   - Single seed, small scale (e.g., small dataset subset, fewer epochs)
   - Estimate compute and storage before launch; fit the smallest informative design to the session policy.
   - Decision criterion defined upfront — including what a positive, negative, and null outcome would each teach. Metric improvement is not required for a diagnostic contribution.

2. **Deploy**: Use `/run-experiment`; choose parallelism from current capacity and the session policy.

3. **Collect results**: Use `/monitor-experiment`; review at meaningful milestones or selected reminders. Keep monitoring and stopping with the existing execution owner under the shared resource contract. Once pilots actually exit, compare:
   - Which ideas showed positive signal?
   - Which showed null/negative results? Classify each: core-hypothesis refuted, informative negative (often publishable), or underpowered pilot — do not eliminate by sign alone.
   - Any surprising findings that suggest a pivot?
   - Observed compute use against the current plan and session policy

4. **Re-rank based on empirical evidence**: Update the idea ranking using pilot results. An idea with strong pilot signal jumps ahead of a theoretically appealing but untested idea.

Note: Skip this phase if the ideas are purely theoretical or if no GPU is available. Flag skipped ideas as "needs pilot validation" in the report.

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

**Skip this phase entirely if `research-wiki/` does not exist.**

This is critical for spiral learning — without it, `ideas/` stays empty and re-ideation has no memory.

`$WIKI_SCRIPT` was resolved in Phase 0 above. If Phase 0 did not run
(no `research-wiki/`), skip this phase. The idea page is written by a
**deterministic helper (`upsert_idea`)** — NOT freehand markdown — so **every
generation, including a re-run with updated constraints, records reliably**
(one CLI call per idea, not a prose step the model can skip). `upsert_idea`
writes the page, wires the `inspired_by` / `addresses_gap` edges, and rebuilds
index + query_pack in a single call. **Default skip-on-exist**: a re-ideation
run records NEW ideas without clobbering an existing idea whose `outcome`
`/result-to-claim` may already have enriched. If `$WIKI_SCRIPT` is empty
(helper unreachable) the ideas are **NOT** recorded and a single WARN prints
(fix: `bash tools/install_aris.sh` or `export ARIS_REPO`).

```
if research-wiki/ exists AND [ -n "$WIKI_SCRIPT" ]:
    for each idea in recommended_ideas + eliminated_ideas:
        # recommended → --stage proposed; eliminated-at-ideation → --stage archived.
        # --outcome stays "pending" (the experiment verdict, negative/mixed/positive,
        # is set LATER by /result-to-claim — never guessed here).
        python3 "$WIKI_SCRIPT" upsert_idea research-wiki/ \
          --slug "<stable-idea-id>" --title "<idea title>" \
          --stage "<proposed|archived>" --outcome pending \
          --thesis "<core hypothesis / direction>" \
          --risks "<novelty / feasibility risks; why killed if eliminated>" \
          --based-on "<paper:slug,paper:slug2>" --target-gaps "<G2,G10>" \
          || echo "WARN: upsert_idea failed for <id> (continuing; audit/report unaffected)" >&2
    python3 "$WIKI_SCRIPT" log research-wiki/ "idea-creator wrote N ideas (M recommended, K eliminated)"
elif research-wiki/ exists AND [ -z "$WIKI_SCRIPT" ]:
    echo "WARN: ideas NOT recorded — research_wiki.py unreachable (see Phase 0). Fix: bash tools/install_aris.sh or smart_update.sh (refreshes ~/.ei/repo), or export ARIS_REPO." >&2
```

## Output Protocols

> Follow these shared protocols for all output files:
> - **[Output Composition Protocol](../../shared-references/output-composition.md)** — see composed-mode note below
> - **[Output Versioning Protocol](../../shared-references/output-versioning.md)** — write timestamped file first, then copy to fixed name
> - **[Output Manifest Protocol](../../shared-references/output-manifest.md)** — maintain `MANIFEST.md` only above the 15-artifact threshold (not "log every output")
> - **[Output Language Protocol](../../shared-references/output-language.md)** — respect the project's language setting

> **Composed mode** — if invoked with `— composed: <canonical-report-path>` (e.g.
> `/idea-discovery` passes `— composed: idea-stage/IDEA_REPORT.md`), that report is the
> single canonical deliverable: fold the literature survey, novelty notes, and any
> external-review conclusions into it as sections/appendices instead of emitting
> `LIT_LANDSCAPE.md` / `RESEARCH_REVIEW.md` / `MANIFEST.md` alongside. Pilot scratch is
> disposable (keep the script + one results file; delete launcher logs and redundant
> `*_summary.json`); review traces stay in `.ei/traces/…` and the report cites the
> path. **Default (no `— composed:` directive): standalone — write `IDEA_REPORT.md` and
> any other documented files as normal.** Never infer composed mode from a report file
> merely existing. Full rules:
> [`shared-references/output-composition.md`](../../shared-references/output-composition.md).

