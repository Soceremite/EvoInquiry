# EvoInquiry 1.6.3

EvoInquiry connects research framing, literature search, fair experiments, implementation, monitoring, objective analysis, case studies and paper preparation through 89 Codex skills. Each skill keeps its own responsibility and reuses the project's evidence and resource policy.

**1.6.3 improves sustained research work while keeping routine progress within the user's existing authorization.** This revision also simplifies budget guidance and defaults new sessions to available server resources without a duration ceiling.

## New capabilities

- Initialize one session resource table from current CPU, GPU, memory and storage. Default to available local capacity without extra hardware caps or a time limit; reuse explicit user choices across skills and continuation.
- Configure optional reminders separately from user-selected limits. Plan and launch against fresh hardware state, including GPU sharing and storage peaks.
- Read trainer-owned first-step timing receipts through the existing execution observer, keeping preparation separate and preserving elapsed training across resume.
- Verify cooperative checkpoint-and-stop receipts while keeping checkpoint validity, user intent and actual process exit distinct.

## Fixes and corrections

- Remove fixed pilot budgets, default search timeouts and repeated timing examples. Planning, execution and monitoring use the same session policy.
- Keep healthy training under observation during reflection and unanswered optional notices. Local review or a completed subtask does not automatically stop the whole Goal.
- Serialize dispatch with review and stop updates. Deferred jobs keep their prepared identity without spending a training retry.
- Preserve trainer exit codes through log pipelines. Partial output or a missing screen session cannot establish completion of a live or unknown process.
- Wait for cooperative saves without an implicit force-kill deadline. Forced termination requires separate authorization; uncertain descendants remain protected.
- Use observed GPU occupants and justified memory peaks instead of blanket idle-memory thresholds, and replace queue state atomically on Windows.
- Keep notification, deployment, comparison and checkpoint responsibilities with their existing owners. Credentials stay outside project guidance.
- Update an existing GitHub release through the same publication gates, preserving its version and release URL.

## Validation

Local acceptance covers fresh session initialization against actual server resources, command-line planning and monitoring, and real short CPU dispatch. Resource-table and queue regression passed 101 tests after two old default-dependent fixtures were changed to explicit user limits. Package preservation, skill discovery, dispatch, timing and monitoring checks also passed; overlapping counts are not added together.

The publication workflow checks complete Linux/macOS regression and both native Windows PowerShell suites before updating release assets. Earlier native Codex Goal/Plan acceptance and the original failed checks retain their own source identities in the [audit record](docs/AUDIT_1_6_3_CN.md). Short CPU fixtures do not establish hour-long GPU research or universal model compliance. Timing and stop receipts require trainer integration; existing frozen jobs retain their original contracts.

## 中文说明

**默认按实际资源初始化，时长不设限。** 每个 session 复用唯一资源表，用户可自行设置资源、提醒和时限。各技能读取同一份配置，避免把具体项目的数值变成通用规则。

**持续推进，适时回顾，停止有据。** 健康训练与可选通知保持持续观察；回顾暂缓不消耗实验重试。训练从实际首步计时，协作保存不再默认强杀，停止已有进程仍需明确授权。

**保持技能协作和证据边界。** 本次统一了 pilot、搜索、规划、队列与监听的预算规则，修正 Windows 状态覆盖、真实退出码和终态核验等问题。两个独立会话及短 CPU 任务已实测，资源表与队列复测 101 项通过；正式附件经过跨平台发布门禁，完整范围与历史记录见审查文档。
