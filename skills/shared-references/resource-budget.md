# Session resource table

Use this contract before arranging resource-consuming research, and again just
before dispatch. Every skill in the same session uses the same table, including
experiment planning, implementation, queues, execution and ongoing research.
Advice, small edits and observing an existing job do not need a new approval.

## Initialize once, choose once

Use the host's stable thread/session ID, preserved across continuation and
compaction. The single canonical table is
`<project>/.ei/resource-sessions/<session-id>.json`, resolved through the existing
state-root resolver. Keep its path in the existing plan/handoff. Do not create
per-skill, per-experiment or per-turn policy copies. If a session spans project
roots, keep the original table owner and pass its path/root to the execution
owner; do not silently initialize another table for the same session.

On first use, run `init`, inspect the target host, show the table and offer:

1. **Maximum available (default):** all visible, permitted local GPUs; GPU sharing
   when memory fits and the existing scheduler/leases permit it; available CPU,
   RAM and disk without extra policy caps; no time limit.
2. **Exclusive GPUs (when GPUs are in scope):** the same ceilings, with idle GPUs required.
3. **Custom:** choose GPU IDs/UUIDs, sharing, duration, memory, storage or costs.

An ordinary planning request in a writable session initializes this policy
record before resource scheduling; it does not initialize an experiment runtime
or start a job. If the first choice is missing, present the table and options,
then end the turn and await the user's response before preparing a detailed
schedule or frozen spec. Do not defer the first choice until launch. If the host's actual
Plan mode or read-only restrictions prohibit writes, inspect without persisting,
offer the choices and retain the initialization as pending.

Wait for that first choice unless the user has already explicitly selected the
profile or equivalent session limits. Present maximum available as the default;
job requirements size the job request, not the session's standing ceilings.
`init` alone leaves `selection_required`; never
record the agent as the approving user. Record the selection once with `select`.
Continuation, another skill, a new experiment, reflection, or restarting the
process in the same session reuses it. A new session initializes its own table;
an old table may be offered as an option, never silently inherited.

| Resource | Maximum-available default | Fresh state and requirement |
| --- | --- | --- |
| GPU allowlist | All visible local devices already permitted by the user/scheduler | Host index/UUID, visibility and existing assignments |
| GPU sharing | Allowed when the execution owner permits it | Each device's total/used/free VRAM, utilization and aggregate additional peak; no taking over another job |
| Total VRAM | No additional policy cap | Current total plus the proposed job; every selected GPU must also fit separately |
| CPU / host RAM | Available capacity within affinity/container bounds | Cores, available RAM, data-loader/cache/optimizer and worker peaks |
| Training duration | No time limit unless the user selects one | Starts on entry into the first actual training step; preparation is recorded separately |
| Job reminder | None unless selected | Optional soft threshold; an unanswered notice continues within the separate authorization ceiling |
| Ongoing Goal duration | No invented total deadline | Keep actual user/host deadlines; do not infer a Goal window from individual experiments |
| Process interruption | Actual user stop consent or a specifically preauthorized condition | Unanswered notices keep observation active; never stop another job to reclaim capacity |
| Dataset storage | Available disk, no extra policy cap | Existing cache, new download/unpack/copies and concurrent temporary peaks |
| Weights / checkpoints | Available disk, no extra policy cap | Existing weights, retained recovery points, complete new save, best/final outputs and simultaneous writers |
| Other disk / concurrency | Available capacity, controlled by the existing runner | Sum simultaneous work on each real filesystem; never count the same free space twice |
| External spending | Reuse established service/compute allocations; no new purchase by default | Existing explicit financial authorization; new spending needs a chosen allowance |

These are ceilings, not targets. Use the smallest adequate investigation. A
maximum profile never expands task scope, overrides explicit device restrictions,
spends unapproved money, weakens fairness/storage rules, or removes an existing
finite run budget. Plan mode retains host execution restrictions. Only an actual
policy exception needs another user decision; a resource shortage calls for
waiting, reducing concurrency or replanning, not repetitive approval prompts.

## Check twice, reuse the existing execution owner

Before arranging the experiment, read the selected table and **fresh target-host
state**, then fit the proposal to it. Do not ask the user to approve an otherwise
in-scope request. Label unknown peaks; use existing measurements or a
small authorized probe rather than guessing available capacity.

Immediately before launch, reload the table and probe again. Account for the
whole concurrent dispatch: per-GPU additional peak (parameters, activations,
gradients, optimizer, allocator headroom), host RAM, dataset growth, weight and
checkpoint save peaks. Sharing includes multiple jobs on one card, not just one
job per card; sufficient VRAM alone does not establish compute isolation or a
fair timing comparison. Record sharing/concurrency conditions in the existing
comparison log. Keep the runner's assignment, leases and reservations.

