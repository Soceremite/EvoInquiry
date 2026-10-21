---
name: problem-synthesis
description: "Assess whether multiple unresolved research problems share a cause, should remain separate, or need a different abstraction. Use after repeated local fixes, overlapping failures or branch growth; ordinary trajectory review belongs to the active workflow owner."
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing evidence and
review contracts. Keep observations, interpretations and unknowns separate;
preserve negative findings and stop at the requested boundary.
<!-- EVO-INQUIRY:END -->

# Problem synthesis

Decide whether several observed problems merit a shared research question.
A shared explanation is a testable hypothesis, not a finding established by
this skill. Keep the explanation separate from the observations it may explain.

Use at a comparison or direction boundary when multiple unresolved problems,
repeated fixes or overlapping failures suggest a common cause. For zero or one
problem, return to the active workflow's ordinary trajectory review. Route
fairness/evaluation drift to `/experiment-audit` first.

## Compare explanations

1. Read the original question, current plan, prior decisions and relevant raw
   evidence, including cases and negative findings. Give the open problems
   stable IDs and separate observations from proposed causes.
2. Consider shared causes alongside `KEEP_SEPARATE`. Do not invent a shared
   cause to fill a template: an empty candidate set is valid. Similar words or
   similar curves alone do not establish a common mechanism.
3. For each plausible candidate, state which problems it explains, a joint
   prediction, supporting and contradicting evidence, explanatory cost versus
   separate fixes, and the smallest check that distinguishes the explanations.
   Address important counterevidence. Missing evidence remains unknown.
4. Choose a structural decision and route it to its owner:

| Decision | Handoff |
| --- | --- |
| `MERGE` | A provisional unified question → `/research-refine`, then `/experiment-plan` for the discriminating test. Requires supporting evidence, a joint prediction and a check. |
| `ABSTRACTION_PIVOT` | Change the framing with `/scientific-brainstorming` or `/research-refine`, then revise the plan. Preserve old branches and evidence. |
| `KEEP_SEPARATE` | One next action per problem → existing workflow owner. No obligation to merge. |
| `DEFER` / `BLOCKED` | Record the missing prerequisite and revisit condition; keep dependent dispatch stopped until resolved. |

If evidence is ambiguous, propose an economical distinguishing check or defer;
do not upgrade a plausible explanation to a proven cause. A higher-level
explanation should simplify the problem without erasing distinct mechanisms.

## Record and return control

For advice, a compact response is enough. For sustained work, link the decision
from the existing decision log through `/research-manager`; keep the actual
checkpoint in the existing iteration ledger, not a new database.

For an existing run, read [record-format](references/record-format.md) when
validating or recording the decision with `tools/problem_synthesis.py`.
For a configured continuation contract, use the brake and recovery commands in
[bounded-inquiry](../shared-references/bounded-inquiry.md). Copy the active gate
ID into the reflection; an earlier reflection cannot satisfy a later checkpoint.

`KEEP_SEPARATE` can release the reflection brake. `MERGE` and
`ABSTRACTION_PIVOT` wait for the revised plan handoff; `DEFER` and `BLOCKED`
retain the brake. Releasing it preserves budget, phase and review requirements.
The recorder checks structure and reference identity, not whether the model's
reasoning or cited evidence is scientifically correct.

This skill owns problem structure only. The pipeline owns continuation,
`experiment-plan` owns experiment design, execution skills own jobs,
`research-manager` owns durable decisions, and review/claim skills own judgments.
