---
name: "auto-review-loop"
description: "Autonomous multi-round research review loop. Repeatedly reviews using Gemini via gemini-review MCP, implements fixes, and re-reviews until positive assessment or max rounds reached. Use when user says \"auto review loop\", \"review until it passes\", or wants autonomous iterative improvement."
---
<!-- GENERATED from skills/auto-review-loop/SKILL.md — do not edit directly -->

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
<!-- EVO-INQUIRY:END -->


# Auto Review Loop: Autonomous Research Improvement

Run the existing bounded review cycle. Read its setup and recovery instructions before review. Load the review, revision, and stop rules at their respective stages. Record each actual round and preserve reviewer evidence.

## Workflow references

Use the applicable stages in order. Load the referenced instructions when the stage is needed.

- [Context: $ARGUMENTS through Phase D: Wait for Results](references/workflow-01-context-arguments.md)
- [Phase E: Document Round through Prompt Template for Round 2+](references/workflow-02-phase-e-document-round.md)
