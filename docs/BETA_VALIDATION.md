# Release validation scope

> This document records the 1.0 release and earlier beta evaluations. For 1.2.0, use [upgrade acceptance](UPGRADE_VALIDATION_CN.md) and the current [release-validation.json](../release-validation.json). Historical results below are not new-version executions.


Release source: **1.0.0**, promoted from the locally validated beta.5 source.
The skill instructions and runtime helpers are unchanged by this promotion;
version metadata, public release documents, and the publication workflow are
updated. The release workflow publishes stable assets only after the complete
Linux and macOS suites pass. The implementation and behavior evidence below
records the beta.5 checks, including their incomplete cases; it is not relabeled
as a new 1.0.0 behavior campaign.

Implementation commit:
`ab30307a9c0b34aa191cdc5af0e8925321561f63`. Preservation remains fixed to
`b9c7861fd22cd2f5471765d583c593f083fa12cc` (beta.3); original upstream:
`3b19a22dc5a64c983d2eafd6c2c94000fadc4f8d`. The current two-case comparison
uses beta.4 commit `a807775afdc26666c82d67c43d43f75e95daa7c4`.
The later end-of-training and comparison-archiving implementation is pinned to
`ab6ed6d285054ed0026fba678d794d71535d6725`.

## Stable-release checks

Version consistency, preservation, inventory, release paragraph formatting, and
47 documentation link targets pass. Two offline tests execute the actual
publication command with a local stub: stable versions select Latest,
prereleases keep their prerelease flag, and neither uploads stale archives.

The 1.0.0 Linux sandbox run records **841 passed, 20 skipped, 9 failed**.
Three existing installer checks cannot preserve file ownership in that sandbox;
six browser/manual-review checks cannot open loopback sockets. All nine pass
when those required permissions are available, in 48.23 seconds, with unchanged
code, API credentials removed, and GPU visibility disabled. Both the failed
attempt and follow-up are retained. These separate local executions are not
described as a single successful full-suite run. The exact release still must
pass the full Linux and macOS suites in the publication workflow.

## Code and preservation

- Linux full regression after lifecycle changes: **848 passed, 20 skipped**,
  Python 3.12.14, 226.26 seconds wall time.
- All **83** retained Codex workflow bodies and non-description metadata, and
  **450** frozen runtime/reference files, pass preservation. Inventory remains
  **84**; changes to 15 retained entrypoints stay within marked extension hooks.
- **54 checkpoint tests** cover 600 save events over a simulated 300,000-step
  schedule, complete-new-save peaks, failed writes/load validation/publication,
  corrupt-latest fallback, pins/roles, shard groups, interrupted deletion,
  cooperative locking, unregistered-file preservation, and concurrent inspection.
  They also exercise completed/stopped training cleanup, validated model exports,
  winner-only consolidation, dependency pins, relocation, ordered locks,
  interrupted retirement and corrupt-survivor refusal before retrying deletion.
- Real CPU continuation checks exercise standard-library SGD/momentum and a
  PyTorch model with Adam, scheduler, global RNG and data RNG. Restored state
  matches uninterrupted training in these witnesses; no GPU training is implied.
- Independent forward checks pass API/CLI scenarios and 200 publications with
  926 concurrent successful status reads. Nested-directory fsync is observed
  before manifest commit; this is not an actual power-loss certification.
- A further independent four-run CPU SGD comparison keeps the validation winner
  and a declared teacher model, preserves all 16 results/configuration files,
  and reduces fixture file use from 65,785 to 5,179 bytes. Actual process-kill,
  ENOSPC and failed-export checks pass. A discovered corrupt-survivor deletion
  retry was fixed: both finish and prune now reject further cleanup until the
  retained model is restored and reverified. No new failure was reproduced.
- Descriptions total **13,235** characters across 84 entries, maximum 172.
  Names, paths and other discovery context are excluded from this count.

The 20 skips are 12 Windows PowerShell checks, 4 credential-gated MiniMax live
checks, and 4 interactive checks requiring expect. The full suite removes API
credential environment variables and disables GPU visibility. It includes the
stronger Adam-state comparison and the final lifecycle code. Preservation and
inventory checks pass again. These are implementation-era results; stable-release
checks are recorded separately in [release-validation.json](../release-validation.json).

