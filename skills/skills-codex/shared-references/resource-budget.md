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
   RAM and disk; automatic approval for individual jobs up to **12 hours**.
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
| Job duration | Automatically approve up to 43,200 seconds | Planned per-job bound; 90 minutes needs no further approval |
| Ongoing Goal duration | No invented total deadline | Keep any actual user/host deadline; multiple short jobs do not create a new 12-hour Goal window |
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
in-scope 90-minute estimate. Label unknown peaks; use existing measurements or a
small authorized probe rather than guessing available capacity.

Immediately before launch, reload the table and probe again. Account for the
whole concurrent dispatch: per-GPU additional peak (parameters, activations,
gradients, optimizer, allocator headroom), host RAM, dataset growth, weight and
checkpoint save peaks. Sharing includes multiple jobs on one card, not just one
job per card; sufficient VRAM alone does not establish compute isolation or a
fair timing comparison. Record sharing/concurrency conditions in the existing
comparison log. Keep the runner's assignment, leases and reservations.

Public CLI (use the actual package path and the original table-owning project):

```text
python <package>/tools/resource_budget.py --root <project> --session <host-session-id> init
python <package>/tools/resource_budget.py --root <project> --session <host-session-id> select --preset maximum --selected-by <user-choice-reference>
python <package>/tools/resource_budget.py --root <project> --session <host-session-id> check --stage plan --markdown
python <package>/tools/resource_budget.py --root <project> --session <host-session-id> check --stage launch --request <requirements.json> --markdown
```

Use `--preset custom --overrides <JSON>` for explicit choices; `null` policy
ceilings mean available capacity. `show` renders the stored table without a new
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
`NEEDS_ESTIMATE` needs reliable requirements or host observations. Pending
decisions do not stop healthy jobs. Recheck after changing requirements or policy.
The duration is a declared allocation estimate, not an invented total Goal
deadline. Actual process timeouts stay with the execution owner; if monitoring
shows a longer allocation will be needed, request that exception once without
silently treating the estimate as a new instruction to kill a healthy process.
This helper samples and compares peaks; it does not meter or atomically reserve
hardware, and does not cover an unbound legacy launcher automatically.
