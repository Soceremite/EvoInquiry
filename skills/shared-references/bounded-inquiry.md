# Bounded research continuation

Use for authorized sustained work or recovery, within the active workflow's
records, resource bounds and review gates. Advice and small edits need no new
run or contract. These helpers account for declared actions; they do not meter
hardware, terminate processes, create a host Goal or certify research claims.

## Start with the smallest useful investigation

Use current evidence to identify the uncertainty, competing explanations and
observation that would change the next decision. Include null or adverse outcomes.
Initial environment and implementation setup is legitimate work. On later waves,
reuse valid inputs, environments and reviewed recipes; check their scope and
identity once, then read only changed interfaces or evidence. An import probe is
readiness evidence, not a promoted frozen environment. Do not manufacture a
`frozen` label to satisfy an interface. Formal governed execution retains its
[project](project-governance.md) and [environment](environment-stewardship.md)
requirements; a small exploratory task need not rebuild an environment or adopt
that execution system solely for bookkeeping.

Prefer an existing runner with adequate input, attempt and terminal evidence to
a new management adapter. If adapting one, exercise its result-reading and
settlement path with zero-cost fixture outputs before costly dispatch. Scientific
payloads have their own formats; the registry's `read_record` accepts JSON objects
only. Use the public CLI/help for interface discovery before reading implementation.

For an existing owned run with declared limits, attach continuation before costly
preparation, or name an external owner providing equivalent identities,
reservations and recovery. A CLI timeout alone is not equivalent. Use the original
authorized start, including preparation/review, and a task-appropriate closeout
reserve inside that budget. Reuse authorization; missing prerequisites do not
require asking again for actions already authorized.

When a report is requested, save a minimum useful artifact after the first
decisive check and update it during work. Keep current findings, evidence,
unchecked work and the next allowed step. Do not defer all reporting to the end.
Persist completed attempts and economical sample evidence incrementally; use
[case-study-analysis](case-study-analysis.md) without adding inference solely for
a panel. Keep storage/recovery accounting in [experiment-storage](experiment-storage.md).
After each completed wave, save available metrics/cases and settle verified
execution before another dispatch. If the next wave or required review cannot fit,
use the remaining scope for closeout: deliver supported findings, missing requested
outputs and blockers, then capture the handoff after the last relevant change.

Choose each later wave for an unresolved question and the remaining resources;
there is no minimum wave count or runtime. A plan may allow seed/configuration
ranges and evidence-dependent branches. Unchanged work within its reviewed scope
can reuse that review; changed method meaning, data/splits, selection/evaluation
or relevant source needs the applicable checks again. A new action key grants no
authorization. Negative findings may justify a pivot or stop, not retrospective
success for the original hypothesis.

Inspect relevant prior decisions before a costly repeat. The optional read-only
`research_memory.py --root <project> --query <question> --source <decisions.md>`
finds candidates in selected Markdown or existing wiki JSONL. Verify original
scope, evidence and revisit conditions. Store decisions with the existing owner
using [research-decisions](research-decisions.md); retrieved text is not permission.

## Use the existing action owner

Public CLI: `python <package>/tools/research_control.py --root <project> --run-id <id> <command>`.
It requires an existing run, creates no scheduler and leaves review statuses intact.

| Command | Contract |
| --- | --- |
| `configure --objective <deliverable> --limits <limits.json>` | Limits: `max_actions`, `wall_seconds`, `max_attempts_per_key`, `resources` (unit → bound). Optional `--started-at <timezone-aware-ISO>` and `--closeout-seconds <seconds>`. Existing clock/limits stay fixed; old callers reserve zero closeout time. |
| `inspect` | Read current phase, evidence, reservations and original timing. Bound actual process/reviewer timeouts by `timing.dispatch_seconds_remaining`. `READY` is neither resource authorization nor success. |
| `claim --request <action.json>` | Fields: `action_key`, `phase`, `question`, `costs` for every unit, optional fixed `input_refs`. Only `claim=new` permits dispatch; `existing` requires inspecting that attempt. |
| `finish --request <completion.json>` | Fields: `action_id`, terminal `outcome` (`succeeded`, `failed`, `cancelled`), observed `actual_costs`, fixed `result_refs`, `reason`. Verify actual termination first. Success requires evidence; costs are observations, not estimates clipped to reservations. |
| `settle-execution --request <settlement.json>` | For registered executions: `action_id`, `execution_run_id`, observed `actual_costs`, optional `result_refs`/`reason`. Verifies the existing terminal execution and derives its process outcome; never launches. |
| `stop --reason <reason>` | Records a stop; does not kill jobs, release live reservations, accept phases or modify a native Goal. |

