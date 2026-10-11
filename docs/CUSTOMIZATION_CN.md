# 工作流控制

[English](CUSTOMIZATION.md) · [README](../README_CN.md)

向选定的 skill 提供研究方向、已有材料、目标产物和资源限制。
具体支持哪些参数及其默认值，以该 skill 的 `SKILL.md` 为准。
流程向下传递的参数，只在下游 skill 支持时生效。

| 控制项 | 含义 |
| --- | --- |
| `AUTO_PROCEED=true` | 报告选定路径，并在同一轮继续执行已获授权的工作 |
| `AUTO_PROCEED=false` | 在选择检查点暂停，收到明确回复后继续 |
| `human checkpoint: true` | 在 skill 定义的评审检查点请求反馈 |
| `venue: <目标>` | 指明投稿目标及其适用要求 |
| `gpu: local` 或 `gpu: remote` | 选择可用算力；远程运行时提供服务器与环境信息 |
| `sources: <可用来源>` | 选择本项目已配置的文献来源 |
| `effort: lite`、`balanced`、`max` 或 `beast` | 选择该 skill 支持的工作深度 |
| `assurance: draft`、`polished`、`conference-ready` 或 `submission` | 在支持的流程中选择必要的审计等级 |

例如：

> 使用 `evo-inquiry:research-pipeline` 处理这个方向。设置
> `AUTO_PROCEED=false`，使用已提供的本地 GPU，并面向指定投稿目标。

在任务中说明 GPU 小时上限、并行任务数、评审轮数、费用上限和停止条件，
启动前核对具体方案。评审分数只是流程信号，研究结论仍需实际证据支持。

显式阻塞的检查点、缺失的必要输入和外部操作，仍遵循各自的授权规则。
一轮结束后的沉默不会恢复被阻塞的流程。`AUTO_PROCEED=true` 只作用于其选择检查点，
不会授权无关操作或额外开支。

项目专属约束放在项目说明中。按[会话恢复说明](SESSION_RECOVERY_GUIDE_CN.md)
保存已完成材料与待办事项。
