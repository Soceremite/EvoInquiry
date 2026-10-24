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
authorized start, including preparation/review. When the user set a finite wall
budget, keep a task-appropriate closeout reserve inside it. Ongoing authorized
work need not have a total wall deadline or action cap: use explicit `null` caps,
not an invented time window or a very large number. Keep declared resource
bounds and per-attempt limits. Reuse authorization; missing prerequisites do not
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
| `configure --objective <deliverable> --limits <limits.json>` | Limits: `max_actions` and `wall_seconds` (positive bound or explicit `null` for no total cap), positive `max_attempts_per_key`, `resources` (unit → bound). Optional `--started-at <timezone-aware-ISO>` and `--closeout-seconds <seconds>` inside a finite wall budget. Existing clock/limits stay fixed; old callers reserve zero closeout time. |
| `inspect` | Read phase, evidence, reservations, completed blocks and original timing; an explicitly configured elapsed-review policy may open a gate. Cap process/reviewer timeouts by `timing.dispatch_seconds_remaining` when non-null. Null means no total wall deadline, not free resources. `READY` is neither resource authorization nor success. |
| `inspect --read-only` | Observe existing gates and `reflection_due` without writing state or the iteration ledger. Use for Plan monitoring; due review still needs its execution owner before new dispatch. |
| `claim --request <action.json>` | Fields: `action_key`, `phase`, `question`, `costs` for every unit, optional fixed `input_refs`. Only `claim=new` permits dispatch; `existing` requires inspecting that attempt. |
| `define-block --request <block.json>` | Fields: `block_id`, disjoint `action_keys`, fixed `plan_ref` to the existing plan. Declare all required comparison members before their first claim; retries keep the same member key. No second experiment planner. |
| `complete-block --request <completion.json>` | Fields: `block_id`, nonempty fixed `result_refs` to completion/analysis evidence. All planned members need settled latest attempts; missing, live or cancelled members do not complete a block. The owner checks scientific completeness and fairness. Identical completion counts once. |
| `finish --request <completion.json>` | Fields: `action_id`, terminal `outcome` (`succeeded`, `failed`, `cancelled`), observed `actual_costs`, fixed `result_refs`, `reason`. Verify actual termination first. Success requires evidence; costs are observations, not estimates clipped to reservations. |
| `settle-execution --request <settlement.json>` | For registered executions: `action_id`, `execution_run_id`, observed `actual_costs`, optional `result_refs`/`reason`. Verifies the existing terminal execution and derives its process outcome; never launches. |
| `stop --reason <reason>` | Records workflow stop intent. Bound local launchers observe it and terminate their owned jobs; retain live reservations until actual terminal evidence. Remote/unbound jobs require their execution owner. No phase or native Goal acceptance. |

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
before retry. It is expected while an owned job is live: continue its watch, and
settle only after actual termination. It is not itself a failure or Goal blocker.
If reservation preceded launch but no execution exists, establish
that fact before cancellation and a permitted retry. Uncertain process identity,
timeout or missing heartbeat cannot release costs or justify duplicate work.
`REVIEW_REQUIRED` retains the workflow gate; `EVIDENCE_CHANGED` needs source
reconciliation. Exhausted wall/action limits stop dispatch; a resource at its
bound still permits zero-cost use of that unit, while an overrun blocks new work.
`CLOSEOUT_REQUIRED` blocks new claims while existing attempts can finish and
reconcile. Use the reserve to save results/blockers and handoff, not expand the
investigation or wait out the clock. Completion, budget stop and claim support
remain separate; `WORKFLOW_TERMINAL` is not a scientific verdict.

## Trajectory brakes and problem synthesis

At a completed comparison block, tuning batch, large milestone or direction
boundary, check whether the next action still answers the original question.
Also look back after repeated local repairs, weak information gain, growing
branches, conflicting evidence or changed data/evaluation. Review progress at
the appropriate scale; do not interrupt every parameter trial or invent a fixed
minimum number of experiments. Set cadence in the existing plan for its cost
and uncertainty. Count new findings by information gained, not improved scores.

