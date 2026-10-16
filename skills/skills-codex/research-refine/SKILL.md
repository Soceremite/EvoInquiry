---
name: "research-refine"
description: "Refine a vague research idea into a focused, implementable method proposal using prior work and critical review. Use for method design; experiment-plan designs its tests."
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
For a proposal-only request, finish a compact implementable proposal before
optional elaboration; keep the detailed experiment roadmap for experiment-plan.
If the required reviewer is unavailable or prohibited, save the proposal and
required recovery records with the actual blocked/provisional status. Do not
simulate review rounds, invent review history, or treat a saved draft as review
acceptance. Keep the existing in_progress checkpoint at the pending review phase
and record reviewer availability separately, so a later session can resume.
Reserve time to verify the saved proposal and deliver the response.
<!-- EVO-INQUIRY:END -->


# Refine a Research Method

Turn the user's visible problem and tentative approach into a focused,
implementable proposal. Keep one dominant contribution, prefer the smallest
adequate mechanism, and use modern components only when they address the actual
bottleneck. A detailed experiment roadmap belongs to `experiment-plan`.

## Start with scope and existing work

Read project instructions, the user's constraints, relevant proposal/notes and
`refine-logs/REFINE_STATE.json` if present. Reuse unchanged guidance; batch
independent relevant reads. Ground the proposal in local material first (at most
15 relevant papers/notes); search only when needed and permitted. Report
insufficient coverage instead of asserting novelty from missing literature.

If a checkpoint exists, validate the project and saved artifacts before resuming.
Read the initialization/recovery section of [the full workflow](references/full-workflow.md)
for an existing refinement loop; retain its phase meaning, reviewer continuity,
prior rounds and history. A saved phase denotes work actually completed.

For a fresh task, freeze a **Problem Anchor**: bottom-line problem, must-solve
bottleneck, non-goals, constraints and success condition. Save it with an
`anchor`, round-0, `in_progress` checkpoint before optional expansion. Carry the
anchor verbatim into every proposal and refinement.

## Produce a useful proposal early

On a fresh run, after minimum relevant grounding, save
`refine-logs/round-0-initial-proposal.md`
and update the checkpoint to `phase: proposal`, `round: 0`, `status: in_progress`.
Do this before optional literature expansion or composing long review reports.
Under a supplied time/action limit, reserve capacity for saving, checking and the
final response; stop optional reads when that reserve is reached. An unsaved
analysis is not a deliverable.

Use a compact outline appropriate to the method; combine related items and mark
inapplicable fields rather than inventing components:

- **Problem Anchor and grounded gap:** evidence, closest known work and limits.
- **Method thesis:** one dominant contribution, at most one supporting claim;
  compare a second route only when it is a plausible alternative.
- **Implementation:** exact inputs/outputs, data flow and update/inference rule
  or pseudocode; reused/frozen versus new/trainable components; supervision,
  loss and training assumptions when relevant. Default to at most two new
  trainable components; justify any larger mechanism.
- **Failure handling:** diagnostic, fallback and highest-risk assumptions.
- **Minimal validation:** 1–3 discriminating checks linked to the anchor/claims,
  necessary baseline/ablation and decisive metric; expected evidence is a
  prediction, not a result. Include a simplification or necessity check when
  the proposed complexity makes it relevant.
- **Feasibility and handoff:** explicit compute/data/time assumptions or unknowns;
  must-prove claims and required inputs for later experiment planning.

Do not pad a small method with a generator, latent representation, foundation
model or separate training stage that the problem does not need. Never invent
results, citations, superiority or reviewer feedback.

## Review availability and acceptance

Check whether the required reviewer is available and permitted before loading
review-only prompts and templates. If it can run, read
[the full workflow](references/full-workflow.md) from Phase 2 onward and execute
its bounded review/revise/re-evaluate loop. Its reviewer configuration, scoring
dimensions, raw responses, anchor/simplicity checks, round history and final
outputs remain required. Defaults: `MAX_ROUNDS = 5`, `SCORE_THRESHOLD = 9`.
Only stop early for a real READY verdict at threshold with no unresolved drift;
never replace a required review with an executor self-review.

- **REVIEWER_MODEL = `gpt-6-astra`** — secondary Codex agent.
- Use `spawn_agent` for the first review and `send_input` for later rounds;
  honor an explicit user-specified reviewer/model override.
- **ALWAYS use `reasoning_effort: xhigh`** for all Codex review calls.
- **Save `agent_id` from Phase 2** and use `send_input` for later rounds.
- A same-family review remains provisional; acceptance requires the workflow's
  actual reviewer provenance and evidence closure.

If the reviewer is unavailable or prohibited, save the best supported proposal
and truthful recovery/output records, then finish the requested response. Keep
`phase: proposal` and `status: in_progress` when proposal is the last completed
phase, so review can resume later; keep the actual last completed phase when
resuming existing work. Record `reviewer_availability` and `review_gate: BLOCKED`
separately. For fresh work with no completed review, use null reviewer identity,
null score/verdict and zero executed review rounds. For resumed work, retain
real prior reviewer identities, rounds, scores and verdicts; only the pending
review is blocked. Do not create fictional `round-N-review.md` or
`round-N-refinement.md` files. A saved proposal does not grant review acceptance.

## Save, verify and hand off

Keep the existing `refine-logs/` output names:

- `REFINE_STATE.json`: last completed phase, round, reviewer continuity ID,
  `last_score`, `last_verdict`, `status` and ISO `timestamp`.
- `round-0-initial-proposal.md`, then real per-round review/refinement files only
  for rounds actually performed. Each refinement contains the full proposal.
- `FINAL_PROPOSAL.md`: clean best current proposal, including when not READY.
- `REVIEW_SUMMARY.md`, `REFINEMENT_REPORT.md` and `score-history.md`: actual review
  history, remaining weaknesses and status. With unavailable review, record the
  pending review concisely and preserve any real prior history. Only a fresh run
  with no review has zero rounds and no score; reference the saved proposal
  instead of copying it into several reports.

Before publishing outputs, read the applicable runtime contracts together:
[versioning](../shared-references/output-versioning.md),
[manifest](../shared-references/output-manifest.md) and
[language](../shared-references/output-language.md).
Use the project's existing layout; fixed names navigate to the retained
revision. Preserve prior work and the runtime's manifest policy; ordinary notes
do not require a governance migration. Keep JSON keys and machine markers in
English. For a failed large write, use smaller chunks with available file tools.

Verify the saved proposal and checkpoint, actual output paths and review status.
Report the method, evidence limits, remaining review and saved paths briefly.
Only after the actual loop and its final reporting are complete set
`phase: done`, `status: completed`; an unavailable required review leaves the
loop resumable. A subsequent detailed roadmap or experiment launch needs the
corresponding user scope.
