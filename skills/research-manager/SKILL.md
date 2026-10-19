---
name: research-manager
description: "Record research decisions, evidence-driven pivots, deferred branches and cross-session handoffs in existing project records. Use to consolidate research history; research-guide selects the next workflow and research-wiki stores knowledge."
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Preserve the user's
scope and the active workflow's review, resource and recovery contracts.

For sustained work or recovery, use [bounded inquiry](../shared-references/bounded-inquiry.md). Save findings and requested deliverables still missing, then refresh the handoff after relevant changes. On resume verify current sources, original timing and unresolved work; do not duplicate an existing attempt.
<!-- EVO-INQUIRY:END -->

# Research decisions and handoffs

Consolidate what changed, why it changed and what evidence could change the
decision again. Read [research-decisions](../shared-references/research-decisions.md)
when writing durable records. Record meaningful choices and findings, not every
command, formatting edit or temporary tool failure.

## Inspect before recording

Find the actual project question, relevant artifacts and existing decision log
or wiki. Distinguish user instructions, user decisions, verified observations,
agent proposals and agent actions. Inferences about what the user wants remain
proposals; a command being planned is not an action already performed.

Check evidence behind resumed statuses and substantial findings. Cite original
results and review receipts rather than copying a summary into a new authority.
When sources conflict or are unavailable, preserve the uncertainty in the handoff.
An absent artifact can limit the conclusion without blocking unrelated preparation.

## Use one record owner

Prefer the project's existing decision document. If a wiki is already enabled
and no decision document owns this information, use its `decisions.jsonl` through
the installed package's `tools/research_wiki.py record_decision` command. Resolve
the actual wiki path; do not assume `.ei/research-wiki` or initialize a wiki just
to answer a question. The shared reference documents the exact input fields.

Preserve stable decision IDs, original choices, dissent and meaningful failed
branches. A later decision supersedes an earlier one with an explicit reference;
do not rewrite the earlier choice as though the project never considered it.
Repeating a handoff should not duplicate the same decision.

For each important decision record the question, alternatives, choice or proposal,
reason, evidence, open uncertainties and a revisit trigger. Keep this proportional:
a short requested handoff can be one paragraph with evidence paths.

## Reuse a decision before repeating its work

When selecting a later investigation, retrieve relevant prior choices from the
existing owner and check their scope, evidence, uncertainty and revisit trigger.
The optional read-only `tools/research_memory.py` accepts explicit Markdown or
wiki decision-ledger paths; see [bounded-inquiry](../shared-references/bounded-inquiry.md).
Lexical similarity does not make a historical proposal true or authorize a retry.
Changed evidence and superseding decisions require reading the original context.
A failed process is not a failed scientific hypothesis. Retain useful negative
findings and identify what changed before reopening a costly rejected branch.

## Respect workflow boundaries

Use an available workflow router when the next step is unclear, and
[research-wiki](../research-wiki/SKILL.md) for paper/entity operations.
The Codex distribution provides `research-guide` for routing.
The manager does not create a second scheduler, run-state file or exploration DB.
It cannot mark a phase accepted, override a pending reviewer, certify a hypothesis,
launch an experiment or delete artifacts just because a decision was recorded.

There is no implicit session-end callback: capture important authorized milestones
while the session is active, or prepare the requested handoff. State remaining
work and its prerequisites honestly; do not promise background continuation.
