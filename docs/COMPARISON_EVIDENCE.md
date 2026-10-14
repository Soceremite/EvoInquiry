# Comparison evidence before weight consolidation

EvoInquiry keeps comparison results independently of disposable training weights. Starting with 1.3.0, the optional local checkpoint helper requires a complete evidence index before consolidating another run into a selected winner. This check verifies declared coverage and file integrity. It does **not** certify preregistration, fair scientific design, correct arithmetic or a claim verdict.

The shared [comparison guidance](../skills/shared-references/comparative-experiments.md) explains design and interpretation. Ordinary advice, analysis and single-run completion do not require this index. Framework-native storage policies can use the same evidence principles without this helper.

## Files and identities

Put `comparison-evidence.json` at a campaign directory containing its protocol, comparison log, effective configurations and execution evidence. References are `{ "path": "relative/path", "sha256": "64 lowercase hex characters" }`, relative to the index's directory. Use portable forward-slash paths; absolute paths, parent traversal, empty files, symlinks and NTFS junctions are rejected. Every referenced file must survive outside the owned checkpoint artifact directories. Keeping logs beside a store's manifest is allowed; placing them inside a `ckpt-*` artifact is unsafe. Structured protocol, index and ledger JSON records are limited to 16 MiB each; raw referenced logs/results are streamed for hashing and do not share that record limit. Large campaigns can keep raw data in separate referenced files and partition their archival records.

The protocol is written before execution and can itself be the governed experiment spec's `protocol_ref`. It records the comparison question, declared run/seed slots, validation selection and failure accounting. The existing governed spec, when used, must agree with these slots; this format does not initialise or migrate a project. Each `run_id` identifies a method/seed slot and must match its checkpoint store. Each retry gets its own `attempt_id` within that run. Seed numbers need not match between methods for an unpaired design; use `null` for genuinely deterministic runs.

## Record format

All three JSON records below use `"schema_version": 1`. This is the record schema version, independent of the EvoInquiry release version.

`protocol.json` contains:

```json
{
  "schema_version": 1,
  "comparison_id": "benchmark-01",
  "comparison_type": "tuned",
  "planned_runs": [
    {"run_id": "a-s42", "method_id": "a", "seed": 42},
    {"run_id": "b-s42", "method_id": "b", "seed": 42}
  ],
  "selection": {
    "partition": "validation",
    "metric": "accuracy",
    "direction": "maximize",
    "aggregation": "mean of independent seed slots per method",
    "tie_break": "lower measured training cost; then predeclared representative checkpoint"
  },
  "failure_policy": "First successful attempt fills each slot; retain failed attempts and report unfilled slots.",
  "common_settings": {
    "data_and_split": "Replace with fixed dataset, split and eligibility references.",
    "evaluation": "Replace with the fixed evaluator and metric definitions.",
    "resources": "Replace with the accounting boundary and method-specific budgets."
  }
}
```

Choose `controlled`, `equal-budget` or `tuned` according to the actual question. The two runs above illustrate the format, not an adequate replication prescription. Plan more independent runs when precision requires them. Selection `direction` is `maximize` or `minimize`; `aggregation` and `tie_break` describe the actual predeclared rules, including representative checkpoint selection. Method-specific settings and documented deviations may be additional protocol fields.

`executions.json` is an independent export of the recorded attempts:

```json
{
  "schema_version": 1,
  "attempts": [
    {"run_id": "a-s42", "attempt_id": "a-001", "status": "failed"},
    {"run_id": "a-s42", "attempt_id": "a-002", "status": "completed"},
    {"run_id": "b-s42", "attempt_id": "b-001", "status": "completed"}
  ]
}
```

Use real execution IDs and status records. Export every attempt from the project's runner or governed execution records; do not reconstruct the ledger from successful result files alone. At consolidation, every listed attempt must be terminal: `completed`, `failed` or `stopped`.