Compare continued local tuning with a discriminating test, a simpler model,
a different framing or stopping. Keep the original objective, counterevidence,
resource use, unresolved problems and a concrete next action in a compact
checkpoint. A contradiction is a reason to inspect, not to force a pivot.
With two or more potentially related problems, use `/problem-synthesis`;
with zero or one, the active owner performs this review. Fairness drift goes
to `/experiment-audit`. Recording or reviewing never grants resource permission.

Prefer progress-based cadence: choose N whole experiments/comparisons in the
existing plan, then use `configure --reflection-every-blocks <N>`. One complete
comparison, including its planned methods, configurations, seeds, evaluation and
analysis, counts once. Preparation, individual seeds, retries and parameter
trials do not inflate this count. Declare membership with `define-block`, then
call `complete-block` after checking the actual outputs and recording analysis,
including negative findings, failures and exclusions. Terminal accounting alone
does not prove a fair, scientifically complete comparison. `complete-block`
opens a gate at the cadence; unfinished groups do not interrupt a comparison.

Keep legacy `--reflection-every-actions` for callers intentionally counting
settled executions; it is mutually exclusive with block cadence. Elapsed review
via `--reflection-interval-seconds` is optional when requested, never the default
or a total runtime limit. Existing monitor/claim calls observe it; no background
scheduler is created. Old contracts keep their original settings and budgets.
A gate binds only the completed block/action IDs present when it opens; results
arriving during review remain unreviewed. Read actual outputs and alternatives
before CONTINUE, a revised plan or STOP; a gate alone is not reflection. CONTINUE
releases new work without resetting cumulative cost or elapsed time. Escalate
earlier for repeated failures, stalled information gain or contradictory evidence;
do not wait for N when the next action is already unjustified.

Optional deterministic signals: `python <package>/tools/problem_synthesis.py due
<context.json>` accepts nonnegative counts `open_problem_count`,
`completed_blocks`, `local_repairs`, `stale_count`, `branch_count`,
`overlapping_failures` and booleans `user_requested`, `milestone_complete`,
`direction_boundary`, `fairness_drift`. Counts describe work since the last
addressed checkpoint; retain the original cumulative resource accounting.
The returned `kind`, `skill`, `level` and `reasons` route a review; `skill: null`
keeps an ordinary checkpoint with its current owner in either runtime. These
signals do not measure research quality. The owner records which boundary was addressed so it
does not reopen the same checkpoint without new work or evidence.

For a run with an existing continuation contract, before dependent dispatch:

```text
python <package>/tools/research_control.py --root <project> --run-id <id> require-reflection --kind checkpoint --level milestone --reason milestone_complete
python <package>/tools/research_control.py --root <project> --run-id <id> inspect
python <package>/tools/research_control.py --root <project> --run-id <id> record-reflection --phase <phase> --request <checkpoint.json>
```

Use `--kind synthesis` and the synthesis recorder for a multi-problem decision.
Ordinary checkpoint JSON contains `kind: "checkpoint"`, `schema_version: 1`,
`gate_id` from inspect, `decision` (`CONTINUE`, `REPLAN`, `DEFER`, `BLOCKED`,
`STOP`), `reason`, `evidence_refs` and a `next_action` object with `skill` and
`description` for continue/replan; defer/blocked need `blocker` and a revisit
condition. `SYNTHESIS_REQUIRED` / `REFLECTION_REQUIRED` block new claims while
real process reconciliation and review remain available. No run or contract
is needed for advice or a small task; do not initialize one just for reflection.

A merge, abstraction pivot or `REPLAN` retains the brake while its owner revises
the plan. Complete that handoff with `clear-reflection --handoff <project-relative-plan>`;
this binds the plan's current identity, not its scientific correctness. Changed
method/data/evaluation still needs its existing review. `DEFER` / `BLOCKED` keep
the brake until a new gate-bound reflection resolves them. `STOP` records intent;
the bound local launcher now observes it. For one obsolete attempt while research
continues, use `execution_registry.py --root <project> stop --execution-id <id>
--reason <reason>` through its execution owner. The request binds snapshot and
process identities; it is not proof of exit. The launcher retains actual exit
and cause in `termination.json` and the final execution record. Its timeout is
capped by an explicit bound, spec `max_seconds_per_attempt` and the original
workflow dispatch time. Preserve the latest valid resume state and settle only
after terminal evidence. POSIX targets the owned group; native Windows currently
certifies the parent only. Ordinary review leaves healthy training running. Retry an interrupted record with the same gate ID and
payload; never reuse an older reflection for a new gate. Review, closeout,
resource exhaustion and unresolved processes retain their original precedence.

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

