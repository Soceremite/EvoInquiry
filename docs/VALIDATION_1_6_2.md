# EvoInquiry 1.6.2 validation

Status: local validation, native-session checks, native Goal/Plan checks and
version preparation passed. This version has not been published. Native testing
used an isolated corrected installation; see the default-installation record
below. The baseline
release is `v1.6.1` at `bbe52387bbf0542d62b6cd8886c9187c573fa023`.

## Changes reviewed

The session resource table supplies a reusable user choice and current capacity
checks through the existing shared principles, planning guidance and execution
owner. The existing launcher and governed queue use that table; resource waits
leave unlaunched work pending and preserve retries. Policy checks do not reset
the action ledger, finite workflow limits, scientific review or STOP intent.
The 89 Codex entrypoints, 88 mainline skills and 83 retained workflows remain.

VERSION and the Codex manifest identify 1.6.2. Only the session resource changes
are assigned new adaptation metadata; historical baselines remain unchanged.
The publication manifest includes the helper, shared references and usage guide.
Both Windows shell CI gates include resource-table and governed-queue modules;
their configuration is not evidence that the native jobs have run.

## Local evidence

| Check | Observed result | Local receipt |
| --- | --- | --- |
| Full regression before the later native-session guidance correction, including resource edge cases and version metadata | 1,410 passed, 39 skipped, 46 subtests passed; no failures; 541.28 seconds | `validation/release-1.6.2/full-suite.xml` |
| Full regression before the final two resource edge cases | 1,408 passed, 39 skipped, 46 subtests passed; no failures | `validation/session-resource-budget/full-suite.xml` |
| Final resource and queue integration, including those edge cases | 45 passed; no failures | `validation/session-resource-budget/final-integration.xml` |
| Version preparation: manifest, package, mirrors, release workflow and contract compatibility | 67 passed; no failures | `validation/session-resource-budget/version-preparation.xml` |
| Resource helper on Python 3.10 before later edge-case additions | 37 passed | Session command output |
| Package preservation and skill inventory at final 1.6.2 | Passed | `validation/release-1.6.2/package.json` and session command output |
| Actual frozen CPU execution repeated on final 1.6.2 | Three first-use choices, fixture choice recorded, 90-minute allocation automatically admitted at planning and launch, process exited 0 and saved its results; one session table | `validation/release-1.6.2/practical-receipt.json` |
| Post-correction resource, queue, mirror and preservation regression | 95 passed; no failures; 36.94 seconds | `validation/release-1.6.2/native-session/guidance-regression.xml` |
| Native fresh-session and continuation behavior after correction | Two independent threads, four completed turns; first choice, reuse, fresh planning and launch checks, CPU outputs and session separation passed | `validation/release-1.6.2/native-session/receipt.json` |
| Final native-mode guidance regression | 95 passed; no failures; 37.17 seconds | `validation/release-1.6.2/native-modes/guidance-regression-final.xml` |
| Actual host Plan and Goal cases | Resource choice and same-thread transition, read-only monitoring and automatic Goal continuation passed | `validation/release-1.6.2/native-modes/receipt.json` |

The full regression used an isolated Python 3.14.7 environment. A pre-test
snapshot fixed 978 source, skill, test and workflow file identities; all remained
unchanged when testing completed. The snapshot, checksums, skip reasons and
summary are in `validation/release-1.6.2/tested-inputs.json` and
`validation/release-1.6.2/test-summary.json`. Targeted checks are included in the
full suite and are not additional distinct passing tests.

Receipts live in the ignored validation directory; they do not contain a real
user's session approval. The CPU calculation was short. The declared allocation
was 90 minutes; no 90-minute training was performed. Live NVIDIA telemetry read
both GPUs without allocating VRAM. A child-process test verifies admitted UUID
visibility, using fixture GPU observations rather than real GPU training.
Skipped tests retain their actual reasons: native Windows semantics and tooling,
missing optional requests/PyTorch/expect support, and unconfigured MiniMax live
API credentials. They are not counted as passed.

