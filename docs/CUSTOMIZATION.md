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
