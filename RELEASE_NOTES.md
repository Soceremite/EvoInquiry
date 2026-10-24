# EvoInquiry 1.6.1

EvoInquiry 1.6.1 makes trajectory review follow completed research work and clarifies how to monitor long training without treating normal waiting as research failure. The existing 89 Codex entrypoints and 88 mainline skills retain their separate owners.

## Added

- Review after N whole experimental blocks: a planned comparison counts once after its methods, seeds, evaluation and analysis are complete.
- Explicit null total wall/action caps for ongoing authorized tasks, with declared resources, retries and individual experiment limits preserved.
- Read-only inspection of current and due review for Plan monitoring and live observation.

## Fixed

- Prepared jobs cannot bypass a pending or due review at the launch checks, including after environment verification. The same prepared identity can launch once its review is addressed.
- Healthy launched jobs continue through ordinary review. Monitoring polls and waiting for results do not count as completed zero-finding research iterations or directly block a Goal.
- Observation-only Plan work reports stop recommendations to the execution owner. One-job cancellation, workflow STOP and native Goal pause remain distinct operations.

## Validation and limits

Local Linux validation passed 242 distinct tests, including three actual CPU comparison blocks and live-worker monitoring/stop checks; see the [1.6.1 validation record](https://github.com/Soceremite/EvoInquiry/blob/v1.6.1/docs/VALIDATION_1_6_1.md). Publication is gated by the full Linux and macOS CI suites and targeted native Windows checks in both PowerShell shells. Native Goal/Plan long-running session behavior remains untested. Skills follow the host's mode, budgets and available continuation tools; Plan-only does not guarantee automatic continuation after a turn. Admission checks do not form an atomic transaction with process creation.

## 中文说明

**EvoInquiry 1.6.1：按研究进展适时回顾，让长训练的正常等待继续推进。** 一组完整的对比实验只计一次，支持不设置总时长窗口的已授权持续研究；真实资源预算、重试次数和单任务上限继续有效。

**修复与边界：** 阻止已准备任务绕过待完成或到期回顾，回顾后复用原执行身份；普通回顾不打断健康训练，监听不累加科研停滞计数。Plan 可以在宿主支持的当前任务内只读观察已有训练，发现异常后报告，不擅自执行停止。单训练停止、工作流 STOP 与 Goal 暂停分别处理。

**实际验证：** 本地 Linux 验证 242 项通过，包含三组真实 CPU 对比实验与活跃进程监听、停止检查。发布流程要求 Linux、macOS 完整回归及两种 Windows Shell 的原生检查通过；原生 Goal/Plan 长程会话尚未实测。跨回合自动监听取决于 Codex 的模式、预算与续跑支持，不能由 skill 保证。

## Install and upgrade

Download `evo-inquiry-1.6.1.tar.gz` or `evo-inquiry-1.6.1.zip` from this release and follow the [Codex plugin installation and upgrade instructions](https://github.com/Soceremite/EvoInquiry/blob/v1.6.1/README.md#installation). `SHA256SUMS` and `release-manifest.json` identify the committed source packages.
