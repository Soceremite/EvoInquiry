# EvoInquiry 1.4.0 validation

Status: implementation and candidate validation in progress. No 1.4.0 stable
release or replacement of the formal installed 1.3.0 has occurred. A separate
public CI candidate branch is recorded below.
The [approved plan](UPGRADE_PLAN_1_4_0_CN.md) defines the release criteria.
Planned tests are not passed tests.

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
  host discovery and support hashes. CLI: 0.162.1; model: gpt-6.1-sol;
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

## Remaining release gates

The complete native behavior matrix and cross-session handoffs remain
incomplete. The dev.6 local full program suite passes as recorded above; native
platform CI passed on the older recorded candidate commit and must cover the
final changes. The eight completed C attempts now have independent-context
provisional assessment, while their baseline comparison remains outstanding.
Those attempts and the six focus pairs do not replace the full matrix,
remaining original/resource cases, critical repeats, fresh holdouts or handoffs.
The four original-case timeouts remain unresolved until remedial execution and
assessment finish. Release metadata must record actual outcomes rather than
inherit old-version passes.
