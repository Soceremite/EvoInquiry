# EvoInquiry 1.7.0

EvoInquiry can now plan experiment placements and queue jobs from the server's current resources. The planner uses the selected session policy and declared peaks. The queue recalculates how many jobs fit as capacity changes.

## Added

- Maintain one source per workflow and reproduce the Codex and reviewer overlays through the surface generator and CI.
- Move the detailed instructions for ten long skills into linked stage references. Share review-cycle guidance across the two external API adapters.
- Upgrade rebuttal with six response modes, a one-page LaTeX template, traceable evidence and revision commitments, optional external rehearsal, and legacy migration guidance.
- Generate `RESOURCE_PLAN.md` and `resource-request.json` from task requirements and a fresh target-host probe. Set the preference for headroom, minimal resource use or the shortest estimated runtime among declared options.
- Calculate concurrency from the combined CPU, RAM, per-device VRAM and filesystem peaks. Apply the session and manifest limits together.
- Share a GPU between resource-bound jobs when both the session and task allow it. Launch receipts record the chosen device UUIDs, overlap and concurrent attempt IDs for comparison logs.
- Dispatch pending work by priority, reserve the next job's capacity and use spare resources. Select validated evaluation profiles and run authorized CPU companions during a monitored execution.

## Fixed

- Remove the default eight-GPU and eight-job values. New unbound queue manifests require explicit device and concurrency settings.
- Recheck the saved assignment, current user policy and active lease before process creation. A capacity deferral preserves the prepared attempt and its retry count.
- Keep placement outside the frozen scientific configuration. A task can select from declared resource options while reusing the original model, data, arguments and seed.
- Estimate the container's available RAM with a conservative allowance for clean inactive file cache on Linux.

## 中文说明

v1.7.0 根据会话资源表和服务器遥测安排实验。队列按显存、内存及各文件系统的叠加峰值计算并发。用户指定的设备和并发上限优先，容量不足的任务保持待运行。

资源和租约允许时，同一队列的实验可以共享 GPU。启动记录保留设备 UUID 和重叠作业供比较引用。真实计时比较使用隔离运行。详细用法见[资源配置](docs/CUSTOMIZATION_CN.md#自适应资源配置)。

技能入口与 Claude、Gemini 评审 overlay 现在可从源文件生成。十个长入口按阶段加载细节，两个外部评审适配器共用流程。Rebuttal 支持一页 PDF、跨轮讨论和作者承诺核对，旧项目可按迁移说明接续。
