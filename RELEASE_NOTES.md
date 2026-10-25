# EvoInquiry 1.6.2

EvoInquiry is an open-source research toolkit with 89 Codex skills spanning brainstorming, literature search, fair experiment design, implementation, monitoring, objective result and case analysis, review, and paper preparation. Its workflows connect research steps through evidence while preserving each skill's responsibility and the user's chosen scope.

**1.6.2 makes resource authorization reusable across a research session.** Choose the session's resource policy once; the relevant skills consult it and current machine state before planning and launching experiments. Routine jobs within that policy can proceed without repeated budget questions, while unavailable resources keep unlaunched work waiting.

## New capabilities

- One table per session, initialized on first use with maximum available, exclusive GPU or custom choices. Continuation and other research skills reuse the selected policy.
- Fresh checks before arranging experiments and again before launch, covering GPU allowlists, per-device and total VRAM, sharing, CPU, host RAM, dataset growth, weights, checkpoint save peaks and disk headroom.
- The existing frozen execution launcher and governed queue consult the same selected table and retain an execution-bound check receipt.

## Practical benefits

- Fewer repeated approvals: within the maximum-available profile, a 90-minute experiment fits the default 12-hour per-job allowance. Existing explicit restrictions and spending boundaries still apply.
- Better use of shared machines: planning checks both declared limits and observed headroom, including overlapping storage peaks and each GPU's available memory.
- More useful long-running sessions: resource waits preserve pending work and retries; healthy ongoing Goal work gains no new total time deadline.

## Fixes and corrections

- Within the maximum-available profile, individual jobs up to 12 hours use standing authorization. A 90-minute allocation needs no repeated budget approval, and an ongoing Goal gains no invented total time window.
- Resource shortages, missing first choices, uncertain estimates and policy exceptions keep unlaunched jobs pending without consuming training retries or becoming failed experiments.
- Storage checks combine concurrent peaks on the same filesystem. GPU checks retain per-device fit and aggregate occupancy, reject index/UUID aliases and pass only admitted GPU UUIDs to the child process.
- Unknown telemetry remains unknown capacity. Changing one custom ceiling preserves unrelated user restrictions, and a policy revision during checking requires a fresh check.
- Ordinary experiment planning in a writable session initializes the resource table and offers the first choice before scheduling. Actual host Plan mode retains its read-only restrictions; creating the policy record does not start an experiment runtime.
- Keep maximum available as the default first choice. A job's estimated CPU, RAM or duration sizes that job; it does not silently select the session's standing policy.
- Rebase declared retry outputs with native Windows and portable separators in both queue expectations and frozen snapshots, preserving parent results and fixed input arguments.
- Verify Windows process exit with non-signaling process handles before releasing a queue lease. Live or inaccessible processes remain protected.

## Validation and scope

The corrected runtime at `d56f9f4` passed full Linux and macOS CI and the targeted native Windows checks in both `powershell.exe` and `pwsh`; see [the successful CI run](https://github.com/Soceremite/EvoInquiry/actions/runs/40105479143). The formal release workflow reruns all four platform gates on the tagged commit before publishing archives.

The queue correction also passed 183 focused local tests with 13 native-Windows-only skips and no failures, including real child-process observation, output-path retries and lease protection. An earlier full local regression passed 1,410 tests with 39 skips and 46 passing subtests before the native-session guidance correction; those historical counts are separate from the final native CI results.

Actual Codex session tests covered first choice, reuse, session separation, read-only Plan monitoring, same-thread policy persistence after a mode switch, and automatic Goal continuation through two completed turns. Monitoring used real four-minute CPU jobs on the earlier native-mode snapshot; those receipts were not rerun for the queue correction. Earlier failed and partial attempts are retained. See the [1.6.2 validation record](https://github.com/Soceremite/EvoInquiry/blob/v1.6.2/docs/VALIDATION_1_6_2.md).

Real GPU training and hour-long Goal/Plan behavior remain untested for this patch. A 90-minute allocation was admitted, but no 90-minute training was run. Observation cadence includes model/tool latency and is not a real-time guarantee. Capacity sampling does not atomically reserve hardware, and sharing depends on the existing scheduler. The 89 Codex entrypoints and 88 mainline skills retain their existing owners.

## Installation and update

Download `evo-inquiry-1.6.2.tar.gz` or `.zip` from this release. `SHA256SUMS` verifies the two archives, and `release-manifest.json` identifies their source commit and skill inventory. Assets contain committed public files only; local credentials, research state and validation output are excluded.

For a new installation, extract the archive into a persistent directory and run:

```sh
cd /path/to/evo-inquiry-1.6.2
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

To replace an existing EvoInquiry marketplace, first run `codex plugin marketplace remove evo-inquiry`, then run the two installation commands from the new extracted directory. Keep that directory available and start a new Codex session. The [English README](https://github.com/Soceremite/EvoInquiry/blob/v1.6.2/README.md) and [中文指南](https://github.com/Soceremite/EvoInquiry/blob/v1.6.2/README_CN.md) cover usage and source switching.

## 中文说明

**EvoInquiry：89 个 Codex skill，连接选题、检索、公平实验、运行监控、客观分析、案例研究、审查与论文写作。** 可以直接完成一个具体任务，也可以根据已有证据接续更长的科研流程。skill 分工、用户范围和审查职责继续保留。

**1.6.2 新增：每个 session 一份资源表，首次选择，后续复用。** 初次使用可选择最大可用、独占 GPU 或自定义配置；安排实验与实际启动前都检查 GPU 白名单、逐卡与总显存、共享策略、CPU、内存、数据集、模型权重、断点保存峰值和磁盘余量。

**使用优势：** 最大可用配置下，单任务 12 小时内无需重复审批预算，90 分钟属于表内常规安排；持续 Goal 不新增总时长窗口。资源暂时不足时等待可用容量，保留待处理任务和训练重试。已有明确限制、新增付费支出边界、停止请求与科研审查继续有效。

**修复问题：** 资源不足保持等待，不消耗未启动训练的重试；同一磁盘合并数据集、权重、断点与临时峰值，逐卡核对显存并保留总占用。未知状态不能冒充可用容量，单项调高额度不再重置其他限制。追加修复 Windows 重试路径未切换到新执行目录、进程退出后租约无法释放的问题；存活或无权限确认的进程继续受到保护。

**验证范围：** 修正版已通过 Linux、macOS 完整 CI 和两种 PowerShell 的 Windows 原生专项检查；正式发布还会在标签对应的提交上重新执行四组门禁。本地专项回归 183 项通过、13 项因需原生 Windows 跳过。真实会话覆盖首次选择、复用与隔离；此前原生 Plan/Goal 实测约 4 分钟的 CPU 任务监听，Goal 自动续出第二轮且两轮均正常完成。这些结果不代表已经完成本补丁的小时级训练、真实 GPU 隔离或长期无人值守科研验收。

**安装与升级：** 下载本页的 1.6.2 压缩包、校验 `SHA256SUMS`，在持久目录解压后执行上面的安装命令。已有安装先移除旧 marketplace 来源，再添加新解压目录，最后启动新 Codex 会话。功能与使用方法见[资源表说明](https://github.com/Soceremite/EvoInquiry/blob/v1.6.2/docs/SESSION_RESOURCE_BUDGET_CN.md)。