Tests cover first choice and reuse, session separation, stable host thread IDs,
concurrent initialization, policy revision during probing, custom changes that
preserve unrelated restrictions, 90-minute and 12-hour approval, GPU allowlists,
sharing and per-device fit, total VRAM, index/UUID aliases, current available RAM,
same-filesystem save peaks, unknown telemetry, read-only planning, preservation
of existing finite budgets, and queue deferral without a process or retry cost.

## Native session validation

A fresh persistent Codex CLI session exposed a conflict between ordinary
planning-only guidance and the resource table's first-use contract. It read the
correct 1.6.2 skill and resource reference, but used a read-only check and
deferred the first choice until launch. No session table was created. That
attempt reached the test's 360-second limit before a final answer; it is retained
as a failed behavior check, not a passing session.

The planning hook and shared resource contract now distinguish the separate
policy record from an experiment runtime. Writable planning initializes the
pending policy and offers the first choice before scheduling. Actual host Plan
mode and read-only restrictions remain in force. The protected mainline file
has a directed adaptation; historical baseline hashes remain unchanged.

The original trace is retained under
`validation/release-1.6.2/native-session/before-guidance-fix/`.
Two intermediate attempts created the correct pending table but continued
preparing plans or implementation interfaces before returning the first-choice
question. They reached the same turn limit and remain partial, not passing,
results in `before-early-choice-fix/` and `before-turn-return-fix/`. The contract
now explicitly ends the first-use turn after presenting the options, resuming
resource-dependent planning after the user responds.
After that correction, two new native threads completed four turns using
`codex-cli 0.164.0`, `gpt-6.1-sol` and `xhigh` reasoning. The original planning
request named no skill or helper. Native discovery verified 89 candidate
entrypoints and 305 runtime/reference inputs, which remained unchanged through
the test. Each attempt used an isolated Codex home with the 1.6.2 development
snapshot.

| Native turn | Observed behavior |
| --- | --- |
| First thread, first request | Loaded the candidate experiment-plan skill, initialized one table under the actual host thread ID, showed three options and ended with selection pending; no experiment started |
| Same thread, fixture user selects maximum available | Selected the existing table once and performed a fresh planning check; the declared 90-minute CPU allocation returned AUTO_APPROVED without another budget question |
| Same thread, requested CPU engineering verification | Loaded run-experiment, reused that table, performed a fresh launch check and invoked the fixed script once; actual exit code 0, six metric rows and 384 predictions matched the fixture reference |
| Second independent thread in the same project | Initialized its own pending table and asked for its first choice; the first thread's selected table remained unchanged |

The choice was a scripted test reply, not a real user resource grant. The CPU
calculation took about 0.25 seconds and created roughly 40 KiB of results; no
90-minute training, GPU training or scientific claim validation was performed.
This checks ordinary native Codex execution and persistent-thread resume, not
host Goal or Plan mode. Results, source identities, full outputs and the retained
failures are under `validation/release-1.6.2/native-session/`.

Post-correction regression passed 95 tests covering resource admission, queue
integration, skill mirrors and package preservation. That focused rerun is
separate from the earlier 1,410-test full regression and is not added to it as a
distinct total.

## Native Goal and Plan validation

The follow-up used the actual `codex-cli 0.164.0` app-server interfaces:
`collaborationMode` selected native Plan/default instructions and
`thread/goal/set` created a native active Goal. It used `gpt-6.1-sol`, `xhigh`
reasoning and the same isolated 1.6.2 package. No provider URL, key or model was
changed. The CLI client name was retained for provider compatibility; a custom
client name had produced a transport refusal before behavioral testing.

Native Plan testing exposed two additional ambiguities. A job's one-core,
128-MiB estimate was treated as an already-selected session policy, and an
intermediate correction recommended custom ceilings ahead of maximum available.
The shared contract now separates job sizing from session policy and keeps
maximum available as the default. Exclusive GPUs are offered when relevant to
the workload. These are shared guidance corrections; no new workflow or
scheduler was added. The failed and partial attempts remain in
`validation/release-1.6.2/native-modes/`.

