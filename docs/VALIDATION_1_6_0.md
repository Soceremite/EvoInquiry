# EvoInquiry 1.6.0 local validation

This record distinguishes local implementation evidence from publication and
scientific acceptance. The implementation uses the existing workflow owners,
run-state coordination, iteration ledger and review gates. One skill is added:
`problem-synthesis`; none is removed. Inventory: 89 Codex / 88 mainline skills,
83 frozen retained workflow records and 450 protected-resource baselines.

The latest follow-up passed **1,349 tests** and observed two actual native-model
decisions from real CUDA outputs: **REPLAN**, followed by **STOP** reaching an
active owned process. Full-state recovery then passed with a normal process
exit. The supplemental window closed after **43 minutes 52 seconds**, retaining
its original one-hour cap and all failed attempts. This is constructed, guided,
same-family provisional evidence; detailed scope and failure records follow.

Before the latest stop/control changes, functional consolidation passed **1,331 tests**, with
36 skipped and 46 passing subtests. A separate real CUDA training loop completed
**3,600.004 seconds and 2,145,720 optimizer steps**, followed by the declared
fault stop and full-state replay checks. The final section records the evidence
and its limits. The subsequent stop/control implementation and supplemental
observation are recorded separately below; the earlier suite is not a test of
those later changes. A universal default emergency watchdog remains outside
the implemented local control bridge.

## Verification record

Local checks on 2026-10-21 use Python 3.12.14, pytest 9.1.1 and installed
PyTorch 2.8.0+cu126 from an existing environment, without a dependency upgrade. The default Python lacks pytest; a separate
existing test interpreter was selected, with fixtures/subprocesses using that
same interpreter. Test output and local model artifacts are retained
under ignored `validation/v160/`; public synthetic inputs are under
`tests/behavior/v160-fixtures/`.

| Check | Observed result | Scope |
| --- | --- | --- |
| Focused reflection, ledger, packaging, mirrors and version contracts | 98 passed in 24.62 s | Gate ID/kind/phase, deferred/blocked decisions, revised-plan identity, append-before-save recovery, UTF-8 CLI from another working directory, no implicit run initialization, three actual CPU waves and frozen contracts. This run preceded the final mainline routing correction; a rerun is recorded below. |
| Controller, recovery, behavior harness, review overlays, release workflow and groups | 108 passed in 91.23 s | Existing continuation, selected handoff identities, overlay compatibility and CI wiring |
| Initial full Linux run | 1,302 passed, 36 skipped, 1 failed, 16 setup errors; 46 passing subtests, 961.07 s | All failure/error paths were the unsynchronized protected DSE file adaptation while integration was still being edited; they are not counted as passing. Adaptation was corrected and packaging retested. |
| Full Linux run before functional consolidation, frozen source | **1,325 passed, 36 skipped, 0 failed; 46 passing subtests**, 970.22 s | Complete `tests/` suite after the routing and packaging-fixture repairs; three deprecation warnings remain. The later consolidation result is recorded below; counts are not additive. |
| Inventory and package verifier | PASS | 89 discoverable Codex entrypoints; retained baselines and shared references resolve |
| New mainline and Codex skill validators | PASS | Skill names/frontmatter, no unfinished scaffold |
| Compile and whitespace checks | PASS | Changed Python modules and `git diff --check` |

A subsequent full run was intentionally interrupted after 238 passing tests to
fix a cross-runtime routing defect: ordinary checkpoints suggested the Codex-only
`research-guide` to mainline installations. They now return `skill: null`, leaving
ordinary reflection with the active owner. The interruption is not a completed
suite or a failure of a research experiment. The focused rerun after that correction passed all 98 checks in 22.64 s.
Earlier counts are not additive.

A later rerun was stopped after a real packaging-fixture regression appeared:
371 passed, 3 skipped and 21 setup errors in 201.05 s. The comparison-package
fixture had not been updated to copy `REQUIRED_REFLECTION_RESOURCES` when that
list was split from earlier research resources. Its copied package correctly
failed verification. The fixture now includes those resources; this run is not
counted as a passing full suite. The affected comparison/reflection/package set
then passed all 78 checks in 20.02 s. The final full command uses command-local
`OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2`
and `python -m pytest tests/ -q -x --junitxml=<local-receipt.xml>`; the thread
settings affect only these test processes.

That pre-consolidation full run completed successfully on unchanged implementation and test
sources. Its JUnit receipt is retained locally as `validation/v160/final-suite.xml`;
`validation/v160/final-source.json` records the checked source identities. The
three warnings are the existing queue `datetime.utcnow()` deprecation (twice)
and the deliberate legacy `.aris` read warning. Skipped checks are not counted
as passed and do not establish native cross-platform acceptance.

