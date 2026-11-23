---
name: proof-checker
description: Rigorous mathematical proof verification and fixing workflow. Reads a LaTeX proof, identifies gaps via cross-model review (external reviewer backend, ultra reasoning), fixes each gap with full derivations, re-reviews, and generates an audit report. Use when user says "检查证明", "verify proof", "proof check", "审证明", "check this proof", or wants rigorous mathematical verification of a theory paper.
argument-hint: "[path-to-tex-file or proof-description] [--deep-fix] [--restatement-check]"
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit, Agent, mcp__codex__codex, mcp__codex__codex-reply, mcp__manual_review__review, mcp__manual_review__review_reply
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
Pin the proof and executable evidence revisions examined; preserve actual review status and test limitations. Do not replace proof reasoning with schema checks.
<!-- EI-GOVERNANCE:END -->


# Proof Checker: Rigorous Mathematical Verification & Fixing

Choose the ordinary or deep-fix route for an existing proof. Follow the evidence and revision rules for each stage. Preserve the exact theorem, verified repairs, and remaining proof obligations.

## Workflow references

Use the applicable stages in order. Load the referenced instructions when the stage is needed.

- [Context: $ARGUMENTS through Phase 0: Preparation](references/workflow-01-context-arguments.md)
- [Phase 0.5: Proof-Obligation Ledger through Phase 1: First Review (reviewer backend, ultra reasoning)](references/workflow-02-phase-0-5-proof-obligation-ledger.md)
- [Phase 1 addendum — `--deep-fix` opt-in through Regression proof-audit](references/workflow-03-phase-1-addendum-deep-fix-opt-in.md)
- [Phase 3.6: Theorem Restatement Regression (opt-in) through Key Rules](references/workflow-04-phase-3-6-theorem-restatement-regression-opt-in.md)
- [Mathematical rigor through Verdict decision table](references/workflow-05-mathematical-rigor.md)
- [Thread independence through Example Invocations](references/workflow-06-thread-independence.md)
