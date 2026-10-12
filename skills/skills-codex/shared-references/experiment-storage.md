# Experiment storage and recoverable checkpoints

Read when planning, implementing, launching, or monitoring a workload that saves
large artifacts. Apply only to relevant outputs; analysis of existing CSV files
does not require a checkpoint system. Reuse an established project policy.

## Plan the actual storage peak

Inspect the target output filesystem, available space, applicable quota, and
inode availability. Include data/cache, predictions, logs, completed runs,
checkpoint replicas/uploads, and concurrent temporary writes. A quota or remote
volume can be tighter than the whole disk. Record unknown limits as unknown.

Estimate a full resume checkpoint from a short save, including optimizer state
and all distributed shards. Measure save duration and step duration. Before a
long run, set an artifact budget, reserve for a new complete save, and a recovery
interval based on acceptable lost training time and measured I/O overhead.
Evaluation, metric logging, and resume saving have separate cadences.

Project peak = data/cache + retained artifacts across all runs + concurrent
save/export/upload staging + results/logs + safety headroom. Account for shared
inputs once and cumulative completed runs. Recheck estimates after the first
real save. Reduce concurrency or optional retention if the peak does not fit;
report infeasibility when necessary recovery or research artifacts cannot fit.
Advice and planning may finish with labeled estimates and execution prerequisites.

## Default retention, adjustable for the research

- Keep the latest **two valid full resume checkpoints** per active run: current
  and fallback. Preserve model, optimizer, scheduler, AMP scaler where used,
  step/epoch, RNG, and necessary sampler/data-stream state. Record configuration,
  code/data identity, and any limit on exact continuation.
- Keep **one best model**, selected with a predeclared validation metric and
  direction. Never select on the test set. Weights alone are sufficient for
  inference/evaluation; preserve full state if resuming from the best is needed.
- Keep a final model when it is a required output. Roles may reference the same
  artifact. Avoid copying a checkpoint merely to call it latest, best, or final.
- Historical milestones are opt-in for trajectory analysis, averaging, or other
  declared research needs. Pin teacher models, downstream initialization inputs,
  publication artifacts, and user-selected checkpoints while dependencies exist.
  Pinned artifacts count toward the budget; they are not an unlimited exemption.
- Retain necessary metrics, seeds/configuration, source identities, selection
  records, and negative results. Checkpoint rotation does not authorize pruning
  raw evidence, datasets, user files, other runs, or caches.

## Publish first, rotate second

Use framework-native checkpoint/callback support where it meets this policy.
Verify the installed framework's actual retention and best/latest semantics;
a checkpoint-count option alone does not establish two recoverable generations.

For a custom loop: write to a unique temporary destination, finish all writes,
validate loading and required state, publish atomically on a suitable filesystem,
update the latest record, then rotate unprotected older artifacts. Reserve space
for the entire new save before writing. On write, validation, or publication
failure, retain prior valid recovery points and report the error.

Single-file rename guarantees do not establish multi-shard or object-store
completion. Use the backend's completion/barrier protocol, verify all shards,
and commit an identifying manifest last. A local filesystem helper is not an
object-store transaction or a distributed checkpoint writer.

Resume from the most recent **validated committed** checkpoint; reject partial
or corrupt saves and fall back to the previous valid one. This restores the
last saved progress, not steps performed since that save. Run a short interrupted
versus uninterrupted continuation witness before a costly long run; record any
non-determinism or missing data-loader state instead of promising exact replay.

## Optional local helper

`tools/checkpoint_retention.py` provides a standard-library CheckpointStore API
for a custom writer and loader validator, plus CLI inspection and dry-run pruning.
Resolve the helper from the loaded package root containing skills/ and tools/.
The API owns a dedicated run directory and an explicit artifact byte budget;
it does not serialize models or infer recoverability from filenames.

Use `init ROOT --run-id ID --budget-bytes N`, then the API's publish method with
writer, validator, expected save size, step, and kind (`resume` or `weights`).
The validator must actually test the project's load and required state. Published
entries record file hashes and that caller's validation receipt. Use best/final
roles and explicit pin reasons for dependencies. At least two resume generations
are retained by this helper; a project with different needs may use native support.

`status ROOT`, `latest ROOT`, and `prune ROOT` inspect without deleting artifacts.
`prune ROOT --apply` removes only unchanged, registered, unprotected artifacts
under that run's established retention policy. Existing unrelated files are
reported and consume capacity but are never adopted or deleted automatically.
Preview legacy cleanup before applying a specifically authorized migration.
Cooperating writers use a per-run lock. Partial/orphaned writes are reported for
recovery diagnosis; they are not silently deleted by a filename pattern.

## Launch and monitoring

Implementation: make cadence, retention, paths, selection metric, and byte budget
configurable; verify saving, failure handling, and actual resume on a CPU/small run.
Launch: inspect the effective trainer configuration and target filesystem; do not
assume a written plan changed the trainer's saving behavior. For batch jobs, cap
concurrency using the shared storage budget and protect phase dependencies.

Monitoring: report current usage, remaining capacity, artifact growth, last valid
save step/time, and failed saves alongside training metrics. Monitoring is
observational unless an established policy authorizes cleanup or stopping.
An endangered recovery budget or persistent save failure needs a concrete
response under the active run's policy, rather than waiting for the disk to fill.
Preserve recoverable outputs before stopping or destroying ephemeral compute.

Sources: [PyTorch saving/loading](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)
and [Transformers Trainer](https://huggingface.co/docs/transformers/main_classes/trainer).
Consult the installed version when implementing framework-specific options.
