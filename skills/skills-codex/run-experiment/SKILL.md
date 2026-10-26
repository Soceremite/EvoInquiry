---
name: "run-experiment"
description: "Launch and collect ML experiments on local or remote GPU resources. Use to execute a ready implementation; experiment-bridge implements an existing plan first."
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.

Before launching an artifact-producing run, apply [experiment storage](../shared-references/experiment-storage.md): check the actual output filesystem and effective checkpoint policy, reserve full-save staging space, and record the valid recovery path.
On completed or explicitly ended training, validate required weights and persist evidence before releasing unused recovery state. For completed comparison groups, apply the shared winner-only policy after checking planned model dependencies.

For this stage, read [project-governance](../shared-references/project-governance.md). Before formal launch bind a frozen source/config snapshot, environment revision and distinct execution ID. Preserve actual imports/exit codes, failed attempts and retry/resume parents; outputs belong to that execution.
Use [code-reuse-and-docs](../shared-references/code-reuse-and-docs.md) for code changes and [environment-stewardship](../shared-references/environment-stewardship.md) for dependency changes.
When executing comparisons, load [comparative-experiments](../shared-references/comparative-experiments.md). Check effective configurations, data/split/evaluator identities, declared resource limits and validation selection. Preserve every seed and failed/retried attempt. Before winner-only cleanup, bind a complete comparison evidence index and keep logs outside checkpoint artifact directories.
When the evaluation produces sample evidence, persist its compact prediction/selection records and the planned small output subset with the run's results before temporary storage or weights are released. Apply [case-study-analysis](../shared-references/case-study-analysis.md) for the relevant identities and storage limits. Do not add evaluation runs, regenerate missing samples or copy whole datasets merely to fill a case panel.

For sustained execution or recovery, use [bounded inquiry](../shared-references/bounded-inquiry.md). Preserve the original owner/budget: reserve before launch, settle from terminal evidence and keep unfinished work visible. Registered executions can use its `settle-execution` helper; it never relaunches or accepts research gates.
For a bound local run, follow [bounded inquiry](../shared-references/bounded-inquiry.md): the existing launcher requires an actual user confirmation for interruption or an explicitly preauthorized automatic stop condition; workflow review stops otherwise hold only new dispatch. Keep per-training time from the first actual step separate from any agreed overall wall deadline, and check live hardware and phase peaks before launch. Verify its actual terminal receipt before releasing the reservation; normal reflection does not interrupt healthy training.
<!-- EVO-INQUIRY:END -->


# Run Experiment

Deploy and run ML experiment: $ARGUMENTS

## Workflow

### Step 1: Detect Environment

Read the project's `AGENTS.md` to determine the experiment environment:

- **Local GPU**: Look for local CUDA/MPS setup info
- **Remote server**: Look for SSH alias, conda env, code directory
- **Vast.ai instance**: Look for `gpu: vast`, `vast_instance`, SSH host/port, remote path, and optional `auto_destroy`
- **Modal serverless**: Look for `gpu: modal`, app/function name, image/dependency setup, and secrets

If no server info is found in `AGENTS.md`, ask the user.

**Environment contract** (`../shared-references/compute-env-contract.md`): before
building or trusting any environment, read the provider's env ledger
(`.ei/compute/<provider>.md`) — an unchanged spec hash means warm-reuse, a
changed one means rebuild. New env → write the declarative spec first, render it
for this provider's shape, and never declare it ready on import-success alone:
run the seeded kernel witness, and after any rebuild/doc edit run the
agent-follows-doc pass (a fresh subagent executes the documented invocation
verbatim and reports doc-vs-reality divergence).

### Step 2: Pre-flight Check

Check GPU availability on the target machine:

**Remote:**
```bash
ssh <server> nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader
```

**Local:**
```bash
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader
# or for Mac MPS:
python -c "import torch; print('MPS available:', torch.backends.mps.is_available())"
```

