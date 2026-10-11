# EvoInquiry

**让科研在证据中持续进化。**

[English](README.md) · [完整 skill 清单](SKILL_AUDIT_CN.md) · [版本下载](https://github.com/Soceremite/EvoInquiry/releases) · [参与贡献](CONTRIBUTING_CN.md)

**1.0 Beta — `v1.0.0-beta.2`**

EvoInquiry 是面向 Codex 的科研工作流工具集，提供 **83 个 Codex skill**，
帮助你从宽泛的研究方向出发，形成具体方案，实施和评估实验，审查证据，
并准备论文与投稿材料。既可以按需使用单个 skill，也可以串联成完整科研流程。

## 能做什么

| 能力 | 适用任务 | 代表 skill |
| --- | --- | --- |
| 文献与知识积累 | 检索论文、梳理相关工作、检查新颖性、维护科研知识库 | `research-lit`、`novelty-check`、`research-wiki` |
| 选题与研究设计 | 探索方向、打磨方法、围绕可检验的主张制定实验方案 | `idea-discovery`、`research-refine`、`experiment-plan` |
| 理论推导与证明 | 整理假设、推导公式、撰写证明、检查证明缺口 | `formula-derivation`、`proof-writer`、`proof-checker` |
| 实验与结果分析 | 实现实验、启动任务、监控进度、分析结果、设计消融 | `experiment-bridge`、`run-experiment`、`analyze-results` |
| 证据审查与评审 | 检查实验完整性、判断结论支持程度、核对引用、质疑替代解释 | `experiment-audit`、`result-to-claim`、`research-review` |
| 论文与图表 | 规划大纲、撰写 LaTeX、制作图表、编译论文 | `paper-plan`、`paper-writing`、`paper-figure` |
| 展示与投稿 | 制作报告和海报、回应评审意见、准备改投材料 | `paper-talk`、`paper-poster-html`、`rebuttal` |
| 项目申请与专利 | 组织基金申请内容、起草专利申请材料 | `grant-proposal`、`patent-pipeline` |

需要全流程时，`research-pipeline` 可以衔接方向探索、实验、评审和论文准备。
各阶段产出的方案、结果、评审报告和研究笔记可供你检查，并作为后续工作的输入。
随着新证据出现，可以通过迭代评审继续修正研究方案与方法。

当前 beta 主要面向 ML、AI 与相关工程科研。
领域专用流程和后端集成见[完整清单](SKILL_AUDIT_CN.md)，请按项目需要选择。

## 安装

请使用提供 `codex plugin` 命令的 Codex 版本。
插件安装已在 Linux 上使用 Codex CLI **0.162.1** 验证。

```sh
git clone --branch v1.0.0-beta.2 https://github.com/Soceremite/EvoInquiry.git EvoInquiry
cd EvoInquiry
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

也可以解压 [Release 下载包](https://github.com/Soceremite/EvoInquiry/releases)，
进入解压后的根目录，再执行上面两个 `codex plugin` 命令。
安装后启动新的 Codex 会话，skill 会以 `evo-inquiry:` 命名空间出现，
例如 `evo-inquiry:research-refine`。

## 从一个具体任务开始

提供项目背景与相关材料，然后告诉 Codex 使用哪个 skill：

> 使用 `evo-inquiry:research-refine` 打磨这个科研方向，明确最接近的已有工作、
> 尚未解决的问题，以及检验该方法需要哪些证据。

> 使用 `evo-inquiry:experiment-plan` 为这个方案制定实验计划，包含基线、
> 评价标准、消融实验与失败条件。

> 使用 `evo-inquiry:result-to-claim` 分析这些原始实验结果，说明它们能支持
> 哪些结论，以及还存在哪些未解决的问题。

> 使用 `evo-inquiry:paper-writing`，根据这份研究报告和配套结果准备论文，
> 投稿目标以项目说明为准。

需要端到端流程时，使用 `evo-inquiry:research-pipeline`，并说明研究方向、
已有工作、目标产物和可用资源。本 beta 安装全部 83 个入口，
其中包括单步工具、总流程和可选服务后端。

可以通过流程检查点设置选择监督方式。`AUTO_PROCEED=true` 时，报告选定路径后
在同一轮继续执行已获授权的工作；显式阻塞的检查点需要用户回复。
`AUTO_PROCEED=false` 启用等待反馈的检查点。整个过程中均遵循项目说明与资源限制。

## 环境配置与 beta 状态

检索服务、外部评审、GPU 平台、图像渲染器和 LaTeX 工具需要各自的依赖，
部分服务还需要凭据。请按实际需要配置，参见
[后端配置与兼容说明](compatibility/codex-backends.md)。

本项目提供的 EvoInquiry 安装方式是上面的 Codex 插件。
随包附带的其他客户端资料与安装资源供参考，各自有独立的兼容条件。

上一 beta 完成了 **777 项测试通过、20 项跳过**，Linux 和 macOS 完整 CI 均通过。
当前版本发布下载包前会运行这两组 CI。详见[验证范围与限制](docs/BETA_VALIDATION.md)。
真实服务与完整科研项目尚未在所有环境和学科中逐一验证。

## 参与贡献

见[贡献说明](CONTRIBUTING_CN.md)。本地检查：

```sh
python -m pip install -r requirements-dev.txt
python tools/verify_evo_inquiry.py
python tools/check_skills_inventory.py
python -m pytest tests/ -q
```

请通过 EvoInquiry Release 更新。Codex 加载的是安装后的缓存副本，
修改源码后需要刷新插件并启动新会话。移动源码目录后，
请重新注册该目录的本地 marketplace。

## 许可证与致谢

采用 MIT 许可证，见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。
EvoInquiry 使用了 [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)
提供的科研工作流工具。
