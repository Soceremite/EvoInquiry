---
name: research-guide
description: "Resume a research project or choose its next step when the stage is unclear or spans workflows. Coordinate relevant skills using existing evidence, goals, and constraints."
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.

For analysis-to-plan requests, use the scope boundaries in [task-scope](../shared-references/task-scope.md). For artifact-producing experiments, carry the established [storage policy](../shared-references/experiment-storage.md) to the execution skill.
<!-- EVO-INQUIRY:END -->


# Research Guide

Coordinate continuation or an uncertain next step; execute the selected work
within the user's requested deliverable. An explicit skill choice takes priority.
For a clear single-step request, read and use that execution skill directly.
Plugin maintenance and ordinary software work retain their own task scope.

## Establish the current task

Use the conversation and project instructions to identify the question, requested
output, existing authorization, resources, and stopping point. Advice-only
requests end with advice. Reuse known constraints rather than asking again.

Find relevant existing proposals, literature notes, raw results, review artifacts,
or run state using targeted searches. Read only material that affects the next
decision. Projects need no particular directory layout or guide-specific state.

For a resumed run, confirm its project and task identity, then inspect the
artifacts supporting each relevant status. File existence or `done` alone does
not establish acceptance. Preserve accepted/provisional distinctions and the
run's policy. Read the active workflow's recovery contract before changing its
state; report missing or contradictory evidence instead of advancing a gate.
Identify which workflow produced a checkpoint before loading its recovery rules.
A state directory alone does not request the full lifecycle. When the producing
workflow is unknown, preserve its record and report that uncertainty; a local
recovery diagnosis or handoff can finish without starting another workflow.
For a recovery diagnosis, verify the checkpoint, prepare only work independent
of its missing prerequisites, and complete the requested handoff once these facts
are established. Keep incidental evidence caveats in that handoff. Load a separate
claim, review, or experiment-planning workflow when its deliverable is requested
or necessary for the authorized goal. A blocked prerequisite stops forward
orchestration; it does not require a formal claim review of the available inputs.

## Choose and perform the next step

Identify the uncertainty that matters for this deliverable. Choose the smallest
adequate investigation and state what its result will change. Useful routes:

| Current need | Execution skill |
| --- | --- |
| Related work or understanding supplied papers | [research-lit](../research-lit/SKILL.md) |
| Focused method proposal | [research-refine](../research-refine/SKILL.md) |
| Evidence design for a fixed method | [experiment-plan](../experiment-plan/SKILL.md) |
| Numerical analysis of existing runs | [analyze-results](../analyze-results/SKILL.md) |
| What results support or experimental integrity | [result-to-claim](../result-to-claim/SKILL.md), [experiment-audit](../experiment-audit/SKILL.md) |
| Single critical review or paper-number audit | [research-review](../research-review/SKILL.md), [paper-claim-audit](../paper-claim-audit/SKILL.md) |
| Implement an existing experiment plan | [experiment-bridge](../experiment-bridge/SKILL.md) |
| Explicit full research lifecycle | [research-pipeline](../research-pipeline/SKILL.md) |

These routes are examples; select other available skills when they better match
the task. Resolve sibling paths from this installed SKILL.md, not a guessed
checkout or a previous installation. Do not load the whole catalog.

Read the selected SKILL.md before execution. Check its inputs, dependencies,
outputs, reviewer requirements, recovery rules, and blocking checkpoints. Carry
forward the evidence paths and constraints it needs. A missing service can block
a dependent step while independent preparation continues; preserve that skill's
required blocked or provisional status. Do not impersonate unavailable reviewers.

Perform the authorized work, then check actual artifacts and tool results against
the requested output. Selecting a skill or describing its plan is not completion.
Separate observed findings, interpretation, missing evidence, and review status.
When a blocker is confirmed, record its evidence in the requested artifact before
optional investigation. Mark unfinished checks so an interrupted attempt leaves
usable findings without implying completion.

## Continue or stop

Continue necessary adjacent steps within the same authorized goal. Reassess
after negative results: revise the explanation, narrow the claim, prepare a
discriminating test, or stop according to the evidence and remaining resources.
End when the deliverable is complete, a required dependency/checkpoint blocks
continuation, or a user-defined budget or stopping condition is reached.

Use the active workflow's existing records for persistence. Leave the completed
work, evidence paths, unresolved issue, and next feasible step in the requested
artifact or existing project notes. Do not create a parallel guide state system.