## Observable control-flow behavior

- A requested checkpoint blocks new dependent claims, while actual process
  reconciliation, budget exhaustion, original review and closeout retain priority.
- Reflection envelopes cannot overwrite stale counters. The existing structural
  pivot at two stale iterations and human escalation at four remain intact.
- Each gate has a fresh identity; old records and identical timestamps cannot
  release a later gate. Retries after a ledger append reuse the same content ID.
- `DEFER` / `BLOCKED` retain the brake. Merge/pivot/replan await a fixed revised-plan
  handoff. Ordinary later reflections retain that active plan's SHA identity.
- The three-wave integration uses the existing CPU study runner for real
  closed-form fits and held-out outputs: negative result, programmed pivot and
  positive control, with twelve fits accounted for. It exercises repeated
  checkpoints, reservation recovery, plan handoff and stopping without changing
  phases or accepting a scientific claim. The decisions are programmed, not LLM
  discovery, and the study is short rather than a multi-hour research run.

## Fresh-context forward use

A fresh `gpt-6.1-sol/high` agent was given the candidate skill, two existing
practice runs and raw synthetic CSVs, without the intended answers. The tables
were actually calculated before the model task: two groups, five seeds, four
variants and 150 evaluation samples per row. The model did not run training.
Each practice run recorded one reflection through the real public CLI.

| Case | Recorded behavior | Limit / remaining state |
| --- | --- | --- |
| T01 | Provisional `MERGE`: both groups' mean RMSE 0.605124 → 0.081511 under the centering intervention. It identified that A/B were identical and retained the null comparisons. | A/B are duplicated evidence, not independent replications. The revised plan remains a draft; the brake stayed `SYNTHESIS_REQUIRED`. |
| T02 | `KEEP_SEPARATE`: A responds to centering; B responds to quadratic capacity, 1.230444 → 0.081656, while cross-interventions do not help. | Reflection brake cleared to `READY`; zero new action reservations, unchanged phases and no scientific acceptance. READY is not resource authorization. |

The agent identified missing sample/split/weight identities and correctly refused
to infer optimizer-duration behavior from the repeated closed-form fit. Its
secondary proposal review actually used `gpt-6-astra/xhigh` and returned
7.25/10, REVISE, same-family/provisional. This was a tool-internal agent, not an
external API call. The agent initially misread the no-external-API limit as also
forbidding a tool-internal reviewer, then corrected that interpretation. The
reviewer missed its stated deadline, and the overall forward task exceeded its
six-minute target. Those timing checks did **not** pass. An earlier sentence in
the raw conclusion says no reviewer was called; its later correction records
the actual call. The timing and report inconsistency are preserved, not counted
as fully successful autonomous execution. No GPU, external API or experiment
was launched by the model.

Public T01/T02 requests are now available to the existing native behavior
harness. They have **not** been run as a matched baseline/candidate or implicit
skill-selection benchmark. The guided forward use above is separate evidence.

## Assumption sweep and repair

A second fresh `gpt-6.1-sol/high` agent reviewed the implementation and stated
assumptions. It reproduced one defect: a later CONTINUE replaced `last_reflection`
and lost the revised plan binding; editing that plan incorrectly left READY.
The repair retains `reflection_plan_ref` in the same coordination record. The
reviewer repeated the failure path and observed `EVIDENCE_CHANGED`; a regression
check covers it. The sweep remains same-family/provisional, not an assertion
that the implementation or research is certified clean.

## Remaining acceptance boundaries

Native Windows/macOS execution and a bounded long-duration model-driven research
trajectory remain unperformed for this candidate. Both Windows CI shell lists
include the new reflection test file. No power-loss guarantee, universal defense
against local optima, general causal validity, automatic skill-selection rate or
full RSI capability is established by these checks. No commit, push, release or
stable installation replacement was performed as part of this work.

## Follow-up: real CUDA stop behavior and functional overlap

The subsequent [boundary and brake assessment](AUDIT_1_6_0_BOUNDARIES_AND_BRAKES_CN.md)
records two actual H100 training attempts with million-step targets, finite
checkpoint restoration and controlled process termination. Explicit signals
and the configured 180-second launcher timeout stopped the owned process groups;
reflection requests and `research_control.stop` did not interrupt active training.
Fast NaN observation was supplied by the disposable test supervisor, not an
existing autonomous watchdog. This is bounded fault-injection evidence, not the
still-unperformed hours-long model-driven trajectory. Production sources were
unchanged. A unified default emergency-stop chain remains an identified gap.

