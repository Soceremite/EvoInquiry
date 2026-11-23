---
name: grant-proposal
description: "Draft a structured grant proposal from research ideas and literature. Supports KAKENHI (Japan), NSF (US), NSFC (China, including 面上/青年/优青/杰青/海外优青/重点), ERC (EU), DFG (Germany), SNSF (Switzerland), ARC (Australia), NWO (Netherlands), and generic formats. Use when user says \"write grant\", \"grant proposal\", \"申請書\", \"write KAKENHI\", \"科研費\", \"基金申请\", \"写基金\", \"NSF proposal\", or wants to turn research ideas into a funding application."
argument-hint: "[research-direction — grant-type] [— style-ref: <source>]"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Skill, mcp__codex__codex, mcp__codex__codex-reply
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


# Grant Proposal: From Research Ideas to Fundable Application

Determine the funder and proposal type, then apply the corresponding requirements. Follow the existing research, outline, drafting and review stages. Keep external evidence and final handoff conditions traceable.

## Workflow references

Use the applicable stages in order. Load the referenced instructions when the stage is needed.

- [Overview through GENERIC](references/workflow-01-overview.md)
- [State Persistence (Compact Recovery) through Year 2](references/workflow-02-state-persistence-compact-recovery.md)
- [2.5 Structural Review through Phase 4: External Review](references/workflow-03-2-5-structural-review.md)
- [Round 1 (full draft review): through Composing with Other Skills](references/workflow-04-round-1-full-draft-review.md)
- [Sub-skills used by this skill through Output Protocols](references/workflow-05-sub-skills-used-by-this-skill.md)
