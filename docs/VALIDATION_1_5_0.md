# EvoInquiry 1.5.0 validation

**Publication status (2026-10-19):** [EvoInquiry 1.5.0](https://github.com/Soceremite/EvoInquiry/releases/tag/v1.5.0)
is published as the latest stable release from
`16abc3ac47eee77f9daf7584cc964ced0fd1521e`. Four native test gates and the
publication job passed; actual public downloads were verified. Earlier sections
retain their original source-specific development, failure and installation
statuses. The final publication record is at the end. This later documentation
record does not alter the frozen tag or its source assets. The formal local
installation remains last verified at 1.4.0; publication did not replace it.

Development started on 2026-10-18 from `180f7d8ebd6690caa3a77328e9cb2bf5eeeee7ce`
on `feat/bounded-research-v1.5.0`, under the
[approved implementation plan](UPGRADE_PLAN_1_5_0_CN.md). At that point, stable
release metadata and the formal local installation remained 1.4.0. This document is not release
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

At the initial local assessment, native macOS and Windows jobs had not yet run
for this development branch. The later commit-specific CI results are below.
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

The candidate was committed as `9e09c85c20a12a42e867255facf0bdef69a9d962` and
pushed to `acceptance/bounded-research-v1.5.0` before the user's subsequent
instruction requiring local practical experience and explicit permission before
further commits. Its [native CI run](https://github.com/Soceremite/EvoInquiry/actions/runs/39106725110)
completed successfully on all four jobs:

| Job | Public JUnit receipt |
| --- | --- |
| Full suite, Ubuntu | 1,224 passed, 34 skipped, zero failures or errors |
| Full suite, macOS | 1,224 passed, 34 skipped, zero failures or errors |
| Windows, powershell.exe | 364 passed, four skipped, zero failures or errors |
| Windows, pwsh | 364 passed, four skipped, zero failures or errors |

The counts above come from each job's JUnit annotations; they are not added to
local pytest summary counts. A clean archive of that commit contained 1,024
source files and passed package preservation and inventory checks. This is an
acceptance branch, not a release or a merge to main. Stable version metadata and
the formal installed plugin remain 1.4.0.

## Later local practical experience — not committed

A real CLI walk-through executed 16 commands on a local filesystem and launched
the actual three-seed synthetic CPU study. It first reserved an action, recovered
the same reservation without dispatching again, blocked another dispatch,
preserved a deliberately injected process exit 7, and retried under a distinct
action identity. It then recorded measured costs, fixed output identities and
the decision. The original phase stopped at `REVIEW_REQUIRED`; neither its
scientific verdict nor the unsupported original claim became accepted. The
existing decision could be retrieved without creating another knowledge store.

Local scale experience revealed repeated whole-source reads and whole-log
rewrites during event import. The pending fix verifies and atomically publishes
one batch under the existing locks. On one local synthetic trace, 1,000 events
took 4.321 seconds before the change and 0.045 seconds after it; 10,000 events
took 0.414 seconds after the change. Reimports added zero observations. These are
individual local measurements, not portable performance guarantees.

The final local source also passed direct CLI imports of a selected actual native
trace (22 observations, zero additions on reimport and zero invocation assertions)
and synthetic 1,000/10,000-event files. Including interpreter startup, those two
CLI calls took 0.447/0.780 seconds. A separate actual Linux process interruption
after import started left the previous log unchanged; recovery added all 20,000
new observations once, and reimport added zero. This does not simulate power loss.

The pending importer passed 19 event tests, including two cooperating importers,
complete-batch visibility, failed replacement preserving prior history and a
source changing after parsing. The broader local changed-component/package
check passed 111 tests. The final source passed the 19 event tests again after
keeping mutable-log reads inside the writer lock and rechecking the selected
source path before publication. These overlap and are not additive counts. The
new batch fix is outside the earlier native CI commit; it has not been submitted
for a new native platform run.

## Paired native local experience

Eight fresh gpt-6.1-sol/high Codex sessions compared the installed 1.4.0 baseline
and a frozen `1.5.0-dev.2` candidate on two public tasks, twice per variant.
Requests, fixtures, discovery snapshots, model settings, budgets and repetitions
were pinned before execution. The sequential order was baseline, candidate,
candidate, baseline. All eight attempts are retained; none was retried.

| Variant / repetition | X01: analysis, seconds / tools | X02: numerical answer, seconds / tools |
| --- | --- | --- |
| Baseline / 1 | 163.15 / 9 | 48.88 / 4 |
| Candidate / 1 | 141.04 / 10 | 47.05 / 4 |
| Candidate / 2 | 141.28 / 9 | 59.16 / 4 |
| Baseline / 2 | 131.11 / 9 | 30.27 / 4 |

All sessions completed within their execution limits. Parent manual inspection
of all reports and traces found that X01 retained the unsupported original
hypothesis, the signal-feature pivot, three-seed and synthetic-data limits,
actual gain/regression cases, and the distinction between an injected process
failure and scientific evidence. Only `REPORT.md` was added to each project;
the existing evidence and run/review state remained unchanged. Every X02 answer
was the correct `10.4` percentage points, with no project file changes.

Execution success is separate from satisfying the frozen rubric. X01's
predeclared required outcome specified two or three cases, but all four reports
contained six. All four are therefore assessed **FAIL on that concision item**,
while their substantive evidence and scope checks pass. The numeric case limit
was absent from the user-facing prompt, so these failures do not establish a
violation of an explicit user count. The rubric remains unchanged; future
evaluations should communicate output-size requirements in the actual request.
All four X02 attempts are assessed PASS. These are same-family parent
assessments, not independent review.

The actual `compare_candidates.py` CLI consumed the pinned run records and
separate source-bound assessments. It returned `NO_CLEAR_GAIN`: both variants
passed two of four planned attempts, with no paired improvement or regression.
This verdict does not mean all tasks passed or that the versions are equivalent.
An additional omission check retained the planned denominator and returned
`INSUFFICIENT_EVIDENCE` when one observation was excluded. Neither report
authorized landing a patch.

X02 was reserved from candidate changes but remained a public, parent-authored,
unsealed local task. Two tasks and two repetitions do not establish general
superiority, statistical significance or complete autonomous research. These
native sessions used a frozen development snapshot; subsequent importer-only
lock/source-path refinements were checked through the final-source CLI and event
tests, not attributed to that snapshot. The temporary development plugin and
marketplace were removed afterward; the stable 1.4.0 selector remains enabled.

## Research from a vague direction — incomplete acceptance

A later candidate-only experience ran for 3,415.95 seconds (56 minutes 56
seconds), starting with “Can small-data classification be more reliable?” Seven
host-dispatched, fresh gpt-6.1-sol/high Codex sessions continued one project with
a frozen `1.5.0-dev.3` plugin. The ceiling was 60 minutes, two CPU cores, no GPU
and 512 MiB of project artifacts. The host scheduled sessions, enforced limits
and delivered review receipts; this was not an unattended daemon test or a
comparison against 1.4.0.

The candidate framed a calibration-versus-training-label question, implemented
four recipes and revised an initially infeasible development plan after review.
It ultimately executed one real development wave: wine, breast_cancer and
digits, one seed, four methods, 12 completed slots. Each dataset used the same
80-label fitting/calibration pool and 20 independent development evaluation
rows; split recipes used 64 fitting and 16 calibration labels. All 60 evaluation
rows and 240 probability outputs were retained. A separate host readback
recomputed all five metrics and matched IDs for every slot successfully.

Temperature calibration reduced NLL on two datasets but increased it on digits;
the equal-dataset NLL difference against the same split baseline was +0.612183.
The process followed its declared diagnostic branch and stopped that route
within the budget. It examined all samples and supplied three cases with an
explicit selection rule: 57 losses improved, three worsened and all 60 predicted
classes remained unchanged. It retained contrary metric evidence, including
lower digits ECE alongside higher NLL and Brier, and did not select a replacement
method from diagnostic probability transformations. This is a limited negative
development finding, not evidence about the original 100-label claim.

Overall acceptance remains **INCOMPLETE**:

- The first real fit occurred about 51 minutes after the global start. Planning,
  implementation, contracts, records and host handoffs consumed most of this
  small study's budget. Only one training wave and subsequent prediction
  diagnostics completed; repeated autonomous method improvement was not tested.
- Two fresh code reviews reached their limits without final reports. The second
  review's actual interim PARTIAL explicitly allowed limited development, while
  its final verdict remained absent. The final 100-label freeze gate stayed
  open, `execution_ready` stayed false and no outer-test evaluation occurred.
- The run never configured the new continuation controller. Candidate sessions
  read its guidance and help, but runtime limits were enforced by the host.
  This experience does not establish automatic controller adoption.
- An early handoff repeated outdated environment/data observations. The next
  session corrected them. Host-side asynchronous setup, allocation clarification
  and late scoring specifications also contributed to rework; those are not
  attributed solely to the toolkit.

All failed setup attempts, revisions and incomplete sessions are retained. Four
complete turns expose token usage; usage for three interrupted turns and total
LLM billing are unknown. Zero paid cost in fit logs refers only to local fitting.
Dependency versions, origins and module entrypoint hashes matched at closeout,
without claiming a complete content lock. Small public datasets, operational
holdout separation and same-family reviews do not establish general novelty,
scientific acceptance or RSI. The project used about 2.11 MiB, with no residual
project processes observed. The temporary plugin and marketplace were removed;
the stable 1.4.0 installation remains enabled.

The untracked local evidence is under
`validation/upgrade-1.5.0/long-research-experience/`, including a Chinese
experience report, raw native traces, the 167-file project archive and its hash
manifest, a numeric readback receipt and cleanup verification. These pending
records do not authorize submission or release.

## Guided repair after the long experience — bounded local checks completed

The authorized repair is specified in [the detailed plan](REPAIR_PLAN_1_5_0_CN.md).
It extends the existing controller with an original start, a closeout reserve
inside the same wall budget, and read-only selected-source handoff checks. Old
contracts keep their clock and default to no reserve. Review and unresolved
execution gates remain unchanged. Codex hooks route sustained work to these
instructions; advice and short tasks do not initialize a runtime.

The controller and new handoff checks passed 58 local tests. A combined focused
suite passed 121 tests after package preservation was corrected without changing
frozen baseline hashes. Five protected mainline instruction files and the root
ignore file were restored byte-for-byte; Codex hooks, mirrored shared guidance
and fixture-local ignore exceptions carry the changes. A fresh same-family
assumption sweep and follow-up found no undeclared consequential assumptions in
their bounded coverage; both remain provisional, not scientific acceptance.

Three public repair-development cases were frozen before native use, with ready
standard-library inputs, gpt-6.1-sol/high, original public start/deadline and fixed
per-case limits. The first candidate attempt exposed real limitations: G01 failed
before any model event with OS resource error 11 during app-server startup; G02
produced the correct scoped metric review but omitted an early INCOMPLETE report
through its audit route; G03 corrected stale sources without state mutation but
read too much implementation and received a harness time-limit flag despite a
completed turn. None is recorded as an unconditional case pass. Added audit-route
and concise-recovery guidance was tested in a second public attempt, preserving
the same prompts, fixture identities, model and per-case bounds. Sessions ran
sequentially to reduce startup contention; that scheduling change prevents a
simple timing improvement attribution to skill edits.

The second attempt completed G01 in 406.90/420 seconds: two real three-seed
synthetic fits, action claims and terminal evidence, original-clock accounting,
adverse cases, a justified stop, unchanged pending gates and a current handoff.
A separate parent arithmetic readback and fresh same-family reviewer matched the
saved predictions, sample pairing, MSE values and fixed references. G02 completed
in 158.95/240 seconds, creating its report before substantive checks and delivering
the correct scoped verdict with unchanged reviewed inputs. The parent observed
its initial INCOMPLETE text; raw CLI events preserve creation/update ordering but
omit patch contents, so an independent reader cannot recover that initial text.
The fresh reviewer records that provenance limitation explicitly.

G03 again reached its ceiling: the turn was observed at about 240.40 seconds and
the harness retained time_limit at 240.43 seconds, although the recovery artifact
and unchanged sources were verified. Its time acceptance remains incomplete.
A final dev6 attempt changed only recovery guidance to save a minimum useful
finding/change/blocker/next-step report after the first source check and reuse
that check's current snapshot. It retains the same public G03 request, inputs,
model, 240-second ceiling and 24-tool limit. It completed in **160.27/240 seconds**,
using 8/24 tool actions, with no limit
flag or variant mismatch. Only RECOVERY.md changed; the run and all seven input
identities matched the frozen fixture. It retained STALE, the unresolved
reservation, expired original execution budget and pending review gates, with
no duplicate launch or replacement contract. All seven attempts across the
three development snapshots remain archived; no further retry was needed. A fresh
same-family independent behavioral review supports these bounded checks and
records no concrete deficiencies within its coverage, while retaining the G02
initial-text provenance limitation and its provisional review status.
The new handoff test is also added
to both ordinary and release Windows job lists; 47 post-change package/CI tests
pass. New runtime guidance does not alter controller source or claim general
research improvement.

The full suite's system-Python attempt stopped during collection because Python
3.10 lacks tomllib used by the existing behavior runner. Its output is retained.
A subsequent isolated Python 3.14.7 environment, built from repository test
requirements, passed the complete suite: **1,259 passed, 38 skipped, 46 subtests
passed**, with three existing deprecation warnings in 508.19 seconds. Focused
counts overlap and are not added to that total. No shared training environment
is changed. New native Windows/macOS checks have not run. G01/G02 were exercised
on dev5; only G03 was rerun on the final dev6 recovery-guidance change, while
controller source stayed identical. Raw evidence is retained locally under
`validation/upgrade-1.5.0/guided-repair/`; all work remains uncommitted and stable
installation remains 1.4.0. Temporary dev4/dev5/dev6 plugin selectors, marketplaces
and caches were removed; cleanup.json verifies the stable 1.4.0 plugin remains
enabled and all evidence is preserved. These public synthetic cases do not establish long-term
autonomy, novel research, general improvement or RSI.

## New vague direction — real image-classification study, incomplete acceptance

A subsequent experience started from a new unimplemented direction: making a
small image classifier robust to missing or perturbed inputs while controlling
inference cost. The unchanged dev6 candidate received 1,437 supplied digits
development samples, an existing interpreter and resource limits, without a
provided implementation, treatment or expected numeric result. The 360 outer
samples were unavailable by the operational protocol; this was not a sealed
holdout or a novelty assessment.

The first attempt's temporary output became unavailable after continuation,
before the host had durably archived its raw results and terminal receipt. Its
cause is unknown. Previously observed reports and cases are retained only as a
secondary record. That attempt remains `INCOMPLETE_EVIDENCE_LOSS`; this host
preservation failure is not attributed to the candidate. A separate public-case
replication retained the same source, prompt, rubric, model and per-attempt limits,
with continuous durable copying. It cannot retroactively pass the first attempt
or be described as blind evaluation. All 67 final raw files matched the terminal
source inventory; all 1,044 frozen candidate files were unchanged.

The replication used gpt-6.1-sol/high, 900 seconds, 80 root tool actions, at most
24 fits, two CPU threads and 64 MiB of project artifacts. It reached the time
limit at 900.08 seconds with 30 root tool actions and no completed native turn.
The original research clock was retained. First model execution was created at
778.94 seconds: preparation, implementation and review still consumed most of
the available time.

The candidate froze a stratified 862/287/288 train/validation/confirmation split
and compared clean, missing-only, noise-only and mixed training under equal
presentation budgets, fixed MLP architecture and three training seeds. All 12
fits completed their fixed 100 epochs, with 7.775 seconds of fitting and retained
nonconvergence warnings. Independent host readback verified 24,108 validation
predictions, all sample/label pairing and 36 reported metrics. The declared rule
selected mixed training: corrupted accuracy improved by 4.123 percentage points,
while clean accuracy declined by 1.161 points. This is a selected validation
finding; confirmation, uncertainty and measured latency remain untested.

Two generated-adapter API errors were observed. An unavailable `inspect_run`
import was corrected. After successful training, the adapter used the
object-only `read_record` helper on a list-valued attempts file. This raised an
error before action settlement: the training subprocess is completed, the outer
management command failed, and its 12-fit reservation remains unresolved. The
read-only controller correctly reports `RECONCILE` without permitting a duplicate
launch. The host preserved this state rather than manufacturing a successful
closeout. These are generated integration errors; the observation also motivates
clearer supported setup examples and zero-fit result/settlement contract checks.

The code-review artifact documents and corrects two real persistence/gate
defects, and its source hashes match. The captured root trace does not establish
the claimed separate reviewer invocation, so reviewer independence is not
certified. The directly constructed environment record demonstrates import
identity and readiness only, not complete registry promotion or environment
acceptance. No shared dependencies were changed.

No native REPORT.md, handoff, confirmatory execution or proactive case analysis
was delivered. Parent-only inspection subsequently retained favorable and adverse
validation cases: in one fixed 287-sample condition, 18 improved, four regressed,
46 remained wrong and 219 remained correct. That zero-fit, zero-inference
readback does not count as native case-analysis acceptance. Overall acceptance
is **INCOMPLETE**. No further experiment was added to make this attempt pass.

The Chinese assessment, protocols, both attempt records, final raw archive,
numeric verification, case images and cleanup receipt are retained locally under
`validation/upgrade-1.5.0/fresh-direction-experience/`. The temporary plugin and
marketplace were removed and the stable 1.4.0 installation remains enabled. This
candidate-only public experience provides no matched superiority, long-term
autonomy or release-acceptance claim. No commit, push or release was performed.

## Compact continuation repair — 2026-10-19

Following that experience, the pending candidate keeps general decisions in
shared guidance and moves execution reconciliation into the existing controller.
The shared continuation reference shrank from 1,888 to 1,287 whitespace-delimited
English words (218 to 142 lines). Across that reference and eight affected Codex
entrypoints, the reduction is 1,040 words. No skill entrypoint was added.
Instructions favor existing runners, a zero-cost adapter check before costly
dispatch, early useful reports and the existing environment/review boundaries.
Dataset, model, seed-count and task-specific protocols remain project decisions.

The public `settle-execution` command verifies a registered terminal execution
against its action's pre-dispatch snapshot binding, preserves observed accounting
and supports repeated identical settlement after interruption or budget expiry.
Scientific payloads retain their own formats. It launches no job and advances no
scientific gate. Regression coverage includes real child success/failure/timeout,
list-valued outputs, changed or mismatched evidence, expired budgets and two
cooperating recovery processes. The complete Linux suite passed **1,269 tests,
38 skips and 46 subtests**, with three existing warnings in 468.92 seconds.
Package preservation and inventory checks also pass. The generic skill validator
passes seven changed entrypoints; experiment-audit retains a pre-existing
`argument-hint` frontmatter incompatibility also reproduced on stable 1.4.0.

A fresh gpt-6.1-sol/high context used the explicit working-tree skill path to
recover one existing arithmetic execution through the public CLI. Host readback
verified its terminal/input/output references, list-valued observations, original
clock, single action, pending phases and `CURRENT` handoff. All 46 project files
were durably archived. This tests scoped recovery, not installed discovery or a
new research study. Exact agent start/end and complete tool counts were not
captured under an enforced cutoff, so acceptance against the declared
420-second/24-action ceiling is **not certified**. Early-report creation ordering
is also not independently certified. The earlier incomplete study verdicts remain
unchanged; no new native macOS/Windows or general-autonomy acceptance is claimed.

Raw checks and the qualified assessment are retained locally under
`validation/upgrade-1.5.0/compact-repair/`. All repairs remain uncommitted;
stable version metadata and the installed plugin remain 1.4.0.

## Interface and closeout follow-up

The user clarified that initial environment and implementation setup is expected;
its cost alone does not establish recurring overhead. Warm-use efficiency still
needs observations. The pending follow-up makes code-side docstrings explicit
for parameters, input/output shapes and returns, and strengthens existing wave
closeout, reviewer-source provenance and host-enforced assessment guidance.
Only existing hooks/shared references and a CLI parameter explanation change;
original workflow bodies and frozen baseline digests remain intact. The public
U01/U02 development cases cover a small scientific utility and an existing pilot
handoff. The focused package/execution/controller/handoff/native-runner checks
passed **152 tests**. Later conditional code-contract links in ablation and
automatic-revision entrypoints passed **44 package/mirror tests**; these overlap
the earlier run and are not additive coverage counts. No original workflow body,
frontmatter contract or frozen baseline digest was replaced.

Three fresh gpt-6.1-sol/high native sessions used a frozen dev8 package, with
source/discovery identities checked and host-enforced monotonic limits of 300
seconds and 24 native tool actions per case:

| Case | Observed time / actions | Assessment |
| --- | --- | --- |
| U01, scientific utility | 81.31 seconds / 9 | PASS within scope: parameter/shape/return docstrings match the implementation; supplied checks and five independent numerical shape readbacks pass; only function/report changed. A git-status probe failed in the non-repository fixture and remains in the trace. |
| U02, existing closeout | 90.32 seconds / 8 | PASS within scope: preserves the supported synthetic validation difference and adverse case, missing outputs, pending gate and unverified labels. It reads the unchanged research-guide, so its success is not attributed to new audit/manager hooks. |
| U03, explicit audit and manager | 102.65 seconds / 10 | PASS within scope: reads both requested changed entrypoints, recomputes all four paired examples and delivers the source-bound report without rewriting inputs or granting acceptance. |

U03 is a separately frozen additional routing check on U02's public fixture,
not a retry, held-out result or matched comparison. All reports and raw traces
are durable. Host polling observed U01/U02 report bytes before session completion;
it does not independently establish every earlier version or initial report
ordering. The later link-only changes are outside the frozen native package and
were structurally checked separately. Generic skill validation preserves any
frontmatter incompatibility also reproduced on stable, rather than deleting
existing metadata to satisfy that validator.

These tests establish limited interface and handoff behavior, not full multi-wave
scientific closeout, warm-run speed, novel research or independent acceptance.
Earlier incomplete/time-limit verdicts remain. Receipts live locally under
`validation/upgrade-1.5.0/interface-closeout-followup/`. The temporary evaluation
plugin/marketplace is removed after checking; stable remains 1.4.0 and all repairs
remain uncommitted.

## Multi-wave warm-project continuation — 2026-10-19

A frozen `1.5.0-dev.9` candidate completed a real four-wave continuation of the
existing digits robustness project. The gpt-6.1-sol/high main session finished
normally in **2,181.58 seconds (36 minutes 21.58 seconds)** with 74 root tool
actions, no execution limit or service errors, and no detected variant mixing.
All 88 installed entrypoints were discovered and all 1,053 frozen candidate
files remained unchanged. This public candidate-only task reused existing data,
code, weights and a numerical interpreter; it is not a comparison against 1.4.0
or a fresh vague-direction study.

The user-authorized follow-up had a new run and clock after an external execution
environment interruption. The first attempt remains a host infrastructure abort
after about 594.84 seconds: the provided review adapter had Python-version and
sandbox-write problems. The second remains `INCOMPLETE_EXTERNAL_INTERRUPTION`:
only its last per-file observations survived, without a terminal native receipt.
The successful follow-up preserves both attempts and the old unresolved run
byte-for-byte. It does not reset an expired clock or retroactively pass them.

| Wave | Evidence-driven question | Actual execution and retained result |
| --- | --- | --- |
| W1 | Does the validation-selected original method meet the frozen internal confirmation criteria? | Reused original weights, zero fits. Primary gain +3.723pp, conditional paired-sample 95% interval [2.373, 5.093], clean difference −0.116pp, forward-only median latency ratios about 0.998. Point thresholds pass; the interval does not guarantee a gain of at least 3pp. |
| W2 | Can replacing one augmentation view address poor block robustness, and at what cost? | Nine fits, equal architecture/presentations/100 epochs. Original mixed replay matches all saved arrays. Validation selects the structural candidate; block robustness improves +21.219pp while noise25 and the original primary decline −9.954/−5.671pp. |
| W3 | Does that tradeoff persist under new matched training seeds? | Twelve fits, including newly trained controls at seeds 44/55/66, with the prior candidate fixed. Block gain +21.489pp, noise25/original-primary losses −10.340/−6.308pp. All six observed seeds retain the tradeoff direction. |
| W4 | Does the structural gain transfer to other equal-area shapes and positions? | Zero fits, 42 mask slots, 72,576 predictions. Gains vary across shapes and some positions regress; equal erased area leaves foreground intensity unmatched. No pure topology mechanism is inferred. |

Later waves explicitly use exposed evaluation data and remain exploratory.
Selection uses validation; the new three-condition objective is distinguished
from the original primary. Uncertainty resamples 288 original samples after
averaging seeds/draws within sample, conditional on this split and fixed models.
The study stops after resolving the adjacent boundary question, leaving 27 fit
slots unused. It does not keep tuning exposed evaluation to obtain a winner.

Separate parent programs, without importing the study's inference or analysis
functions, reconstructed **376,272 saved predictions** from supplied pixels and
actual weights and checked frozen grids, true labels, selection, exact replay,
162 mean metrics, 123 paired contrasts/intervals and 24 paired case entries.
The records comprise 252,288 evaluation and 123,984 validation predictions, not
that many independent samples. Proactive case panels retain ordinary, improved,
regressed and shared-failure cases with explicit pools and selection rules.

All 21 new fits completed 100 epochs; their measured fitting wall time sums to
9.860 seconds, with a maximum of 1.672 seconds and nonconvergence warnings
retained. The 12 historical fits are separate. All 12 current research actions
are settled: ten succeeded and two review calls failed at their limits. The old
run's reserved/unknown action remains unresolved. Source snapshots, terminal
receipts and accounting pass parent readback. The project occupies about
18.91 MiB; 492 final archived files match, and a fresh check of 81 selected
handoff identities returns `CURRENT` with continuation `STOPPED`.

The final evidence review completed with a scope-only PASS and no material
scientific correction. It is same-family provisional review, not independent
scientific acceptance; scientific phases retain that qualification. Two earlier
reviews timed out despite COMPLETE prose and were not accepted as gates.
Narrower interface reviews then completed in 112.787 and 100.696 seconds; the
final result review took 212.832 seconds. This is a remaining scope/time-management
concern, not evidence assigning sole blame to the model or skill. First scientific
dispatch occurred about 896 seconds into this warm session, including evidence
rechecks and failed reviews; it is not attributed to cold environment setup.

Function-level interface documentation also remains inconsistent: the modified
diagnostic routine has a module explanation but no parameter/return docstring.
That source observation is outside the frozen success rubric and is not a
numeric failure. Broader documentation compliance still needs verification.

Overall, the follow-up passes its bounded multi-wave behavior and deliverable
checks. It does not establish general superiority, independent discovery,
cross-dataset generalization, autonomous recovery without host support, or
unattended research over hours or days. No new GPU, network or dependency work
was used; model billing is unknown. Raw protocols, all attempts, parent checks,
the Chinese assessment and the actual report/decisions/handoff remain under
`validation/upgrade-1.5.0/multiwave-retest/`. Temporary plugin/marketplace/cache
and test trust entries were removed; original configuration semantics and the
enabled stable 1.4.0 install were verified. No commit, push or release was made.

## Scoped review and interface follow-through — 2026-10-19

The multi-wave observations above motivated two narrow shared-reference repairs,
mirrored to the mainline and Codex surfaces. No new skill, schema, universal
timeout or protected workflow body was introduced. Reviews now explicitly size
their scope to the pending decision, preserve uncovered cross-interface checks
when split, and finish once required coverage is met. Implementation guidance
adds a function-local contract check before the first consumer or handoff for
changed scientific code; it reuses the existing parameter/shape/return contract
rather than adding a longer checklist or cleaning up untouched helpers.

One fresh gpt-6.1-sol/high context reviewed the actual four-file patch and source
observations. Its same-family provisional recommendation found no blocking issue
(P1 8/10, P2 7/10); these scores are patch judgments, not scientific acceptance or
measured improvement. The evidence remains one multi-wave study, not five
independent completed workflows. Its five review traces yield 94 normalized
observations and three completed native turns; the other two calls retain their
actual host time-limit outcomes. An initial import was correctly refused by the
authoring filesystem's lock-exclusion guard; import then succeeded on a local
temporary filesystem. That infrastructure observation adds no durable skill rule.

The frozen `1.5.0-dev.10` practical test discovered all 88 canonical entrypoints
and retained all 1,064 candidate file hashes. Fresh native sessions saw only the
requests, fixtures and public execution budgets, with gpt-6.1-sol/high pinned:

| Case | Observed time / actions | Actual outcome |
| --- | --- | --- |
| V01, forecast diagnostic | 141.83 seconds / 10 | Completed within 300 seconds; changed only the scientific routine and requested handoff. Its local docstring covers shape, masking, weights, returns, empty inputs and errors. Supplied consumer checks pass, and the untouched helper is unchanged. |
| V02, direct scoped review | 111.49 seconds / 9 | Completed within 240 seconds; wrote only REVIEW.md. Recomputes weighted MAE 3.8 → 2.2 while retaining far-horizon regression 3.0 → 5.0. Missing ingestion/adapter evidence remains pending; no whole-system or independent acceptance is claimed. |

Both sessions read the respective changed shared reference through canonical
installed paths, completed their native turn and had no time, action or service
limit. Parent readback verifies unchanged supplied sources and an additional
40 generated inputs: direct weighted-row calculations, non-mutation, duplicated
samples, translation/scaling and horizon counts/errors (478 assertions, not 478
independent tests). It does not exhaust numeric types, extreme overflow or all
possible callers. The initial stub's expected consumer failure and two failed
Git probes remain in V01's trace; its final numerical checks pass.

Package, mirror, overlay and preservation checks passed **66 tests** in 44.97
seconds. The system quick validator accepts research-review but rejects the
unchanged `argument-hint` field in research-implement-feature; the same rejection
and identical frontmatter are reproduced on stable 1.4.0. Native discovery and
repository contracts accept the retained metadata; it was not deleted to satisfy
the generic validator.

This is limited candidate-only forward use and same-family artifact assessment,
not a matched speed comparison, a reliability estimate, a repeated large formal
review or full 1.5.0 release acceptance. No new macOS/Windows CI was run. Local
receipts, failures, patch backups, review and reports remain under
`validation/upgrade-1.5.0/review-interface-repair/`; public V01/V02 fixtures are
available under `tests/behavior/`. The temporary plugin and marketplace were
removed, original configuration semantics were restored, and the enabled formal
installation remains 1.4.0. No commit, push, release or formal replacement occurred.

## 1.5.0 submission checks — 2026-10-19

The user authorized committing 1.5.0 after the practical follow-ups above. VERSION,
the Codex manifest, both READMEs, changelog and bilingual release notes now identify
1.5.0. The final submission tree retains the same runtime and Codex skill/reference
bytes as the frozen dev.10 forward-use candidate; publication metadata and
validation documents are updated separately. No additional skill is introduced.

A fresh isolated Python 3.14.7 Linux environment ran `python -m pytest tests/ -q
-rs --junitxml=validation/release-1.5.0/full-tests.xml`: **1,269 passed, 38 skipped,
three warnings and 46 passing subtests in 1,072.62 seconds**. There were no failures
or errors. The XML SHA-256 is
`219bc55d71d55282802b63ad459c87f55e27d1220b2896c72b2da586336dfab6`.
Counts overlap the earlier focused runs and must not be added to them.

Skips cover native Windows behavior, unavailable requests/PyTorch/expect and
unconfigured MiniMax live tests; they do not demonstrate unavailable GPUs.
The warnings concern two existing queue UTC calls and intentional legacy-state
deprecation. This Linux run does not certify native macOS or Windows execution.
New-commit native CI remains pending submission, separate from the passing
ancestor checks above.

Package preservation and inventory checks pass with 88 Codex entrypoints, the
frozen original 83-workflow/450-resource baselines and explicit directed
adaptations. Release-note wrapping and staged-file publication checks pass.
The public synthetic fixtures include their two named recovery-state JSON files;
real local validation, credentials, model weights and experiment state remain
excluded. Raw local receipts are retained under ignored
`validation/release-1.5.0/`. Submission, release publication and installation are
distinct actions; the formal installation still remains 1.4.0 at this checkpoint.

## Native publication failure and checkpoint repair — 2026-10-19

Submission `7003c6000ea907cd016f44d369c05814194c0b97` passed all four
[native CI jobs](https://github.com/Soceremite/EvoInquiry/actions/runs/39235374741):
Ubuntu and macOS each reported 1,273 passed / 34 skipped, and each Windows shell
reported 413 passed / four skipped. The user subsequently merged it as main
`f49380777c8f54c8ebc3c286007f6219c7e5ea63`, whose tracked tree is identical and
whose normal CI also passed. These observations did not eliminate an intermittent
checkpoint cleanup race.

The first `v1.5.0` tag run
[failed](https://github.com/Soceremite/EvoInquiry/actions/runs/39237501171).
Windows `powershell.exe` reported 412 passed, four skipped and one failure: the
monitoring/publisher test's child process hit native WinError 32 deleting an old
`state.json` while a status reader held the file open. Linux, macOS and `pwsh`
passed; publication was skipped and no Release was created. The original failed
job and its exception annotation remain available. A successful rerun alone is
not used as a fix.

The existing one-second Windows I/O retry is now also used during journaled
artifact removal. Deletion retries only native sharing violation 32; general
access denial, errno-only errors, unrelated failures and POSIX errors propagate.
Partial deletion retains its journal entry until removal succeeds. An exhausted
retry still reports the error, preserving the committed newest recovery points
and the journal for a later explicit retry. There is no change to checkpoint
formats, retention counts, storage budgets or skill entrypoints.

Six deterministic regression cases exercise real publication and cleanup with
controlled OS failures. Against the original source, two fail as expected: a
transient sharing failure aborts rotation, and persistent sharing has no bounded
retry. The other four error classifications pass. With the repair, checkpoint
and comparison-archive checks report **85 passed / two skipped in 13.64 seconds**.
A Windows-only test additionally holds an actual checkpoint file open in another
thread, observes the native sharing error, releases the handle and checks that
rotation finishes with both newest recoveries intact. Its native result remains
pending CI at this checkpoint; Linux simulation is not native Windows evidence.

Full regression against a local-filesystem snapshot reported **1,274 passed,
39 skipped, one failed, three warnings and 46 passing subtests in 1,025.99
seconds**. The 1,064 tracked files matched the authoring tree at dispatch;
subsequent note and validation-record edits are separate. The failure was
`test_ping_progress_and_cancel_while_child_runs`, which received no first progress
message within its existing three-second queue wait. The bridge and test bytes
are unchanged from the earlier passing source. A separate unchanged invocation
of all seven bridge tests passed, including seven subtests, in 13.06 seconds.
That recheck does not rewrite the failed full run or establish the cause or
frequency of the timeout. Both raw receipts remain.

The repaired checkpoint cases pass locally; native Windows and complete native
Linux/macOS suites remain required for the repair commit and publication tag.
The initial tag is still unpublished and will be updated after repair validation.
The formal installed plugin remains 1.4.0.


## Verified stable publication — 2026-10-19

The checkpoint repair was committed as
`16abc3ac47eee77f9daf7584cc964ced0fd1521e` and pushed directly to main.
[Normal CI](https://github.com/Soceremite/EvoInquiry/actions/runs/39241073667)
passed all four native jobs. The original unpublished tag was then updated using
an exact expected-ref lease after confirming that no 1.5.0 Release existed.
The first failed publication remains in Actions history; no published release
or main history was rewritten.

The final [tag workflow](https://github.com/Soceremite/EvoInquiry/actions/runs/39241625001)
repeated the four checks and published successfully. Ubuntu and macOS each
reported **1,279 passed / 35 skipped**; Windows powershell.exe and pwsh each
reported **420 passed / four skipped**, with no failures or errors. Both native
Windows gates include the real held-file sharing test and the cooperating
monitor/publisher test. These are platform-specific software checks, not a
guarantee against every storage failure or new scientific acceptance.

[EvoInquiry 1.5.0](https://github.com/Soceremite/EvoInquiry/releases/tag/v1.5.0)
was published at **2026-10-19T11:06:31Z** as a stable, non-draft release and
confirmed as Latest. Actual public tar.gz, zip, SHA256SUMS and manifest downloads
were checked. Their checksums agree, both archives contain the same **1,064
files** as the locally built committed source, all **88 Codex entrypoints** are
present, private runtime state is excluded and the release body matches the
bilingual source notes. Raw transfer attempts and verification receipts remain
under ignored `validation/release-1.5.0/`.

The source and validation records retain the initial Windows publication failure
and the later local Python 3.14 three-second Grok progress timeout with its passing
unchanged seven-test recheck. Neither is retrospectively marked passed. Final
Python 3.12 native checks establish publication acceptance for their stated
scope, without assigning a cause or frequency to the local timeout. Earlier
scientific limitations remain. This post-publication record changes documentation
only; the published tag and assets remain fixed at the release commit above.
