# EvoInquiry

**让科研在证据中持续进化。**

[English](README.md) · [完整 skill 清单](docs/SKILLS_CATALOG.md) · [版本下载](https://github.com/Soceremite/EvoInquiry/releases) · [参与贡献](CONTRIBUTING_CN.md)

**1.2.0 正式版 — 科研工作流与证据治理**

EvoInquiry 是面向 Codex 的科研工作流工具集，提供 **86 个 Codex skill**，
帮助你从宽泛的研究方向出发，形成具体方案，实施和评估实验，审查证据，
并准备论文与投稿材料。既可以按需使用单个 skill，也可以串联成完整科研流程。

**1.2.0** 将 1.1.0-beta.2 已验收的项目治理、固定执行证据和环境维护能力正式发布，帮助课题在多组实验、方案修订和多人协作中持续推进。治理能力按任务需要启用。具体使用见[治理使用指南](docs/GOVERNANCE_USAGE_CN.md)，实际测试与适用范围见[验收记录](docs/UPGRADE_VALIDATION_CN.md)。已有安装在升级前继续使用其安装版本。

正式版包含方法验证覆盖、虚拟环境启动、导入探测和源码编码兼容改进，以及目录别名和原生 Windows 路径保护。历史冻结记录按原格式核验，覆盖范围见[兼容性验收](docs/PORTABILITY_VALIDATION_CN.md)。

<a id="capabilities"></a>

## 能做什么

| 能力 | 适用任务 | 代表 skill |
| --- | --- | --- |
| 课题接续 | 复用已有证据、定位当前不确定性、协调下一项授权工作 | `research-guide` |
| 项目与证据治理 | 固定实验输入与执行身份、恢复报告发布、规划旧状态迁移 | `project-governance` |
| 环境维护 | 验证独立候选环境、保护排队绑定与论文复现依赖 | `environment-maintenance` |
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

长时间实验会考虑存储预算与有界的断点保留。默认保留最近两个有效的训练恢复点、
按验证指标选出的最佳模型，以及需要交付的最终模型。计划同时考虑并发保存峰值
和已完成实验的累计占用；实现与监控检查实际保存行为和恢复能力。
训练完成或用户明确结束后，验证推理权重，再释放不再需要的恢复状态；完成的
对比实验优先仅保留按验证指标选出的最优模型，同时保护计划中的模型依赖和所有实验记录。
框架集成与可选的本地断点工具见[存储策略](skills/skills-codex/shared-references/experiment-storage.md)。

EvoInquiry 主要面向 ML、AI 与相关工程科研。
领域专用流程和后端集成见[完整清单](docs/SKILLS_CATALOG.md)，请按项目需要选择。

<a id="installation"></a>

## 安装

请使用提供 `codex plugin` 命令的 Codex 版本。
插件安装已在 Linux 上使用 Codex CLI **0.162.1** 验证。

从 [1.2.0 Release](https://github.com/Soceremite/EvoInquiry/releases/tag/v1.2.0)
下载并解压 `evo-inquiry-1.2.0.tar.gz` 或 `.zip`，进入解压后的根目录，
执行下面两个插件命令安装。
Codex CLI 0.162.1 会把安装来源目录复制到缓存，包括本地未跟踪文件；
使用只含公开文件的源码包，可避免复制验证记录、构建目录和 Git 历史。

```sh
cd /path/to/evo-inquiry-1.2.0
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

需要查看和开发源码时，可以使用
`git clone --branch v1.2.0 https://github.com/Soceremite/EvoInquiry.git EvoInquiry`。
安装插件时使用干净的 Release 解压目录。
安装后启动新的 Codex 会话，skill 会以 `evo-inquiry:` 命名空间出现，
例如 `evo-inquiry:research-refine`。

<a id="usage"></a>

## 从一个具体任务开始

提供相关材料、目标和约束，直接用自然语言描述任务，Codex 会选择相关 skill：

> 将这个研究设想细化成简洁、可实现的方法方案，结合项目中的文献笔记，
> 明确最接近的已有工作和未解决的问题。

> 为这个已经确定的方法制定实验计划，包含基线、
> 评价标准、消融实验与失败条件。

> 判断这些原始结果能支持哪些主张，以及还缺哪些证据。

> 继续这个课题，利用已有方案和初步结果，完成当前最有用的分析，
> 再准备受控比较计划；到计划完成为止，暂不启动新实验。

明确的单步任务直接进入对应 skill。阶段不明确或需要跨阶段接续时，
`research-guide` 会检查已有证据，读取实际执行 skill，完成授权工作，
并遵守原有评审门槛与停止条件。局部修改和只要求建议的任务保留原来的范围。
也可以继续显式指定任何已有 skill，例如：

> 使用 `evo-inquiry:analyze-results` 汇总这些 CSV 中各个种子的结果，
> 保存比较表，完成分析后停止。

需要端到端流程时，使用 `evo-inquiry:research-pipeline`，并说明研究方向、
已有工作、目标产物和可用资源。工具集提供 86 个 skill 入口，
包括单步工具、课题协调、总流程和可选服务后端。

如果需要项目级科研使用说明，可以将可选的
[AGENTS.md 片段](templates/EVOINQUIRY_AGENTS_SNIPPET.md)合并到实际科研项目的指令中，
保留该项目已有规则与资源限制。安装插件不会自动把本仓库的 AGENT_GUIDE.md
加载到其他项目中。

可以通过流程检查点设置选择监督方式。`AUTO_PROCEED=true` 时，报告选定路径后
在同一轮继续执行已获授权的工作；显式阻塞的检查点需要用户回复。
`AUTO_PROCEED=false` 启用等待反馈的检查点。整个过程中均遵循项目说明与资源限制。
详见[工作流控制](docs/CUSTOMIZATION_CN.md)与[会话恢复](docs/SESSION_RECOVERY_GUIDE_CN.md)。

<a id="setup"></a>

## 环境配置与验证状态

检索服务、外部评审、GPU 平台、图像渲染器和 LaTeX 工具需要各自的依赖，
部分服务还需要凭据。请按实际需要配置，参见
[后端配置与兼容说明](compatibility/codex-backends.md)。

本项目提供的 EvoInquiry 安装方式是上面的 Codex 插件。
保留的后端与客户端兼容资源用于支持已有流程约定，按需启用并单独配置。

已完成的检查及其适用范围见[发布验收](docs/UPGRADE_VALIDATION_CN.md)及[兼容性验收](docs/PORTABILITY_VALIDATION_CN.md)。
[离线行为评估](docs/SKILL_BEHAVIOR_EVAL.md)使用冻结案例和实际执行轨迹比较自然请求表现。
下载包需要 Linux、macOS 完整 CI，以及 `powershell.exe`、`pwsh` 两组 Windows 原生安装与治理验收全部通过后发布。
真实服务与完整科研项目尚未在所有环境和学科中逐一验证。

<a id="contributing"></a>

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

切换版本或移动来源目录时，进入目标 Release 的干净解压目录，先替换已有 marketplace 来源，再重新安装：

```sh
codex plugin marketplace remove evo-inquiry
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

然后启动新会话，保留当前使用的来源目录。保留旧版目录即可用相同步骤回滚；插件切换不会自动迁移科研项目。存储探测、持久项目部署、备份边界与已验证的版本切换见[部署指南](docs/DEPLOYMENT_GUIDE.md)。

<a id="license"></a>

## 许可证与致谢

采用 MIT 许可证，见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。
EvoInquiry 使用了 [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)
提供的科研工作流工具。
