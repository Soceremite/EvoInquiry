# 1.6.1 local validation scope

This record covers local validation of the 1.6.1 patch to the published 1.6.0
implementation. It changes existing continuation and monitoring contracts without
adding skills or creating a scheduler. Release CI and publication receipts are
separate from the local checks below.

## Changes reviewed

Complete experimental blocks, rather than individual seeds or retries, drive the
new opt-in review cadence. Explicit null total wall/action caps support ongoing
authorized work. Existing finite contracts, costs, retry ceilings, per-experiment
timeouts, scientific gates and STOP remain intact. Review receipts cover only the
completed blocks present when their gate opened.

Prepared dispatch checks pending and due review before and after environment
verification. A review that appears after the last admission check can still race
with process creation: these checks are not an atomic transaction spanning
separate processes. Ordinary review does not interrupt a healthy launched job.

Plan observation uses the pure `inspect --read-only` path. Monitoring polls and
normal waits must not add completed blocks or zero-finding research iterations.
Existing monitoring and execution owners retain their responsibilities; an
observation-only STOP recommendation cannot authorize process termination.
Conversation steering, one-job stop, workflow STOP and Goal pause have distinct
scopes. These contracts live in the shared bounded-inquiry reference and concise
entrypoint hooks; original retained workflow bodies remain frozen.

## Verification record

Local Linux validation passed **242 distinct tests**: 135 control, block-review,
execution and iteration-ledger checks, plus 107 handoff, pilot, guidance, mirror,
package, queue, version and release-workflow checks. The two existing queue
`datetime.utcnow` deprecation warnings remain. The current machine-readable status
is [release-validation.json](../release-validation.json); it is not a publication
receipt or a reuse of 1.6.0 release results.

The admission defect was reproduced before repair: both already-pending review
and review created during environment verification allowed a prepared CPU job to
launch. The failing JUnit record remains in the local validation directory.
An initial compatibility run also caught accidental replacement of Codex-specific
review guidance during reference synchronization. Its original adaptation was
restored, the three new monitoring lines were applied without replacing it, and
all 107 compatibility checks passed on rerun. That failed report is retained.

The practice fixture launches three complete comparisons with two methods and
three seeds each (18 actual CPU subprocesses), reviews after the second group,
then executes the third group. An original start three hours earlier is simulated;
the test is not an actual three-hour run or a native Goal acceptance test.

Live-worker tests check that read-only polls leave state and stale counters
unchanged, ordinary review leaves the worker running, and continuation reuses the
same prepared identity. Existing actual process-group STOP and fixed timeout
checks passed, including a cooperating save followed by exit zero remaining a
cancelled attempt. The CLI read-only test leaves both state and ledger bytes
unchanged; launch tests exercise persisted and due review before and after
environment verification. These are programmed engineering checks, not model
judgment or a native Plan/Goal session.

## Limits and retained failures

The repository mount does not provide the cross-process lock exclusion required
by governed runtime state. An initial in-repository temporary-directory test run
was correctly rejected and retained locally. Accepted execution fixtures use a
verified local `/tmp` filesystem; lock checks were not weakened.

Native Windows/macOS CI, Codex Goal auto-continuation/stalled behavior and Plan
watch behavior have not been exercised by this Linux patch validation. Skills
cannot override host budgets, interruptions or continuation support. Official
documentation says Plan-only does not trigger Goal automatic continuation; the
patch permits supported read-only observation without promising a resident
monitor. This patch does not repeat or inherit the historical 1.6.0 one-hour CUDA
acceptance as new evidence. See [monitoring boundaries](BOUNDED_RESEARCH_CN.md).
