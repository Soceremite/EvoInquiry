---
name: research-lit
description: "Find and synthesize research literature, including supplied local paper excerpts, reading levels, and evidence boundaries. Use for literature reviews and paper explanations."
argument-hint: "[paper-topic-or-url]"
allowed-tools: Bash(*), Read, Glob, Grep, WebSearch, WebFetch, Write, Agent, mcp__zotero__*, mcp__obsidian-vault__*
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


# Research Literature Review

Choose applicable sources and a reading depth for the literature request. Trace statements to verified material, record evidence and uncertainty, and run the write-back stages only when applicable.

## Workflow references

Use the applicable stages in order. Load the referenced instructions when the stage is needed.

- [Constants through Step 0c: Scan Local Paper Library](references/workflow-01-constants.md)
- [Step 1: Search (external)](references/workflow-02-step-1-search-external.md)
- [Step 1.5: Verify Candidate Papers (anti-hallucination, mandatory) through Step 5: Save (if requested)](references/workflow-03-step-1-5-verify-candidate-papers-anti-hallucination-.md)
- [Step 6: Update Research Wiki through Key Rules](references/workflow-04-step-6-update-research-wiki.md)