For registered execution, prepare its frozen snapshot with the existing
`execution_registry.py prepare --request <request.json>`, binding
`workflow_run_id` to the original run. Include that returned `snapshot_ref` in
the action's `input_refs` before launch. Use `execution_registry.py launch` for
new dispatch and `settle-execution` afterward or on recovery. Settlement verifies
that binding plus terminal/input/output identities, attaches the terminal ref and
records explicit observed costs. It accepts result-file references without
assuming their payload schema. Repeating identical settlement is idempotent,
even after the wall deadline. Older unbound actions still need the existing
manual `finish` path after actual execution/ownership inspection; do not rewrite
their original inputs or rerun to repair accounting.

`RECONCILE` means verify the original execution, process/queue, outputs and leases
before retry. If reservation preceded launch but no execution exists, establish
that fact before cancellation and a permitted retry. Uncertain process identity,
timeout or missing heartbeat cannot release costs or justify duplicate work.
`REVIEW_REQUIRED` retains the workflow gate; `EVIDENCE_CHANGED` needs source
reconciliation. Exhausted wall/action limits stop dispatch; a resource at its
bound still permits zero-cost use of that unit, while an overrun blocks new work.
`CLOSEOUT_REQUIRED` blocks new claims while existing attempts can finish and
reconcile. Use the reserve to save results/blockers and handoff, not expand the
investigation or wait out the clock. Completion, budget stop and claim support
remain separate; `WORKFLOW_TERMINAL` is not a scientific verdict.

## Review and hand off within scope

Size each required review to the pending decision and remaining budget. Reuse
valid scoped receipts; send changed interfaces and necessary evidence instead of
restarting the whole audit. If the work cannot fit, split at meaningful interfaces
and keep cross-interface checks and uncovered requirements pending. A completed
subreview closes only its covered scope.

Give the reviewer the question, artifacts/diff, required checks, allowed write
scope, deadline and output path. Set a finish target before the hard timeout;
start `INCOMPLETE`, save findings progressively, then finalize and return once
required coverage is met. Use saved coverage to narrow a subsequent request after
a timeout; partial prose or process success cannot close a gate. Preserve the
workflow's independence policy. Bind findings to the reviewed source revision and
observable reviewer call/result; metadata labels alone do not prove a call,
covered checks or independence. Missing provenance stays unverified; same-family
provisional review is not independent scientific acceptance. Direct local
assessment uses the same reporting discipline without automatically requiring
another reviewer or new run.

After the last relevant state change, capture selected current identities:

```text
python <package>/tools/research_control.py --root <project> --run-id <id> handoff --watch <manifest-or-receipt>
python <package>/tools/research_control.py --root <project> --run-id <id> check-handoff --receipt <saved-handoff.json>
```

Save the JSON in an existing handoff location outside watched files; do not hash
it back into the watched run. These read-only commands never initialize state.
`check-handoff` returns `CURRENT` (exit 0), `STALE` (exit 3), or malformed/unreadable
input (exit 2). Missing selected files are tracked. `CURRENT` concerns selected
identities only, not truth, all project facts or scientific approval. A vanished
run cannot authorize a replacement.

On recovery use the returned fresh timing/status and inspect changed sources,
unresolved work and gates. Never trust saved remaining seconds. For a narrow
recovery, save the finding, changes, blocker and next step after that first check;
link existing receipts instead of copying full accounting/hash tables. Avoid
duplicate inspection or an unrelated profile inventory. The old execution's
expired budget still blocks execution, not an authorized read-only diagnosis.
Watch relevant manifests rather than entire datasets or unrelated credentials.
Verify the requested artifact and affected identities once, then deliver.

## Optional host features and telemetry

Use the current host mode. Plan-only requests end with a plan; approved
implementation continues within scope. Create a native Goal only on explicit
request with available host support. It does not grant resources, bypass gates
or prove success. Mark it complete only when its actual objective is met; never
invent a mode switch or background service. Without Goal support, use the
authorized turn and existing project handoff.

There is no implicit Codex session hook. For an explicitly selected local export,
`research_events.py --root <project> --source <relative-trace.jsonl> --session <id>`
adds source-line-bound observations to `.ei/meta/events.jsonl`; reimports are
idempotent. Raw commands/prompts/credentials are not copied. Keep raw traces under
their existing access policy. Failed tools, partial turns and completed turns
remain distinct. `skill_reference` is a mention candidate, not invocation or
compliance; cached instruction reuse is not observable. Assess behavior through
actual task traces and scoped artifact review, not reference counts.
