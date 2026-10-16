# Research decisions and record ownership

Load when the requested work needs durable decisions or a handoff. Ordinary
analysis and advice do not require initialization, a new database or this format.

## One authority

Use the project's existing decision log if present. Otherwise an already enabled
wiki may own `<wiki_root>/decisions.jsonl`. Do not maintain both as authoritative
copies. Wiki indexes and handoffs may summarize and link to the authority.
Runtime status remains owned by `run_state.py`; evidence and reviewer receipts
remain owned by their producing workflows. A recorded decision does not accept
a phase or prove a research claim.

Capture meaningful choices, evidential turning points and deferred branches.
Preserve the original research question, rejected alternatives and criteria for
revisiting the choice. Distinguish failed execution from evidence against a method.
Keep null and negative findings that affect a decision.

## Provenance and revision

Use `user_instruction`, `user_decision`, `verified_observation`, `agent_proposal`
or `agent_action`. The tag describes the recorded event, not merely who typed
the note. Never infer that the user approved a suggestion. Evidence availability
and a true scientific conclusion are separate questions; the writer checks record
structure and referenced files, not semantic validity.

Each record has `id`, `question`, nonempty `alternatives`, `choice`, `reason`,
`provenance`, `evidence` (project-relative paths), `uncertainties`, `revisit_when`,
and optional `supersedes`. Use a new ID for a changed decision and point at the
old one; the original remains. Identical writes with the same ID are idempotent,
different content with that ID is rejected. `evidence` may be empty for a clearly
identified proposal; a verified observation requires evidence.

When the wiki owns the record, save this JSON to a local file and use:

```text
python <installed-package>/tools/research_wiki.py record_decision <wiki-root> --input <record.json> --project-root <project-root>
```

This command requires an existing initialized wiki. It writes only its decisions
ledger under a cooperating-writer lock; malformed or interrupted ledger contents
block further writes and are preserved for recovery. It does not migrate other
project records. Read or hand off the original record when uncertain rather than
silently repairing or overwriting it.

## Handoff

Report the active question, completed work with source paths, current decision,
unfinished checks, relevant review status, resource limits and next feasible step.
Verify material paths before saying they are available. Missing evidence remains
missing after a handoff. Update the existing artifact rather than proliferating
new checklists or histories for every short follow-up.
