---
name: auto-review-loop
description: Autonomous multi-round research review loop. In Copilot CLI it defaults to the native complementary rubber-duck subagent with host-event model evidence; elsewhere it uses Codex, while explicit external reviewer overrides remain available. Implements fixes and re-reviews until a policy-approved positive assessment or max rounds is reached.
argument-hint: "[topic-or-scope]"
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit, Skill, Task, mcp__codex__codex, mcp__codex__codex-reply, mcp__manual_review__review, mcp__manual_review__review_reply
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.

When changing research code, use [code-reuse-and-docs](../shared-references/code-reuse-and-docs.md) for readable interfaces and code-side documentation.
<!-- EVO-INQUIRY:END -->


<!-- EI-GOVERNANCE:BEGIN -->
Resolve runtime state through tools/state_paths.py before .ei operations. Use
[project-governance](../shared-references/project-governance.md) for fixed evidence,
profiles and controlled migration; missing profiles retain compat-v1.
<!-- EI-GOVERNANCE:END -->


# Auto Review Loop: Autonomous Research Improvement

Run the existing bounded review cycle. Read its setup and recovery instructions before review. Load the review, revision, and stop rules at their respective stages. Record each actual round and preserve reviewer evidence.

## Workflow references

Use the applicable stages in order. Load the referenced instructions when the stage is needed.

- [Context: $ARGUMENTS through Reviewer Calling Convention](references/workflow-01-context-arguments.md)
- [State Persistence (Compact Recovery) through Loop (repeat up to MAX_ROUNDS)](references/workflow-02-state-persistence-compact-recovery.md)
- [Phase A: Review through Instructions](references/workflow-03-phase-a-review.md)
- [Phase B: Parse Assessment through Phase B.5.1: Stop-Evaluation Gate](references/workflow-04-phase-b-parse-assessment.md)
- [Phase B.6: Debate Protocol (hard + nightmare only) through Phase C: Implement Fixes (if not stopping)](references/workflow-05-phase-b-6-debate-protocol-hard-nightmare-only.md)
- [Phase D: Wait for Results through Key Rules](references/workflow-06-phase-d-wait-for-results.md)
- [Prompt Template for Round 2+ through Stop-Gate State-Transition Tests](references/workflow-07-prompt-template-for-round-2.md)
