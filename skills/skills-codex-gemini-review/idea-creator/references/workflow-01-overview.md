<!-- EI-WORKFLOW-REFERENCE -->

# Overview

Read this file when the workflow reaches Overview through Phase 5: Parallel Pilot Experiments (for top 2-3 ideas). In commands and examples, interpret relative skill paths from the entrypoint directory.




> Override for Codex users who want **Gemini**, not a second Codex agent, to act as the reviewer. Install this package **after** `skills/skills-codex/*`.

# Research Idea Creator

> **Gemini overlay assurance:** verify the actual different-family reviewer before recording `review_independence: cross-family`; `acceptance_status: accepted` requires a positive disposition and the workflow's evidence closure. Negative, unavailable and budget-stop outcomes grant no phase acceptance; same-family responses retain the base provisional contract.

Generate publishable research ideas for: $ARGUMENTS

## Overview

Given a broad research direction from the user, systematically generate, validate, and rank concrete research ideas. Standalone, Phase 1's landscape survey is **inline** (WebSearch — it does not invoke `/research-lit`); Phases 4-5 invoke `/novelty-check`, `/run-experiment`, and `/monitor-experiment` for validation and pilots. For the full sub-skill pipeline (`/research-lit` → idea generation → `/novelty-check` → `/research-review`), run `/idea-discovery` (Workflow 1), which orchestrates this skill.

## Constants

Pilot duration, reminders, compute and concurrency follow the
[session resource table](../../shared-references/resource-budget.md) and current plan.
Prefer the smallest informative pilot; ideas or planning alone do not launch one.

- **MAX_PILOT_IDEAS = 3** — Pilot at most 3 ideas in parallel. Additional ideas are validated on paper only.
- **REVIEWER_MODEL = `gemini-review`** — Gemini reviewer invoked through the local `gemini-review` MCP bridge for brainstorming and critique. Set `GEMINI_REVIEW_MODEL` if you need a specific Gemini model override.

- **OUTPUT_DIR = `idea-stage/`** — Directory for idea output files.

## Workflow

### Phase 1: Landscape Survey

Map the research area to understand what exists and where the gaps are.

1. **Scan local paper library first**: Check `papers/` and `literature/` in the project directory for existing PDFs. Read first 3 pages of relevant papers to build a baseline understanding before searching online. This avoids re-discovering what the user already knows.

2. **Search recent literature** using WebSearch:
   - Top venues in the last 2 years (NeurIPS, ICML, ICLR, ACL, EMNLP, etc.)
   - Recent arXiv preprints (last 6 months)
   - Use 5+ different query formulations
   - Read abstracts and introductions of the top 10-15 papers

2. **Build a landscape map**:
   - Group papers by sub-direction / approach
   - Identify what has been tried and what hasn't
   - Note recurring limitations mentioned in "Future Work" sections
   - Flag any open problems explicitly stated by multiple papers

3. **Identify structural gaps**:
   - Methods that work in domain A but haven't been tried in domain B
   - Contradictory findings between papers (opportunity for resolution)
   - Assumptions that everyone makes but nobody has tested
   - Scaling regimes that haven't been explored
   - Diagnostic questions that nobody has asked

### Phase 2: Idea Generation (brainstorm with external LLM)

Use the local `gemini-review` MCP bridge for divergent thinking:

```
mcp__gemini-review__review_start:
  prompt: |
    You are a senior ML researcher brainstorming research ideas.

    Research direction: [user's direction]

    Here is the current landscape:
    [paste landscape map from Phase 1]

    Key gaps identified:
    [paste gaps from Phase 1]

    Generate 8-12 concrete research ideas. For each idea:
    1. One-sentence summary
    2. Core hypothesis (what you expect to find and why)
    3. Minimum viable experiment (what's the cheapest way to test this?)
    4. Expected contribution type: empirical finding / new method / theoretical result / diagnostic
    5. Risk level: LOW (likely works) / MEDIUM (50-50) / HIGH (speculative)
    6. Estimated effort: days / weeks / months

    Prioritize ideas that are:
    - Testable with moderate compute (8x RTX 3090 or less)
    - Likely to produce a clear positive OR negative result (both are publishable)
    - Simple at the core: one mechanism, few moving parts — an idea a colleague
      could restate after hearing it once. If the novelty only appears once a
      second module or an extra gate is added, that is packaging, not novelty.
    - Aware of the 10-15 papers above — awareness, not avoidance. Differentiation
      is the novelty check's job later, not a constraint on brainstorming.

    "Apply X to Y" is legitimate when the application would reveal something
    non-obvious — judge it by what it reveals, not by the template. A direct,
    well-executed attack on a central problem is a valid idea when nobody has
    executed it well; do not steer around crowded areas — proximity to strong
    work is a sign the problem matters, not that it is taken.

    Be genuinely creative: surprising connections, inverted assumptions,
    questions nobody thought to ask. Creativity is a new angle on a problem
    that matters — not an obscure corner nobody visits, and not extra modules
    stacked until something looks new. Generate first, filter later — the
    filters come after you, and they are strict enough. A bold, creative idea
    with a named risk beats a hedged, complicated one with none. A great idea
    is one where the answer matters regardless of which way it goes.
```

