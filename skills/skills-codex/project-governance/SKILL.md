---
name: project-governance
description: "Initialize or audit research project identities, fixed evidence references and layouts, or plan and execute an authorized state migration to .ei. Use for project governance and reproducibility handoffs."
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md), or reuse
it if already loaded and unchanged. Preserve the user's scope, resource budgets,
review provenance and recovery contracts while completing authorized work.
<!-- EVO-INQUIRY:END -->

# Project Governance

Use [project-governance](../shared-references/project-governance.md) and
[output-versioning](../shared-references/output-versioning.md).

Identify the requested mode from the task; do not turn an audit into a migration.

- init: establish project_id and an explicit compat-v1/governed-v1 profile.
- audit: read-only inventory, artifact/reference integrity and unresolved writers.
- migrate: namespace dry-run first; apply only the authorized project/plan, with
  external writers stopped and source hashes rechecked; verify/resume/rollback.

Resolve the loaded plugin root containing tools/ from this SKILL.md location.
For a new formal deployment, inspect its filesystem with filesystem_doctor.py;
use --probe for the authorized directory before the first governance write.
Keep the project on persistent storage with verified local locks/rename/fsync.
A passing probe does not establish persistence or multi-host exclusion.
Use project_registry.py --root <project> init/audit/plan-migration/
apply-migration/rollback-migration, or plan-layout/apply-layout/rollback-layout
for a separately selected layout transition. The plan and approval files are structured
JSON evidence, not an interactive approval substitute. Preserve already granted
authorization; ask only for missing scope or a genuinely unapproved operation.

Use artifact_registry.py for fixed records, publication and recovery. An audit
should state the exact source/ref examined, diagnostics and remaining uncertainty.
Unverifiable legacy evidence remains legacy-unverified. Do not rearrange existing
manual files, change scientific verdicts or delete environments/checkpoints.

Deliver the requested profile, inventory, fixed refs, or migration plan/receipt
and actual checks. run_state.py and the existing queue continue their roles.
