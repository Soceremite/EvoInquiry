# EvoInquiry 1.6.2

EvoInquiry 1.6.2 introduces a session resource table so research skills can reuse an established allocation instead of repeatedly asking whether a routine experiment may run. This source update has passed local validation; a tagged 1.6.2 release has not been published.

## New capabilities

- One table per session, initialized on first use with maximum available, exclusive GPU or custom choices. Continuation and other research skills reuse the selected policy.
- Fresh checks before arranging experiments and again before launch, covering GPU allowlists, per-device and total VRAM, sharing, CPU, host RAM, dataset growth, weights, checkpoint save peaks and disk headroom.
- The existing frozen execution launcher and governed queue consult the same selected table and retain an execution-bound check receipt.

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

The full regression before the native-session guidance correction passed 1,410 tests with 39 skipped and 46 passing subtests, with no failures. The latest guidance passed 95 resource, queue, mirror and package tests. Two independent ordinary Codex threads completed four turns covering first choice, reuse, a short CPU execution and session separation. Additional actual host Plan/Goal tests passed: read-only Plan monitoring, same-thread policy persistence after a mode switch, and automatic Goal continuation through two completed turns. Monitoring used real four-minute CPU jobs; earlier failed and partial attempts are retained. No 90-minute training was performed. See the [1.6.2 validation record](docs/VALIDATION_1_6_2.md).

The first 1.6.2 source submission passed full Linux and macOS CI; both Windows jobs exposed queue retry-path and process-exit issues addressed by this correction. The corrected commit requires its own native CI results. Real GPU training and hour-long Goal/Plan behavior remain untested. Observation cadence includes model/tool latency and is not a real-time guarantee. Capacity sampling does not atomically reserve hardware, and sharing still depends on the existing scheduler. The 89 Codex entrypoints and 88 mainline skills retain their existing owners.

The queue correction passed 183 focused local tests with 13 native-Windows-only skips and no failures, including real child-process observation, output-path retries and lease protection. The prior native Plan/Goal receipts describe the earlier snapshot; they were not rerun for this queue correction.

## 中文说明

**EvoInquiry 1.6.2：每个 session 一份资源表，首次选择，后续复用。** 安排实验与实际启动前都检查当前 GPU、内存和存储状态；最大可用配置下，单任务 12 小时内无需重复审批，90 分钟属于表内常规安排。持续 Goal 不新增总时长窗口，原有明确预算、停止请求与科研审查继续有效。

**修复问题：** 资源不足保持等待，不消耗未启动训练的重试；同一磁盘合并数据集、权重、断点与临时峰值，逐卡核对显存并保留总占用。未知状态不能冒充可用容量，单项调高额度不再重置其他限制。追加修复 Windows 重试路径未切换到新执行目录、进程退出后租约无法释放的问题；存活或无权限确认的进程继续受到保护。

**验证与发布状态：** 真实会话覆盖首次资源选择、同会话复用和新会话隔离；原生 Plan/Goal 另验证约 4 分钟的 CPU 任务监听，Goal 首轮结束后自动续出第二轮，两轮均正常完成。本机插件已同步经过验收的 1.6.2 修正版，全部 89 个子 skill 可被重新发现。1.6.2 尚未正式发布；小时级运行与跨平台验收仍待覆盖。功能与用法见[资源表说明](docs/SESSION_RESOURCE_BUDGET_CN.md)。
