# Shared research review cycle

Read when running `auto-review-loop`, `auto-review-loop-llm` or
`auto-review-loop-minimax`. The entrypoint selects the backend and its additional
review gates; this reference owns the common cycle and recovery rules.

## Continue the same work

Use the existing `review-stage/REVIEW_STATE.json` and cumulative
`review-stage/AUTO_REVIEW.md`; retain legacy root-level paths when resuming them.
Inspect the producing workflow, raw reviews, pending jobs and relevant evidence
before resuming. A timestamp older than 24 hours prompts reconciliation, never
deletion, a fresh budget or an assumption that a job stopped.

Keep the same `run_id`, completed round count, backend session, pending work and
original resource limits. Legacy state without a run ID gets one identity once,
with that migration recorded; unrelated old receipts cannot satisfy its gates.
Malformed or conflicting state stays intact while its specific recovery issue
is reported. A new invocation after completion has a new ID and preserves the
earlier log; it still needs authorization for any additional work/resources.

For sustained loops, use [bounded-inquiry](bounded-inquiry.md) with the existing
run, including its trajectory checkpoints. A connection failure is not evidence
of termination. Reconcile an actual failed attempt before retrying; preserve
failed attempts, cumulative costs and the original deadline. Do not create a
native host Goal unless the user explicitly requested one.

Do not wrap these review loops in `/loop`, `/schedule`, `CronCreate` or another
external timer: each entrypoint already owns its rounds and reviewer continuity.
Use [external-cadence](external-cadence.md) only for waiting on external facts;
scheduled status checks cannot rerun or replace a review verdict.

## One cycle, backend-specific review

Defaults remain four rounds and a positive threshold of score >= 6/10 **AND**
verdict in `ready | almost`; `not ready` never qualifies. The active entrypoint's
stricter review, trace, acquittal and acceptance requirements remain binding.

1. Read relevant artifacts and changes, then invoke the selected reviewer. Pass
   prior unresolved concerns and their evidence into later rounds. Keep the
   complete raw response and actual model/backend provenance. A failed or
   unavailable review is BLOCKED/ERROR, not an invented score or positive verdict.
2. Extract score, `ready | almost | not ready`, material concerns and minimum
   useful fixes. Agreement or a high score does not resolve a material issue:
   each needs a checked fix or a specific, evidenced scope exclusion.
3. Evaluate closure, remaining budget and information value. Stop for a qualified
   positive assessment only after all material issues are addressed and the
   entrypoint's gates pass. Budget/stall/user stops grant no acquittal. Never add
   objections to justify another round, or change the primary outcome to hide
   an unfavorable result. Label exploratory reframing.
4. Implement authorized, evidence-driven changes with the existing execution
   owners. Reuse valid results and artifacts. Wait for actual terminal evidence
   before treating a pending experiment as complete or launching a replacement.
5. Append the raw review, checked issue dispositions, actions, results and stop
   reason to the cumulative log. Save the state after every round and before a
   pending-job handoff: `run_id`, `round`, `status`, `last_score`, `last_verdict`,
   `pending_experiments`, timestamp, backend/session and original limits where
   established. Refresh reviewer memory when that entrypoint uses it.
6. On termination, set the loop's state to `completed`, save the supported
   findings and remaining unknowns, and return control. Completion, acceptance
   and scientific support remain different judgments. Any acquittal receipt
   is append-only, bound to this run and actual trace, and written only at the
   entrypoint's single designated receipt site.

Reviewer family and independence follow
[reviewer-independence](reviewer-independence.md). An external API or a second
agent alone does not establish cross-family acceptance. Keep actual
accepted/provisional/blocked status; file checks and rendering cannot upgrade it.
