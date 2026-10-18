# EvoInquiry 1.5.0 candidate validation

Development started on 2026-10-18 from `180f7d8ebd6690caa3a77328e9cb2bf5eeeee7ce`
on `feat/bounded-research-v1.5.0`, under the
[approved implementation plan](UPGRADE_PLAN_1_5_0_CN.md). Stable release metadata
and the formal local installation remain 1.4.0. This document is not release
acceptance, a scientific verdict, or evidence of general autonomous research.

## Directed adaptations

The 83 original workflow records and 450 protected-resource baseline hashes remain
frozen. New exact digests identify the targeted adaptations separately. They cover
bounded research actions in existing run-state metadata, explicit Codex export
logging, read-only reuse of original decisions, and paired candidate assessment.
No extra skill entrypoint or parallel phase scheduler is introduced.

Guide, brainstorming, manager, experiment planning, analysis and research pipeline
instructions connect these optional capabilities within the requested scope.
Review-loop gates remain. Codex meta-optimize's obsolete self-apply path is removed
and its incorrect claim of no Codex evaluation path is corrected to the existing
native behavior harness. Meta-apply retains human selection, fresh landing review,
provisional/accepted distinction, backups and provenance requirements.

Plan and Goal are optional host capabilities, not automatic workflow activation.
The Plan/Goal references were checked against official OpenAI documentation.
No native Goal was created by this implementation request.

## Observed checks so far

- First control/events/run-state check: 46 passed, one failed. The failure showed
  that a zero GPU allowance incorrectly blocked CPU-only actions. The corrected
  controller checks each proposed resource reservation and reports exhausted
  units separately from a real overrun.
- Focused new components, run-state and harness check after that correction:
  99 passed. Later focused components and actual CPU-study integration: 84 passed.
  These overlapping runs are not additive coverage counts.
- Export telemetry now reports `skill_reference` candidates rather than claiming
  verified invocation from shell text. Previous completed turns cannot complete
  new unfinished work; changed/truncated imported sources are rejected.
- Three actual synthetic CPU-study integrations recompute held-out metrics from
  paired prediction rows, preserve original hypotheses, save cases and decisions,
  and stop at the original review-required gate. They are deterministic software
  exercises, not LLM behavior or scientific acceptance.

## Final local assessment — 2026-10-18

The implementation is available as a development candidate. Package verification
and inventory pass: 88 Codex skills, all 83 original workflow records and 450
protected-resource baselines retained. No stable version tag, release publication
or formal installation replacement was performed.

| Check | Observed result and scope |
| --- | --- |
| Complete Linux regression | 1,212 passed, 38 skipped, three warnings and 46 passing subtests in 504.96 seconds. This invocation began before the final accounting/input-identity refinements; the final focused run below covers those later changes. Counts are not additive. |
| Final changed components | 93 passed in 22.06 seconds. Covers corrupted accounting rejection, cooperating-process deduplication, native shell-wrapped events, explicit export idempotence, decision retrieval, fixed request/fixture pairing, real CPU studies and the original execution-registry snapshot/terminal receipt. |
| Overlay and packaging | 76 passed and 26 passing subtests after regenerating the changed Claude-review overlay. The original missing-adaptation and stale-overlay failures remain in local receipts. |
| Independent forward use | One fresh gpt-6.1-sol/high agent completed a synthetic queueing handoff using only the task and candidate skill/context, without expected results. It preserved average improvement and long-class regression, selected a discriminating next inquiry and created no Goal, experiment or runtime state. Parent assessment: PASS with a source-scope qualification. The agent also read the locally installed openai-docs skill as required by host guidance; no online material was used. |
| Native candidate discovery | All 88 installed entrypoints and reachable support bytes matched the frozen `1.5.0-dev.1` snapshot. CLI 0.163.0, gpt-6.1-sol/high, sequential sessions, request-only protocol, 180 seconds and 24 tool actions per case. |
| Six native public development tasks | Six completed and were assessed PASS against their individual rubrics after inspecting traces, file changes and artifacts. One attempt per case; no automatic retries. See the table below. |
| Actual native-export import | A selected N02 trace yielded 22 normalized observations, two skill-reference candidates, zero invocation assertions; reimport added zero records. One completed turn remains distinct from complete research/workflow acceptance. |
| Test-install cleanup | Candidate plugin and marketplace removed after the tests. The stable 1.4.0 cache remains present and its selector remains enabled. |

| Case | Focus | Seconds | Tool actions | Artifact / outcome |
| --- | --- | ---: | ---: | --- |
| N01 | Vague direction and Plan-only scope | 103.46 | 9 | PLAN.md only; competing predictions, synthetic-data limits and no Goal/experiment/state initialization |
| N02 | Prior decisions and challenge to an unsupported claim | 92.93 | 10 | NEXT.md only; quality loss and latency gain retained, old revisit condition checked, no optimistic retraining claim |
| N03 | Interrupted dispatch | 142.54 | 13 | RECOVERY.md only; unresolved reservation preserved, remote execution unknown, expired wall budget and original phase retained |
| N04 | Small numerical request | 36.29 | 4 | Correct 16.67 percentage-point answer; no file changes or workflow expansion |
| N05 | Self-optimization with insufficient data | 89.31 | 7 | REPORT.md only; one synthetic trace, failed tool and reference/compliance distinction preserved; no patch or landing |
| N06 | Goal consultation | 44.85 | 4 | Concise advice; no Goal activation, mode-switch assertion or new state |

These are candidate-only public development tasks with same-family artifact
assessment. They do not establish improvement over the released baseline, sealed
held-out generalization, autonomous selection of the three CPU-study routes, or
complete RSI. The later final helper refinements were verified by the focused
tests, not silently attributed to the earlier native snapshot.

The first full regression was interrupted after failures identified a missing
`.gitignore` adaptation and stale derived overlay; its log remains. The fixture
exception now names only one public synthetic recovery record, keeping other
runtime state ignored. The derived overlay was regenerated with its existing
description and reviewer interface preserved; its byte-level generator check passes.

New native macOS and Windows jobs have not run for this development branch.
The 38 Linux skips include platform-only checks, unavailable optional Python
dependencies and unconfigured live API tests; they do not show absence of GPUs.
Live paired baseline/held-out evaluation is still needed before any claim of
general improvement or release acceptance based on that claim.

Raw local receipts stay under ignored `validation/upgrade-1.5.0/` or the test
temporary directories. Failures and earlier attempts are retained. Neither
`CANDIDATE_SIGNAL`, source checks nor reviewer identity fields establish reviewer
independence, statistical significance or authorization to land a toolkit patch.

## Publication preparation

The continuation preflight passed 86 tests covering the original run state, all
five new research modules and release workflow arguments. Both development and
publication CI now run these portable modules under `powershell.exe` and `pwsh`;
the release coverage regression also requires their inclusion. Package
preservation and diff whitespace checks pass. The unreleased changelog describes
new capabilities, fixes and changed behavior separately from the stable notes.

The candidate is prepared for the existing `acceptance/**` branch CI. Native
platform results will be recorded against its actual commit; changing the CI
configuration alone does not count as a successful platform run. Stable version
metadata and the formal installed plugin remain 1.4.0.