## Functional consolidation and hourly run

The follow-up requested three functional refinements before an hour-scale local
training witness. The three review-loop entrypoints now share one cycle/recovery
reference while retaining their reviewer backends and additional gates. An old
timestamp triggers reconciliation rather than deletion or a new round budget.
Both review overlays use the same recovery rule. The deprecated poster name
forwards its unchanged arguments to `paper-poster-html`; it has no second
rendering workflow. The Codex guide clarifies output ownership and reuses valid
child artifacts instead of repeating composition stages. Invocation policy and
the skill inventory are unchanged.

These refinements and the local endurance witness are complete. Source snapshots,
test receipts and constrained fresh-context forward-use artifacts are retained
under `validation/v160/consolidation/`; terminal endurance evidence is under
`validation/v160/hourly/`. The fault injection, finite-loss guard and supervisor
are disposable test code. They do not establish a product-default emergency
watchdog or a model-driven research trajectory.

The focused consolidation run passed **114 checks in 29.08 seconds**, including
four no-network integration cases: each documented adapter call is validated
against the shipped MCP handler's actual tool schema and delivered user content.
The first sweep reproduced an incorrect `message` argument (the services require
`prompt`) and an omitted external-timer fence. Both were repaired. A second sweep
found that mainline legacy state had lost its missing-backend default; the
original `codex` / `requires_external_acquittal=false` migration is restored.
These are preserved original interfaces, not new acceptance criteria. The sweep
remains same-family/provisional; its two rounds do not certify correctness.

The constrained fresh-context forward use retained the stale review's identity,
pending job and original limits, preserved truncated state without inventing a
replacement, forwarded all poster arguments unchanged, and selected analysis or
problem synthesis according to the requested output. All supplied input hashes
were unchanged. No reviewer API, experiment or poster render ran in that pass;
its blocker handoffs do not establish those services' end-to-end acceptance.

The generic skill-creator validator accepted six of eleven checked entrypoints.
Five were rejected for the **pre-existing** `argument-hint` frontmatter unsupported
by that generic validator. Those frontmatter fields were preserved; the package's
own inventory, mirror and preservation checks passed. This generic-validator
limitation is not reported as an all-green result.

The first warm fixture was rejected before training by the experiment schema's
aggregation enum. The corrected fixture uses `all-attempts`, with no scientific
comparison or ranking. Its eight-second CUDA loop completed 4,818 optimizer
steps, rejected the injected nonfinite loss before backward, and exited 23.
The latest finite state at step 3,965 restored model, AdamW, scheduler and four RNG
layers; two replays to step 3,968 produced identical complete-state hashes. The
failed preflight and actual failed/continued attempts are retained. The 3,600-second
attempt uses the same trainer/supervisor source hashes as the accepted warm run.

An early follow-up full suite was intentionally interrupted for the legacy
backend correction after 191 passing tests, one skip and 39 passing subtests in
60.25 seconds. It is not a completed suite. The final follow-up regression passed
**1,331 tests, with 36 skipped, three warnings and 46 passing subtests in 1,067.36
seconds**. All 971 implementation, skill, test and CI files in the replacement
source snapshot remained unchanged through endurance closeout. Its receipts are
`validation/v160/consolidation/full-suite.xml` and `regression-result.json`.
The final package verifier also passed: 89 entrypoints, 83 retained workflow
contracts and resolved shared references.

| Hour-scale engineering check | Actual terminal evidence |
| --- | --- |
| Real optimizer work | One H100, CUDA float32 synthetic batches and a small MLP; **3,600.003729 seconds, 2,145,720 steps**, with no artificial sleep in the training loop. Peak allocated tensor memory was 69,101,568 bytes. |
| Milestone gates | Three programmed health reviews at 15, 30 and 45 minutes used three fresh gate IDs. Each CONTINUE retained the original phase and resource budget. These were engineering checks, not LLM research judgments. |
| Checkpoint retention | 30 full-state publications; the parent run retained the latest two valid recovery points, **336,100 bytes** total. The test's conservative save-peak upper bound was 569,910 bytes, below the 8 MiB per-store budget. |
| Injected numerical fault | A predeclared NaN after 3,600 seconds was rejected before backward or optimizer update. The guard receipt followed the fault record by about 2.3 ms; the terminal execution receipt followed by about 1.68 s. The actual attempt remained **failed, exit 23**. No supervisor signal was needed. |
| Actual recovery | The latest finite state at step **2,065,798** restored model, AdamW, StepLR, step and Python/CPU/CUDA/data-generator RNG. Two three-step CUDA replays to **2,065,801** produced identical complete-state hashes. No uninterrupted hour-run oracle was captured, so this does not prove equivalence to uninterrupted continuation. |
| Resource settlement and shutdown | Conservative GPU accounting was 3,659.98 seconds against a 4,000-second allowance; the original wall limit was 4,100 seconds. After recovery and settlement the workflow was **STOPPED**, and all four owned warm/hour training and recovery processes had exited. |

