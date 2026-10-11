# 会话恢复

[English](SESSION_RECOVERY_GUIDE.md) · [README](../README_CN.md)

将项目状态保存在磁盘上，让新会话根据实际材料继续工作。
在 Codex 中，可在项目说明或其链接的状态文件里维护简短的 `Pipeline Status`。
保留的流程模板可能称该文件为 `CLAUDE.md`；可以按项目使用的客户端调整存放方式，
同时保留真实科研材料，不把计划中的工作写成已经完成。

记录当前阶段、选定方向、研究契约、分支、已完成产物、运行中的任务、资源限制、
阻塞问题与下一步。每个运行任务应记录服务器、进程或会话标识、输出路径和状态检查命令。
阶段切换、重要决策、任务启动或结束，以及交接前，都应更新状态。

恢复时先读取状态记录，再依次检查：

1. `idea-stage/docs/research_contract.md`，或当前方向实际保存的研究契约。
2. 相关方案、实验日志、原始结果和评审报告。
3. 已记录的后台任务的实时状态，确认后再决定是否启动任务。
4. 待授权事项或缺失输入，然后继续记录的下一步。

新建材料时，可使用[研究契约模板](../templates/RESEARCH_CONTRACT_TEMPLATE.md)
和[实验日志模板](../templates/EXPERIMENT_LOG_TEMPLATE.md)。简短状态用于指向证据，
不会替代证据。

有状态的流程遵循 skill 的
[可恢复运行约定](../skills/skills-codex/shared-references/resumable-runs.md)，
并使用包内的 `tools/run_state.py`。证明项目另由 `proof-orchestrator` 管理自己的运行目录。