After this start call, immediately save the returned `jobId` and poll `mcp__gemini-review__review_status` with a bounded `waitSeconds` until `done=true`. Treat the completed status payload's `response` as the brainstorm output, and save the completed `threadId` for follow-up critique in Phase 4.

### Phase 3: Mechanical consolidation + objective feasibility gate

> This phase does NOT judge idea quality, novelty, or impact — those are the
> job of the Phase-4 cross-model reviewer (a different model family). Dropping
> ideas here on a same-family novelty or impact call would pre-filter the
> reviewer's input with same-family judgment — the opposite of why ARIS uses a
> cross-model reviewer at all. Phase 3 only (a) clusters near-duplicate ideas
> and (b) drops ideas that are OBJECTIVELY out of budget; everything else
> passes through ANNOTATED, not eliminated.

1. **Objective feasibility gate (safe to gate here)**: drop an idea ONLY on a
   mechanical, budget-based fact — estimated compute > 1 week of available GPU
   time, OR a dataset that is provably unavailable. Do NOT drop on
   "implementation looks complex" — annotate complexity instead.

2. **Novelty signal — ANNOTATE, do not eliminate**: do 2-3 targeted searches
   and attach a `prior_work` note (what looks related, with links). This is
   input for the Phase-4 reviewer, not a filter; full `/novelty-check` runs in
   Phase 4. Do NOT drop an idea here because it "might already be done."

3. **Impact signal — ANNOTATE, do not eliminate**: attach a one-line `so_what`
   note (why the result would matter either way). Do NOT drop on a same-family
   "a reviewer wouldn't care" call — that is exactly what the Phase-4
   cross-model reviewer is for.

Every feasible, non-duplicate idea — with its `prior_work` and `so_what`
annotations — proceeds to Phase 4, where the cross-model reviewer does the
quality/novelty narrowing.

### Phase 4: Deep Validation (for top ideas)

For each surviving idea, run a deeper evaluation:

1. **Novelty check**: Use the `/novelty-check` workflow (multi-source search + Gemini cross-verification) for each idea

2. **Critical review**: Use `mcp__gemini-review__review_reply_start` with the saved completed `threadId`:
   ```
   mcp__gemini-review__review_reply_start:
     threadId: [saved completed threadId from Phase 2]
     prompt: |
       Here are our top ideas after filtering:
       [paste surviving ideas with novelty check results]

       For each, make the strongest case both ways:
       - What is the best case FOR it — what would make this the paper people cite?
       - What's the strongest objection a reviewer would raise?
       - What's the most likely failure mode?
       - Rank by expected information and upside within the pilot budget — which results would matter most, whichever way they come out?
       - Which 2-3 would you actually work on?

       Keep the original candidate traceable; revise a hypothesis explicitly when evidence warrants it. An objection is answered or recorded as a named
       risk on the idea — never absorbed by adding a module, a gate, or a
       qualifier. A bold idea with a named risk outranks a hedged idea with
       none, and complexity added since the brainstorm is a red flag, not
       progress. And do not let your picks be uniformly the safest — if
       the top set is all LOW-risk, name the high-upside idea that most
       deserves a pilot slot and what result would convince you.
   ```

   After this start call, immediately save the returned `jobId` and poll `mcp__gemini-review__review_status` with a bounded `waitSeconds` until `done=true`. Treat the completed status payload's `response` as the follow-up critique.

3. **Combine rankings**: Merge your assessment with Gemini's ranking. Select top 2-3 ideas for pilot experiments.

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