The 3,780-second launcher timeout was configured but did not fire in this hour
attempt; its actual 180-second firing belongs to the earlier short test. Another
process shared GPU 0 during part of the run, so this is not an isolated throughput
benchmark. Training and supervisor source hashes matched the accepted warm run.

The finalized local summary is `validation/v160/hourly/observed-summary.json`;
`report.json` retains attempts, milestone receipts, recovery and accounting.
`runtime-evidence/` contains the terminal project copy, with file identities in
`runtime-evidence-sha256.json`. The initial schema rejection and warm attempt
remain preserved. These checks establish bounded Linux/H100 training endurance,
retention and fault recovery for this fixture. Native cross-platform endurance,
large-model or distributed failures, model-driven long research decisions and a
product-default unified emergency-stop chain remain unverified or unimplemented.

## Automatic review and local stop follow-up

The user authorized observing the two missing behaviors: a real model changes
the research trajectory from actual evidence, and a stop decision reaches an
active owned training process. The terminal one-hour record above is immutable.
The supplemental live observation has its own maximum **3,600-second** clock,
including model calls, failures and closeout, and may finish early. It is not
another completed one-hour endurance witness. Implementation and fixture
preflight precede that clock.

Production changes stay in `research_control` and `execution_registry`.
Configured action-count boundaries count settled successes/failures, excluding
cancellations. Configured elapsed boundaries are observed by existing monitor
inspection or before another action claim; they do not add a background service
or call a model from the launcher. A gate requests review without selecting a
verdict. Late results remain unreviewed, and recovery preserves original limits.
The existing bound local launcher polls STOP, identity-bound execution requests
and the original dispatch deadline. Its effective timeout includes the spec
attempt limit. Ordinary reflection does not kill healthy training. POSIX cleanup
targets the launcher's own process group; Windows termination currently covers
the parent only, not a certified descendant tree.

The first focused controller/reflection run passed 82 checks in 197.77 seconds.
A first fixture incorrectly tried concurrent reservations; the original controller
correctly returned RECONCILE. That failed fixture receipt remains preserved.
The next 55-check execution/control run passed in 264.64 seconds. A subsequent
combined run was deliberately interrupted after 48 passes in 304.28 seconds
to repair the assumption review's cancellation finding; it is not a completed
suite. Package verification initially rejected two newly changed protected
mainline hook hashes. The explicit adaptation records now name their current
identities, without changing frozen baselines, and package verification passes.

The same-family assumption sweep found that cooperative SIGTERM save/exit 0
was incorrectly classified as completed. The launcher and terminal validator
now preserve stopped independently of the actual exit code; a real-process
test verifies exclusion from successful aggregation and cancelled settlement.
The execution file then passed all 16 checks in 276.17 seconds. The follow-up
sweep identified the analogous independent-observer recovery path; explicit
`stopped: true` is now retained there, while legacy ordinary exit-0 observations
keep their existing completed semantics. The full current regression passed
**1,349 tests, with 36 skipped, three existing warnings and 46 passing subtests
in 2,402.06 seconds**, including all 19 execution-governance cases. All 192
Python source identities in the pre-run manifest remained unchanged. The JUnit
and summarized receipt are `autonomous-brake/full-suite.xml` and
`regression-result.json` beneath the ignored validation directory. The two raw
sweep reports remain unchanged; the last repair has deterministic verification,
not a third fresh sweep or an independent CLEAN verdict.

The current server has two RTX 5090 GPUs. The older cu126 interpreter detects
CUDA but cannot run an sm120 kernel; this preflight failure is retained. An
existing, unchanged PyTorch 2.8.0+cu128 interpreter passed actual optimizer
updates and four frozen-environment receipt layers. The constructed regression
fixture uses three fixed domains, two initialization seeds, independent fixed
train/validation generators and full per-sample predictions. It is a capability
fixture, not a scientific novelty benchmark or significance test. Warm-up,
live model traces, original decisions, terminal receipts, storage and full-state
replay checks are retained under `validation/v160/autonomous-brake/`.