Refresh the same table's observed/effective capacity when devices disappear,
fail telemetry, are replaced, or CPU/RAM quotas change; keep the user's selection
and policy revision. An all-visible choice follows current permitted hardware;
an explicit device allowlist does not expand. Use UUIDs when physical identity
matters. Missing/unusable telemetry is unknown capacity, not zero occupancy or
proof of healthy hardware. A partial GPU failure need not exclude other usable
devices. Read-only observation reports changes without updating the table.

Review existing launcher gates against the actual host and phase requirements.
Use measured or justified estimated peaks plus appropriate headroom for training,
evaluation and saving, including overlapping phases. Do not impose a universal
free-memory threshold or exclusive-GPU rule when sharing is authorized. Correct
unsupported estimates/gates in a checked future attempt; do not silently lower
requirements to fit or mutate frozen running inputs. Requirements exceeding
physical capacity need replanning, not indefinite waiting for free memory.

Public CLI (use the actual package path and the original table-owning project):

```text
python <package>/tools/resource_budget.py --root <project> --session <host-session-id> init
python <package>/tools/resource_budget.py --root <project> --session <host-session-id> select --preset maximum --selected-by <user-choice-reference>
python <package>/tools/resource_budget.py --root <project> --session <host-session-id> check --stage plan --markdown
python <package>/tools/resource_budget.py --root <project> --session <host-session-id> check --stage launch --request <requirements.json> --markdown
```

Use `--preset custom --overrides <JSON>` for explicit choices; `null` resource
ceilings mean available capacity, and `auto_approve_job_seconds: null` means no
time limit. `show` renders the stored table without a new
sample. An observer in the host's actual Plan mode or another read-only context
uses `check --read-only`; it never initializes or revises policy. A request to
write a plan in a writable session still follows first-use initialization above.
Live checks run on the target host, not a different control
machine. Remote owners must carry the same selected table and reconcile their
actual scheduler state; do not claim a local probe checks a remote GPU.

A launch request declares `host`, `job_seconds`, `cpu_cores`, `ram_bytes`,
`new_spend`, `gpus` (`id`, additional `peak_bytes`), and `storage`. Each storage
row contains its absolute `path` and incremental `dataset_bytes`, `weight_bytes`,
`checkpoint_peak_bytes`, `other_bytes`, `reserve_bytes`, including explicit zeros.
Existing cached bytes are already reflected in disk usage; do not count them
again as growth. Use the retention owner's verified storage estimates. The helper
groups paths by real filesystem and checks their combined additional peak.
`job_seconds` is for one independently planned experiment, such as a fixed
configuration and seed, measured from its first actual training step, not a
serial queue or comparison's summed duration. Keep preparation, downloads,
environment setup and code review separate. Their compute/storage still count.
Check each member's duration and the whole dispatch's simultaneous resource
peaks. A complete comparison can still count as one reflection block.

For registered executions, bind
`configuration.resource_budget = {"session_id": <id>, "request": <requirements>}`
in the frozen configuration. The existing launcher performs another fresh check
after environment verification; the governed queue reaches that same launcher.
If the table belongs to another project root in the same session, include its
absolute `table_root` in that binding. An existing current-session table also
prevents that launcher from silently dispatching an unbound new execution.
For another existing runner, call the check from its admission path instead of
building a second scheduler. User-defined limits, workflow reflection and actual
execution completion still belong to their existing owners.

`AUTO_APPROVED` authorizes the declared in-scope resource use; it does not accept
scientific claims or promise hardware reservation. `READY_TO_PLAN` permits
planning, not launch. `SELECTION_REQUIRED` needs the first session choice;
`NEEDS_APPROVAL` names an exceeded policy ceiling; `WAIT_RESOURCE` needs capacity;
`REPLAN_REQUIRED` means the request exceeds physical capacity;
`NEEDS_ESTIMATE` needs reliable requirements or host observations. Pending
decisions do not stop healthy jobs. Recheck after changing requirements or policy.
This helper samples and compares peaks; it does not meter or atomically reserve
hardware, and does not cover an unbound legacy launcher automatically.

## Reminders and nonblocking notices

Keep the optional `job_notice_after_seconds` separate from
`auto_approve_job_seconds`, the selected authorization ceiling. A reminder does
not lower or raise that ceiling. Do not infer a hard cutoff by adding an informal
tolerance to a soft threshold. New sessions have no duration ceiling or reminder
unless selected; existing tables keep their explicit limits. Read values from
the session table, not examples or skill-specific time constants.
Other resource limits and separately agreed hard execution deadlines still apply.

