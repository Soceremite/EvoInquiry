---
name: "auto-paper-improvement-loop"
description: "Autonomously improve a generated paper via Gemini review through gemini-review MCP → implement fixes → recompile, for 2 rounds. Use when user says \"改论文\", \"improve paper\", \"论文润色循环\", \"auto improve\", or wants to iteratively polish a generated paper."
---
<!-- GENERATED from skills/auto-paper-improvement-loop/SKILL.md — do not edit directly -->

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
<!-- EVO-INQUIRY:END -->


# Auto Paper Improvement Loop: Review → Fix → Recompile

Run the existing bounded improvement loop on a supplied draft. Confirm edit scope before revision, preserve reviewer and compile evidence, and stop at the specified round or acceptance gate.

## Workflow references

Use the applicable stages in order. Load the referenced instructions when the stage is needed.

- [Context through Step 4: Recompile Round 1](references/workflow-01-context.md)
- [Step 5: Round 2 Review through Key Rules](references/workflow-02-step-5-round-2-review.md)
- [Typical Score Progression](references/workflow-03-typical-score-progression.md)
