# EvoInquiry 1.6.3

EvoInquiry connects research framing, literature search, fair experiments, implementation, monitoring, objective analysis, case studies and paper preparation through 89 Codex entrypoints. Each skill keeps its own responsibility and reuses the project's evidence and resource policy.

**1.6.3 improves sustained research work without turning routine reminders into repeated approval gates.** It preserves the existing skill boundaries while improving execution, monitoring and cross-platform reliability.

## New capabilities

- Use an optional per-experiment reminder in the existing session resource table, separate from its standing authorization ceiling. The maximum-available profile still allows individual jobs up to 12 hours; continuation reuses the same user-selected table.
- Read trainer-owned first-step timing receipts in the original execution observer. Exclude engineering preparation, retain training time across resume, and persist deduplicated notices for the monitoring owner.
- Refresh effective GPU, CPU and RAM capacity before planning and launching, preserving the user's device restrictions and other limits when observed hardware changes.
- Support verified cooperative checkpoint-and-stop receipts. Keep actual process exit and checkpoint validity distinct from a recorded stop intention.

## Fixes and corrections

- A two-hour reminder is not a hard deadline for an experiment, a comparison or an entire Goal. A 3.5-hour pilot inside the selected 12-hour allowance does not need another duration approval. Unanswered optional notices keep observation active; silence never expands authorization.
- Serialize final dispatch with workflow review and stop updates. Review holds new dispatch while healthy running jobs remain observed. Prepared jobs deferred by review or resources retain their identity and do not consume a training retry.
- Preserve trainer exit codes through `tee` and require matching terminal evidence. A partial output or missing screen session cannot complete a live or unknown process, and a user cancellation is not an automatic OOM retry.
- Remove the implicit five-second forced-kill deadline. An authorized cooperative stop waits for saving and actual exit; forced termination requires a separate explicit grant. Windows parent-only termination retains descendant reconciliation before lease release.
- Use GPU process inventory and current phase peaks instead of fixed zero/500 MiB memory heuristics. Driver baseline memory alone does not establish occupancy; an idle compute context remains an occupant, and unavailable inventory remains unknown.
- Align pilot, queue, analysis and notification instructions with shared ownership. Finishing an analysis subtask returns to its parent workflow. Notification timeout is unanswered; required approval still needs a real reply, and configuration alone does not authorize external delivery.
- Scope deployment commits to reviewed files and existing authorization, and keep credentials in the existing environment or credential store rather than project guidance.
- Replace existing queue state atomically on native Windows, preserving the previous file on failure. Pipeline acceptance uses Git Bash rather than an unconfigured WSL shim, with normalized shell paths.
- Include the new timing and dispatch regressions in both normal and publication Windows validation lists. Preserve the original workflow baselines and the existing 89/88 Codex/mainline skill inventories.

## Validation and limits

The Linux/Python 3.14.7 full regression produced **1501 passed, 39 skipped and one publication-list failure**. After synchronizing the publication Windows list, all **59 release, plugin, mirror and package checks passed**. These checks overlap; their counts are not additive. The original failed receipt is retained alongside the successful correction. Native Windows follow-ups also passed 107 local queue/package checks and 22 behavior checks; these overlap the larger suites.

Fresh native Codex sessions using **gpt-6.1-sol** passed Goal, Plan and ordinary-dialogue acceptance. Goal continued automatically into a second host turn after an interim analysis and verified a real 210-step CPU task. Plan observed a real 180-step CPU task through natural completion within one read-only turn, without workspace changes. Ordinary dialogue correctly handled the pilot, timing, queue, save/stop, GPU occupancy, notification and deployment scenarios. Runtime regressions include a real six-second checkpoint save and actual CPU children.

These are short engineering fixtures, not hour-long GPU research or proof of universal model compliance. The corrected runtime passed full Linux/macOS regression and both native Windows shell checks in [run 40307318785](https://github.com/Soceremite/EvoInquiry/actions/runs/40307318785). Before this pass, native Windows CI exposed a queue-state replacement bug and two stages of pipeline-fixture portability errors; the fixes and failed receipts remain recorded. Native popup interaction has not been rerun for this patch. Plan-only does not itself schedule another turn. Timing/save receipts need trainer integration; installing a skill does not hot-patch existing frozen owners. Current hardware sampling is not atomic reservation. See the [audit and repair record](docs/AUDIT_1_6_3_CN.md) for reproducible checks and preserved evidence.

## 中文说明

**1.6.3：适时回顾，持续推进，停止有据。**现有 89 个 Codex 入口和 88 个主线 skill 继续各负其责，没有新增调度器、重复资源表或监控所有者。

**预算与计时：** 每个 session 沿用唯一、由用户选择的资源表。两小时可以是软提醒，不能自动变成整个 Goal 的时限或三小时审批线；3.5 小时 pilot 在已选 12 小时额度内无需重复审批。训练从首个实际 step 开始计时，准备另计，续训累计。原执行监听读取真实时钟并记录去重提醒，每次安排和启动前刷新硬件观测。

**派发与队列：** 最终派发与回顾/停止更新共用协调锁。未启动任务的资源或回顾暂缓保持原身份，不算失败、不耗重试；健康在途任务继续监听。保留训练器真实退出码，部分输出、tee 成功或 screen 消失都不能冒充训练成功。

**保存与停止：** 用户同意保存后停止，不等于同意五秒后强杀。协作保存等待实际完成，核验检查点与退出收据；强杀需另有明确授权。独占 GPU 根据真实进程占用判断，不因少量驱动基线显存永久等待，也不把零利用率的已有上下文视为空闲。

**规则协作：** pilot 不再默认超时 kill，分析子任务完成后返回父流程；可选通知未回复继续已有授权工作，必需审批只约束依赖动作。Feishu 配置不提供发送授权，部署不擅自纳入无关改动或将密钥写入项目指导文件。修复 Windows 队列状态覆盖，并在原生 Git Bash 中验证真实管道退出码。

**实测：** 全量回归先得到 1501 通过、39 跳过和 1 项发布清单漏项；补齐后，59 项发布、插件、镜像和包契约复测通过。新建的 Goal、只读 Plan 与普通会话均通过实际使用验收，包含跨轮自动接续、持续观察及真实六秒保存。原生 Windows 还暴露并修复了状态覆盖和测试参数转义问题。修正版已通过 Linux/macOS 全量和两种 Windows PowerShell 检查，见[CI 记录](https://github.com/Soceremite/EvoInquiry/actions/runs/40307318785)。保留原失败证据，不将短程 CPU 结果外推为小时级 GPU 或原生弹窗已验证。
