# Project identity and fixed evidence

Use this contract when project organization, experiment identity, reproducibility,
artifact handoff or namespace migration matters. Do not require a profile or a
layout conversion for a small existing task.

## State and profiles

Resolve the project state root through tools/state_paths.py. New writes use .ei.
Only explicit legacy-read may read unmigrated .aris. Conflicting roots or an
unfinished migration stop writes. Preserve runs/<workflow_run_id>.json and the
existing run_state.py coordinator; never create a second phase state machine.

A missing project.yaml uses compat-v1 without creating files. Explicit init may
choose compat-v1 (existing stage/timestamp paths) or governed-v1
(reports/history/<artifact>/<revision>/). Layout choice is independent of
namespace migration. Authoritative text is published once; current is navigation.
Read [output-versioning](output-versioning.md) for the single publication protocol.

## Identity and handoffs

Project scope, optional implementation family, hypothesis/spec, method variant,
actual execution, workflow and artifact revision are different identities.
A spec freezes hypotheses, methods, data/split/label map/evaluator, seeds,
budget, aggregation, decision and failure policies. Update it with a new revision.

Every actual retry or checkpoint resume gets a new execution_run_id. Keep the
failed attempt; record retry_of or resumed_from plus checkpoint digest. Queue
submission binds a source/config snapshot and environment revision before
launch. A Git SHA does not freeze imports from a mutable checkout.

Use tools/execution_registry.py to register specs, freeze an explicit source
allowlist, prepare distinct attempts and verify snapshots. Dataset manifests
stay fixed; exclude credentials and large unintended files. Record actual
interpreter, imports, job and exit, including failed launches. Save terminal
records and fixed result refs. Resource permission still comes from the user.

Analysis states every included/excluded attempt and the predeclared slot rule.
Do not silently drop failed seeds, pick the best retry or resolve current again
during a historical analysis. Papers pin report/spec/evaluator/execution/verdict
revisions; a changed reference is a manuscript revision, not an alias refresh.

## Registry mechanics

tools/artifact_registry.py provides validate_record, resolve_ref,
register_existing, publish_artifact, rebuild_index and reconcile. APIs and CLI
share tools/registry_common.py and the local versioned schemas. Governance
record validation requires jsonschema>=4,<5; YAML profiles may use PyYAML.
These dependencies belong in a maintenance environment, not a live trainer.

Publish verified staged bytes to an unused fixed authority path, append a
hash-chained event, compare expected_current under the artifact lock, then update
the alias and projection. Append MANIFEST once per transaction. Retry a
transaction only with the same record and content. A CAS conflict retains both
revisions and reports the failed alias update. Existing manual content is not
overwritten merely because it was registered.

Unfinished journals, partial events, orphan content, digest mismatch and alias
drift are visible diagnostics. Stop further publication until explicit recovery.
Local filesystem locks/renames do not make several files an atomic transaction;
distributed/object-store filesystems need another verified protocol.

A schema or integrity PASS cannot create scientific accepted. Preserve actual
review receipts and the existing accepted/provisional distinction. Legacy inputs
without verifiable provenance remain legacy-unverified; never invent old reviews.

## Migration and rollback

First run read-only inventory and plan-migration; dry-run creates no state,
directory or lock. The plan binds source digests, path mapping and writer state.
Use existing user authorization for the selected project and action. Apply
requires plan-bound approval evidence and confirmed external writer/queue shutdown;
a live lease/running phase or participating writer lock blocks switching.

The migration journal retains a verified backup, staging, commit points and
receipt. Copy legacy bytes unchanged, keep IDs/statuses/review/code hashes and map
old locators through the receipt. Rewrite only declared current path fields when
such an extension is needed; do not replace strings in historical evidence.
Only .ei becomes the active root; .aris remains a registered legacy backup.

Resume the same verified transaction after interruption, or explicitly roll it
back after stopping writers. New post-switch content must be preserved and
reconciled before rollback. Migration never includes environment/weight deletion.
Legacy compatibility may retire in a later major release only after known users
migrate, references resolve, rollback tests pass and a deprecation is announced.

## Separate layout changes and interruption repair

After namespace migration, explicitly initialize a profile before plan-layout.
apply-layout changes selection only and saves the prior profile/index/aliases;
it does not move or overwrite manual bodies. rollback-layout restores the
profile and rebuilds navigation from retained events, keeping post-switch revisions.
An unfinished layout intent blocks new writes until it is resumed or rolled back.

For an unterminated event tail, plan-event-repair is read-only. repair-events
requires plan-bound authorization, preserves the complete damaged log and writes
a durable intent before truncating only the diagnosed tail. Retry finishes its
receipt; complete corrupt events require manual review. New publications stop
while the repair is unfinished. Orphan staged directories are diagnosed rather
than accepted as committed content.

Formal execution snapshots include frozen argument arrays; declare execution-local
output_argument_indices so retries change only output locators, not input/checkpoint
paths. The governed queue rejects parameter drift. Historical compat snapshots
without frozen arguments remain readable; their recorded command is not a claim
that the arguments were frozen before launch.

The governance management interpreter needs Python 3.10+ and
requirements-governance.txt. The training interpreter is separate and is not
modified to install registry dependencies. This MVP is validated on local POSIX
filesystems. Mutations probe actual lock exclusion before committing state;
virtual mounts that merely accept flock without excluding another writer are
rejected. Read-only inventory and dry-run do not create probe files. Windows and network/distributed lock semantics require their own
platform acceptance before formal use; no cross-filesystem atomicity is assumed.
