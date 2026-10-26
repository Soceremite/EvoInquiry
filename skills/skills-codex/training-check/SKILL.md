---
name: training-check
description: "Continuously monitor training metrics in the current session using W&B or logs, checking NaN, divergence, plateaus, and failed runs. Use for ongoing training supervision."
argument-hint: "[wandb-run-or-monitoring-brief]"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.

For runs saving large artifacts, include the [storage checks](../shared-references/experiment-storage.md): capacity, artifact growth, and valid-save age/failures. Apply established run policies to storage incidents and preserve valid recovery state when stopping.
For a governed run, use [bounded inquiry](../shared-references/bounded-inquiry.md) at the existing monitoring cadence: inspect configured trajectory gates, read actual experiment evidence, and record a reasoned decision. A STOP is a recommendation until the user explicitly confirms interruption (or previously authorized that exact automatic condition). Keep monitoring while a nonblocking stop notice is unanswered. After confirmation, the execution owner preserves recovery state and verifies actual exit; a saved intention is insufficient.
Apply its [monitoring and mode boundaries](../shared-references/bounded-inquiry.md#monitoring-interruption-and-host-modes): Plan observation is read-only, so stop behavior and note-writing below require execution authority. A healthy run waiting for results does not add stall iterations or block a Goal. Pair quality reviews with lightweight progress/liveness checks and interruptible waits; retain one monitoring owner.
<!-- EVO-INQUIRY:END -->


# Training Check

You are now in **interactive watch** / 交互式训练监控模式.

Keep the current session open and report directly in the current terminal. The user is watching this terminal for updates. By default, run a training health check every 30 minutes, output a concise but complete analysis report after each check, state the next check time, then continue monitoring.

This skill checks training **quality**, not basic process health. Process health checks such as whether a tmux session exists or whether the GPU is idle can be handled by watchdog-style tooling; this skill focuses on whether the run is still worth continuing.

## Inputs To Establish First

Before the first check, identify or ask for the minimum monitoring context:

- WandB run path or URL, if available.
- Fallback log path, SSH command, or local command for reading recent training logs.
- Training target, expected baseline, and key metrics that define success.
- How the training was launched, so it can be stopped if needed.
- Project notes path for recording decisions and evidence.

If a source is unavailable, say so clearly and continue with the available source. If both WandB and fallback logs are unreachable, report the connectivity issue, classify the round as `WAIT`, and check again later. Do not infer that training is bad only because data is unreachable.

## Per-Round Check

Read the existing execution owner’s `training-budget-observations.json` when present. Present newly recorded duration notices once, keep observing while optional choices are unanswered, and report invalid/missing timing evidence without substituting process uptime. A confirmed save-and-stop needs a validated checkpoint receipt and actual exit; do not impose an implicit five-second force-kill deadline.

Every round, read WandB first when configured. If WandB is unreachable, read the fallback logs. Inspect at least:

- Training loss trend over recent checkpoints or steps.
- Eval metrics and whether they improve, flatten, or degrade against baseline.
- NaN or Inf in loss, gradients, activations, or logged metrics.
- Sudden loss spikes, divergence, or repeated failed evaluations.
- Learning rate schedule behavior.
- Gradient norm, if logged.
- Plateau patterns that suggest the run is no longer useful.

Output one report in the current terminal with this structure:

```text
## Training Check - <local timestamp>

- Data source: wandb_ok | log_fallback | unreachable
- Run: <wandb run or training identifier>
- Recent metrics: <loss/eval/lr/grad summary>
- Anomalies: <NaN/Inf/spike/divergence/plateau findings>
- Evidence: <WandB URL, log lines, metric values, or files inspected>
- Decision: CONTINUE | WAIT | STOP
- Reason: <why this decision is justified>
- Next check: <local timestamp, normally 30 minutes later unless ending>
```

Use the decisions as follows:

| Decision | Meaning | Action |
|----------|---------|--------|
| `CONTINUE` | Run looks healthy enough to keep training. | Keep monitoring and check again in 30 minutes. |
| `WAIT` | Evidence is inconclusive, noisy, too early, or temporarily unreachable. | Do not stop training; keep monitoring and check again later. |
| `STOP` | Evidence supports recommending an end to this training. | Save the evidence and request the user's stop choice without blocking observation. Interrupt only after confirmation or a specifically preauthorized condition. |

## Stop Behavior

When the decision is `STOP`:

- Identify the exact experiment, process/job scope, evidence and recovery implications; offer continue (default) or checkpoint and stop through a nonblocking popup when available. An unanswered notice keeps monitoring active. Report once through ordinary commentary if a popup would suspend the turn.
- An actual user stop reply, or a previously agreed automatic condition covering this run, authorizes the execution owner to stop it. A configured `stop_command`, a reviewer verdict, elapsed time or Goal/Plan mode alone does not.
- After authorization, use the existing owner's identity-bound cooperative checkpoint/stop path; target only that experiment. Verify real exit before releasing resources or ending its watch.
- Save evidence: WandB URL, key metrics, relevant log snippets, files inspected, and the reason for stopping.
- Append a project note for debugging and future analysis.
- Output `FINAL_SUMMARY` and end this experiment's watch after verified exit. A pending stop choice does not end monitoring or block the broader Goal.

Never stop on the first sign of ordinary metric noise. Look for sustained trends, hard failures, or clear divergence. Always preserve enough evidence for a later agent or human to understand why the run was stopped.

## Interactive Loop Guidance

- The normal interval is 30 minutes.
- If a round is `CONTINUE`, announce the next check time and wait until then.
- If a round is `WAIT`, explain what evidence is missing or noisy and check again later. Use a shorter interval only when the run looks suspicious but not yet stop-worthy.
- If an anomaly recovers, say so explicitly and continue monitoring.
- Keep the user-facing report short enough to read in a terminal, but include concrete metric values and evidence paths.
