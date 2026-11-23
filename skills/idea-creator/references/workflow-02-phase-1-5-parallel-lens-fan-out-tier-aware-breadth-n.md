<!-- EI-WORKFLOW-REFERENCE -->

# Phase 1.5: Parallel lens fan-out (Tier-aware) — breadth, not verdict

Read this file when the workflow reaches Phase 1.5: Parallel lens fan-out (Tier-aware) — breadth, not verdict through Phase 3: Mechanical consolidation + objective feasibility gate. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 1.5: Parallel lens fan-out (Tier-aware) — breadth, not verdict

Idea generation benefits from **breadth**: more independent analytic angles
surface more candidate ideas. This skill fans out *candidate generation*
across analytic **lenses**, then funnels every candidate through the single
Phase-4 cross-model jury. Fan-out widens the jury's input; it never makes the
accept/reject decision. This follows
[`shared-references/fan-out-pattern.md`](../../shared-references/fan-out-pattern.md);
the verdict stays cross-model per
[`shared-references/acceptance-gate.md`](../../shared-references/acceptance-gate.md)
(idea novelty/quality is a Type-B verdict — same-family generation is fine,
same-family *acquittal* is not).

**Lenses** (the structural-gap angles from Phase 1, step 3):
`method-transfer` (works in domain A, untried in B) · `contradiction`
(conflicting findings to resolve) · `untested-assumption` (everyone assumes,
nobody tested) · `scaling-regime` (unexplored regime) · `diagnostic`
(question nobody asked). This set is a floor, not a ceiling — add a
domain-specific lens when the direction warrants.

**Tier-portable dispatch** (the Phase-4 jury downstream is identical on every tier):
- **Tier 1** (Workflow available): spawn one **Claude subagent per lens**;
  each runs the Phase-1 survey *through its lens* and the Phase-2 generation
  prompt *restricted to that lens*, returning candidates as structured output.
- **Tier 2** (Agent tool, no Workflow): spawn the same per-lens subagents via
  the Agent tool.
- **Tier 3** (no spawning): enumerate the lenses sequentially in one pass —
  the original single-thread behavior, made explicit. No capability assumed.

> **Why the lens shards are Claude, not Codex.** Generation is candidate
> production, not a verdict, so same-family is safe — and Codex MCP is
> **serial** (concurrent codex calls hang), so spending its scarce capacity
> on parallel generation is both unsafe-to-parallelize and wasteful. Reserve
> Codex for the one Phase-4 jury call. On Tier 1/2 the lens subagents are the
> generators; the single Phase-2 codex brainstorm below still runs once as an
> optional cross-model *seed* (a generator, not a judge), and its ideas join
> the merged pool.

**Per-shard output** (the generation-fan-out schema from
[`fan-out-pattern.md`](../../shared-references/fan-out-pattern.md) — `shard_id` +
`candidates[]` + per-item `dedup_key`):
```json
{"shard_id": "<lens id>", "candidates": [{"summary": "...", "hypothesis": "...",
  "mve": "...", "contribution_type": "...", "risk": "...", "effort": "...",
  "dedup_key": "<hypothesis slug — the mechanical-dedup identity>"}]}
```

**Merge + mechanical dedup**: union all lenses' ideas; cluster near-identical
ideas by hypothesis (mechanical similarity only — **never** drop one for being
"weak"; weakness is a Phase-4 verdict, not a merge step). The deduped union is
the candidate set that enters Phase 3.

### Phase 2: Idea Generation (brainstorm with external LLM)

Use the selected reviewer backend (see Reviewer Calling Convention) for divergent thinking.

For the `codex` backend, **do not inline the full landscape + gaps prompt**
once it stops being tiny. Write the full brainstorming request to
`idea-stage/codex_brainstorm_bundle.md`, then keep the MCP prompt short:

```
mcp__codex__codex:
  model: REVIEWER_MODEL
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    Read the idea-generation bundle at <absolute path to
    idea-stage/codex_brainstorm_bundle.md> and follow all instructions in it.
```

Run the bundle through **two reviewer models** and take the union — the two
fail differently as generators, and the union keeps either model's taste from
capping the pool:

1. Once with the default reviewer model (`gpt-6-astra` today), as above.
2. Once more with `model: "gpt-5.5"` — same `xhigh` effort, same bundle, a
   fresh thread. Save both threadIds; Phase 4's triage follow-up goes to the
   default-model thread.

Tag each candidate with the model that produced it, then merge both sets the
same way the lens shards merge: union, cluster near-identical ideas by
hypothesis, and never drop a candidate for being "weak" — weakness is a
Phase-4 verdict, not a merge step.

If the second call errors (older codex-cli, or the model is unavailable on
this account), print one WARN line and continue single-model. The union is an
upgrade, not a new requirement.

*For `manual` backend:* use `mcp__manual_review__review` with the same bundle
contents. If the manual-review UI supports attachments, attach
`idea-stage/codex_brainstorm_bundle.md`; otherwise paste the bundle contents
inline. Save the returned `threadId` for Phase 4 follow-up.

Bundle contents:

```
    You are a senior ML researcher brainstorming research ideas.

    Research direction: [user's direction]

    Here is the current landscape:
    [write the Phase-1 landscape map into this bundle file]

    Key gaps identified:
    [write the Phase-1 gap summary into this bundle file]

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

### Phase 3: Mechanical consolidation + objective feasibility gate

> **This phase does NOT judge idea quality, novelty, or impact.** Those are
> Type-B verdicts reserved for the Phase-4 cross-model jury (see
> [`shared-references/acceptance-gate.md`](../../shared-references/acceptance-gate.md)).
> Eliminating ideas here on a same-family novelty or impact call would
> pre-filter the jury's input with same-family quality judgment — exactly
> what [`fan-out-pattern.md`](../../shared-references/fan-out-pattern.md) forbids.
> Phase 3 only (a) finishes the mechanical dedup from the fan-out merge and
> (b) drops ideas that are **objectively** out of budget. Everything else
> passes through **annotated, not eliminated** — the jury decides.

1. **Objective feasibility gate (Type-A — safe same-model)**: drop an idea
   ONLY on a mechanical, budget-based fact:
   - estimated compute > 1 week of available GPU time, OR
   - requires a dataset that is provably unavailable.
   These are objective resource facts. Do **not** drop on "implementation
   looks complex" — annotate complexity as `effort_note` instead.

2. **Novelty signal — ANNOTATE, do not eliminate**: for each surviving idea,
   do 2-3 targeted searches and attach a `prior_work` note (what looks
   related, with links). This is *input for the jury*, not a filter. The
   authoritative novelty verdict is Phase 4's `/novelty-check` (multi-source +
   cross-model). Do **not** drop an idea here because it "might already be
   done."

3. **Impact signal — ANNOTATE, do not eliminate**: attach a one-line
   `so_what` note (why the result would matter either way). Do **not** drop on
   a same-family "a reviewer wouldn't care" call — "would a reviewer care?" is
   *precisely* the question the Phase-4 cross-model devil's-advocate asks.
   Forward the note; let the jury rule.

Every feasible, non-duplicate idea — carrying its `prior_work`, `so_what`, and
`effort_note` annotations — proceeds to Phase 4. Typically only the
budget-infeasible are dropped; the cross-model jury, not the executor, does
the quality narrowing.

