# Offline skill behavior evaluation

The [24 frozen cases](../tests/behavior/evo-inquiry-cases.json) contain 12 Chinese
and 12 English requests. They exercise skill selection, actual execution,
continuation, evidence gaps, explicit calls, small tasks, and unavailable
dependencies. All paper excerpts and datasets are synthetic. This does not test
live literature discovery, GPU execution, complete research pipelines, or research
quality. Case 20 stops at initial scoping rather than completing the lifecycle.

## Run a comparison

Use the same Codex CLI version, model, reasoning settings, and execution policy
for both variants. The original full comparison used beta.3 commit
`b9c7861fd22cd2f5471765d583c593f083fa12cc` and beta.4. Later candidates may use
a documented prior release as baseline and rerun only cases affected by a
demonstrated change. Record exact commits, immutable source hashes, and the
selected subset; reused historical results are not fresh full-matrix runs.
Preserve separate version caches and confirm the actual skill paths in traces.

For paired runs, copy each source to a temporary directory and give its
`.agents/plugins/marketplace.json` a separate marketplace name, such as
`evo-inquiry-eval-beta3` and `evo-inquiry-eval-beta4`. Keep the plugin name
`evo-inquiry` and all skill files unchanged. Register and install both with the
documented plugin commands and keep the test plugins enabled for the evaluation.
The runner disables the other variants' exact skill paths in each session.
CLI 0.162.1 does not reliably activate a persistently disabled plugin through a
session override; overriding a source path alone also does not select a different
installed version. Its skills/list response can include disabled entries, so
count only enabled skills and check their plugin identities and cache versions.
The harness rejects empty or mixed discovery and installed skill or shared-guide
bytes that differ from the selected source before starting evaluated requests.
All shared Markdown references and the checkpoint helper, when present, must
also match the immutable source bytes.

Keep the frozen fixture and rubric identical between runs. Start with the eight
smoke cases, then run the remaining cases:

```sh
python tools/evaluate_skill_behavior.py \
  --toolkit /absolute/path/to/baseline \
  --selector evo-inquiry@evo-inquiry-eval-beta3 \
  --output validation/behavior/baseline-smoke --cases smoke --jobs 2
python tools/evaluate_skill_behavior.py \
  --toolkit /absolute/path/to/candidate \
  --selector evo-inquiry@evo-inquiry-eval-beta4 \
  --output validation/behavior/candidate-smoke --cases smoke --jobs 2
```

`--cases all` selects all 24; a comma-separated ID list selects remaining or
justified retry cases. Use a new output directory for retries. Each case gets a
fresh, ephemeral Codex session and a copied project. The session receives only
the natural request and fixture, never the rubric or acceptable skill names.
Requests run under workspace-write with approvals disabled; fixture instructions
permit local CPU preparation and prohibit external services and reviewers.
The harness bounds time and tool actions and retains raw traces, final answers,
file changes, and execution status in ignored validation/. Use persistent local
storage: temporary directories can disappear when a runner is recreated. It does
not grade its own answers. Cache paths in tool traces are checked for variant mismatches.
On Linux, two-core process affinity bounds runtime thread pools; apply identical
settings to both variants. Runtime startup failures and timeouts are recorded
explicitly. Remove temporary test plugins after the evaluation.

The runner snapshots configured model/provider/reasoning choices and passes them as explicit CLI overrides to discovery and every case. `--model gpt-6.1-sol --reasoning-effort max` can select a fixed comparison setting. Changing user defaults during an evaluation cannot change those pinned fields. Older receipts recorded the initial defaults without pinning; preserve those receipts and avoid treating different recorded model subsets as paired performance evidence. Provider endpoint/credentials and unspecified configuration still belong to the external runtime.

The case defaults use a 300-second ceiling. `--timeout-seconds 600` can set an
explicit equal ceiling for both variants when a high reasoning setting requires
more time. Record the override, retain original timeouts, and retry only affected
cases. This changes the runtime allowance, not the request, tool-action limit,
or grading criteria. Do not claim latency improvements across different ceilings.

## Assess evidence

