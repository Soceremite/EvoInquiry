# Session recovery

[中文](SESSION_RECOVERY_GUIDE_CN.md) · [README](../README.md)

Keep project state on disk so a new session can resume from actual artifacts.
In Codex, use the project's instructions or a linked status file for a short
`Pipeline Status` record. Retained workflow templates may call this file
`CLAUDE.md`; the record can be adapted to the project's host without inventing
completed work or replacing the underlying research artifacts.

Record the current stage, selected idea, research contract, branch, completed
outputs, active jobs, resource limits, blocking questions, and next action.
For each active job, save its server, process/session identifier, output path,
and a command that can check its state. Update the record after stage changes,
major decisions, job start/stop, and before a handoff.

Read the status record first on recovery, followed by:

1. `idea-stage/docs/research_contract.md`, or the saved path for the active idea.
2. The relevant plans, experiment logs, raw results, and review reports.
3. Live status of any recorded background jobs, before relaunching them.
4. Pending authorization or required inputs, then the recorded next action.

Use the [research contract template](../templates/RESEARCH_CONTRACT_TEMPLATE.md)
and [experiment log template](../templates/EXPERIMENT_LOG_TEMPLATE.md) when
starting those artifacts. A compact status record points to evidence;
it does not replace it.

For stateful runs, follow the skill's
[resumable-run contract](../skills/skills-codex/shared-references/resumable-runs.md)
and the bundled `tools/run_state.py` helper. Proof projects also maintain their
own run directories through `proof-orchestrator`.
