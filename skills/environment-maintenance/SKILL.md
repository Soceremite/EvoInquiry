---
name: environment-maintenance
description: "Inspect or maintain research environments through independent candidates, validation receipts, frozen revisions and consumer/lease/pin protection. Use for dependency changes, environment reuse and retirement planning."
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
<!-- EVO-INQUIRY:END -->


# Environment Maintenance

Read [environment-stewardship](../shared-references/environment-stewardship.md)
and the relevant [code-reuse-and-docs](../shared-references/code-reuse-and-docs.md)
constraints for consumer interfaces.

Use the task to select inspect, plan-change, validate, bind or retire-plan.
Resolve the loaded plugin's tools/ directory and use environment_registry.py.

Inspect actual interpreter/imports, dependencies, recipe/lock/build identity,
platform/device needs, consumers and existing authorization. Choose unchanged
frozen reuse when real checks establish compatibility. For changes, propose a
complete diff and use existing conda/uv tools in an independent candidate.
Do not install into an active formal environment.

Validate metadata, imports/ABI/device, small numerical behavior and representative
consumers; save actual command, output digest and exit receipts. CPU-only tests
do not certify a GPU environment. Promote only within the approved candidate/
consumer scope. Bind selected future tasks; queued/running bindings stay fixed.

Register leases for active work and pins for historical reproduction. Reconcile
expired heartbeats with actual scheduler/process evidence. Unknown consumers,
missing coverage, active leases or pins prevent retirement. retire-plan is
deletion-free; any later deletion uses applicable user authorization and the
existing retention policy. Explicit selected-pin release uses plan-pin-release/
release-pins; record an approved intent and recover it without losing history.

Deliver observed compatibility/diff, real receipts, selected bindings and
unresolved checks. Do not fabricate solver output, hide a failed candidate or
replace an existing coordinator.
