# 有边界的持续科研与 Codex Plan / Goal

这是 1.5.0 的用法说明，正式发布和安装状态见
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

明确授权的持续研究已有所属 run 和资源边界时，默认在昂贵准备前接入；外部已
提供等价的动作身份、预留、对账和全局预算时，可以记录其所有者并复用。
单独的外层超时不具备动作恢复能力。咨询、纯规划和小修改不需要初始化。

在现有运行中先 `configure` 固定目标和边界；`claim` 只有返回 `new` 才允许考虑
调度，返回 `existing` 必须核对原尝试。完成后确认真实进程终止，再用 `finish`
记录实际成本与固定证据引用。预算超支照实保留。`stop` 不杀进程或释放未知任务。
请求 JSON 的字段和完整命令见
[共享规范](../skills/skills-codex/shared-references/bounded-inquiry.md)。

对注册执行，可在启动前把已准备执行的 `snapshot_ref` 放入动作 `input_refs`，并将
`workflow_run_id` 绑定原 run。结束或恢复时用 `settle-execution --request <JSON>`：
请求包含 `action_id`、`execution_run_id`、观察到的 `actual_costs` 和可选 `result_refs`。
工具核验真实终态和绑定后结算，不重新运行，也不接受科研阶段；相同结算可重复调用。
结果文件可以是列表、CSV 或二进制，不必为记账重写科学输出格式。

已有 runner 足够时直接复用。需要适配时，先用零拟合样例检查结果读取和结算路径；
导入探测仅说明其实际检查范围，不能伪装成完整环境冻结。报告在取得首个有用事实后
即保存并逐步更新，避免最后才开始收尾。

断线不等于进程结束。预留后启动前崩溃、启动后未收集回执、结果已经完成等情况
必须依据原执行身份分别核对，不能按“还没看到结果”重发任务。若无法核对，交接
中写明阻塞证据。`done` 仍可能需要评审；终端状态和科研结论分别报告。

### 保留原始预算并预留收尾

```text
python <package>/tools/research_control.py --root <project> --run-id <id> configure --objective "交付有证据的分析" --limits limits.json --started-at <原始带时区ISO时间> --closeout-seconds 90
python <package>/tools/research_control.py --root <project> --run-id <id> inspect
```

90 秒只是示例，应按实际工作设置；收尾包含在原始 wall_seconds 中。恢复时不能
刷新起点。旧调用兼容，默认预留为零。inspect 返回截止、当前剩余和可派发时间；
进入 CLOSEOUT_REQUIRED 后禁止新 claim，已有动作仍可对账和 finish。该工具不
终止进程，需要把实际执行/复核超时设置在剩余可派发时间内。

### 核对交接是否过时

```text
python <package>/tools/research_control.py --root <project> --run-id <id> handoff --watch ENVIRONMENT.json --watch DATASET_MANIFEST.json
python <package>/tools/research_control.py --root <project> --run-id <id> check-handoff --receipt HANDOFF_STATE.json
```

第一条只输出 JSON，在最后一次相关状态更新后保存到现有交接位置，不要把交接
哈希回写入被监测的 run。第二条重新读取来源，CURRENT 退出 0，STALE 退出 3，
参数或读取错误退出 2。文件从缺失到出现、内容变更、删除以及 run 更新都会被
发现；预算重新计算，不沿用保存的剩余秒数。选择少量 manifest/receipt 即可。
检查不会写状态或接受评审；CURRENT 仅覆盖选定文件身份，不能证明科研结论。

### 在预算内推进与复核

先核对输入、解释器并复用有效收据，争取尽早运行最小可区分实验。预先声明允许的
配置/种子范围、波次成本、结果分支和停止条件；范围内复用审查，关键方法/数据/
指标/源码变化须重新核验。没有必须完成的波次数，负结果可合理停止。

复核应提供准确范围、必要证据、截止和输出路径，先保存 INCOMPLETE、覆盖范围和
阻塞项，再渐进更新。超时不能把中途评论当成正式通过；同系列新上下文复核仍按
原门禁作为 provisional。保留时间交付正式结论或清楚标明尚未完成的检查。

## 真实操作如何进入优化

只有显式指定的本地 Codex JSONL 导出会被导入：

```text
python <package>/tools/research_events.py --root <project> --source trace.jsonl --session session-001
python <package>/tools/research_events.py --root <project> --summary
```

压缩日志存入已有 `.ei/meta/events.jsonl`，不复制原始命令、提示、工具输出或凭据。
原始导出仍可能包含敏感内容，应按原访问策略保存。安装不代表自动装上日志钩子。
失败、未知、截断和正常结束分别记录；路径提及不等于 skill 调用或遵守规范。
一次导入按批次校验和原子写入，避免每条事件反复读取整份来源和重写日志。
重复导入保持幂等；并发导入使用同一锁，替换失败时保留原日志。

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