The [storage policy](../skills/skills-codex/shared-references/experiment-storage.md)
defaults to two valid full recovery generations during active/paused training,
one validation-selected best model, required final outputs and dependency pins.
After completed or explicitly ended training, validated inference exports allow
unused recovery states to be released. Finished comparable groups prefer only
the validation winner's weights, preserving future dependencies and all evidence;
unresolved retention choices go to the user. Completed runs and new-save staging
count toward capacity. The optional local helper needs
project-specific writer and loader validation; it cannot serialize models or
provide distributed/object-store transactions. Monitoring alone does not
authorize cleanup. Existing training programs must implement the configuration.

## Scoped behavior checks

**All 13 selected original cases pass.** This iteration selects cases from the
[unchanged original 24](../tests/behavior/evo-inquiry-cases.json); it does not
claim a fresh full 24-case matrix. The previous beta.4 matrix had 22 PASS and
2 INCONCLUSIVE (04, 13). Those are historical results, not new beta.5 results.

Fresh Codex CLI **0.162.1**, **gpt-6.1-sol**, reasoning **max**; 600 seconds
and 32 actions per case. Sessions receive requests and synthetic fixtures, not
the judging rubric. Installed skill, shared-reference and helper bytes match
immutable selected sources. The [assessment protocol](SKILL_BEHAVIOR_EVAL.md)
requires actual computations, meaningful artifacts, scope checks and final
handoff; process exit or a saved draft alone is not a pass.
These cases and the initial four storage cases assess the core changes through
`ab30307`, reusing earlier unaffected completed cases under the protocol; the
subsequent archive extension has separate deterministic,
independent forward and native CLI lifecycle checks. The reused cases do not
constitute new executions against every later instruction byte.

| Original case | Task | Assessed outcome |
| --- | --- | --- |
| 04 | Detailed experiment roadmap | PASS |
| 05 | Numerical analysis | PASS |
| 06 | Formal causal claim assessment | PASS |
| 09 | Valid workflow checkpoint resume | PASS |
| 10 | Evidence-linked next-step plan | PASS |
| 11 | Missing workflow artifact | PASS |
| 13 | Authorized analysis followed by plan | PASS |
| 14 | Exhausted budget and explicit stop | PASS |
| 15 | Title edit | PASS |
| 16 | Ordinary bug fix | PASS |
| 17 | Translation | PASS |
| 18 | Explicit analyze-results | PASS |
| 24 | Unavailable external reviewer | PASS |

The first fresh planning pair timed out on 04 for both beta.4 and candidate at
600 seconds. A concrete soft sizing guide and shared experiment tables reduced
the candidate plan from about 4,000 to 1,900 words; its corrected case 04
completed in 532.33 seconds with verification and a standalone tracker.
Analysis-to-plan selected the intended two skills and delivered the requested
files, but omitted its standalone tracker. That attempt is not counted as full
workflow completion; the preserved output requirement was clarified and case 13
then completed in 533.59 seconds with all three outputs verified. Earlier
completed 04/05/06 results remain applicable: 04
already includes the tracker, while 05/06 do not invoke experiment-plan.

Three zero-action CLI startup failures are retained; separate retries complete.
User
continuation interrupted two parent harnesses. Completed raw turns and artifacts
for 06/10 and S02 survived and were inspected; their process exit codes and
monotonic times were not recovered or inferred. The interrupted first S01 lacks
handoff and is not a pass. Remaining checks use persistent bounded harnesses.

## Separate storage behavior checks

[Four frozen additional cases](../tests/behavior/evo-inquiry-storage-cases.json)
test storage without modifying the original rubric or its 22/24 target.

| Storage case | Task | Assessed outcome |
| --- | --- | --- |
| S01 | Bounded CPU saves and actual interruption/resume | INCONCLUSIVE |
| S02 | Cumulative 12-run capacity and concurrent save peaks | PASS |
| S03 | Read-only diagnosis of corrupt latest recovery point | PASS |
| S04 | Block an infeasible launch before training starts | PASS |

