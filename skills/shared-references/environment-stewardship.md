# Environment revisions and consumer protection

Read this for dependency/ABI/runtime changes or shared-environment maintenance.
Use tools/environment_registry.py as a metadata registry; existing conda/uv tools
continue solving, installing and scheduling.

Inspect actual requirements, interpreter, imports, platform, authorized changes
and consumers first. Prefer a verified existing frozen revision without package
changes. Native/compiled scientific stacks may favor conda; compatible Python
projects may use uv. Specify one primary solver, sources and install order.
Do not let tools solve the same dependencies twice or share a writable uv
site-packages directory casually.

Any dependency/runtime change uses an independent recipe/lock/build candidate.
Inspect the complete diff: downgrades, removals, transitive packages, sources,
Python and platform. Preserve actual failed checks. Promotion needs candidate-
bound authorization and metadata, actual-import/ABI-device, small numerical and
representative-consumer receipts. No layer's PASS substitutes for another.
If a critical consumer or platform is untested, stop promotion and record why.

The registry supports record_candidate, find_compatible, promote_candidate and
bind_consumer. Exact requirements are supported by the MVP; unresolved version
ranges need the existing solver and real checks, not a guessed match.
Promotion copies recipe/lock/build inputs into the frozen revision. Record
expected and observed fingerprints separately; verify_environment probes the
actual interpreter/imports before formal launch and stops on drift.

Observe interpreter, package versions/import origins, Python/platform/host and
relevant CUDA runtime/driver/device facts. GPU facts require actual device checks
when needed. CPU-only receipts do not validate GPU ABI or bitwise reproducibility.
Use inspect --device-probe for explicitly authorized PyTorch/CUDA/driver
inspection and save numerical device checks separately. The driver inventory is
physical host metadata; it does not replace a check on the selected launch device.
A lockfile or image alone is insufficient.

Distinguish hardware absence from failed access. Driver communication errors or
sandbox-hidden devices do not establish that the server has no GPUs. Record the
actual error and, within existing authorization, retry in a runtime with device
access before reporting availability. Do not change drivers or rent compute to
repair a permission-limited probe.

Consumers retain project/experiment/entrypoint, job/workflow/execution, env
revision, purpose/importance/lifecycle and source/confirmed_by/confirmed_at.
bind_consumer returns an immutable consumer-history reference; consumers/<id>.json
is a mutable lookup. unknown is protected. abandoned cannot remove a paper reproduction pin.
Queued/running jobs keep their bound revision; promote only selected future
tasks. A new candidate does not retarget a queue or patch a live environment.

acquire_lease protects queued/running jobs. Expiration requests reconciliation
with the real scheduler/process; it never releases protection by TTL alone.
reconcile_leases needs fixed termination receipts confirming not queued and
not running, including the bound execution identity. Historical reproduction needs
a pin independent of a lease. A completed pinned consumer cannot change its
environment; create a separate future consumer. plan_pin_release is read-only;
release_pins requires approval for the exact selected pins and a durable intent.
An interrupted release protects retirement until the same plan is reconciled.

plan_retirement produces a deletion-free plan. Every dependent consumer/lease/
pin and unconfirmed consumer inventory is a blocker. Instance deletion needs
the existing retention policy and separate applicable authorization; retain
recipe, references and retirement receipt. Do not add another cleanup manager.

Compatible projects may reuse immutable revisions and content-addressed download
caches. Use a verified cache lock/atomic publish, or independent cache paths.
Keep development environments, mutable caches and execution output isolated.
Add a host-wide owner registry only for actual physical cross-project sharing.

Primary references: [conda environments](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html),
[uv configuration](https://docs.astral.sh/uv/concepts/projects/config/),
[uv caching](https://docs.astral.sh/uv/concepts/cache/) and
[PyTorch reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html).
