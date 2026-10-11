# Beta validation scope

Candidate: **1.0.0-beta.4**, not published. Preservation baseline:
`b9c7861fd22cd2f5471765d583c593f083fa12cc` (beta.3). Original upstream snapshot:
`3b19a22dc5a64c983d2eafd6c2c94000fadc4f8d`.

## Checked locally

- Linux regression suite: **792 passed, 20 skipped**, Python 3.12.14.
- All 83 retained Codex workflow bodies and non-description frontmatter match
  the frozen beta.3 contract after removing the marked EvoInquiry hook.
- 450 protected baseline files, including runtime helpers, reviewer overlays,
  original skills and recovery references, match the fixed source commit.
- The registered research-guide extension brings the Codex inventory to 84;
  its metadata and shared-reference links pass validation.
- Description text totals 13,229 characters across 84 entries, compared with
  23,910 across the 83 baseline entries. This omits names and paths and does not
  prove that every environment will display the full discovery catalog.
- The publication policy still excludes the 193 previously retired files and
  requires all 13 workflow reference documents.
- Fresh Codex CLI 0.162.1 discovery distinguishes isolated baseline and candidate
  caches, with 83 and 84 enabled entries respectively. Installed skill bytes
  match their selected source snapshots.
- A source copy relocated into a directory with spaces passes preservation and
  shared-reference checks. Installing the pinned beta.3 then restoring beta.4
  discovers 83 then 84 source-matching entries without changing model settings.

The 20 skips comprise 12 Windows PowerShell checks, 4 credential-gated MiniMax
live checks, and 4 interactive installer/picker checks requiring `expect`.
The local full suite removes API credential environment variables and permits
only the loopback servers required by its tests.

## Behavior comparison

The [24 frozen cases](../tests/behavior/evo-inquiry-cases.json) use 12 Chinese
and 12 English natural requests and synthetic project fixtures. See the
[execution and assessment protocol](SKILL_BEHAVIOR_EVAL.md).

Status: **complete with limits**. Candidate **22/24 PASS**, **2 INCONCLUSIVE**;
baseline **23/24 PASS**, **1 INCONCLUSIVE**. No critical evidence, scope or gate
errors were observed in inspected traces and artifacts. The minimum 22-case
target is met; explicit skill calls (18, 20), checkpoint resumption (09, 11, 14)
and small tasks (15–17) pass. Authorized analysis-to-plan case 13 remains
inconclusive and limits continuation under this time budget.

Codex CLI **0.162.1**, **gpt-6.1-sol**, reasoning **max**; identical requests,
fixtures, model settings, workspace policy and 32-action limits. Final cases use
a 600-second ceiling except the unchanged case-05 smoke pair, which uses 300
seconds for both variants. The frozen manifest SHA-256 is
`a3967b120a2a9bfdc962ae74ae2cfbffdf6505e65a902a8d28b2b3181aeb9651`. Sessions received no judging rubric.

| Case | Task | beta.3 | Candidate |
| --- | --- | --- | --- |
| 01 | Related work | PASS | PASS |
| 02 | Supplied paper | PASS | PASS |
| 03 | Method refinement | PASS | PASS |
| 04 | Detailed experiment roadmap | PASS | INCONCLUSIVE |
| 05 | Numerical analysis | PASS | PASS |
| 06 | Causal claim support | PASS | PASS |
| 07 | Paper number audit | PASS | PASS |
| 08 | Proof gap | PASS | PASS |
| 09 | Valid checkpoint resume | PASS | PASS |
| 10 | Next-step plan | PASS | PASS |
| 11 | Missing checkpoint artifact | PASS | PASS |
| 12 | Negative-result reassessment | PASS | PASS |
| 13 | Authorized analysis then plan | PASS | INCONCLUSIVE |
| 14 | Exhausted budget / stop | PASS | PASS |
| 15 | Title edit | PASS | PASS |
| 16 | Ordinary bug fix | PASS | PASS |
| 17 | Translation | PASS | PASS |
| 18 | Explicit analyze-results | PASS | PASS |
| 19 | Advice only | PASS | PASS |
| 20 | Explicit pipeline: initial scope | PASS | PASS |
| 21 | Unavailable search backend | PASS | PASS |
| 22 | CPU preparation / future GPU | INCONCLUSIVE | PASS |
| 23 | Missing raw results | PASS | PASS |
| 24 | Unavailable external reviewer | PASS | PASS |

Cases 04 and 13 save substantial planning drafts but reach the time limit before
final verification or handoff; case 13 also leaves referenced workflow records
unfinished. They are not passes. Baseline CPU preparation case 22 likewise times
out, while the candidate finishes close to its deadline. Twenty-one paired
outcomes are unchanged; two candidate outcomes are inconclusive where baseline
completes, and one candidate completes where baseline is inconclusive.
**Stable overall proactivity improvement is not established.**

The first full matrix had 22 baseline and 21 candidate passes. A demonstrated
recovery-boundary correction was retested in all six guide cases. It finishes the
missing-artifact diagnosis while preserving the original state. Narrowing the
result-to-claim discovery cue was retested in cases 06, 10, 12, 13 and 19. Formal
claim assessment still works; case 10 selects guide plus experiment-plan. Case
13 still selects extra claim assessment and times out: this overlap is not
claimed solved. Only affected, unstable or runtime-failed cases were retried;
original attempts remain in local ignored storage.

Initialization failures, model-stream concurrency retries and a storage-related
batch interruption are recorded separately. Lost temporary records were repeated
rather than counted. Immutable source snapshots were deduplicated without byte
changes to restore writes. These conditions and retries prevent latency or
statistical efficacy claims. Median recorded tool actions were 8.5 for baseline
and 9 for candidate; this describes reading/execution overhead, not token cost.

Judgments use actual skill reads, calculations, requested artifacts and scope
boundaries. Adequate alternative paths are allowed; baseline case 14 completes
its stop handoff directly without an EvoInquiry skill read. Unavailable reviewers
remain blocked or provisional, never accepted reviews. Raw traces, source/cache
hashes, judgments and incomplete attempts remain local.

## Release and limits

[release-validation.json](../release-validation.json) records the candidate's
machine-readable status. Raw local sessions remain in ignored validation storage
and are excluded from Git and source archives. Temporary storage lost during
runner recreation cannot support a pass; affected comparisons are repeated.

Linux and macOS full suites must pass in GitHub Actions before public publication;
local Linux results do not establish macOS or Windows support. The inherited
workflows primarily target ML, AI, and related engineering research. Live search
providers, GPUs, image renderers, complete research pipelines and broad discipline
coverage are not verified end to end. Case 20 stops at initial scoping. Same-family
review remains provisional. These small synthetic cases cannot establish research
correctness, stable model behavior, or better research outcomes.
