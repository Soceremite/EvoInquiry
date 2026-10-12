# Workflow controls

[中文](CUSTOMIZATION_CN.md) · [README](../README.md)

Give the selected skill your research direction, available artifacts, desired
output, and resource limits. Read its `SKILL.md` for supported parameters and
defaults. Parameters passed through a pipeline apply only where the downstream
skill supports them.

| Control | Meaning |
| --- | --- |
| `AUTO_PROCEED=true` | Report the selected path and continue authorized work in the same turn |
| `AUTO_PROCEED=false` | Pause at selection checkpoints and resume after an explicit reply |
| `human checkpoint: true` | Request feedback at the review checkpoints defined by the skill |
| `venue: <target>` | Specify the submission target and its applicable requirements |
| `gpu: local` or `gpu: remote` | Select available compute; supply the server and environment when remote |
| `sources: <available sources>` | Select literature sources already configured for this project |
| `effort: lite`, `balanced`, `max`, or `beast` | Choose the workflow depth supported by that skill |
| `assurance: draft`, `polished`, `conference-ready`, or `submission` | Select the required audit level where supported |

For example:

> Use `evo-inquiry:research-pipeline` for this direction. Set
> `AUTO_PROCEED=false`, use the supplied local GPU, and target the stated venue.

Specify maximum GPU hours, parallel jobs, review rounds, spending, and stopping
conditions in the task. Check the concrete plan against these limits before
launching work. A review score is a workflow signal; substantive conclusions
must remain tied to actual evidence.

Explicitly blocking checkpoints, missing required inputs, and external actions
still follow their authorization rules. Silence after a turn ends does not
resume a blocked workflow. `AUTO_PROCEED=true` governs its selection checkpoints;
it does not authorize unrelated actions or additional spending.

Set project-specific constraints in the project's instructions. Save completed
artifacts and pending work using [session recovery](SESSION_RECOVERY_GUIDE.md).

## Experiment storage

Specify a storage budget together with compute resources, for example:

> Use the existing trainer. Budget 80 GiB for experiment artifacts, keep the
> latest two full recovery points and one validation-selected best model, and
> allow at most 15 minutes of training progress to be lost on interruption.
> After training finishes or I explicitly end it, release unused recovery states
> after validating inference weights. Prefer only the completed comparison group's
> validation-selected winner weights; preserve planned dependencies and ask if
> retaining all comparison weights needs a decision. Check peak storage before launch.

These are project requirements to translate into the actual trainer's supported
options and callbacks, rather than universal command-line flags. See the
[storage policy](../skills/skills-codex/shared-references/experiment-storage.md).
Existing running code keeps its saving behavior until that code/configuration
is changed and, when required, restarted from a valid checkpoint.

The two-generation default applies to active or temporarily paused training.
When all steps finish or the user explicitly ends training, validate required
inference exports and persist evidence before releasing unused recovery state.
For comparable finished experiments, prefer only the predeclared validation
winner's weights. Inspect the future plan and pin ablation, ensemble or downstream
inputs; if retention needs a choice, present measured costs and ask the user
whether to retain winner-only or all comparison weights. Keep every run's metrics,
configuration, seeds and negative results. Explicit continuation or all-model
requirements take precedence and count toward the cumulative budget.

Framework counts may include the best checkpoint: for example, Trainer retention
must leave room for both recent recovery generations when the best is older.
Weights-only exports omit training state. Verify the installed version's options.

Custom local loops can use [checkpoint_retention.py](../tools/checkpoint_retention.py)
with their own writer and loader validator. Its byte limit counts artifacts and
unregistered files in a dedicated run directory, excluding current manifest/lock
metadata; allow additional filesystem headroom for metadata and its atomic writes.
Inspection hashes files, so measure its I/O cost on large checkpoints. A policy
cannot remove the need for adequate capacity for a complete new save.

The helper's `finish` API/CLI ends recovery retention after a verified final
weights export. It also supports an explicitly chosen finished winner via
`--archive-to WINNER_ROOT`, pinning that model before releasing the losing run's
best/final roles. Dependency pins and unregistered/changed files stay protected.
It does not rank experiments or infer future research needs. Example previews:

```bash
python tools/checkpoint_retention.py finish RUN_ROOT --outcome completed --step 300000 --reason "Training completed"
python tools/checkpoint_retention.py finish LOSER_ROOT --outcome completed --step 300000 --reason "Validation-selected winner" --archive-to WINNER_ROOT
```

Add `--apply` only under the established cleanup policy, after stopping writers
and persisting results. A permanent user stop uses `--outcome stopped` and the
actual last step. A temporary pause keeps recovery states.
