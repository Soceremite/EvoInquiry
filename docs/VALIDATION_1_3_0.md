# EvoInquiry 1.3.0 validation

This report describes the 1.3.0 source changes and their current acceptance scope. It does not reuse the 1.2.0 release's test counts as results for the changed checkpoint helper. Final local Linux regression passes; native macOS and Windows CI remains pending. The machine-readable companion is [release-validation.json](../release-validation.json).

## Implemented scope

Eight existing skills load the new comparison reference when their task involves empirical comparison: experiment-plan, ablation-planner, experiment-bridge, run-experiment, experiment-queue, analyze-results, experiment-audit and result-to-claim. Both skill collections carry the reference. The opt-in research-guidance helper, scoped instruction template, comparison evidence validator and checkpoint evidence gate are included.

The source retains 86 Codex entrypoints, 83 protected workflow bodies, 450 protected resources and 34 previously approved digest-pinned adaptations. Current source-preservation and inventory checks pass. The checkpoint helper itself deliberately changes in 1.3.0; its current digest is recorded in the machine-readable report.

## Current local checks

| Check | Current result | Scope |
| --- | --- | --- |
| Focused regression | 164 passed, 2 native Windows cases skipped | Real files, declared slots, attempts, selection, evidence hashes, archive preview/apply/retry, dependency pins, legacy binding, scoped routing and mirrors |
| Packaging and release tests | 26 passed | Required new resources, version metadata, retained-source contracts and actual publication arguments without a network publication |
| Full Python 3.12 regression | 1053 passed, 35 skipped; no failures | Final fixed Linux runtime; includes the real PyTorch training/restoration pilot |
| Native Codex discovery | 86 unique enabled entries per scope; 801 source files matched | Isolated candidate installation and native skills/list, without a model completion or changes to the user's installed plugin |

The focused run includes the existing real PyTorch CPU interrupted-versus-continuous training witness. The complete Python 3.12 run also passes the governed two-method, three-seed training/restoration pilot. It required local test services and file-attribute operations beyond the filesystem sandbox. The first sandboxed run failed ten cases: nine of them passed when those host operations were allowed; the remaining single-file helper dependency was a real implementation regression, repaired by lazy-loading the archive validator. A preliminary complete run then passed 1052 cases; the final immutable-source result above additionally covers bounded JSON records and configures the two new NTFS cases for native Windows. These counts describe separate runs and are not added together. Its system test environment needed the process-local protobuf Python implementation setting; no live training environment was modified. The dedicated full-suite runner uses Python 3.12 and existing compatible dependencies in an isolated temporary virtual environment. A Python 3.10 full-suite attempt stopped at collection because the harness imports the Python 3.11+ `tomllib` standard library; that attempt is not counted as a complete regression.

The generic skill-creator frontmatter validator passes five changed skill entries and rejects an existing `argument-hint` field in experiment-queue, experiment-audit and result-to-claim. The same three failures are reproduced on the unchanged 1.2.0 entries. Their fields are preserved under the retained-source contract; native Codex discovery is the loader compatibility check.

## What the evidence gate establishes

File-backed tests exercise complete and incomplete method/seed coverage, missing failed attempts, allowed different optimisers, deterministic seed slots, cancellation of unstarted slots, permanently stopped winners, mismatched validation selection, changed or missing configurations/results/logs, unsafe paths, bounded structured-record reading and checkpoint-contained evidence. NTFS-junction cases await their native Windows runner. Integration tests perform actual deletion of disposable weights and verify retained raw evidence, failed attempts, winner bytes and dependency weights.

Interruption tests commit an archive or deletion journal, alter its bound evidence, and confirm that a new store instance refuses further deletion. Restoring the recorded evidence permits safe completion. Legacy comparison receipts remain readable, block destructive cleanup without evidence, and accept binding only to their recorded winner and training outcome. Standalone checkpoint trainers retain single-file normal operation; comparison consolidation additionally requires the companion validator in the frozen source.

This does not establish that a ledger records every job that actually ran, that a protocol predates observed results, or that selection/aggregation is numerically correct. The gate verifies declared coverage, identities and fixed bytes. Scientific fairness and claim support still require inspection of raw outputs, configurations and code through the existing review workflows.

## Platform and behaviour limits

The Linux/macOS full-suite workflows and both native Windows shell workflows are configured to include the new portable tests. They have not yet run against a published 1.3.0 tag in this implementation session. Historical governance/platform evidence is available in [governance validation](UPGRADE_VALIDATION_CN.md) and [portability validation](PORTABILITY_VALIDATION_CN.md); it is not a new cross-platform acceptance result for 1.3.0.

Native skill discovery demonstrates loader visibility, not a guaranteed implicit invocation rate. No new paid model behavioural evaluation, large GPU comparison, distributed writer, object-store retention, network-filesystem or power-loss acceptance is claimed. The CPU/file tests need no GPU resources. Persistent routing is opt-in; installation alone does not add global preferences.

## Reproduce

Use Python 3.12 and install `requirements-dev.txt` in a separate environment. Run:

```bash
python -m pytest tests/ -q -rs
python tools/verify_evo_inquiry.py
python tools/check_skills_inventory.py
```

Run the native Windows gate under both `powershell.exe` and `pwsh`, as declared in CI. For a specific campaign, validate its actual comparison index with `tools/comparison_evidence.py`; passing synthetic test fixtures does not validate that campaign's evidence.
