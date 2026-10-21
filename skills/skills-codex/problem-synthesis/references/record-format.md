# Recording a synthesis checkpoint

Resolve `<tools>` from the actual loaded package: a mainline skill is under
`<package>/skills/<name>`; its Codex mirror is under
`<package>/skills/skills-codex/<name>`. Use the absolute `<package>/tools` path,
or the project's existing `.ei/tools` / `tools` deployment. Do not assume the
research project is the toolkit repository. A missing required helper blocks
checkpoint completion; do not silently dispatch past it.

```text
python <tools>/problem_synthesis.py due context.json
python <tools>/problem_synthesis.py validate reflection.json
python <tools>/problem_synthesis.py record <root> <run-id> <phase> reflection.json
```

`validate` is read-only. `record` requires an existing run and appends an
idempotent reflection envelope to its `.iterations.jsonl`; it never creates a
run, changes phases or accepts results. When configured, it updates only that
run's existing coordination gate. The returned `reflection_gate` is `required`,
`cleared` or `unconfigured`.

A minimal independent-problems record:

```json
{
  "schema_version": 1,
  "kind": "synthesis",
  "problems": [
    {"id": "P1", "observation": "Observed failure A", "evidence_refs": ["results.json#A"]},
    {"id": "P2", "observation": "Observed failure B", "evidence_refs": ["results.json#B"]}
  ],
  "candidates": [],
  "decision": "KEEP_SEPARATE",
  "reason": "The interventions affect different mechanisms in the recorded cases.",
  "next_actions": [
    {"problem_id": "P1", "action": "Check the first mechanism"},
    {"problem_id": "P2", "action": "Check the second mechanism"}
  ]
}
```

For an active brake add `gate_id` from `research_control.py inspect`.
Each candidate requires `id`, `affected_problem_ids` (at least two),
`shared_cause`, `joint_prediction`, `discriminating_test`,
`supporting_evidence_refs`, `contradicting_evidence_refs` and
`complexity_assessment`. For `MERGE` / `ABSTRACTION_PIVOT` add
`selected_candidate` and `next_action: {"skill": "research-refine",
"description": "Revise the question and plan"}`. Supporting references must be
nonempty; an empty contradiction list means none recorded, not none possible.
`DEFER` / `BLOCKED` require `blocker`; include the revisit condition there.
Evidence references are traceable pointers, not a verified scientific receipt.
Do not add acceptance/verdict fields; use the applicable claim/review skill.
