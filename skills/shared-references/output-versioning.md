# Output Versioning Protocol

Research evidence uses fixed artifact identity and immutable content. Layout
profiles select locations; they do not change publication or review semantics.
Read [project-governance](project-governance.md) for identity and migration.

## Layouts and compatibility

Without project.yaml, keep compat-v1: idea-stage/, refine-logs/, review-stage/,
paper/ and existing timestamped histories. Read old root-level inputs when their
stage path is absent. Do not relocate manual files merely to introduce governance.
A named latest copy is navigation; resolve and retain its backing fixed revision
once before a formal analysis, review or paper.

governed-v1 is explicitly selected. Its authority path is
reports/history/<artifact_id>/<revision>/<filename>; reports/current/<artifact_id>.json
holds a replaceable pointer. Current never becomes historical evidence identity.
Existing workflow state remains .ei/runs/<workflow_run_id>.json, with the original
coordinator, IDs and accepted/provisional/done policy.

Namespace conversion and artifact-layout choice are independent. Legacy state
is read only through explicit compatibility or a verified migration receipt.
A layout rollback does not remove immutable revisions already produced.

## Publishing an evidence artifact

Use tools/artifact_registry.py and its shared schema/digest/lock implementation:

1. Freeze and verify input refs, producer, authority path and content hash.
   Preserve actual review provenance; never infer acceptance from a file.
2. Stage unique bytes and a transaction journal; verify staged content.
3. Publish the unused fixed body path. Historical bytes cannot be overwritten.
4. Append the digest-bound metadata event.
5. Under the publication lock, compare expected_current and update the pointer.
   A conflict retains both revisions and reports the failed pointer update.
6. Rebuild index.json and append MANIFEST once per transaction.

Retries reuse the same transaction, record and bytes. Do not double-write
metadata authority or authoritative text. Compat fixed-name copies, when a
project needs them, are replaceable navigation; the timestamped/registered
revision is evidence. An existing manual fixed-name file needs applicable
authorization before replacement. The registry never overwrites unregistered text.

A multi-file publish is not atomic. Local locks and verified atomic rename are
the MVP boundary. Unfinished journals, orphan content, partial events, missing or
wrong hashes and stale aliases stop new publication and require explicit
reconcile/repair. Never silently truncate damage or select newer inputs to repair
historical evidence.

## Files outside the evidence publication protocol

Append-only findings/wiki logs and MANIFEST retain their existing roles.
Per-round outputs already have distinct round identities. Dashboards and workflow
state are mutable operational records, not scientific verdicts. Ordinary notes,
small edits or advice do not require a governance profile or registry workflow.

When retaining the legacy timestamp mechanism, use second precision plus a
collision suffix, keep prior timestamped files, and fix references at evidence
handoff. Register unverifiable legacy artifacts as legacy-unverified; do not
create fictional historical review receipts.

## Resume and stale operational state

Inspect task/project identity and evidence behind resumed statuses. Time alone
cannot determine whether a long research run remains valid. Existing workflow
staleness policies may request a decision; reuse an already supplied choice and
authorization. Archive replaced operational records instead of deleting history.
Execution completion, review acceptance and claim support remain separate.
