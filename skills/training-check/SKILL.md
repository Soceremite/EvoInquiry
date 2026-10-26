---
name: training-check
description: Periodically check WandB metrics during training to catch problems early (NaN, loss divergence, idle GPUs). Avoids wasting GPU hours on broken runs. Use when training is running and you want automated health checks.
argument-hint: "[wandb-run-path]"
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit, mcp__codex__codex, mcp__codex__codex-reply
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
For a governed run, use [bounded inquiry](../shared-references/bounded-inquiry.md) at the existing monitoring cadence: inspect configured trajectory gates, read actual experiment evidence, and record a reasoned decision. A STOP is a recommendation until the user explicitly confirms interruption (or previously authorized that exact automatic condition). Keep monitoring while a nonblocking stop notice is unanswered. After confirmation, the execution owner preserves recovery state and verifies actual exit; a saved intention is insufficient.
Apply its [monitoring and mode boundaries](../shared-references/bounded-inquiry.md#monitoring-interruption-and-host-modes): Plan observation is read-only, so stopping jobs or writing notes requires execution authority. A healthy run waiting for results does not add stall iterations or block a Goal. Retain one monitoring owner and use the host's supported observation cadence.
<!-- EVO-INQUIRY:END -->


# Training Check

Periodically read WandB metrics during training to catch problems early. Do not wait until training finishes to discover it was a waste of GPU time.

> ⏱ This skill is **correctly** cron-wired (see below): it polls
> machine-checkable training health (NaN / divergence / idle GPU) — the additive
> external-wait shape in
> [`shared-references/external-cadence.md`](../shared-references/external-cadence.md).
> The occasional Codex call for an ambiguous metric is a **one-shot** check per
> tick, not a multi-round verdict loop, so it stays additive — it never grows
> into a wrapped verdict skill.

## Context: $ARGUMENTS

## Constants

- WANDB_ENTITY and WANDB_PROJECT: read from CLAUDE.md or passed as argument (format: `entity/project/run_id`)
- CHECK_INTERVAL: starts at 10 minutes, then gradually increases if consistently healthy: 10 min → 20 min → 30 min → 60 min (cap)
- REVIEWER_MODEL = `gpt-6-astra` — used via Codex MCP for ambiguous cases only

## When to Use

- After training is confirmed running (session alive, loss decreasing for first few steps)
- Set up via CronCreate to fire periodically during training
- **This skill checks training QUALITY, not process HEALTH.** Process health (session alive, GPU utilization) is [watchdog.py](../../tools/watchdog.py)'s job.

## Workflow

Read the existing execution owner’s `training-budget-observations.json` when present. Present newly recorded duration notices once, keep observing while optional choices are unanswered, and report invalid/missing timing evidence without substituting process uptime. A confirmed save-and-stop needs a validated checkpoint receipt and actual exit; do not impose an implicit five-second force-kill deadline.

### Step 1: Read WandB Metrics

```python
import wandb
api = wandb.Api()
run = api.run("<entity>/<project>/<run_id>")
history = run.history()
```

If WandB is unreachable (API error, network issue), fall back to reading the log file directly via SSH:
```bash
ssh server "tail -100 /path/to/training.log"
```

Check these signals:
- **Loss trend**: Is training loss decreasing over the last N steps?
- **Eval metrics**: Are evaluation metrics improving (or at least not degrading)?
- **NaN / Inf**: Any NaN or Inf values in loss or gradients?
- **Spikes**: Sudden large jumps in loss (>10x normal variance)?
- **Learning rate**: Is the schedule behaving as expected?
- **Gradient norm**: Exploding or vanishing?

### Step 2: Judgment

| Signal | Judgment | Action |
|--------|----------|--------|
| NaN/Inf in loss | **Clearly bad** | Stop training, investigate |
| Loss diverging (increasing for >N steps) | **Clearly bad** | Stop training, investigate |
| Eval metrics significantly worse than baseline | **Clearly bad** | Stop training, investigate |
| Loss decreasing, metrics improving | **Clearly fine** | Continue, increase check interval |
| Loss flat but not diverging | **Unsure** | → Step 3 (Codex judgment) |
| Metrics noisy, can't tell trend | **Unsure** | → Step 3 (Codex judgment) |
| Slightly worse than baseline but still early | **Unsure** | → Step 3 (Codex judgment) |

### Step 3: Codex Judgment (only when unsure)

Only escalate to Codex when the signal is ambiguous. For clearly good or clearly bad signals, act directly.

```
mcp__codex__codex:
  model: gpt-6-astra
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    TRAINING HEALTH CHECK — need your judgment on ambiguous metrics.

    Run: <entity>/<project>/<run_id>
    Current epoch/step: X / Y total
    Training loss (last 10 checkpoints): [values]
    Eval metrics (last 3 evals): [values]
    Baseline reference: [numbers from paper/reproduction]

    What I'm unsure about: [specific concern]

    Please respond with exactly one of:
    - STOP: evidence supports recommending a stop; execution still needs the user's stop authorization
    - CONTINUE: looks fine, check again next interval
    - WAIT: not enough data to judge, check again sooner
```

### Step 4: Act

| Decision | Action |
|----------|--------|
| **Stop** | Save the evidence and offer a nonblocking continue/stop choice for this experiment. Keep monitoring while unanswered. The execution owner interrupts only after actual user confirmation or a specifically preauthorized condition, preserves recovery state and verifies exit. |
| **Continue** | Do nothing. Will be invoked again at next interval (increase interval if consistently healthy). |
| **Wait** | Do nothing but keep the current short interval (don't increase). |

## Integration with Watchdog

Training-check and [watchdog.py](../../tools/watchdog.py) operate at different levels:

| Layer | Tool | What it checks | Frequency |
|-------|------|----------------|-----------|
| Process health | watchdog.py | Session alive? GPU active? | Every 60s (continuous) |
| Training quality | training-check | Loss trend? Metrics improving? | Every 10-60 min (periodic) |

Use both together:
- Watchdog catches crashes and idle GPUs immediately
- Training-check catches subtle quality issues (loss plateau, metric degradation)

## Rules

- Do not stop training on first sign of noise — some loss spikes are normal. Look at **trends over multiple checkpoints**.
- When stopping training, always save the WandB run URL and key metrics as evidence.
- A reviewer STOP, resource pressure, a configured stop command or Goal/Plan mode is not user consent. Never kill a process or close its screen merely to make room for another experiment. Silence leaves the live process running and the watch active.
- If both WandB and log files are unreachable, report the connectivity issue and try again next interval. Do not assume training is broken.
- Gradually increase check interval when healthy (10 → 20 → 30 → 60 min). Reset to 10 min after any anomaly.
- This skill is meant to be automated via CronCreate — do not ask the user whether to set it up. Just set it.

## CronCreate Setup Example

```
After training is confirmed stable:
  CronCreate (recurring, every 10 minutes initially):
    "Run /training-check for wandb run <entity>/<project>/<run_id>"
```

As the check interval increases, delete the old CronCreate job and create a new one with the longer interval.