Use the current session resource table and a fresh host probe. Shared admission compares measured phase peaks with free VRAM; exclusive admission checks observed GPU occupants and scheduler allocations. Driver baseline memory alone does not establish occupancy, and unknown process inventory does not establish an idle device. Never reuse a fixed free-memory gate from another machine.

### Step 3: Sync Code (Remote Only)

Check the project's `AGENTS.md` for a `code_sync` setting. If not specified, default to `rsync`.

#### Option A: rsync (default)

Only sync necessary files — NOT data, checkpoints, or large files:
```bash
rsync -avz --include='*.py' --exclude='*' <local_src>/ <server>:<remote_dst>/
```

#### Option B: git (when `code_sync: git` is set in AGENTS.md)

Within existing commit/push authorization, stage only the reviewed deployment files, then pull on the server. Otherwise use the source allowlist with rsync:
```bash
# 1. Push from local
git diff -- <reviewed_source_files>
git add -- <reviewed_source_files>
git diff --cached
# Commit and push only within the existing user-authorized delivery scope.
git commit -m "sync: experiment deployment" && git push

# 2. Pull on server
ssh <server> "cd <remote_dst> && git pull"
```

Benefits: version-tracked, multi-server sync with one push, no rsync include/exclude rules needed.

#### Option C: Vast.ai instance

If `gpu: vast` is configured, treat the Vast.ai machine as a remote server with an explicit lifecycle:

1. Verify the instance is running and reachable.
2. Sync code to the configured remote path.
3. Confirm data/checkpoints are already mounted or intentionally copied.
4. Record the instance id in the launch summary for later cleanup.

Do not silently ignore a requested Vast.ai route. If Vast.ai CLI credentials or instance metadata are missing, stop and ask the user to configure them.

### Step 3.5: W&B Integration (when `wandb: true` in AGENTS.md)

**Skip this step entirely if `wandb` is not set or is `false` in AGENTS.md.**

Before deploying, ensure the experiment scripts have W&B logging:

1. **Check if wandb is already in the script** — look for `import wandb` or `wandb.init`. If present, skip to Step 4.

2. **If not present, add W&B logging** to the training script:
   ```python
   import wandb
   wandb.init(project=WANDB_PROJECT, name=EXP_NAME, config={...hyperparams...})

   # Inside training loop:
   wandb.log({"train/loss": loss, "train/lr": lr, "step": step})

   # After eval:
   wandb.log({"eval/loss": eval_loss, "eval/ppl": ppl, "eval/accuracy": acc})

   # At end:
   wandb.finish()
   ```

3. **Metrics to log** (add whichever apply to the experiment):
   - `train/loss` — training loss per step
   - `train/lr` — learning rate
   - `eval/loss`, `eval/ppl`, `eval/accuracy` — eval metrics per epoch
   - `gpu/memory_used` — GPU memory (via `torch.cuda.max_memory_allocated()`)
   - `speed/samples_per_sec` — throughput
   - Any custom metrics the experiment already computes

4. **Verify wandb login on the target machine:**
   ```bash
   ssh <server> "wandb status"  # should show logged in
   # If not logged in:
   # Use the target's configured WANDB_API_KEY or credential store; do not place a key in this command.
   ssh <server> "wandb status"
   ```

> The W&B project name may come from `AGENTS.md`; obtain credentials from the existing environment or credential store. Keep keys out of project guidance, snapshots, command history and logs. The experiment name is auto-generated from the script name + timestamp.

### Step 4: Deploy

#### Remote (via SSH + screen)

For each experiment, create a dedicated screen session with GPU binding:
```bash
ssh <server> "screen -dmS <exp_name> bash -c 'set -o pipefail; \
  eval \"\$(<conda_path>/conda shell.bash hook)\" && \
  conda activate <env> && \
  CUDA_VISIBLE_DEVICES=<gpu_id> python <script> <args> 2>&1 | tee <log_file>'"
```

#### Vast.ai instance

Use the same SSH + screen pattern, but include the Vast.ai instance id, public SSH endpoint, and remote working directory in the report. If `auto_destroy: true`, write a cleanup command to the run notes before launch.

