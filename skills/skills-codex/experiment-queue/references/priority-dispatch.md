# Priority dispatch and concurrent work

Use these options when pending jobs have different urgency or when useful CPU
work can run during a longer execution. Keep the existing governed launch
binding and session resource table.

## Queue scheduling

In each manifest job, `priority` is an integer. Greater values go first once
phase dependencies are satisfied. The default is zero. Equal priorities keep
their persisted enqueue order. Adding a job to a running queue or updating the
priority of a pending job takes effect when the manager next reads the manifest.
Keep each existing job ID, scientific inputs and phase dependencies stable.
Update the manifest with an atomic replacement.

Use a timezone-aware `ready_at` only for a known earliest start. The first
waiting job with a feasible placement keeps a reservation. Lower-priority
jobs can use the remaining devices and host capacity. A job with a
`backfill` object can borrow that capacity before a future reservation.
Provide `seconds` as the conservative runtime bound and `evidence` as a
fixed reference to a comparable run record with `elapsed_seconds`. Without
a usable estimate, dispatch uses capacity independent of the reservation.
Changes in priority affect pending placements. Interruptions follow the
existing explicit stop and checkpoint rules.

`isolate_host: true` reserves the queue's host capacity for a timing run.
Use provider or scheduler isolation when other queues and processes share
the host. Capture actual device, concurrency, timing and precision in the
measurement so comparisons use matching conditions.

Use the existing queue helper in observation-only mode or to brief an optional
dispatch adviser.

```text
python <package>/tools/experiment_queue/queue_manager.py --manifest <manifest.json> --state <queue-state.json> --inspect
```

The adviser receives this queue summary and current approved constraints. Ask
for candidate priorities, placements and reasons under the session's model
preference. The queue owner applies accepted priority changes. The launch
check still verifies session resources, the frozen execution and the lease.
The same queue operates when a host has no adviser available.

## Optional CPU tasks during a primary run

Set `during` to the primary job's ID in the same governed queue. Use an
independent ready phase or the primary's phase. Freeze the companion's
CPU-only binding, either a request with `gpus: []` or zero-device task options.
Declare its CPU, RAM, filesystems and optional `io_bytes_per_second` peak.
The session's optional `max_io_bytes_per_second` caps combined declared I/O.
Write companion output under its own execution outputs directory. Build or
review candidate code and datasets independently of the live primary inputs.

During authorized work, the monitoring owner can publish a health observation
for the primary execution. The JSON includes `decision`, `reason` and any
fixed `evidence_refs`. `WAIT`, `STOP` recommendations and `RESULT` defer
new companions while the monitor or research owner evaluates the change.
`CONTINUE` reopens the launch window. A completed primary closes its window.
Return deferred tasks to project planning if they still matter to the goal.

```text
python <package>/tools/execution_registry.py --root <project> health --execution-id <primary-execution> --observation <health.json>
```

Read health without `--observation` in an observation-only Plan session.
Monitor liveness and research quality on the existing cadence throughout.

## Choosing a validated evaluation configuration

Use one fixed cohort, evaluator, environment, variant, seed and precision.
Collect sample IDs in `{"sample_ids": [...]}`. Each shard holds
`{"samples": [{"id": "<id>", "prediction": <JSON>, "metrics": {...}}]}`.
Provide original per-sample metric contributions. The helper supports
`mean`, `sum` and `max` with a declared absolute tolerance. Metrics with
another reducer use their project-specific evaluation before publication.

Run each supported configuration in isolation. The profile request names
`host`, `precision`, `spec_ref`, `env_revision`, `variant_id`, `seed`,
`sample_ids_ref`, `metrics`, optional `prediction_atol` and fixed
`input_refs` for model or other evaluation artifacts. It declares a
`baseline` and `alternatives`. Each profile has an `id`, `batch_size`,
`gpu_uuids`, fixed `shards` and a fixed `measurement_ref`. Measurement
records carry those same controls plus `host`, `precision`, `isolated: true`,
`elapsed_seconds` and the maximum `peak_bytes_per_gpu`. Use zero peak for
CPU-only measurements.

```text
python <package>/tools/evaluation_profiles.py --root <project> --request <profile-request.json> --output <project-relative-receipt.json>
python <package>/tools/evaluation_profiles.py --root <project> --collect <evaluation-result.json> --output <project-relative-summary.json>
```

Freeze the receipt reference as `resource_budget.task.evaluation_profiles_ref`.
Use it as the task's placement options. Keep conservative CPU, RAM, disk and
duration peaks for the supported profiles. Bind the same `evaluation_input_refs`
in the expanded configuration. The launcher provides
`EVOINQUIRY_EVAL_BATCH_SIZE`, `EVOINQUIRY_EVAL_GPU_COUNT`,
`EVOINQUIRY_EVAL_PROFILE` and `EVOINQUIRY_EVAL_PRECISION` to the compatible
evaluator with its admitted CUDA devices. The evaluator owns batching and
sharding. Keep sample-level randomness and preprocessing consistent.

The default evaluation preference chooses the fastest feasible measured
profile. Use `balanced` to consider total GPU time, or `lowest_resource`
to favor a smaller footprint. Collect the final shards using the full cohort
and the declared metric reducers. The collector checks every sample ID exactly
once and reduces the raw contributions across all shards.
