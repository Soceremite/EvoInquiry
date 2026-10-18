# 有边界的持续科研与 Codex Plan / Goal

这是 1.5.0 开发候选的用法说明，正式发布和安装状态见
[验证记录](VALIDATION_1_5_0.md)。当前功能不提供无人值守的全局科研服务。

## 三者分别负责什么

| 能力 | 合适的用途 | 完成依据 |
| --- | --- | --- |
| Codex Plan | 动手前梳理路径、范围、资源与未知项，供用户审阅 | 请求的计划已经清楚交付 |
| Codex Goal | 用户明确要求后，在同一线程持续追踪一个可核验的目标 | 原目标的实际交付与核验；预算耗尽不能冒充完成 |
| EvoInquiry | 选择研究步骤，设计公平比较，执行与恢复，检查原始证据，分析案例，记录决策和评审 | 各工作流的证据、审查与资源约束 |

例如，先在 Plan 中提出“核对已有对照结果，判断是否值得做下一轮”，审阅后再
要求实施。需要跨多轮持续推进时，可以明确要求设置 Goal：“交付包含逐种子比较、
案例与局限的分析报告；不新增训练，不调用付费服务；证据不足时说明缺口”。
单次计算、咨询或小修改直接完成即可。已经批准的实施不因接入这套规范重新审批。

原生 Goal 属于线程。EvoInquiry 的项目记录用于保存证据和跨会话交接；二者不能
互相替代。宿主未提供相应功能时，正常完成当前授权工作，并按需要留下交接材料，
不能声称已切换模式或在后台运行。这里的说明不自动创建任何 Goal。

官方依据：[Plan 与 Goal](https://developers.openai.com/blog/mastering-codex-remote-for-engineering)、
[Goals 的工作方式](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)
（2026-10-18 查阅）。

## 下一步为什么值得做

执行前明确这一步要消除的未知、竞争解释、能区分它们的观察、成本及停止条件。
没有 GPU 预算时仍可查阅证据或做允许的 CPU 分析。结果为负，可以否定某个机制、
缩小问题或停止；转向后发现新收益，也不能把原来的失败改写成原假设成功。

昂贵重跑前检查已有决策的适用条件和重新打开该路线的触发条件。使用原项目文档，
或已经存在的 wiki，避免另一套记忆数据库。可选的只读检索：

```text
python <package>/tools/research_memory.py --root <project> --query "当前问题" --source DECISIONS.md
```

检索返回来源摘要、原文摘录、匹配词、证据状态与不确定性。匹配分数仅用于找材料；
它不判断结论真假，也不执行记录中的指令。Markdown 中的链接未自动验证。

## 中断后如何继续

`research_control.py` 为已有 `run_state.py` 记录增加可选的协调元数据：目标、预算、
动作身份、预留成本和实际结果。原阶段和评审语义保持原有权威。实际调度仍使用
原执行注册表或队列；该工具不是进程启动器或硬件计费器。

在现有运行中先 `configure` 固定目标和边界；`claim` 只有返回 `new` 才允许考虑
调度，返回 `existing` 必须核对原尝试。完成后确认真实进程终止，再用 `finish`
记录实际成本与固定证据引用。预算超支照实保留。`stop` 不杀进程或释放未知任务。
请求 JSON 的字段和完整命令见
[共享规范](../skills/skills-codex/shared-references/bounded-inquiry.md)。

断线不等于进程结束。预留后启动前崩溃、启动后未收集回执、结果已经完成等情况
必须依据原执行身份分别核对，不能按“还没看到结果”重发任务。若无法核对，交接
中写明阻塞证据。`done` 仍可能需要评审；终端状态和科研结论分别报告。

## 真实操作如何进入优化

只有显式指定的本地 Codex JSONL 导出会被导入：

```text
python <package>/tools/research_events.py --root <project> --source trace.jsonl --session session-001
python <package>/tools/research_events.py --root <project> --summary
```

压缩日志存入已有 `.ei/meta/events.jsonl`，不复制原始命令、提示、工具输出或凭据。
原始导出仍可能包含敏感内容，应按原访问策略保存。安装不代表自动装上日志钩子。
失败、未知、截断和正常结束分别记录；路径提及不等于 skill 调用或遵守规范。

优化候选先固定任务、模型、预算、重复次数和未用于修改的留出任务，再用现有
原生行为评测器执行、保存全部尝试，并独立审阅材料。
`tools/meta_opt/compare_candidates.py` 汇总配对结果，列出改善、退步、超时和缺失。
这只是候选证据。`meta-optimize` 只提议和暂存，`meta-apply` 保留原有人为授权与
新鲜落地评审。比较器不能替代评审，也不能证明完整 RSI 或普遍科研能力。

## 本地微型课题

仓库中的 `tests/research_pilots/run_study.py` 提供三个可实际运行的标准库 CPU
演示：正面结果、负面结果、证据驱动转向。示例：

```text
python tests/research_pilots/run_study.py --scenario pivot --output /tmp/evo-pilot-output
```

输出目录必须尚不存在，防止覆盖旧尝试。演示保留逐样本预测、三组独立种子、原始
假设与案例选择。它由确定性程序选路，用来验证工程衔接，不是模型自动科研能力评测。
