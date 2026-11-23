<!-- EI-WORKFLOW-REFERENCE -->

# Phase 2: Idea Generation (brainstorm with external LLM)

Read this file when the workflow reaches Phase 2: Idea Generation (brainstorm with external LLM) through Phase 5: Parallel Pilot Experiments (for top 2-3 ideas). In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 2: Idea Generation (brainstorm with external LLM)

Use a secondary Codex agent for divergent thinking:

```
spawn_agent:
  model: REVIEWER_MODEL
  reasoning_effort: xhigh
  message: |
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

Save the agent id for follow-up.

Then spawn the **same bundle once more** with `model: gpt-5.5` (same xhigh
reasoning, a fresh agent) and take the union — the two models fail differently
as generators, and the union keeps either model's taste from capping the pool.
Save both agent ids; Phase 4's `send_input` follow-ups go to the default-model
agent. Tag each candidate with the model that produced it; merge both sets by
mechanical dedup only — never drop a candidate for being "weak" (that is the
Phase-4 verdict). If the second spawn errors (model unavailable on this
account), print one WARN line and continue single-model.

Save a Review Tracing record for this `spawn_agent` call following `../shared-references/review-tracing.md`, including the landscape summary, prompt summary, raw idea list path, reviewer route, and saved agent id.

### Phase 3: Mechanical consolidation + objective feasibility gate

> This phase does NOT judge idea quality, novelty, or impact — those are the
> job of the Phase-4 fresh reviewer (same-family provisional in the base mirror). Dropping
> ideas here on a same-family novelty or impact call would pre-filter the
> reviewer's input with same-family judgment — the opposite of why ARIS uses a
> fresh reviewer at all. Phase 3 only (a) clusters near-duplicate ideas
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
   fresh reviewer is for.

Every feasible, non-duplicate idea — with its `prior_work` and `so_what`
annotations — proceeds to Phase 4, where the fresh reviewer does the
quality/novelty narrowing.

### Phase 4: Deep Validation (for top ideas)

For each surviving idea, run a deeper evaluation:

1. **Novelty check**: Use the `/novelty-check` workflow (multi-source search + GPT-6-Astra cross-verification) for each idea

2. **Critical review**: Use GPT-6-Astra via `send_input` (same agent):
   ```text
   send_input:
     target: [saved reviewer id from the earlier idea review]
     message: |
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

3. **Combine rankings**: Merge your assessment with GPT-6-Astra's ranking. Select top 2-3 ideas for pilot experiments.

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