The corrected native Plan resource case passed: it offered the initial choice
with maximum available first, kept the project unchanged in read-only mode,
created no Goal or resource record, then saved one selected table under the same
thread ID after switching to Default. Its fresh 90-minute CPU request returned
`AUTO_APPROVED` without another budget question.

Native Plan monitoring also passed against a separate, already-running CPU
gradient-descent process: 240 paced steps over approximately four minutes, real
logs and a natural-completion receipt. The observer repeatedly checked process
identity and finite, decreasing loss, verified terminal evidence, and left the
project unchanged without initializing a resource policy. The fixture owner
confirmed exit code 0. A denied `/proc/<pid>/exe` read was recovered by checking
the readable command and process-start identity; it did not stop the training.

The native Goal case passed with one client `turn/start`, two host-started turns
and two completed turns. The first turn reported progress and returned; the host
automatically started the second without a user continuation. Goal status stayed
active while the owned process was alive and reached complete after natural
process exit and terminal verification. The project remained unchanged and the
fixture owner confirmed exit code 0. A prior attempt is retained as partial:
the harness had stopped at Goal completion before collecting the final turn.
The rerun drained both the Goal state and the final response. Two grading defects
were also corrected against retained traces: visible custom-option descriptions
count as part of the choice, and client requests must be counted in the outbound
trace, not the inbound message list. Original grades remain available.

The Goal and Plan monitoring processes each ran for approximately four minutes,
with 240 genuine CPU updates. Tool/model overhead caused some observations to
arrive later than the requested 20–30-second cadence; this was not a strict
real-time watchdog test. No synthetic user continuation, new training dispatch,
GPU work or file-writing authority was needed for observing these existing jobs.

The latest resource, queue, mirror and package regression passed 95 tests in
37.17 seconds with no failures. Its receipt is
`validation/release-1.6.2/native-modes/guidance-regression-final.xml`. Runtime
identity checks compare 305 source, private-package and private-cache inputs.
These results do not establish an hour-long training, native platform portability
or scientific discovery performance.

## Default installation observation

Before synchronization, the default Codex cache identified itself as 1.6.2, but its
experiment-plan hook and resource reference still predated these native-test
corrections. The admission helper matched the working copy. The configured
marketplace source still identified itself as 1.6.1. These observations do not
establish who changed the cache or when it became active. The historical receipt is
`validation/release-1.6.2/native-session/default-installation.json`.

After native-mode acceptance, the default installation was synchronized through
Codex's native plugin marketplace and install commands, using a clean local
1.6.2 development snapshot. The source and cache now identify 1.6.2, and all 305
runtime inputs match the tested working copy. A fresh native `skills/list` with
cache reload discovered all 89 plugin entrypoints without errors. Unrelated
Codex configuration remained unchanged; the previous cache and configuration
are retained in a private rollback backup. The snapshot excludes local
credentials, Git state, experiment state, validation output and build output.

The first source-switch attempt was rolled back: the native CLI requires
removing a same-named marketplace before adding its replacement source. The
retry used that supported transition and passed. Installation and discovery
receipts are under `validation/release-1.6.2/native-modes/default-installation/`.
Private test authentication/configuration copies were removed after testing.
This is an installed local development snapshot, not a published release.

## Remaining scope

Native Windows/macOS checks for 1.6.2 and hour-long Goal/Plan behavior have not
been run. The native mode cases validate approximately four-minute CPU jobs,
not hours of unattended research, UI stall indicators or context compaction.
Platform telemetry outside NVIDIA GPUs may require a target
execution owner's own observations. Shared GPU policy permits use when capacity
and the existing scheduler allow it; it does not add sharing to a scheduler that
still assigns devices exclusively. Capacity sampling does not atomically reserve
resources or guarantee process isolation. Unbound legacy launchers require the
documented integration before they receive these checks. The session owner must
carry the original table root when the session spans project roots.

See the [session table guide](SESSION_RESOURCE_BUDGET_CN.md) and
[shared contract](../skills/shared-references/resource-budget.md).