The first native `gpt-6.1-sol/high` review read the candidate guidance, real
metrics, fixed source and paired cases. It returned **REPLAN**, identifying a
shared representational obstruction: the bias-free odd network cannot model
the two domain offsets. It proposed one bias-enabled comparison matching the
first baseline's 12-second budget. The disposable driver erroneously substituted
900 seconds. That attempt was explicitly cancelled, retained and excluded from
fair comparisons; its cancellation is not a model STOP. The executed driver and
first segment summary are preserved separately. The corrected driver requires
an explicit model-specified duration rather than substituting one.

Continuation retains the original **08:07:10.430180 UTC** start and **09:07:10.430180
UTC** deadline, including the intervening repair time and prior resource costs;
it does not restart another hour. The exact 12-second comparison completed in
12.025 seconds of actual training-loop time. A/B per-seed validation RMSEs changed
from approximately 2/3 to 0.01446–0.01786, meeting the fixture criterion. A separate
paired-case calculation retained the control's mixed results: RMSE improved for
seed 11 but rose from 0.00992 to 0.01048 for seed 22; respectively 114 and 128
of each seed's 256 control cases had larger absolute errors. These are not
grounds for claiming improvement everywhere.
The longer active-stop witness is explicitly engineering-only and excluded from
the matched comparison.

At the elapsed boundary, a second native review verified all 15 frozen evidence
hashes, recomputed the cases and returned **STOP**: the matched comparison had
answered the fixture question, so additional training was unnecessary. The
model call completed in 120.19 seconds. The existing controller recorded that
decision without replacing it; the bound launcher observed `workflow_stop`.
The active CUDA worker saved and exited at step **29,560**, after 237.56 seconds
of its actual loop. Stop intent to actual terminal receipt took **3.505 seconds**.
Actual exit was 0, final status `stopped`, and settlement was cancellation rather
than successful research evidence. The store retained two valid recovery points,
92,276 bytes in total. This observes a real model decision reaching a running
owned Linux job; ordinary review alone still does not terminate healthy work.

The first post-stop replay produced identical full-state hashes at steps
29,560 → 29,563, but its process exceeded the fixture's 35-second bound during
exit cleanup and was stopped with exit -15. The fixture's generic exception
misreported this as a hash mismatch; the actual replay receipt says `identical:
true`. Diagnosis now distinguishes terminal failure from hash disagreement.
The timeout attempt remains preserved and is not an end-to-end recovery pass.
A separately declared recovery retry retains the original start/deadline,
accounts for every preceding action/cost and uses a 90-second process limit.

That retry **passed end to end**: two actual three-step CUDA replays from step
29,560 to 29,563 had the same complete-state hash, and the process completed
normally with exit 0. No trainer or checkpoint format change was required.
The final supplemental observation closed at **08:51:02.815790 UTC**, after
**2,632.386 seconds** on its original clock. Seven actions and a conservative
**781.870 GPU-allocation seconds** were accounted against the original limits
of eight actions and 2,200 seconds. All four live/recovery owners were STOPPED
with no unresolved actions. All ten owned training/preflight/recovery processes
had exited. An unrelated GPU process was left alone.

The final package verifier passed 89 entrypoints and 83 retained contracts;
the three CI wiring tests also passed after both native Windows shell lists
were extended with execution-governance coverage. This is CI wiring verification,
not native Windows acceptance. Whitespace checks passed and the 192 Python file
identities remained unchanged through the final regression and observation.

`validation/v160/autonomous-brake/final-observed-summary.json` aggregates the
actual decisions, original timing, retained errors, terminal/recovery evidence
and resource accounting. `runtime-evidence/` preserves the terminal fixture;
`runtime-evidence-sha256.json` identifies all 248 files. The selected handoff
check returned CURRENT. Prior summaries and the executed driver versions remain
unchanged; the final result does not erase either harness failure.

These observations close the two requested local capability gaps in this
constructed case. They do **not** establish model-driven unattended research for
an entire hour, general protection against local optima, an implicit skill-selection
rate, independent scientific acceptance, or a default cross-platform watchdog.
Existing monitors must observe the configured boundary and the execution must
be bound to the local control contract. SSH, schedulers and Windows descendant
trees still need their own owner-specific execution evidence. No commit, push,
release, installation replacement or training-environment change was performed
during that local implementation and observation stage.

## Publication preparation

Publication was authorized on 2026-10-21 after the practical checks above. The
release preparation updates the bilingual README, natural-wrapping release notes,
changelog date and `release-validation.json` to 1.6.0. Runtime Python sources
remain those of the completed local regression and live observation. Source
assets are built from committed Git files; ignored validation traces, checkpoints,
credentials and local research state remain outside the package. Native CI and
the actual tag, release and public download checks are recorded separately from
the local evidence. Existing installations and training environments are unchanged.
