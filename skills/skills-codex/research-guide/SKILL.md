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

For authorized sustained work or recovery, use [bounded inquiry](../shared-references/bounded-inquiry.md): reuse the existing owner, original budget and valid evidence; choose the smallest discriminating step and save useful progress before closeout. Use documented helpers before inspecting implementation. Advice and small tasks need no new runtime.
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

When project identity or runtime state matters, discover the existing profile
through the shared .ei resolver; a missing profile still uses compat-v1 without
initialization. Route requested project audits/layouts/migrations to
[project-governance](../project-governance/SKILL.md) and dependency/environment
maintenance to [environment-maintenance](../environment-maintenance/SKILL.md).
Carry fixed evidence refs and existing consumer/lease/pin constraints into the
selected step. Do not add governance setup to an unrelated small task.

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
| Vague direction, problem framing or a research pivot | [scientific-brainstorming](../scientific-brainstorming/SKILL.md) |
| Several open problems may share a cause, or local fixes are multiplying | [problem-synthesis](../problem-synthesis/SKILL.md) |
| Record decisions, pivots or a research handoff | [research-manager](../research-manager/SKILL.md) |
| Related work or understanding supplied papers | [research-lit](../research-lit/SKILL.md) |
| Concrete method candidates within an established problem | [idea-creator](../idea-creator/SKILL.md) |
| Focused method proposal | [research-refine](../research-refine/SKILL.md) |
| Evidence design for a fixed method | [experiment-plan](../experiment-plan/SKILL.md) |
| Numerical analysis of existing runs | [analyze-results](../analyze-results/SKILL.md) |
| Requested formal judgment of a specified claim | [result-to-claim](../result-to-claim/SKILL.md) |
| Comparative fairness or execution integrity | [experiment-audit](../experiment-audit/SKILL.md) |
| Single critical review or paper-number audit | [research-review](../research-review/SKILL.md), [paper-claim-audit](../paper-claim-audit/SKILL.md) |
| Implement an existing experiment plan | [experiment-bridge](../experiment-bridge/SKILL.md) |
| One status check or continuous training observation | [monitor-experiment](../monitor-experiment/SKILL.md) or [training-check](../training-check/SKILL.md), respectively |
| New poster, including an old `/paper-poster` call | [paper-poster-html](../paper-poster-html/SKILL.md); the old name only forwards arguments |
| Explicit full research lifecycle | [research-pipeline](../research-pipeline/SKILL.md) |

These routes are examples; select other available skills when they better match
the task. Resolve sibling paths from this installed SKILL.md, not a guessed
checkout or a previous installation. Do not load the whole catalog.

Keep one owner for the requested output. Ordinary trajectory review stays with
the active workflow; multiple unresolved problems can use `problem-synthesis`
for their structure, then return to the existing planner or executor. The guide
routes, the manager records decisions, and the wiki stores and queries relationships.
An ordinary numerical question does not automatically require claim adjudication.
Composition workflows reuse valid child artifacts and completed reviews rather
than redoing them. Select one review-loop backend for a run, preserving its
identity and pending work when resuming through a compatibility entrypoint.

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

## Sustained tasks and host modes

For a multi-step continuation with budgets or interrupted work, read
[bounded-inquiry](../shared-references/bounded-inquiry.md). Reuse the existing run
and decision owner. Inspect relevant prior failed or deferred routes before a
costly repeat; verify evidence and the condition that would justify reopening one.
Select the next investigation by its ability to distinguish competing explanations,
including a null outcome, at an authorized cost. Use action reservations and real
execution reconciliation when that existing run needs them. Short tasks do not
require initialization or a new contract.

Codex Plan helps review the path before implementation. A planning-only request
ends with the plan; requested monitoring of existing jobs can continue read-only
while the host supports it. Route that watch to `training-check`; do not launch,
stop jobs or persist research state from observation-only work. Approved
implementation continues within its authorization.
Native Goal is optional and only created on an explicit user request with available
host tooling. It tracks a thread objective, while project records hold evidence.
A Goal does not grant resources, remove review gates or prove a scientific result.
Waiting for healthy long training is active monitoring, not a zero-finding research
iteration or a reason to mark the Goal blocked/stalled. Use available host waits
and continuation; Plan-only does not guarantee automatic continuation after a turn.
Do not claim to switch modes or persist background work without host support.
For ongoing authorized work, prefer reflection after N complete experimental
blocks; a multi-method, multi-seed comparison counts once after analysis. Choose
N for the project and review earlier when evidence warrants it. Do not invent a
total time window. Reflection and authorized replanning are active Goal work:
resolve them and continue rather than marking the Goal `blocked`. Honor explicit
budgets and the host's genuine-blocker rules; review cadence grants no resources.

## Continue or stop

Continue necessary adjacent steps within the same authorized goal. Reassess
after negative results: revise the explanation, narrow the claim, prepare a
discriminating test, or stop according to the evidence and remaining resources.
End when the deliverable is complete, an unavailable required dependency prevents
further useful authorized work, or a user-defined budget or stopping condition is
reached. An ordinary checkpoint is the next task to perform within that work.

Use the active workflow's existing records for persistence. Leave the completed
work, evidence paths, unresolved issue, and next feasible step in the requested
artifact or existing project notes. Do not create a parallel guide state system.