When a launch estimate exceeds the reminder, or elapsed time reaches it,
the execution/monitoring owner presents one optional continue/stop notice for
that experiment. Include its identity, elapsed/remaining estimate and authorized
boundary. Offer “continue (default; no reply continues)” and “checkpoint and stop
this experiment.” Use a
nonblocking popup, such as `request_user_input_async` when available. Keep
monitoring while unanswered; record the notice with the existing owner so polls
and continuation do not send it repeatedly. Submission is not a user response.
If the host's popup would suspend execution or Goal continuation, use a passive
notice and continue the authorized watch instead of a mandatory question.

Read-only advice for an existing experiment:

```text
python <package>/tools/resource_budget.py --root <project> --session <id> duration --elapsed-seconds <elapsed>
```

Supply **training** seconds only. The existing execution owner records entry
into the first real training step, rather than process launch, an import probe
or the first sparse log line. Before that event, training has not started; absent
evidence remains unknown. Keep prior training time across retries/resumes while
excluding their preparation gaps. After the first step, ordinary pauses inside
that training segment still count; do not repeatedly reset it at evaluations.
An explicitly agreed overall wall deadline has its own original start and still
includes preparation. It is not the per-training reminder or allowance.

For an owner already keeping a timing receipt, `duration --training-clock <JSON>
--experiment-id <stable-id>` reads schema version 1, `experiment_id` and `segments`.
Each segment contains `attempt_id`, timezone-aware `first_step_at`, and `ended_at`
(null only for the running last segment). The owner retains completed segments
and binds them to actual attempts. The helper checks identity/order and sums
segments; it neither creates a second runtime nor certifies first-step provenance.
`TRAINING_NOT_STARTED` permits continued authorized preparation/observation.

`NOTICE_CONTINUE` relies on the recorded prior authorization and leaves the
response null. Pass `--response stop` or `continue` only for an actual reply.
Stop requests route checkpoint/stop to that experiment's execution owner;
they do not stop other jobs or pause the Goal. A reply cannot reset the clock or
expand the policy. Keep the original experiment identity/time across resume and
retry; do not split or rename a long experiment to renew its allowance.

Beyond the selected authorization ceiling, request a specific exception rather than assuming
silence grants unlimited time. Keep useful authorized work and monitoring active;
a pending optional notice alone never justifies Goal `blocked`. Actual process
timeouts stay with the execution owner: a planning estimate or reminder is not an
instruction to terminate healthy training. Configure authorized bounds and save
reserve before launch, retain separately agreed hard deadlines, and do not
live-edit frozen inputs or claim a legacy runner already honors this contract.

Interrupting a live process requires an actual user stop choice for that
experiment, or a specifically preauthorized automatic stop condition. The
maximum-resource profile, Goal/Plan mode, a review STOP, a time notice and silence
grant no interruption permission. Use a nonblocking continue/stop popup when the
host supports it, otherwise a passive notice; keep watching while unanswered.
Do not send signals, close its screen/session or cancel a scheduler job merely
to free resources. Preserve the checkpoint and verify exit after confirmed stop.

### Execution-owner integration

For registry launches, freeze `training_clock: {path, experiment_id}` beside
`resource_budget` in the expanded configuration. `path` is project-relative
inside that execution's outputs; the stable experiment ID survives resume.
The trainer atomically writes the clock at its first actual step and retains
prior segments. The existing launcher polls it during its own wait, checks the
current attempt identity, and records `training-budget-observations.json`.
The monitoring owner reads its deduplicated notices and presents the optional
popup/passive update; the launcher does not create another UI or monitoring loop.
Missing clock evidence is not process uptime. Invalid receipts raise a diagnostic
notice while observation continues. Legacy runners need explicit instrumentation.

For cooperative save-and-stop, verify the trainer's SIGTERM handler before
launch and freeze `stop_protocol: {mode: checkpoint_then_stop, receipt_path}`.
After loader validation, the trainer writes an identity-bound receipt containing
`execution_run_id`, `snapshot_ref`, `checkpoint_ref`, and
`validation: {passed: true, label: <loader>}`. The launcher verifies these fixed
references after actual exit; missing/failed validation stays unverified.
A stop request waits for actual exit without a default forced-kill deadline.
`force_after_seconds` requires separate, explicit forced-termination permission;
ordinary stop consent does not grant it. Optional frozen `stop_authorization`
retains its specific automatic conditions; its force interval and
`force_on_confirmed_stop` must likewise reflect actual explicit permission.
Keep leases until the owned process tree is observed gone; Windows parent-only
termination requires separate descendant reconciliation before lease release.
