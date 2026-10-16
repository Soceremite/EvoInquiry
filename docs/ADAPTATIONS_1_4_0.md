# Directed adaptations for 1.4.0

Implementation in progress, 2026-10-16. The frozen 83 original workflow records
and 450 original protected-file hashes remain intact. Schema 3 separately pins
adapted bodies and resources with rationale and test/review references. A digest
match proves recorded identity; it does not judge the adaptation's scientific
merit or certify behavioral correctness.

The source baseline is commit `6275c2946a724e170d364bbd030cdadc6fe9a191`.
The released 1.3.0 baseline is the peeled `v1.3.0` commit
`2dd900b8f08cee2e607f0bad003d45e7655b2fb2`; these have different bytes.
The original preservation baseline remains
`b9c7861fd22cd2f5471765d583c593f083fa12cc`. None is silently substituted.

| Adaptation | Reason and preserved boundary | Verification |
| --- | --- | --- |
| Review, plan, pilot, novelty, claims and writing instructions | Evidence-calibrated judgments, disconfirming outcomes, primary metric fidelity, bounded review and explicit unknowns; existing verdict enums, fresh-review obligations and receipts remain | Frozen O cases, J development cases, existing receipt tests; behavioral results tracked separately |
| Literature instructions and record tool | Question-dependent `sources: auto`, unchanged legacy `all`, explicit failed sources, reading levels and source-preserving identity normalization | `test_literature_records.py`; offline L cases; live canary status separately recorded |
| Brainstorming and decision manager | Two scoped entrypoints; use existing research artifacts and one decision authority, no second run coordinator | New R cases and `test_research_decisions.py` |
| `research_wiki.record_decision` | Cooperating-writer lock, stable IDs, immutable evidence refs, revisions and preserved interrupted history; existing wiki writers and state ownership remain | Actual subprocess concurrency, retry, failed commit and evidence-change tests |
| `run_state` and idea gate | Optional versioned phase contract adds framing to new v2 runs; old v1 records remain unchanged and cannot be migrated by restart | `test_workflow_contract_versions.py` plus all existing gate/state tests |
| Figure instructions and canonical renderer | Correct routing, explicit units and uncertainty, finite geometry validation; legacy renderer remains a forwarding shim | Deterministic SVG/legacy CLI and malformed geometry tests |
| Figure evidence helper | Existing `evidence_check` checks literal numbers but has no input/output/source identity receipt; small helper uses existing `fixed_ref`/`verify_ref`, no second renderer or statistical certification | `test_figure_evidence.py` and F behavior cases |
| Shared references distributed to mainline | Common principles, task scope and storage become reachable from new mainline entries without relying on the Codex tree | Inventory, relative-link and selective-install tests |
| Catalog, metadata, overlays and CI | Register two entries and package their resources; carry targeted base instruction changes into generated reviewer overlays; run new deterministic tests on Windows | Inventory, installer, generator and CI test suites |
| Mainline principles and actual path identity | Common hook reaches all 87 mainline entries; native traces expose noncanonical reads and discovery pins reachable mainline/overlay bytes | Historical hook receipts, relative-link checks and actual-cache drift tests; behavior assessed separately |
| Audit evidence levels | Separate supplied-record support, direct execution verification and independent review; missing evidence limits the affected conclusion without demonstrating method failure. Existing fresh-review requirements, verdict fields and acceptance gates remain | Independent HJ01 adjudication; preserved original failures and replacement holdout evaluation reported separately |
| Final overlay formatting | Remove duplicate blank separators and trailing blank line in Gemini `paper-plan`; update only its existing candidate digest, preserving original baseline maps and all instruction text | `git diff --check`, existing overlay/contract tests; dev.3 behavioral evidence remains pinned to its original snapshot |
| Optional original-baseline comparison | Normalize both historical and current namespaces and recognize original protected files only against their frozen digest; keep strict current-file checks and reject unregistered semantic changes | `test_evo_inquiry.py` namespace and mutation regressions; comparison with actual original preservation commit |
| Proactive case studies, user-requested supplement on 2026-10-16 | Add sample-level diagnosis to substantive `analyze-results` work and connect planning, bounded evidence instrumentation/collection, audit, figure and outline stages. Preserve aggregate interpretation, fair input pairing, evidence provenance, compact storage and narrow-request scope; no new skill entrypoint or inference permission | Required-resource removal and mirror/package regressions; frozen dev.4 native development attempts and their limits are recorded in the validation report |
| Bounded analysis followup | Condition governance/design-reference loading on the actual task, lead with the observed comparison and keep metrics, cases, selection and limits in one concise report. A small full-pool census needs no extra sample. Codex sessions use the exact discovered mirror and stop after the requested artifact; repeated service failures produce an incomplete infrastructure record rather than a scientific conclusion. Required evidence and review gates remain | Local package/mirror/harness tests cover the path and service-error controls. The earlier C01/C05 traces remain historical and behavior of the revised wording still needs a fresh authorized native run |

Followup review corrected primary-outcome fidelity in paper improvements,
read-only artifact access in generated Claude calls, and v2 framing completion.
The framing helper advances only mechanical framing; v1 runs and scientific
review gates remain unchanged. Rendering a stopped log grants no acceptance;
generated prose requires actual reviewer identity and existing evidence closure.

An independent same-family implementation review used `gpt-6.1-sol` in a fresh
context. Its first pass reported 92 relevant tests passing and four additional
reproductions: output/input path aliases bypassing figure overlap checks, Unicode
stdout under ASCII pipes, empty v2 framing artifacts, and unstable ordering of
possible title matches after re-export. Fixes and regression cases were added.
This is an implementation review, not independent scientific acceptance. Further
source/behavior reviews and actual validation outcomes belong in
[the validation report](VALIDATION_1_4_0.md).
