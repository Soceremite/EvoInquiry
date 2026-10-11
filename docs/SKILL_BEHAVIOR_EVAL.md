# Offline skill behavior evaluation

The [24 frozen cases](../tests/behavior/evo-inquiry-cases.json) contain 12 Chinese
and 12 English requests. They exercise skill selection, actual execution,
continuation, evidence gaps, explicit calls, small tasks, and unavailable
dependencies. All paper excerpts and datasets are synthetic. This does not test
live literature discovery, GPU execution, complete research pipelines, or research
quality. Case 20 stops at initial scoping rather than completing the lifecycle.

## Run a comparison

Use the same Codex CLI version, model, reasoning settings, and execution policy
for both variants. The baseline is beta.3 commit
`b9c7861fd22cd2f5471765d583c593f083fa12cc`; the candidate adds research-guide and
changes only registered descriptions and hooks in the retained skill corpus.
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
[release-validation.json](../release-validation.json) for this candidate's actual
status. A process exiting successfully is not a passed case. A small paired
evaluation cannot establish general proactivity or better research outcomes.