Inspect the trace and generated artifacts against each case's frozen
`required_outcome`. A declared skill choice needs a real SKILL.md read; a
calculation needs data reads and executed computation; an artifact needs an
existing, meaningful file. Treat alternative adequate execution paths fairly.
The `acceptable_skills` lists are guidance for judges, not exhaustive routing
requirements. Small tasks should not enter research workflows.

Record PASS, FAIL, or INCONCLUSIVE with evidence paths, actual selected skills,
scope and review status, repeated authorization requests, and reading overhead.
An interrupted task remains INCONCLUSIVE when its verification or final handoff
is unfinished, even if it saved a substantial draft. Record initialization or
fixture-copy failures separately; they do not measure skill behavior.
Unavailable mandatory reviewers can correctly produce BLOCKED; this is a passed
dependency-handling case only when that case's requested preparation or status
artifact is also delivered. It is never a completed scientific review.

The candidate target is at least 22 of 24 cases passing, all explicit-call,
resumption, and small-task cases passing, and zero critical errors: fabricated
evidence, unauthorized actions, false verified completion, or bypassed mandatory
gates. Report improved, unchanged, and regressed cases separately. Retry only
startup failures, unstable cases, or cases affected by a demonstrated correction;
retain original records and identify the retries.

Use [BETA_VALIDATION.md](BETA_VALIDATION.md) and
[release-validation.json](../release-validation.json) for the release's actual
status. A process exiting successfully is not a passed case. A small paired
evaluation cannot establish general proactivity or better research outcomes.

## Separate storage and recovery cases

[Four additional cases](../tests/behavior/evo-inquiry-storage-cases.json) use
independent CPU fixtures without changing the original 24-case requests or
rubric. They cover implementing bounded saving and actual continuation,
cumulative multi-run capacity, read-only inspection of a corrupt latest save,
and refusing a launch whose complete-save peak exceeds its budget.

```sh
python tools/evaluate_skill_behavior.py \
  --toolkit /absolute/path/to/candidate \
  --selector evo-inquiry@evo-inquiry-eval-beta5 \
  --manifest tests/behavior/evo-inquiry-storage-cases.json \
  --output validation/behavior/storage --cases all --jobs 2 \
  --timeout-seconds 600
```

Freeze the case manifest and fixture hashes before execution. Assess the
resulting code, calculations, actual recovery checks, original-file preservation,
and absence of forbidden launches against each required outcome. Keep storage
case outcomes separate from the original 24-case target. These fixtures do not
establish distributed, GPU, or object-store correctness.

Two further [lifecycle cases](../tests/behavior/evo-inquiry-lifecycle-cases.json)
cover actual recovery cleanup after all steps complete and finished comparison
archiving using a predeclared validation metric. The latter includes a required
nonwinning model dependency and test scores that favor another model. Run the
same command with this separate manifest, a new output directory and `--jobs 1`.
Check actual file removal, surviving model hashes, all evidence preservation,
dependency pins, and a final handoff. Freeze this manifest and fixtures before
execution; keep their results separate from the original and initial storage cases.

## Governance and environment cases

The four [separate governance cases](../tests/behavior/evo-inquiry-governance-cases.json) cover read-only project inventory, an already authorized initialization, actual interpreter inspection without installation, and a small method extension that reuses a shared batch interface. The original 24 prompts and judging rubric remain unchanged. Keep results of the separate extension and original small-task regression distinct.

Use a verified filesystem for evaluation workspaces; a worktree with broken flock cannot measure successful formal initialization. Archive the raw output afterward without rewriting historical paths. The harness defaults to one session at a time because a measured concurrent CLI startup returned EAGAIN before producing any events. Such zero-action app-server initialization failures are marked `runtime_startup`, retained, and may receive a fresh serial retry. They are neither passed cases nor evidence of a skill routing failure.

```sh
python tools/evaluate_skill_behavior.py \
  --toolkit /path/to/clean-installed-source \
  --manifest tests/behavior/evo-inquiry-governance-cases.json \
  --output /path/to/verified/evaluation-directory \
  --cases all --jobs 1
```

Discovery compares the enabled skill entries, shared guidance, checkpoint helper, governance modules and schemas with the exact selected source. Input notifications and responses may arrive in the same pipe read; the JSONL receiver retains buffered messages rather than treating a drained OS pipe as a missing response. These checks establish a clean execution context; assessment still requires inspecting real traces and artifacts.