The index contains `protocol_ref`, `comparison_log_ref`, `execution_log_ref`, `runs` and `selection`. Each `runs` item repeats its declared `run_id`, `method_id` and `seed`, then supplies `status`, boolean `included`, a nonempty `disposition`, `configuration_ref`, and `attempts`. Each attempt supplies `attempt_id`, `status` and `evidence_ref`. Results can be JSON, CSV or another retained raw format; a failed attempt can reference its failure log rather than nonexistent metrics. Excluded runs and failures must still have records and reasons. A planned slot that was never started uses `status: "not-run"`, `included: false`, an empty `attempts` list and a fixed `cancellation_ref` recording the actual cancellation and reason. Do not invent an execution attempt for it or include it as a measured result.

`selection` contains the selected `winner_run_id` and `rule`, an exact copy of the protocol's `selection`. The winner must be a completed or permanently stopped, included run with retained evaluation evidence, and must match the surviving checkpoint store's validated weights. Failed and unstarted runs cannot be winners. Validation selection is required for this weight-consolidation helper. Preserve all seed statistics even though one representative model is retained. Early termination and unfilled slots limit the comparison's conclusions even when its remaining models can be archived safely.

Create references without typing hashes manually:

```python
from pathlib import Path
from tools.comparison_evidence import file_reference, validate_evidence

campaign = Path("results/comparison-01")
protocol_ref = file_reference(campaign, "protocol.json")
configuration_ref = file_reference(campaign, "runs/a-s42/configuration.json")
# Populate the index from the real protocol, ledger, configuration and result records.
# Persist it as comparison-evidence.json before checking or discarding any weights.
report = validate_evidence(campaign / "comparison-evidence.json")
assert report["scientific_verdict"] == "not-assessed"
```

Freeze the index only after the log, inclusion decisions, selection reasoning and necessary raw evidence are complete. The validator verifies every declared slot and every recorded attempt; it does not parse arbitrary result formats to recalculate the winner or detect unrecorded jobs. The research audit checks those meanings against the actual protocol and code. Timestamps and hashes alone do not prove that a protocol was fixed before results were seen.

## Preview, apply and resume

Stop the relevant writers, inspect future dependencies and pin required models. Finish the winner after exporting and actually load-validating its inference weights. Then preview the specific losing store:

```bash
python tools/comparison_evidence.py results/comparison-01/comparison-evidence.json \
  --source-run-id a-s42 --winner-run-id b-s42

python tools/checkpoint_retention.py finish results/a-s42/checkpoints \
  --outcome completed --step 20000 --reason "declared validation selection" \
  --archive-to results/b-s42/checkpoints \
  --comparison-evidence results/comparison-01/comparison-evidence.json
```

The preview changes no manifests, pins or files. Apply the reviewed operation by adding `--apply`. The API accepts the same `comparison_evidence=Path(...)` argument to `CheckpointStore.finish`. The helper binds the index's path and digest, pins the winner before releasing local roles, and preserves existing dependency pins, changed artifacts and unrelated files. It does not rank methods, stop trainers, infer future dependencies or authorise deletion. Single-file trainers can continue to copy just `checkpoint_retention.py` for normal saving and completion; comparison consolidation additionally needs `comparison_evidence.py`. Include both files in the source allowlist when freezing a comparison-archive program, rather than importing an unfrozen live helper.

Interrupted cleanup rechecks the winner and every bound evidence reference before proceeding. Editing a log, configuration, result, protocol or index blocks further deletion; restore the recorded evidence and investigate rather than refreshing hashes to bypass the receipt. Completed runs can reuse the bound index for an idempotent finish without supplying it again.

Pre-1.3 comparison receipts remain readable. Further destructive cleanup requires binding a complete index to the same recorded winner through `finish` with `--archive-to` and `--comparison-evidence`. The training outcome, terminal step and recorded winner cannot change. A relocated comparison archive needs deployment-specific verification of its recorded paths; ordinary local completion continues to support relocating its store before consolidation.

These guarantees cover cooperating local processes and verified file contents. Raw evidence writers must remain stopped during consolidation. External concurrent edits, network filesystems, object stores, distributed writers and power-loss durability need their own backend guarantees and acceptance tests.
