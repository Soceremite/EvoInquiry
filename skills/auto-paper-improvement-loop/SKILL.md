---
name: auto-paper-improvement-loop
description: "Autonomously improve a generated paper via GPT-6-Astra xhigh review → implement fixes → recompile, for 2 rounds. Use when user says \"改论文\", \"improve paper\", \"论文润色循环\", \"auto improve\", or wants to iteratively polish a generated paper."
argument-hint: "[paper-directory] [— style-ref: <source>] [— edit-whitelist <path>]"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Skill, mcp__codex__codex, mcp__codex__codex-reply
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
<!-- EVO-INQUIRY:END -->


<!-- EI-GOVERNANCE:BEGIN -->
Resolve runtime state through tools/state_paths.py before .ei operations. Use
[project-governance](../shared-references/project-governance.md) for fixed evidence,
profiles and controlled migration; missing profiles retain compat-v1.
<!-- EI-GOVERNANCE:END -->


# Auto Paper Improvement Loop: Review → Fix → Recompile

Run the existing bounded improvement loop on a supplied draft. Confirm edit scope before revision, preserve reviewer and compile evidence, and stop at the specified round or acceptance gate.

## Workflow references

Use the applicable stages in order. Load the referenced instructions when the stage is needed.

- [Context through Rationale](references/workflow-01-context.md)
- [Inputs through Step 4: Recompile Round 1](references/workflow-02-inputs.md)
- [Step 4.5: Restatement Regression Test through Step 7: Recompile Round 2](references/workflow-03-step-4-5-restatement-regression-test.md)
- [Step 8: Format Check through Review Tracing](references/workflow-04-step-8-format-check.md)