S01 reaches 600.33 seconds after only preparation and a zero-step spine. Its
implementation notes do not establish code changes or recovery; this remains
INCONCLUSIVE despite the separate checkpoint helper and CPU tests passing.
S02 computes the unavoidable 144 GiB of full recovery states (154 GiB with
shared inputs) against 120 GiB. It includes wave/rolling save peaks, preserves
requirements and launches nothing. Reducing concurrency cannot fix cumulative
retention infeasibility.
The 144 GiB is specific to this synthetic fixture's explicit requirement to keep
two full 6 GiB states for all 12 completed runs, not the default archive policy.
S03 loads and hashes the actual files, excludes damaged step 2000 and identifies
step 1000 as the valid fallback, with 1,300 logged steps unprotected. It only
writes STATUS.md. S04 blocks a 16,384-byte budget that needs at least 24,576 bytes
for two retained states plus a complete new save; configuration stays unchanged
and the launch marker is absent.

Two additional [lifecycle cases](../tests/behavior/evo-inquiry-lifecycle-cases.json)
are frozen separately against `ab6ed6d`; both pass in native CLI sessions.

| Lifecycle case | Task | Assessed outcome |
| --- | --- | --- |
| L01 | Actual completed-training recovery cleanup | PASS |
| L02 | Validation winner archive and planned dependency protection | PASS |

L01 completes in 481.38 seconds and 11 actions: final JSON weights are loaded
and hash-checked, two full recovery states are actually removed (15,035 fixture
bytes), and the final weights, metrics/configuration, logs and unregistered
evidence remain unchanged. A generated verification receipt briefly loses
nanosecond timestamp precision; the session refuses cleanup at that check,
diagnoses it, and completes with same-process exact checks and hash preservation.
L02 completes in 405.10 seconds and 10 actions: beta's validation mean .86 wins
over gamma .83 and alpha .81; gamma's higher test score does not select it.
Beta and the planned alpha ablation model remain; gamma's 64-byte synthetic
model is actually removed, with a winner pin/receipt and all results preserved.

Original manifest SHA-256:
`a3967b120a2a9bfdc962ae74ae2cfbffdf6505e65a902a8d28b2b3181aeb9651`.
Storage manifest SHA-256:
`e72474cbcf4f15a58b1b37729e2f597ec78076e0d0db41a10ef5daec380aaf07`.
Lifecycle manifest SHA-256:
`765639412dc08b7bfa1cf6db629aeebca980ec917bb593e3fec34eb1ff3196c3`.
Original attempts, fixture/source hashes, raw traces and judgments stay private.
**Stable overall proactivity improvement is not established.**

## Packaging, installation and limits

The historical beta.5 lifecycle implementation archives contain 730 committed files, with matching
tar.gz/zip inventories and bytes. Extraction into a directory with spaces passes
preservation/shared-link checks and a terminal-fixture helper query. The helper,
policies and all synthetic fixtures are present; private validation is excluded.
Public validation reports record these completed results. Release archives are
built from committed reports and source; their separate release
manifest records the exact source commit and checksums.

The official beta.5 Codex installation passes ordinary skill discovery without
variant overrides: all 84 entries appear once, and all 730 public source files,
shared references and the helper match the project. Temporary evaluation plugins
and marketplaces are removed, and model/provider/reasoning settings are unchanged.
Codex CLI 0.162.1 copies local source directories into its cache, including
untracked files. Installation therefore uses a clean public source directory at
`dist/installed-source/evo-inquiry-1.0.0-beta.5`, excluding private validation,
build archives and Git history; keep this marketplace source available.

[release-validation.json](../release-validation.json) records actual status.
The stable publication workflow checks the exact tag/version, preservation,
inventory and release-note formatting, then runs the full Linux/macOS suites.
Only successful suites allow publication, and only that version's archives,
checksums and manifest are uploaded. Stable versions become the latest release;
version suffixes retain prerelease status. Local Linux checks
do not establish macOS or Windows support. GPU/distributed training, object-store
recovery, live providers, complete research pipelines and broad discipline
coverage are unverified. This inherited toolkit primarily targets ML/AI and
related engineering research. Synthetic checks cannot establish general research
correctness, stable model behavior or better research outcomes.