Record the estimated hourly cost, expected run duration, and cleanup owner. If the command fails to start or the instance becomes unreachable, do not relaunch blindly; capture logs and ask for a rescue / second opinion before spending more GPU time.

#### Modal (serverless)

If `gpu: modal` is configured, deploy through Modal instead of SSH:

```bash
modal run <module_or_app>.py -- <args>
```

Before launch, verify required secrets, volumes, image dependencies, and output persistence. If Modal is requested but the project lacks Modal configuration, stop and ask the user to configure it rather than falling back to local execution.

Record the Modal app/function name, GPU type, timeout, mounted volumes, and where results will be stored. If Modal reports an image, secret, or volume error, preserve the exact error and run a configuration fix before retrying.

#### Local

```bash
# Linux with CUDA
set -o pipefail
CUDA_VISIBLE_DEVICES=<gpu_id> python <script> <args> 2>&1 | tee <log_file>

# Mac with MPS (PyTorch uses MPS automatically)
python <script> <args> 2>&1 | tee <log_file>
```

For local long-running jobs, use `run_in_background: true` to keep the conversation responsive.

### Step 5: Verify Launch

**Remote:**
```bash
ssh <server> "screen -ls"
```

**Local:**
Check process is running and GPU is allocated.

### Step 6: Feishu Notification (within authorized delivery scope)

After deployment is verified, check `~/.codex/feishu.json`:
- Send `experiment_done` notification: which experiments launched, which GPUs, estimated time
- If config absent or mode `"off"`: skip entirely (no-op)

### Step 7: Auto-Destroy Vast.ai Instance (when `gpu: vast` and `auto_destroy: true`)

Only run this after the experiment has completed and results/logs/checkpoints have been copied or otherwise persisted.

1. Verify the target process has exited.
2. Copy result files and logs to the configured durable location.
3. Ask for confirmation unless AGENTS.md explicitly says `auto_destroy: true`.
4. Destroy only the recorded instance id for this run.

If any artifact copy fails, do not destroy the instance.

## Key Rules

- ALWAYS check GPU availability first — never blindly assign GPUs
- Each experiment gets its own screen session + GPU (remote) or background process (local)
- Use `tee` with `set -o pipefail`; retain the trainer exit code and an attempt-bound terminal receipt. A screen disappearing or an output file appearing is not proof of successful training
- Run deployment commands with `run_in_background: true` to keep conversation responsive
- Report back: which GPU, which screen/process, what command, estimated time
- If multiple experiments, launch them in parallel on different GPUs

## AGENTS.md Example

Users should add their server info to their project's `AGENTS.md`:

```markdown
## Remote Server
- SSH: `ssh my-gpu-server`
- GPU: 4x A100 (80GB each)
- Conda: `eval "$(/opt/conda/bin/conda shell.bash hook)" && conda activate research`
- Code dir: `/home/user/experiments/`
- code_sync: rsync          # default. Or set to "git" for git push/pull workflow
- wandb: false              # set to "true" to auto-add W&B logging to experiment scripts
- wandb_project: my-project # W&B project name (required if wandb: true)
- wandb_entity: my-team     # W&B team/user (optional, uses default if omitted)

## Vast.ai
- gpu: vast
- vast_instance: 123456
- SSH: `ssh -p 12345 root@ssh.vast.ai`
- Code dir: `/workspace/experiments/`
- auto_destroy: false

## Modal
- gpu: modal
- modal_app: `train.py`
- modal_secrets: `wandb-secret`
- modal_volume: `experiment-results`

## Local Environment
- Mac MPS / Linux CUDA
- Conda env: `ml` (Python 3.10 + PyTorch)
```

> **W&B setup**: Run `wandb login` on your server once (or set `WANDB_API_KEY` env var). The skill reads project/entity from `AGENTS.md` and adds `wandb.init()` + `wandb.log()` to your training scripts automatically. Dashboard: `https://wandb.ai/<entity>/<project>`.
