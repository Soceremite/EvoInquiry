# EvoInquiry 1.4.0 validation

## Current release assessment — 2026-10-17

The implementation is prepared for the 1.4.0 publication gate. Current source
`40ff2c20c059ed639180e9c903233f70b20c54eb` passed **1,150 local tests, with
38 skips**, and [all four native platform CI jobs](https://github.com/Soceremite/EvoInquiry/actions/runs/38991160599).
Release documentation, version metadata and the Windows publication-coverage
correction are later changes; the final tag must pass its own CI before archives
are published. Publication and formal installed-version replacement are separate
operations, not inferred from these candidate results.

| Area | Current evidence and qualification |
| --- | --- |
| Package | 88 Codex and 87 mainline skills; 83 original workflow and 450 protected-resource baseline records retained, with directed adaptations pinned separately. |
| Objective analysis | Public comparison and challenge cases reviewed; local audit calibration repaired prospectively. J05 has explicit case-specific user acceptance, while its original timeout remains. |
| Case studies | Candidate and released-1.3.0 baseline outputs reviewed against the eight public cases; content completion is separate from actual media-viewing provenance. No general superiority is claimed. |
| Storage and governance | Fixed supplied-resource planning, actual bounded CPU restoration and terminal cleanup, plus successful local-filesystem initialization and a declared positive-precondition comparison cleanup. Original prerequisite failures remain. |
| Held-out routing | One prospectively registered current-candidate isolation verification completed in 62.60 seconds with six actions at unchanged limits; original failures remain and their cause is unknown. Private inputs and rubrics remain withheld. |
| Platform and publication | Ubuntu/macOS full CI and both native Windows shells pass at the fixed implementation source. A new regression reproduces the release workflow's omitted Windows modules, then passes after repair. Exact-tag publication CI is still required. |

The [approved plan](UPGRADE_PLAN_1_4_0_CN.md) defines the criteria. Reviews here
are same-family/provisional engineering assessments, not scientific acceptance
or a guarantee of reliable behavior on every request. Appropriate unavailable
scientific-review blockers remain blockers even when a software task's required
preparation and truthful status are complete. Earlier failures, runtime surface
deviations and superseded open assessments below are historical evidence; use
the dated closure section at the end for the current disposition.

The user added proactive case studies on 2026-10-16 after the dev.3 behavior
snapshot and the first successful native platform CI. Those older results
remain attributed to their exact candidates; they do not validate the new
sample-level behavior. The supplement and its validation are recorded below.

## Baselines and identity

- Released 1.3.0: peeled v1.3.0 commit `2dd900b8f08cee2e607f0bad003d45e7655b2fb2`.
- Source before upgrade: `6275c2946a724e170d364bbd030cdadc6fe9a191`, also
  labeled 1.3.0, with different bytes and later unpublished changes.
- Initial hashes, source snapshots and raw evidence are retained under ignored
  `validation/upgrade-1.4.0/`; they are not release files.
- Development plugins use separate marketplace IDs. Each batch records actual
  host discovery and support hashes. Initial batches used CLI 0.162.1; the later
  closure batches pin CLI 0.163.0. Model: gpt-6.1-sol;
  reasoning: high; configured provider label: OpenAI. This label does not
  authenticate the external endpoint. The formal installation remains separate.

## Deterministic checks and independent source review

The first four-module run returned **49 passed, 2 failed**. Expectations were
corrected against existing semantics: done-but-unaccepted old phases remain
resume targets, and literal number checks retain conservative matching and the
existing `verified` status. Original failing XML is preserved.

A fresh same-family implementation reviewer reported **92 passed** and reproduced
four additional edge cases. Fixes cover canonical-path overlap, Unicode output,
empty v2 framing artifacts and stable literature candidate ordering. This is
implementation review, not independent scientific acceptance.

The full Linux suite subsequently returned **1,132 passed, 37 skipped**, three
warnings, in 586.49 seconds (`full-tests-v2.xml`). After overlay/framing and
hook/path followups (**106** and **110** passing focused tests), the frozen dev.2
full run returned **1,141 passed, 37 skipped**, three warnings, in 554.13 seconds
(`full-tests-final.xml`). A fresh implementation review also returned **62 passed**.
These runs predate the audit wording clarification. Its affected contract,
package, overlay and harness checks returned **79 passed** in 22.73 seconds;
package verification still passes with all original baselines retained. Earlier failed
runs are retained. Sandbox ownership-preservation and socket restrictions were
separately rechecked in the actual execution environment: **32 passed**. No
installer behavior was weakened to hide them. Fresh temporary directories avoid
cleanup noise from differently owned earlier artifacts. These Linux checks do
not establish native macOS or Windows success.

The later installation, portability, guidance, comparison, checkpoint,
literature, decisions, workflow-contract and figure-evidence regression returned
**272 passed, 29 skipped** in 57.27 seconds. Native Windows/PowerShell and NTFS
checks remain skipped on Linux; the default interpreter lacks usable PyTorch,
while the separate actual CPU checks below passed in the existing environment.
Final overlay formatting and preservation checks returned **33 passed** in
4.77 seconds. Inventory, package verification and `git diff --check` pass.

The optional original-baseline comparator subsequently exposed false mismatches
for the recorded `.aris` to `.ei` namespace migration. Both sides now use the
same normalization, and an original protected file is recognized only when its
raw or normalized digest matches the frozen historical contract. Current files
still pass the existing strict contract check; unknown original/current changes
remain rejected. Focused preservation and package tests returned **57 passed**
in 17.02 seconds. Verification against the actual original preservation commit
`b9c7861fd22cd2f5471765d583c593f083fa12cc` passes. Earlier failed checks and a
fixture-setup failure are retained rather than replaced by these results.

An earlier full Linux sandbox run on 2026-10-16 returned **1,136 passed,
9 failed, 37 skipped**, three warnings, in 607.32 seconds
(`full-tests-local-final-v2.xml`). Three local-copy tests hit the sandbox's
ownership-preservation restriction; a separate diagnostic also exposed its
read-only user directory. Six manual-review HTTP/cancellation tests could not
create local sockets. Separate host-permission rechecks of the unchanged tests
returned **3 passed** in 13.96 seconds and **6 passed** in 22.19 seconds. The
optional global repository pointer was restored. These rechecks make no model
calls; the HTTP tests use only loopback and fixed synthetic responses. No product
code or assertions were changed to hide the failures.

All **1,145 non-skipped cases** therefore have observed passing results across
the full run and those targeted rechecks. This is not a single green full run;
the original failures remain in the XML and machine-readable summary. An earlier
attempt left only a partial log and no terminal result, so it is not counted as
passed. Skips cover native Windows/PowerShell/NTFS cases, unavailable `expect`,
live MiniMax tests without credentials and the default interpreter's PyTorch
limitations. They are not advertised as passed integrations or platforms.

The actual CPU checkpoint restoration test passed using an existing Python 3.12
PyTorch environment. The governed training acceptance test also passed in 230.47
seconds, checking multi-seed execution, an interrupted/resumed run against its
continuous control, full training-state identity and bounded checkpoint storage.
The test driver used its existing schema dependencies and selected the unchanged
PyTorch interpreter via `EI_PILOT_TRAINING_PYTHON`; no environment was installed
or modified. An earlier attempt using that interpreter as the driver failed for
missing jsonschema. Two escalation approval checks timed out before launch;
the successful test ran inside the ordinary sandbox. These are engineering
checks, not evidence of scientific superiority or native GPU success.

Followup review corrected three concrete issues: primary outcomes could be
hidden by secondary wins in paper improvements; two generated Claude calls
lacked file-read access; completed v2 framing remained the resume target.
Framing completion now binds a nonempty artifact and advances only framing;
scientific phases retain existing review gates. Rendering and generated review
prose grant no automatic acceptance on budget stops, missing reviewers or
unverified identities.

Packaging currently passes with **88 Codex entrypoints and 83 original retained
workflow records**. Original frozen hashes remain intact; adaptations are
separately pinned. All 87 mainline entries now expose common principles.
Historical before/after receipts prove that hook insertion itself preserves
workflow bodies and frontmatter; later description/rendering edits are separate.

### Native platform CI

On 2026-10-16, [the candidate test-suite run](https://github.com/Soceremite/EvoInquiry/actions/runs/38835451265)
completed successfully at commit
`c2e9f6034286333161425d7d89d90f5c1715fa84` on the separate branch
`ci/evo-inquiry-v140-validation-20261016T012646Z`:

- Ubuntu: full `tests/` pytest suite passed.
- macOS: full `tests/` pytest suite passed.
- Windows `pwsh`: the focused installation, governance, portability, comparison,
  checkpoint and new literature/decision/workflow/figure tests passed.
- Windows `powershell.exe`: the same focused gate passed.

The CI checkout contains the 926 reviewed public files. Its only difference
from the implementation-review-v2 source snapshot is a workflow trigger for
that exact CI branch; no original preservation map or runtime code changed.
Private validation material, credentials and replacement holdouts were not
published. The user worktree and formal installation were not switched to this
branch. Source identities, the push receipt and actual run/job statuses are
retained locally. The main branch and release tags were not updated.

These successful native program checks complete the platform gate for the
specified candidate. They do not execute or certify the outstanding model
behavior matrix. Later validation-document changes record these outcomes;
the CI result remains attributed to the exact commit above.

### Proactive case-study supplement

The user-requested supplement extends the existing `analyze-results` workflow
and connects planning, bounded evaluation evidence collection, audit, figures
and outlines. It adds no skill entrypoint, new run registry, renderer or inference
service. Both execution-skill bodies remain unchanged outside their guidance
hooks; the analysis/plan/audit/figure/outline adaptations are separately pinned.
The original 83 workflow and 450 protected-file baseline maps remain intact.

Eight new C development cases contain classification predictions, regression
residuals, synthetic image outputs, timestamped synthetic frames, aggregate-only
results, a narrow numerical request, a cherry-picked panel claim, and incomplete
paired outputs under a tight storage budget. The 60 fixture files occupy
22,964 bytes; prompts and grading criteria are separate from project inputs.
An offline audit recomputed classification and regression values, checked
pairing/missing coverage, decoded PNG checksums and verified the toy image/frame
annotations. These are material-consistency checks, not model-behavior passes.

The first seven-module focused run returned **118 passed, 1 skipped** in
29.45 seconds. The skip is the interactive installer menu test because `expect`
is unavailable, not a case-study behavior pass. Package verification
against the original preservation baseline, inventory checks and skill-creator
validation of `analyze-results` passed. After the execution collection-hook
and figure-description edits, the final affected recheck returned **118 passed,
1 skipped** in 29.30 seconds, with the same `expect` limitation. Final package,
inventory, both changed discovery descriptions and fixture checks pass.

The user then authorized a bounded candidate-only batch against the configured
endpoint and synthetic/public payload. The frozen dev.4 snapshot SHA-256 is
`ec53fda9f41d8a3cc9ccdf33e8587db4d843d2fb296abb75e2beee13b9e0ca4b`.
Native discovery verified 88 Codex entrypoints and 250 reachable support
resources. The first three development cases used `gpt-6.1-sol`, high reasoning,
one job, a 300-second ceiling and 32 tool actions, with no case retries:

| Case | Artifact and scientific content | Execution and routing |
| --- | --- | --- |
| C01 classification | Report preserves 6/12 to 8/12, four improvements, two regressions, shared failures and bird 1/2 to 0/2. It uses a traceable 12-row census and invents no media inspection | Report saved near 292 seconds, but no completed turn before the 300.26-second stop; canonical Codex entrypoint and common-principles read observed |
| C05 aggregate-only | Inputs and descriptive statistics were inspected, but no report or final answer was produced | 300.45-second stop with two client reconnect messages reporting server overload; noncanonical mainline entrypoint observed |
| C06 narrow arithmetic | Correct concise answer: `16.7个百分点`; no unsolicited case report or file output | Completed in 96.93 seconds; noncanonical mainline entrypoint and no common-principles read observed |

The implementing agent manually checked these traces and artifacts; this is not
independent review. No input file changed and no source evidence was deleted.
The two reconnects are recorded separately from case retries. Overload was
observed during C05 but does not establish the cause of every delay. Correct
content and a correct number do not erase timing or guidance deviations. No
complete behavior pass is claimed. At the end of that dev.4 batch,
C02/C03/C04/C07/C08 remained unstarted because the initial gate had unresolved
issues; no timeout extension or automatic retry was used in that batch. Later
dev.5 attempts are recorded separately below.

The classification report repeats several findings. Local source guidance now
makes reference loading conditional on the task, leads with the observed
comparison and keeps metrics, cases, selection and limits in one concise report.
A small full-pool census needs no extra sample. The followup also makes the
Codex mirror path explicit and teaches the harness to stop after repeated
overload/reconnect/stream errors while retaining the raw trace as an incomplete
infrastructure result. These changes are absent from frozen dev.4, so earlier
outputs do not validate them. The affected package, mirror, preservation and
harness checks rerun after the edits with **75 passed** in 24.17 seconds;
original workflow-body digests and the 83/450 baseline maps remain intact.
Native adherence and revised-wording timing still require a fresh authorized
run, and the final candidate still requires release-stage program CI.

After the stop, the temporary dev.4 marketplace and cache were removed. The
formal 1.3.0 installation remains enabled, all 814 files match its preserved
source snapshot, and the Codex configuration SHA-256 remains
`f52854f9e5cc655b5c0dc3586550f4a50c410ba2452d971248aca08b6964e064`. The
cleanup receipt is `validation/upgrade-1.4.0/case-study-formal-installation-after.json`.

The previously frozen dev.3 traces and 116-session payload inventory remain
historical. They cannot be relabeled as coverage of this changed candidate.
The authorized candidate-only batch does not replace the paired matrix, affected
reruns or fresh holdout requirements. Those identities and budgets must be fixed
for the revised candidate. Authorization for these eight development cases does
not extend to the historical remaining 116-session inventory or establish
release acceptance.

## External sources and live canaries

[The source audit](UPSTREAM_ADOPTION_1_4_0.json) fixes commits, licenses, file
hashes and adoption choices. External code was not executed or installed. Two
files remained unavailable after three retrieval attempts. The optional
nature-academic-search adapter stays disabled and unvalidated. The noncommercial
academic suite is reference-only, neither copied nor bundled. Complete external
skill collections do not enter the distribution.

Live canaries on 2026-10-15 used existing helpers, one invocation per source,
a 60-second outer ceiling and bounded helper retries:

- arXiv returned 1706.03762 and abstract metadata in 1.90 seconds.
- OpenAlex completed in 2.94 seconds but returned another DOI and a 2025 date
  for a title match. This identity conflict is not a verified replacement for
  the 2017 arXiv paper. HTTP success does not establish citation identity.
- Semantic Scholar returned HTTP 429 after 8.88 seconds; coverage is incomplete.

Raw output and assessment are retained in `source-canaries/`. Other optional
sources and image services have not been validated end to end.

## Native behavioral evaluation

Eight original O cases remain unchanged. Twenty-four development cases are
written. Eight original independent holdouts were unsealed after the dev.2
source freeze. The first pair triggered a stop and an evidence-level
adjudication, detailed below. Eight replacement holdouts were independently
authored, sealed before the dev.3 freeze, and subsequently executed. Process
completion alone is not a passed case.

The paired smoke used O03/J01/J07/R01/L01/F03. The candidate produced six correct
required deliverables. Five first routes matched frozen sets. L01 loaded a
noncanonical mainline research-review path instead of a discovered Codex
literature entrypoint and did not read common principles. Content correctness
therefore does not establish native-guidance compliance. The common mainline
hook, clearer literature discovery and noncanonical-path recording address that
gap. The final smoke slot confirmed that common principles were read, but L01
still selected a noncanonical mainline research-review path rather than a
discovered literature entrypoint. Its correct content does not erase that route
mismatch. The final attempt took 362.27 seconds.

The baseline completed five first attempts correctly; J01 failed at CLI startup
with Resource temporarily unavailable (os error 11). A single recovery completed
correctly in 82.09 seconds. Independent same-family assessment found no critical
rubric errors in the 12 completed outputs. J07 was more proportionate in the
candidate (54 lines versus 148), with correctness a tie. This small development
sample does not establish general improvement.

Two initial 300-second baseline attempts timed out and remain recorded. The
paired diagnostic batch used an equal **900-second** ceiling on both variants.
Baseline J07 took 572.65 seconds and did not meet its original 300-second ceiling.
Candidate discovery also failed once before a model case; the old harness
discarded its stderr, so the cause is unknown. Later discovery stderr is retained.
All **16 model attempts** within the smoke cap have now been used. Retries do
not erase first-attempt failures or establish improvement over a startup
failure. Any supplementary development check is separately budgeted.

The dev.2 matrix stopped after its first holdout pair, HJ01. Both versions
correctly calculated a reported 25% byte reduction and identified missing raw
execution evidence. Both centered a fatal acceptance gap instead of clearly
separating the favorable supplied-record result from unavailable independent
verification. Candidate: 320.86 seconds (over the original 300); baseline:
284.78 seconds (within 300); both used the equal 900-second override.

Independent same-family adjudication found mixed outputs **and an ambiguous
test**: the rubric demanded actual roundtrip verification but supplied only
boolean summaries. The frozen failure and outputs remain unchanged. No candidate
improvement is established. The correction clarifies evidence levels without
granting acceptance or weakening provenance checks. HJ01 becomes development
evidence; all eight original holdouts are retired from unseen evaluation because
their concrete cases were exposed. Eight fresh holdouts replace them in the
40-case primary matrix; replacement and supplementary executions are counted
separately. A case-dependent source change cannot retain an unseen-test claim.

One separately budgeted development check of the exposed HJ01 case preserved
the favorable supplied-record outcome and did not fabricate execution or review.
Its final communication still overemphasized the certification block. Independent
assessment remains **mixed/partial**, not a clean pass; no further tuning on that
case or relabeling of its original failure is claimed.

Four two-session projects cover queueing framing/design, a non-training theorem
and counterexample, conflicting local literature, and a result-driven pivot/stop.
Session two receives only persisted project files and the current request. The
complete paired matrix, old cases, resource cases, repeats and handoffs remain
pending.

### Dev.3 replacement holdouts and execution restrictions

The replacement manifest SHA-256 is
`eb0dc51a01017d1591bcd0dd1c6650be7edd60beb8ba9cfe713257e95550c28f`.
It was unsealed after candidate snapshot
`99d9407f74e97b6773105cefe74e8b10abf3d1ad962f7f5b4115bf6ea01b8fd7`
was frozen. Two independent same-family assessors inspected the actual traces
and artifacts. Their findings are behavioral validation, not cross-family
scientific acceptance.

| Outcome | Candidate | Released baseline |
| --- | --- | --- |
| Substantive terminal outputs assessed | 8 | 8 |
| Critical or unambiguous required-content failures found | 0 | 0 |
| Within original 300-second ceiling | 8 | 5 |
| Within 900-second override | 8 | 7 |

The outputs preserve the requested findings, including favorable bounded proof
results, a failed primary quality criterion alongside a throughput gain,
literature conflicts and missing runs in figures. Baseline H2L02 has a mild
rubric/request ambiguity: an explicit next-check list was added by the rubric,
while the answer identifies relevant evidence gaps. It is not recorded as an
unambiguous content failure. Candidate H2J01 used canonical `result-to-claim`
outside the frozen acceptable first-route list; this route deviation remains
separate from its correct content. The two candidate R cases selected the new
brainstorming and manager entries and respected their scope; the required
eight-case R gate is still incomplete. Baseline H2L01/F01 used noncanonical
first entrypoints without an observed principles read. H2J02/L01/F01 exceeded
300 seconds, and F01 also hit the 900-second harness limit despite producing
final artifacts. The first three discovery failures and their three capped
recoveries remain preserved. No broad or causal upgrade advantage follows.

The development matrix's first four launches then failed before model turns
because the parent sandbox made the global Codex state directory read-only.
A separate writable temporary state directory allowed discovery and
`turn.started`, but the parent sandbox blocked model-service connections.
These four attempts produced connection-error traces, no answers and no
terminal `run.json`; they were stopped without waiting for another timeout.
An authorized read-only probe outside that sandbox received HTTP 401 without
credentials, confirming reachability, not model availability. The earlier
inference of an endpoint outage was corrected. No behavior result is assigned
to these infrastructure failures.

The subsequent network-enabled historical matrix launch was rejected by
automatic approval review because endpoint/payload authorization was
insufficient. It did not start any model session. The user later authorized only
the distinct eight-case supplement above; the historical 116-session inventory
has not been resumed under that narrower authorization. Evidence, hashes,
unchanged inputs and separate attempt histories remain in the ignored validation
directory. At that historical checkpoint, six valid baseline outputs were
reusable and only 22 of the 138 primary slots had substantive terminal artifacts,
including one timed-out
baseline. Content support, successful timed execution and release acceptance
are separate outcomes.

Source changes recorded at that checkpoint after the dev.3 freeze were validation documentation, a
whitespace-only Gemini overlay cleanup with its exact candidate digest update,
and the optional original-baseline comparator correction and regression tests.
All original baseline hash maps remain intact. Existing native findings remain
attributed to dev.3; they are not asserted to certify byte-identical final source.

[Official packaging guidance](https://developers.openai.com/plugins/build/plugins)
and [harness-aware evaluation guidance](https://developers.openai.com/cookbook/examples/partners/harness_aware_plugin_evals/harness_aware_plugin_evals)
were consulted on 2026-10-15. Results apply to the actual CLI and settings.

### Later dev.5 bounded checks on 2026-10-16

The later candidate was packaged as `1.4.0-dev.5` from source commit `7fa8255`.
Native discovery verified 88 Codex entrypoints and 250 support resources; the
common-guidance SHA-256 was
`bb58ecba76775a8694d38b2e7a5e78e67f78039e2b659a3221646a719956f2f0`.
The released baseline exposed 86 entrypoints and 237 support resources. These
runs used `gpt-6.1-sol`, high reasoning, one job, and a 300-second ceiling unless
explicitly labeled as a separate diagnostic. Their harness SHA-256 was
`c5d0356357d8a12b91f11b5d2a99f05686b1b26f7c3adf6fa0d4789578709a36`.
Every batch retains its discovery metadata, manifest identity, raw events,
stderr, artifacts and terminal run records in the private validation directory.

All eight C development cases now have a completed bounded candidate attempt:

| Case | Completed attempt, seconds | Required output observed |
| --- | --- | --- |
| C01 classification | 152.06 | `ANALYSIS.md` |
| C02 regression | 141.55 | `ANALYSIS.md` |
| C03 image generation | 169.31 | `ANALYSIS.md` |
| C04 video | 152.27 | `ANALYSIS.md` |
| C05 aggregate-only evidence | 174.53 | `ANALYSIS.md` |
| C06 narrow arithmetic | 40.39 | Concise answer, no new files |
| C07 selected-panel claim | 123.36 | `REVIEW.md` |
| C08 incomplete pairs and storage limit | 225.75 | `ANALYSIS.md` |

These completed attempts have no recorded service errors, variant mismatches or
noncanonical entrypoint reads. Implementer inspection found that the reports
retain regressions, tail failures, full-pool denominators and missing-evidence
limits. For the synthetic generation census, both methods meet the prompt in
2/4 outputs; individual improvements and regressions do not establish a higher
overall prompt-success rate. C06 answers the requested 16.7-percentage-point
calculation without starting a report workflow.

The table indexes completed attempts, not eight first-attempt successes.
Earlier timeouts, reconnects and a tool-execution failure remain preserved.
The separate C03 900-second diagnostic is not used as a 300-second result.
These are implementer-reviewed development outputs; the C baseline comparison
and independent acceptance are still outstanding.

The six focus cases O03/J01/J07/R01/L01/F03 also have completed candidate
attempts within 300 seconds, taking 129.74/118.90/243.90/234.30/85.30/170.37
seconds respectively. Their completed baseline counterparts took
287.70/207.91/116.52/168.10/221.60/213.97 seconds. Baseline O03, J07 and F03
needed separately retained bounded retries after service errors; J01 completed
despite one service-error event. These results cannot be presented as a
first-attempt robustness advantage or as proof of general improvement. The
interrupted baseline attempt without a terminal record remains incomplete.
Figure outputs retain their actual preview limitations.

The original candidate cases 01–08 then produced four completed sessions
(01/02/05/08) and four timeouts. The timeout assessment is:

| Case | Observed state at the 300-second stop | Remaining issue |
| --- | --- | --- |
| 03 method refinement | Proposal and provisional, review-blocked records saved near the deadline | No completed CLI turn |
| 04 experiment planning | Sixteen tool actions, including repeated reference reads | Neither requested plan nor tracker saved |
| 06 claim assessment | One reconnect; three evidence-helper invocations while correcting input shape and literal values; mainline rather than discovered Codex entrypoint read | Requested assessment file absent; guidance deviation retained |
| 07 paper-number audit | One reconnect; audit identifies the 0.860/0.840 mismatch, training-budget confound and unsupported domain scope | No completed CLI turn or independent reviewer acceptance |

No service error was observed for 03 or 04. The errors observed for 06 and 07
do not establish the cause of their entire delay. Saved files do not convert
timeouts into completed sessions. The initial empty legacy batch contained no
model runs because its launcher built an empty case selection; it is an
invocation error, not a passed batch. Raw evidence and implementer triage are
retained in `current-legacy-execution-status.json` and
`current-legacy-timeout-triage.json`.

### Evaluation cancellation and local API configuration

The evaluation harness now rejects an empty selection before discovery, stops
its isolated CLI process group when inspection raises, and propagates SIGINT or
SIGTERM cancellation to active sessions. Queued cases do not launch after
cancellation. Canceled runs retain their traces and an unassessed cancellation
record; the batch exits unsuccessfully and records cases without terminal
results. Cleanup also stops group members that ignore SIGTERM after the CLI has
already exited. The initial focused harness regression returned **21 passed**
in 11.32 seconds. After adding that surviving-process regression, the combined
harness, packaging, Codex-mirror and skill-group checks returned **72 passed**
in 32.37 seconds (`harness-followup-final-regression.xml`), including actual
signal and process-group checks. Package preservation and skill inventory
checks also passed. This changes evaluator lifecycle handling, not the frozen
research rubrics or previous results. Future batches must record the updated
harness identity:
`32a185d31091e3ea1943212e8ead53b26559bcb8f9544022fa52d77d2fdc864d`.

The user also configured a local, Git-ignored `.env`. A bounded canary against
that configured gateway returned HTTP 200 and `READY` for
`deepseek-v4.1-flash` in 2.21 seconds and `mimo-v2.6-flash` in 1.87 seconds.
`glm-5.3-flash` reached the 45-second timeout without a response. Each model
received one request, with no automatic retries. The local fallback was then
changed to MiMo at the user's request. The credential is not included in
validation receipts or release files. These checks establish minimal generation
through that configured account and endpoint; they do not authenticate the
upstream implementation or replace the frozen Codex behavior matrix. Earlier
401 responses from different endpoint/account combinations remain historical
diagnostics, not a current blanket claim that these models are unavailable.

### Dev.6 remediation and acceptance continuation

On 2026-10-16 the user explicitly resumed 1.4.0 acceptance. A narrow followup
clarifies bounded proposal/plan delivery, preserves resumable pending-review
state, permits labeled preliminary paper-number findings when required fresh
review cannot run, and documents the evidence helper's existing array input,
CSV boundary policy and per-item statuses. The helper API and original frozen
preservation maps are unchanged. An independent implementation review found no
blocking issues; its two nonblocking clarifications were applied before freezing.

The dev.6 snapshot SHA-256 is
`cd36241b8c0612d8c66dedb0f428ea5e9fbe3af6e71ed24f264b617f3fddf1ca`.
It records base commit `33d8963` plus the exact working-tree source hashes and
modified paths; that commit alone does not contain the followup. The isolated
package has 989 files, with only `VERSION` and the Codex plugin version changed
to `1.4.0-dev.6` for installation. Native discovery confirms 88 candidate and
86 baseline entrypoints, and 250/237 support resources, respectively.

The runtime uses a private temporary Codex home outside the repository and
leaves the formal installation/configuration unchanged. An earlier preparation
attempt put that home inside this repository, causing native system skills to
inherit its namespace; strict discovery rejected it before any model session.
The relocated runtime passed discovery. Remedial model attempts keep
`gpt-6.1-sol`, high reasoning, one job, a 300-second ceiling, and zero automatic
retries. First failures and subsequent diagnostic attempts remain distinct.

The targeted regression returned **58 passed** in 19.01 seconds. A fresh
Python 3.12 test environment containing `requirements-dev.txt` then ran the
complete suite: **1,141 passed, 38 skipped, three warnings and 46 subtests
passed** in 497.06 seconds (`full-tests-native-acceptance-20261016.xml`).
This is a current local program pass, not a native behavior or platform CI pass.

Two fresh independent contexts also assessed the eight completed dev.5 C
attempts against their frozen inputs and rubrics. All eight satisfy the
substantive case requirements as **same-family provisional behavior passes**.
The reviewers recomputed calculations and inspected relevant images; the
native CLI export does not establish the evaluated sessions' claimed direct
image-viewing provenance. That remains unverified rather than silently assumed
or asserted to be fabrication. These reviews neither erase first failures nor
complete the missing C baseline comparison.

Eight new holdouts were independently authored and sealed before source freeze.
Their index SHA-256 is
`f872ee3c794511969e6c40fc4a86412553db5479b555db5410cc4ae6271992a2`.
The implementer had not opened their inputs, manifest or rubric at freeze time.
Their execution and assessment are still pending; sealed fixtures are not
coverage.

Dev.6's exposed original case 03 then reached **300.52 seconds** with ten
successful tool actions, no recorded service error, no saved proposal and no
completed turn. The zero CLI exit code does not make that attempt complete.
The other three remedial attempts were not started on that build. An independent
diagnosis counted 49,764 characters of command output, about 95.7% entrypoint or
reference material. The trace has no per-event timing, so this supports a
loading-cost concern rather than an exact attribution of elapsed time.

### Progressive refinement followup

The followup makes `research-refine` progressively disclose its original full
workflow. Its compact Codex entrypoint is about 8 KB rather than 32 KB and asks
for an early saved anchored proposal/checkpoint. Each runtime retains the full
reviewer workflow in `references/full-workflow.md`, including original reviewer
prompts, scoring, round limits, recovery and final output names. Required review
remains required; unavailability leaves a truthful BLOCKED, resumable state.

The Claude overlay generator now also converts deferred resources. Overlay
checks inspect those files, and native discovery pins all runtimes' per-skill
references so a stale deferred workflow cannot silently pass byte verification.
An initial focused run exposed three missing adaptation registrations and a
Claude entrypoint conversion mismatch; those were corrected without changing
the original frozen preservation maps or relaxing the checks. The subsequent
focused run returned **85 passed and 26 subtests passed** in 32.36 seconds;
package verification also reports PASS with 88 entrypoints and 83 retained
contracts. This does not establish that the timeout is fixed; new same-budget
native execution and independent assessment remain necessary.

Independent implementation review confirms all four extracted full workflows
match the frozen dev.6 bodies after only relative-link corrections. Its compact
recovery clarifications were applied: initial round-0 persistence is fresh-run
only, resumed histories retain real reviewer rounds/scores, and the Gemini
entrypoint supplies an explicit compatible phase/continuity recovery map.

The next full local suite returned **1,145 passed, 38 skipped and one failed**
in 485.89 seconds. That failure was a retained payload-guidance check reading
only the entrypoint after the prompts had moved. Its existing assertions now
also inspect entrypoint-linked local references; missing or unlinked prompt
files do not satisfy them. Native platform CI for the exact followup is pending.
The repaired focused regression returned **87 passed and 26 subtests passed**
in 33.51 seconds, including that original payload test.
The test workflow permits `acceptance/**` branch pushes as well as main/PRs,
allowing an isolated acceptance branch to trigger the same four platform jobs
through the available Git SSH authentication without changing the default branch.

### Dev.7 execution and independent assessment

The clean source commit `de26cde8e7b0314c41ee4ab23817763f5c675005` was frozen
as isolated `1.4.0-dev.7`. Snapshot SHA-256:
`1e8be3164745f16066572dbf1018b5a170b7362d2d1454c8290d1c1af4fbb74f`.
Native CLI 0.163.0 discovery pins 88 entrypoints and 270 support resources;
the separate released baseline has 86 and 253. The additional support coverage
includes deferred runtime references, rather than additional skills.

The final full local program run on this source returned **1,146 passed,
38 skipped, three warnings and 46 subtests passed** in 499.90 seconds
(`full-tests-progressive-refinement-final-20261016.xml`). This supersedes the
earlier failed local run only for current program status, not its retained
history. Native platform checks for this exact source remain unobserved: the
acceptance branch push succeeded, but the public Actions API returned no run
for it. The older platform CI successes do not cover this followup.

Four original exposed cases were run with the unchanged request-only protocol,
300 seconds, 32 actions, `gpt-6.1-sol` and high reasoning. A recorded resource
check permitted at most two isolated CPU-only sessions concurrently. No
automatic case retries were enabled.

| Case | Execution | Observed deliverable and assessment |
| --- | --- | --- |
| 03 method refinement | 300.52 seconds, time limit; no service error | No proposal saved. The proposed write failed with an f-string `NameError`; no completed recovery before the limit. INCONCLUSIVE execution, with the writing error retained |
| 04 experiment plan | Completed in 225.93 seconds | Plan and tracker saved; independent frozen substantive criteria PASS. A separate medium runtime-policy deviation remains: output links led to mainline references and no Codex-required manifest was saved |
| 06 causal assessment | 300.34 seconds, time limit; no service error | Literal evidence precheck saved, but no requested `CLAIM_ASSESSMENT.md` or completed turn. INCONCLUSIVE |
| 07 paper-number audit | Completed in 170.14 seconds | Independent PASS: correct 0.840 rather than 0.860, training-step confound and unsupported domain scope. Executor findings are labeled preliminary and the required reviewer gate remains truthfully BLOCKED |

The independent 04/07 reviewer verified all original input bytes unchanged and
found no critical integrity failure. A completed CLI and a frozen substantive
pass do not excuse the separate case-04 runtime-policy issue. The corresponding
repair changes only actual Codex/overlay output-reference destinations; policies,
original workflow contracts and the frozen preservation maps remain intact.

A separate independent review of the six historical dev.5 focus pairs returned
6/6 candidate passes. Baseline deliverables pass in 5/6; J01 invents a required
proof correction. L01 uses `research-review` rather than a suggested literature
skill; an adequate alternative is not a failure solely because it falls outside
the non-exhaustive `acceptable_skills` list. All 16 attempts, including
service failures and selected retries, remain indexed. These limited development
results do not validate dev.7 or prove a general reliability advantage.

### Explicit-budget evaluation protocol

Independent methods review confirmed that the original harness enforced its
300-second ceiling without supplying the numerical wall-time limit or deadline
to the model. The fixture did disclose the 32-action cap. This does not excuse
the missing outputs or writing error, and those attempts retain their original
status. It limits conclusions about compliance with a known numerical deadline.

The evaluator now has a default-off `--public-budget-context` option identifying
future runs as `public-execution-budget-v1`. It supplies only wall seconds,
maximum actions, UTC start and deadline; the timer includes CLI startup and is
still enforced monotonically. Original request, exact model-visible prompt,
notice/prompt hashes and protocol metadata are retained. No rubric, expected
route, answer hints or save-early instruction is exposed. Paired variants must
use the same disclosure setting; previous attempts are neither edited nor pooled
with the new protocol. This change does not itself establish better completion.

The budget-only harness regression returned **30 passed** in 17.04 seconds.
After the independently identified path correction, the combined harness,
mirror, overlay, generator and preservation regression returned **89 passed
and 26 subtests passed** in 35.47 seconds. New native execution and final
platform CI remain necessary.
The subsequent full local suite returned **1,150 passed, 38 skipped, three
warnings and 46 subtests passed** in 513.32 seconds
(`full-tests-output-reference-budget-20261016.xml`), with no failures. This
includes the new protocol's default-off and opt-in fake-CLI checks; those checks
are not model-behavior passes.

### Dev.8 matched diagnostics

The output-reference and evaluator changes were committed as
`6dca6745c2aa71fa4cd578b31f2bfb2d228129f5`, pushed on the feature branch and
the separate `acceptance/v140-dev8-20261016` branch, and frozen as isolated
`1.4.0-dev.8`. Snapshot SHA-256:
`9ddb5ccfad97dbfc9a13a3dd764f8227e4e4fc0a6817527ca840424133f9ff7e`.
The formal installed plugin and release metadata remain 1.3.0. The private
evaluation does not replace that installation.

Independent implementation review found no blocker, reproduced **55 passing
focused tests**, verified 352 shared-reference links at their installed Codex
destinations, reproduced all nine generated Claude files, and confirmed both
original frozen preservation maps unchanged.

A separately registered six-session diagnostic used the new public-budget
protocol equally for released 1.3.0 and dev.8: 300 seconds, 32 actions,
`gpt-6.1-sol`, high reasoning, CLI 0.163.0, concurrency at most two and zero
automatic retries. All six sessions completed without recorded service errors
and received independent same-family provisional substantive PASS:

| Original case | Candidate seconds | Baseline seconds | Independently checked outcome |
| --- | --- | --- | --- |
| 03 method refinement | 184.61 | 187.13 | Implementable proposal, local evidence and limitations, no full experiment roadmap or invented reviewer acceptance |
| 04 experiment plan | 233.82 | 231.81 | Matched controls, data isolation, Brier/uncertainty/failure criteria, resources, plan and tracker; candidate reads actual Codex output policies and saves the required manifest |
| 06 causal assessment | 179.59 | 187.68 | Correct 80% to 84% observation, 100-versus-200-step confound, missing calibration outcome and required review kept unavailable/BLOCKED |

All original inputs remain unchanged. Baseline-specific output/recovery
differences and a failed outside-project empty-placeholder write in case 04
are retained separately. No file was created by that failed write. A local
baseline unavailability-response file explicitly identifies executor-authored
blocked status, with no reviewer call or response; it is not a reviewer verdict.

These outcomes do not establish that budget disclosure caused completion or
that either toolkit is faster or generally better. They are not pooled with
the previous request-only timeouts. No required scientific review is accepted
by these dependency-handling outcomes.

The affected J07 narrative case was also rerun as one matched **request-only**
pair at its unchanged 300-second/28-action limit. Candidate 121.78 seconds and
baseline 85.92 seconds both completed and independently PASS: both preserve the
80% to 78% primary-result decline and missed target alongside an exploratory
50-to-30-ms latency gain, without retrospective primary-metric substitution.
Candidate timestamp/fixed outputs and manifest entries match; original inputs
and provisional review status remain intact.

Independent source-applicability review permits bounded historical coverage for
13 earlier dev.5 focus/C cases whose actual loaded source slices and advertised
frontmatters remain unchanged. It does not label them dev.8 executions or new
protocol passes. J07 was affected and therefore received the rerun above.
Original 01/02/05/08 outputs also satisfy their current substantive criteria;
however, their historical full manifest hash differs and its original copy is
unavailable. Saved requests, fixture bytes, limits and loaded source were checked
separately; historical whole-rubric identity remains INCONCLUSIVE.
An independent methods adjudication permits these four as explicitly bounded
historical coverage against the current selected-case criteria: saved requests,
inputs, observed limits, loaded slices and substantive outputs are directly
checkable. This does not restore the missing original rubric or label them
fresh dev.8 runs. Case 04 retains its historical substantive PASS with the
recorded noncritical deviation; current request-only runtime repair confirmation
has not been executed and is not inferred from the public-budget diagnostic.

Four two-session handoffs and the independently sealed eight-case holdout
comparison are registered separately. Their prepared fixtures and launch
registrations are not passes. Handoff session two receives only the hashed
persisted project and current request in a fresh ephemeral session, excluding
the earlier answer, event trace, prompt and conversation. Outcomes are recorded
only after actual execution and independent assessment.

### Dev.8 handoffs and platform verification

All four registered two-session projects completed and received independent
same-family provisional PASS for both sessions and their persisted-artifact
boundaries. The original request-only limits remained 900 seconds and 28 actions
per session; no evaluator retries were added.

| Project | Independently checked behavior |
| --- | --- |
| H01 queueing | A frames a bounded synthetic question; B incorporates longest-task waiting into an implementable matched design without running simulations or training |
| H02 theory | The arbitrary-real range-sum identity and empty boundaries remain correct; B rejects false universal nonnegativity using valid counterexamples |
| H03 literature | Both contradictory excerpts, actual reading levels and uncertainty survive the handoff; B rejects universal benefit without declaring certain harm, no effect or equivalence |
| H04 direction change | Primary quality loss and secondary latency gain remain distinct; B appends the explicit user stopping choice to the existing decision authority without training, deletion or a second state system |

Original inputs remain unchanged, with the existing decision record retained as
an exact prefix where appending was requested. Each second session used a fresh
ephemeral thread with only the prior project files and its current request.
The recorded file hashes match. H01/H02 first-session full derived manifests are
not retained at their historical hashes; saved requests, fixtures, limits and
loaded resources were independently verified, without claiming equivalence of
the missing whole manifests. H04's first session recovered one recorded server
overload reconnect and completed within its original limit; it is not an
error-free attempt. H04's executor wording about nonacceptance is interpreted
narrowly under the original question, not as an invented user pivot.

GitHub Actions now reports **success on the exact `6dca674` source** for Ubuntu,
macOS, Windows PowerShell and Windows pwsh, plus inventory and advisory lint.
The [current-source test-suite run](https://github.com/Soceremite/EvoInquiry/actions/runs/38909689758)
supersedes the earlier no-run-observed status. Its platform success and the
1,150-pass local suite are program evidence, separate from behavioral coverage.

The acceptance inventory was independently corrected to retain 40 focus
positions: eight independently authored unseen replacements occupy the retired
holdout positions, with their category-only metadata confirming two J, R, L and
F cases each. Exposed originals and prior failures remain development/history;
additional executions are recorded without requiring duplicate current passes
or double-counting them. Neither preparation nor CLI completion is a pass.

The next registered request-only block completed O01, O02, J02 and J03 for both
variants at their original limits. Independent assessment returned **candidate
4/4 PASS and baseline 4/4 PASS**, with no critical failures. Original inputs and
actual loaded-source identities were verified. These cases cover ranking with
exceptions, correcting an inaccurate objection, resource/test-selection
confounding, and a negative pilot's limited but useful evidence. Both J02
reviewer gates remain honestly unavailable/BLOCKED. All eight sessions completed
without recorded service errors, but incidental command/helper failures remain
in the evidence. This block supports task-specific parity, not a general
candidate advantage.

The first two independently authored unseen J replacements completed for both
variants under their original request-only limits. All four outputs pass their
frozen substantive criteria, with no confirmed critical integrity failure. The
implementer received category/status summaries, not the private task inputs or
judging criteria. The remaining six unseen replacements were executed later and
are reported below.

Candidate `fresh_01` retains a **separate runtime-entrypoint deviation**: native
discovery advertises the Codex entrypoint, but the captured first tool reads the
retained mainline skill and subsequently follows mainline references. That file
explicitly directs Codex to the correct discovered path; no later canonical read
is recorded. The harness correctly flags the noncanonical entrypoint. Package
identity is correct and the substantive outcome passes, but canonical-runtime
acceptance fails for this attempt. The cause of its initial path choice is
unknown; no mislinked helper or deterministic source defect is demonstrated.
Candidate `fresh_02` uses its discovered Codex entrypoint. This deviation is
neither erased by the content pass nor promoted into an unsupported critical
data/review fabrication finding. No source changes were made from these unseen
case contents, and the build remains frozen for subsequent execution.

During the next public block, candidate J05 saved its requested experiment plan,
tracker, matching timestamped revisions and valid output manifest. Independent
review passes every substantive behavior and artifact criterion. The native
session nevertheless reached its 300-second ceiling at 300.50 seconds, with no
completed turn or final answer and no recorded service errors. The user explicitly
accepted **J05 as PASS** on the completed artifacts. This case-specific human
disposition closes J05 for acceptance; its original execution remains recorded
as time-limited and incomplete. No retry or implementation change is required
solely for that timeout. This does not waive other cases, alter raw evidence,
establish budget compliance or accept an unavailable scientific review.

The next two unseen R replacements have separate content and execution results.
Both variants chose adequate first entrypoints for both cases. In `fresh_03`,
neither saved the required deliverable before its original 300-second limit:
candidate 300.36 seconds with no recorded service error; baseline 300.28 seconds
with one overloaded-server/reconnection error. Both attempts fail bounded
completion. Baseline `fresh_04` passes at 236.20 seconds. Candidate `fresh_04`'s
saved artifacts pass independent checks, but the parent user interruption left
no terminal receipt; session completion remains inconclusive, not a timeout.
The implementer received only status and public-runtime diagnostics. Loaded
resources match the frozen packages; these observations establish neither a
general source defect nor a candidate runtime advantage.

The first storage attempt remains unaccepted because S01 timed out at 600.23
seconds: two patch-validation errors left the script unchanged, without its
implementation report or recovery checks. S02's original partial attempt was
user-interrupted and remains ungraded. Separate, later recovery attempts are
reported independently: S01 recovery met all public storage requirements, and
the first S03/S04 recovery attempts met their public required outcomes,
including cumulative storage infeasibility, corrupt-latest/valid-fallback
recovery, and blocking an over-budget save peak. No supplied evidence was
removed and no experiment was launched. Independent methods review corrected
an overly strict S03 reporting judgment: its saved-point, unsaved logged
progress and recovery recommendation already communicate the loss; an exact
1,300-step calculation is optional.

Qualifications remain visible. S02 incorrectly says a weights-only export size
was unspecified although the input gives 2 GiB; its resume-only lower-bound
infeasibility calculation still holds. It also omits the selected planning
skill's tracker. S04 uses the mainline surface from the correctly pinned
candidate package rather than the discovered Codex surface. Its resource
blocker is correct, while runtime conformance fails; this does not demonstrate
a different version or identify the cause of the initial path choice. Original
reviews and the narrower methods correction are both retained.

An external temporary evaluation home was absent after the user interruption.
One baseline launch failed preflight without a model call. The same isolated
path was rebuilt from matching configuration/guidance and the frozen plugins;
native discovery passed for both variants before the separately registered
recovery executions. The formal installed 1.3.0 was not changed.

The candidate and baseline routing block then completed all eight cases. The
candidate had seven substantive PASS and one PARTIAL (J09); J09 correctly
identified the evidence boundary but framed the missing audit material as a
broad certification/auditability failure and loaded the mainline experiment
audit path. The baseline had six PASS, the same J09 PARTIAL, and R06 was
INCONCLUSIVE because its recorded runtime loaded the dev.8 candidate package
under a baseline launch. These are retained as runtime/calibration findings,
not candidate integrity violations or comparison advantages.

The literature/figure block met all six public outcomes on each side. Candidate
sessions were ordinary completed runs with canonical paths. Baseline F02 saved
the required material but reached its 300.50-second time boundary; the
time-limit deviation remains visible. F01/F02/F04 visual or external review
gates were unavailable/provisional, so mechanical artifacts do not establish
visual quality or a scientific advantage.

The eight critical repeats met their public outcomes on both variants and
supported key-category stability in all eight pairs, with no service errors or
critical integrity failures. J02 used an alternate result-to-claim route on
both sides and candidate J03 used research-manager outside the registered list;
the public outcomes still met their criteria, but the route deviations remain
separate evidence. Repeat results are additive and do not replace first runs.

Candidate lifecycle/governance cases met four of six public outcomes. L02
correctly stopped on a missing comparison-evidence ledger and G02 correctly
stopped after a filesystem-lock exclusion failure; both are valid dependency
handling, not completed research verification. S01's second, separately
registered recovery attempt met all public storage requirements in 337.37
seconds. Its first 600.23-second timeout and failed patch attempts remain a
distinct incomplete attempt. S02–S04 met their public blockers/recovery checks,
with S02 documentation omissions and S04 mainline-surface loading retained.

Candidate legacy cases 09–24 produced 15/16 public outcomes. Case 22 reached
the 300.45-second limit with only partial preparation and no final answer; it
is INCONCLUSIVE/partial, not a pass. Case 20 used a noncanonical entrypoint
while its substantive artifact met the case requirement. The original 01–08
records and all first attempts remain preserved.

The remaining fresh L/F replacements completed for both variants within their
registered budgets (fresh_05–08). The safe independent review reports **4/4
public outcomes MET for each variant**, four paired matches, zero service
errors, zero variant mismatches and zero critical-integrity findings. Three
cases per variant retain blocked or unavailable visual/independent-review
gates; fresh_05 had no formal gate in its public task. The selected task
content and criteria remain withheld from the implementer, and no comparative
advantage or aggregate scientific verdict is inferred from terminal execution
or these mechanical outcomes. The detailed receipts remain private; the
public summary is preserved at
`validation/upgrade-1.4.0/fresh-05-08-candidate-baseline-safe-summary-20261016.json`.

A separately registered third attempt for the fresh R pair preserved the prior
failures and interruptions. Candidate `fresh_03` completed in 140.74 seconds
with no service error or variant mismatch; candidate `fresh_04` again reached
the 300-second limit at 300.46 seconds without a completed session. Baseline
`fresh_03` completed in 176.36 seconds and baseline `fresh_04` in 42.50
seconds; both had no service error or variant mismatch. These are runtime-only
facts pending the authorized independent selected-case review; they do not by
themselves establish the private public outcomes or a candidate advantage.
The runtime-only receipt is
`validation/upgrade-1.4.0/fresh-R-third-attempt-runtime-only-20261016.json`
(SHA-256 `fd810e8487c3c112cab6b7e1aca96e6e96c05518acb94ac6c2a29787223159ac`);
it assigns no scientific outcome or holdout release.

The baseline R06 routing mismatch was also rerun in a fresh home containing
only the pinned 1.3.0 plugin. The independent public review recorded a
64.09-second completed session, zero service errors, `variant_mismatch=false`
and no critical-integrity finding. The original mismatch remains preserved;
this is a separate prospective baseline recovery record, not a rewrite of the
first comparison.

The third-wave public-safe progress report consolidates the routing,
literature/figure, repeat, lifecycle/governance, storage-recovery, legacy and
fresh-holdout evidence without double-crediting attempts. It records the exact
CI result separately from native acceptance and keeps public outcomes,
runtime/route deviations, review-gate availability and integrity findings as
separate axes. Its conclusion remains **release OPEN**: no aggregate clean
pass, comparative advantage or release-ready claim is made. The report is
`validation/upgrade-1.4.0/acceptance-progress-third-wave-20261016.{json,md}`;
the JSON SHA-256 is
`f3923fd011b8f5b9ad4fd55c5af432f8e2328412091f1374d16e104a8ee59fe0`.

## Historical open assessment — before 2026-10-17 closure

The complete native behavior matrix remains incomplete. The dev.8 full local
suite and exact-source platform CI pass, and all four cross-session projects
have the qualified independent assessment above. The eight completed C attempts
have independent-context provisional assessment, while their baseline
comparison remains outstanding. The completed blocks above do not erase the
unavailable reviewer gates, runtime deviations, incomplete attempts or missing
scientific acceptance.
Original request-only 03 and 06 attempts remain incomplete; the new explicit-budget
03/04/06 diagnostic passes separately and verifies case 04's path repair. Case 07's
substantive criteria pass with its required review gate still BLOCKED.
Release metadata must record actual outcomes rather than
inherit old-version passes.


## Final candidate closure — 2026-10-17

### Scope, planning and metric-normalization repairs

Source `21b2b65fd398e3f022bcd936ff6ca97b40575df0` separates a local assessment
of supplied records from formal execution certification and preserves supplied
resource quantities in planning. A separately frozen dev.9 plugin was tested
with original request-only inputs and prospective public controls. J09,
AUDIT_NEGATIVE, AUDIT_GATE and S02 all meet their registered outcomes with actual
canonical skill/principles reads, preserved inputs, saved artifacts and final
handoffs. The formal audit control remains BLOCKED when independent review is
unavailable; the positive local assessment does not bypass that gate.

S02 now retains the supplied 2 GiB weights-only export size, identifies the
154 GiB recovery-state lower bound against 120 GiB of available storage, considers
cumulative saving peaks and writes the requested 12-slot blocked tracker. This
does not authorize an infeasible run. The first pre-execution SQLite discovery
failure and the original documentation omission remain separate records.

The review is `dev9-scope-calibration-independent-review-20261017.json`, SHA-256
`ef3b34a68a8e208e69903252b008648aecce6ffe78d1f99a1b4ddad3aa49e8e2`.
It verifies all 88 entrypoints and 270 reachable support resources against the
frozen package. The source-specific affected regression passed 90 tests.

A further source review found that the old denominator wording could reject
legitimate prediction-dependent metrics. Source
`40ff2c20c059ed639180e9c903233f70b20c54eb` corrects both audit surfaces and
both shared integrity references: evaluate the declared formula, aggregation,
zero-denominator handling and actual claim. Disclosed display scaling does not
justify claims of absolute accuracy, calibration or relative improvement, and
missing evidence is not proof of misconduct. Original protected maps and formal
review gates remain unchanged. The affected preservation/package regression
passed 59 tests.

Two prospectively registered public contrasts on frozen dev.10 both pass:
N_VALID completes in 113.47 seconds with eight actions and N_INVALID in 89.75
seconds with seven. Exact-fraction recomputation distinguishes valid
precision/F1/IoU and direction-only normalization from invalid interpretations
of display scores. Both sessions directly read the repaired audit Step B; they
do not directly open the shared integrity reference, so isolated use of that
reference is not behaviorally established. Their same-family review is
`dev10-normalization-behavior-review-20261017.json`, SHA-256
`a4aa3afd94e9d06fd77bfac59e90ae7c98dac7d30b026e446ee7c56d21f0b863`.

The unchanged original legacy06 request also completes prospectively on dev.10
in 200.87 seconds with 14 actions. It preserves all six rows and the descriptive
+4 percentage-point result, identifies the unequal training and missing
calibration evidence, proposes useful controls and truthfully records the
independent claim review as unavailable. This is a completed software-case
outcome, not causal claim acceptance. Earlier request-only timeouts and the
budget-disclosed diagnostic are retained and not relabeled.

### Actual local positive paths and retained prerequisite failures

G02 was executed with its unchanged public request and fixture on a verified
local overlay outside the repository. The session completed in 151.29 seconds,
ran the filesystem probe before initialization, created and checked the actual
requested project profile, preserved existing notes and stated unknown
persistence. This verifies only the tested local operations. The original
`/lyd` filesystem's cross-process lock-exclusion failure remains a valid blocker;
its safety check was not weakened.

The original resource L02 cleanup case correctly blocked because its synthetic
inputs lacked the complete comparison ledger. A separately registered
L02_POSITIVE_PRECONDITION variant adds explicitly synthetic, pinned nine-run,
nine-attempt evidence before execution. It uses the unchanged request, rubric
and limits, and completes in 150.03 seconds. Validation selection retains beta,
protects alpha's dependency, actually deletes gamma's unneeded state and binds
the winner receipt to valid evidence. Logs, results and configuration records
survive; 39 input files remain unchanged. The successful canonical
`analyze-results` route is adequate but outside the literal registered skill
list. This outcome does not turn the original blocked fixture into a positive
execution or validate historical unrecorded experiments.

The same-family reviewer authored that explicit synthetic fixture, but did not
implement or execute the candidate. Review limitations remain declared. Fifteen
G02 and 51 L02 archive files match their original output bytes. Absolute runtime
paths are retained; these archives are evidence, not relocated active stores.
The review is `dev9-resource-positive-independent-review-20261017.json`, SHA-256
`a4c377c7a471c4a017e529ea7602ab43e8cc93a96d6fa0cedd2ad6aa87fc098d`.

### One bounded held-out isolation verification

The custodian completed the previously pending third-attempt review without
revealing the private task to the implementer. Fresh_03 has a qualified positive
original-protocol outcome; fresh_04's substantive artifact passes but its old
terminal timeout remains. A prospective methods disposition permits exactly
one unchanged-limit current-candidate isolation verification after the old home
was lost and separate runtime-state failures had been observed. Source and
runtime both change, so this does not identify the original timeout cause.

The custodian executes only that one frozen dev.10 request, without hints,
budget disclosure or automatic retry. It completes in **62.60 seconds and six
actions** at the original 300-second/32-action ceiling. Substantive delivery,
input preservation, bounded scope, suitable routing, actual principles read,
final handoff and clean-session checks all pass provisionally. Discovery matches
88 entrypoints and 270 support resources. The raw output archive is byte-identical;
private inputs, criteria and detailed outputs stay withheld from the implementer
and are excluded from publication.

The public-safe report is
`fresh04-dev10-isolation-review-safe-20261017.json`, SHA-256
`1ee004ec26e2566da78fff10c4bbddeb3249646d65a358df62dae3d3335a023d`.
This is new bounded evidence, not a retroactive pass, a causal diagnosis of the
old failure, an unseen-case generalization or independent scientific acceptance.

### Current program and publication checks

The complete local regression at source `40ff2c2` returns **1,150 passed,
38 skipped, three warnings and 46 subtests** in 476.47 seconds. Its XML is
`full-tests-normalization-20261017.xml`; it predates the new publication-coverage
regression. Skips and warnings are not integration or platform passes.

[Exact-source CI run 38991160599](https://github.com/Soceremite/EvoInquiry/actions/runs/38991160599)
passes Ubuntu full tests, macOS full tests, Windows `powershell.exe` and Windows
`pwsh`. These are actual completed job outcomes, not planned runs. The later
release workflow correction adds literature, research decisions, workflow
versions and figure evidence to its two Windows jobs, matching ordinary CI.
The new coverage regression first reports one failure and two passes against
the old workflow, then three passes after repair. Both XML receipts are retained.
Publication requires the exact final tag's full Linux/macOS suites and both
native Windows jobs again; no earlier source's CI is substituted for that gate.

The final version metadata, publication workflow/arguments, package and Codex
mirror checks return **47 passed** in 18.04 seconds, with no failures or skips
(`final-release-materials-tests-20261017.xml`). Inventory, preservation, local
README links, release-note wrapping and `git diff --check` also pass. These
focused results complement, rather than relabel, the earlier full suite.

All report paths above are relative to ignored `validation/upgrade-1.4.0/` and
are local evidence references, not files included in the release archives.


### Case-study comparison and legacy threshold

The eight newly completed baseline sessions use the actual released 1.3.0,
original request-only cases, 300-second/32-action limits and isolated native
discovery. All eight satisfy their substantive frozen criteria, within their
limits. Baseline C03 has observed successful PNG pixel decoding after an
unavailable optional decoder; C04 and C07 retain **INCONCLUSIVE direct-view
provenance** despite correct content. Their statements of viewing are not
promoted to verified visual acquisition, nor does the absent acquisition event
alone prove fabrication. Existing candidate media-provenance qualifications
remain the same. No universal visual-tool requirement is added after execution.

The candidate C outputs are previously reviewed selected dev.5 completions,
not eight new dev.10 sessions or eight first-attempt successes. Every loaded
analysis/principles/comparison/case-study dependency matches dev.10 and current
bytes; reuse applies to those unchanged slices only. Different harness versions
and runtime histories prevent interpreting descriptive times as a speedup.
Both versions meet these fixed content cases, so no general candidate advantage
is established. The 207-hash same-family methods report is
`case-study-baseline-and-legacy-closure-20261017.json`, SHA-256
`6074725a408468b83c3f93e9fa0595362e28ab06249082bdcddc667151ac53cd`.
It was written before the final fresh_04 safe receipt; the completed custodian
receipt above supersedes only that report's pending status.

With the new original-protocol legacy06 outcome, **22 distinct legacy IDs** now
have qualified positive request-only outcomes across the documented applicable
candidate sources: 01, 02, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15,
16, 17, 18, 19, 20, 21, 23 and 24. All seven mandatory categories/IDs remain
covered: resumption 09/11/14, small tasks 15/16/17 and explicit invocation 18.
Case 03's positive budget-disclosed diagnostic is excluded from this count;
case 22 remains incomplete at its original timeout. Case 20's noncanonical
surface and earlier failures remain visible. This satisfies the approved
at-least-22-of-24 threshold with its historical-source/protocol qualifications,
not 22 fresh current-source or first-attempt clean runs.

### Release-owner disposition

The approved engineering acceptance criteria are satisfied with the explicit
qualifications above: focus cases and unchanged-slice comparisons have reviewed
outcomes, critical repeats and handoffs have their earlier qualified evidence,
the legacy threshold and mandatory categories are met, and the repaired storage,
local positive paths and held-out completion have separate prospective receipts.
J05 alone uses the user's explicit case-specific acceptance. No new scientific
acceptance is inferred from software task completion or the lack of a reviewer.
There is no demonstrated unresolved critical source defect in these reviews.

Proceed to committed packaging and exact-tag publication CI. Failed final CI
would block publication and require a new recorded correction; prepublication
checks do not stand in for it. Formal installation must be verified separately
from a clean committed release archive, with the prior version retained for
rollback. The release does not promise universal skill activation, perfect
bounded completion, visual understanding on every backend, or general research
superiority. All private case material and runtime credentials remain excluded.