## Monitoring, interruption and host modes

Use `monitor-experiment` for one status check and `training-check` for requested
continuous observation. Reuse the existing execution and monitoring owner. Check
process identity, step/log freshness and available metrics at a cadence appropriate
to the run; quality reviews can be less frequent than lightweight health checks.
Use interruptible host waits or bounded process polls, inspect fresh evidence on
each wake, and respond to steering. Do not busy-loop, launch keepalive experiments,
or manufacture findings to keep a session active.

When a run exits, verify its terminal record and outputs, then return results to
the existing workflow owner instead of polling a finished job. Finishing or
stopping one job does not complete or pause the broader Goal. A request to stop
watching ends observation, not training; report any jobs still running.

A live run advancing toward its expected next output is waiting, not a failed
research iteration. Polls, log gaps within the expected output cadence and
`WAIT` are not completed blocks or zero-finding iterations: do not call
`iteration_log.py note` for them. Unreachable telemetry is an observation problem;
cross-check process/queue and fallback logs before inferring a stuck or dead job.
Likewise, a watchdog `STALE` heartbeat or one `IDLE` reading requests inspection;
it does not by itself establish training failure or native Goal stalling.
Actual stalled execution and repeated uninformative completed investigations need
their respective execution recovery or trajectory review.

| Context | Allowed continuation |
| --- | --- |
| Ordinary status question or discussion | Answer the requested check. An interjection does not stop training, reset review counts or cancel an already authorized watch. Do not start a continuous watch unless requested or part of the active task. |
| Plan | A planning request delivers its plan. Requested observation of existing jobs may continue read-only while the host permits: read logs/processes and report, without launching, changing configurations, persisting gates/notes, or stopping jobs. `STOP` here is a recommendation to the execution owner. Plan-only does not guarantee automatic continuation after the turn. |
| Active native Goal | Monitor healthy long training and keep waiting for its evidence; ordinary waiting, reflection and authorized replanning do not themselves block or complete the objective. Use the host's available continuation and wait mechanisms. |

A pending or due review holds new dispatch, including prepared jobs. Healthy
in-flight work continues through ordinary review. A revised plan does not live-edit
frozen running inputs: carry changed protocols into separately checked attempts.
Stopping one attempt uses its identity-bound execution stop; workflow `stop` targets
all bound owned jobs. User-controlled Goal pause is a separate operation. Match the
user's intended scope, verify actual exit before settlement, and preserve valid
recovery state. A stop recommendation in observation-only work is not execution
authorization. Explicit safety/resource policies and agreed stop conditions still
apply through the authorized execution owner.

Create a native Goal only on explicit request with host support. It grants no
resources, bypasses no review gate and proves no scientific result. Never map
`WAIT`, `REFLECTION_REQUIRED`, `SYNTHESIS_REQUIRED`, `REPLAN`, or a self-imposed
time window directly to native Goal `blocked` or `stalled`. Respect actual host
budgets, interruptions and continuation limits; a skill cannot override them or
promise a resident background service. A genuine unresolved prerequisite blocks
the Goal only when no useful authorized work remains, under the host's recurrence
rules. Mark it complete only when its actual objective is met. Without Goal
support, use the authorized turn and existing project handoff.

## Optional telemetry

There is no implicit Codex session hook. For an explicitly selected local export,
`research_events.py --root <project> --source <relative-trace.jsonl> --session <id>`
adds source-line-bound observations to `.ei/meta/events.jsonl`; reimports are
idempotent. Raw commands/prompts/credentials are not copied. Keep raw traces under
their existing access policy. Failed tools, partial turns and completed turns
remain distinct. `skill_reference` is a mention candidate, not invocation or
compliance; cached instruction reuse is not observable. Assess behavior through
actual task traces and scoped artifact review, not reference counts.
