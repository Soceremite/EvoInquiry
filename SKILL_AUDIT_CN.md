# EvoInquiry 子 skill 审计

审查日期：2026-10-11。对象：继承的 ARIS 快照
`3b19a22dc5a64c983d2eafd6c2c94000fadc4f8d`，不是对所有历史版本或最新上游版本的判断。

## 数量与范围

Codex 实际发现目录包含 **83 个子 skill**。六条科研原则是一个共享参考文件，
不额外计为六个子 skill。仓库中另有其他客户端的镜像和评审后端变体，
它们不叠加到本插件的 83 个入口中。

| 上游目录分组 | 数量 |
|---|---:|
| 文献检索 | 10 |
| 选题与方向 | 9 |
| 科研评审 | 5 |
| 公式与证明 | 4 |
| 实验与算力 | 16 |
| 论文主线与报告 | 13 |
| 配图与展示 | 10 |
| 投稿与基金 | 3 |
| 专利 | 9 |
| 元工具与杂项 | 4 |

上游分类存在一个已确认问题：`specification-writing` 是专利说明书撰写，
却被 catalog 放进论文组并描述为“技术规格文档”。按实际用途归类，论文组应为 12，
专利组应为 10，总数仍为 83。当前保留上游 catalog，审计清单标明真实用途。

## 明确弃用

`paper-poster` 在 frontmatter 和正文明确标注 DEPRECATED / retired，
只把参数传给 `paper-poster-html`。新任务应使用后者。
它是兼容旧调用的别名，不应算作另一套有效海报流程；本次保留该别名。

## 重叠与互补

剥离 frontmatter 和本次添加的共同原则块后，83 个正文没有完全相同的文件。
这个结果只排除了逐字重复，不证明功能上没有冗余。

| 入口 | 判断与处理建议 |
|---|---|
| `auto-review-loop` / `auto-review-loop-llm` / `auto-review-loop-minimax` | 相同的评审循环目标、不同后端，存在流程重复维护成本。通用入口优先，第三方后端按需启用；后续统一适配器前必须核对停止条件、恢复状态和产物合同。 |
| `paper-illustration` / `paper-illustration-image2` | 替代渲染后端；image2 明确为实验性，并保留 Claude 规划者描述。应按实际渲染器可用性选择。 |
| `arxiv` / `semantic-scholar` / `openalex` / `alphaxiv` / `deepxiv` / `gemini-search` / `exa-search` | 来源、元数据或阅读方式不同。可以减少默认入口，但不能据此认定检索覆盖完全等价。 |
| `research-refine` / `research-refine-pipeline` | 后者编排前者和实验计划；是组合与步骤的关系。 |
| `research-pipeline` / `idea-discovery` / `experiment-bridge` / `paper-writing` | 总编排、阶段编排与步骤的关系，保留其依赖。 |
| `analyze-results` / `result-to-claim` / `experiment-audit` / `paper-claim-audit` / `citation-audit` | 分别负责统计、结论支撑、实验完整性、文稿数值溯源、引用真实性；互补，不能一起合并或删除。 |
| `monitor-experiment` / `training-check` | 进度与产物收集、训练健康检查，关注点不同。 |
| `formula-derivation` / `proof-writer` / `proof-checker` / `proof-orchestrator` | 理论组织、证明撰写、证明验证、长期证明项目编排，不能只按“证明”关键词裁剪。 |
| `paper-slides` / `paper-talk` / `slides-polish` | 幻灯片生成、演讲编排、逐页打磨，存在显式调用依赖。 |

## 已确认的配置与适配问题

1. `auto-review-loop-llm` 的 Codex 配置示例使用 `~/.codex/settings.json`
   和 `mcpServers`。当前 Codex 使用 `config.toml` 和 `[mcp_servers.<name>]`。
   同一个 skill 的 curl JSON 示例处于单引号中，`${LLM_MODEL}` 不会展开。
   两个第三方循环的 MCP 示例还使用 `message` 参数，而随包服务要求 `prompt`。
2. `auto-review-loop-minimax` 把 `~/.codex/settings.json` 写成读取 key 的路径；
   在 Codex 中不应把它当成正常用户配置来源。环境变量路径仍可以使用。
3. `paper-illustration-image2` 是实验性入口，存在 Claude/Codex 文案混用，
   必须验证实际 bridge/helper 后才能宣称此后端可用。

EvoInquiry 为以上三个入口加入了定向兼容说明，保留原始正文及产物合同。
这些是文档与路由纠正，**不是第三方服务的端到端运行通过**。
具体操作见 [Codex 后端兼容说明](compatibility/codex-backends.md)。
配置依据：[OpenAI 官方 MCP 文档](https://developers.openai.com/codex/mcp)。
旧模型名称或 fallback 的存在，不能单独作为“整个 skill 已落后”的证据。
本次没有用付费请求逐一确认所有供应商型号、接口和检索服务。

## 面向多人使用的建议

保留完整发行包，提供“通用科研核心 + 可选模块”的入口配置，比删除目录更安全。
下面的 **45 个核心入口、38 个可选入口只是配置提案，尚未裁剪当前安装**。
核心提案涵盖选题、文献、实验、证明、论文、投稿与知识库。
其闭包按上游 `tools/skill-groups.tsv` 的默认调用依赖计算；
可选分支仍可能需要额外入口，不能把 catalog 当成完整运行时验证。
机器可读清单见 [docs/skill-inventory.json](docs/skill-inventory.json) 和
[docs/proposed-core-skills.txt](docs/proposed-core-skills.txt)。

专利（10 个真实用途入口）、机器人/通信/系统论文特化、启智/Vast/Modal 平台、
第三方评审、演示与海报、飞书通知、像素画、面试准备等，应按人群和任务选择。
它们是可选，不是落后。元优化模块修改的是 skill 自身，不能混同日常科研任务。

科研原则面向跨学科判断；继承的执行流程目前主要面向 ML/AI 与相关工程科研。
本次没有验证所有学科方法；公开 beta 的验证范围见
[docs/BETA_VALIDATION.md](docs/BETA_VALIDATION.md)。
稳定发行前，还需要不同操作系统、不同安装路径、真实后端和实际科研任务的验证。

## 全部 83 个入口

“核心候选”表示上述提案的依赖闭包，不代表在所有环境均已验证可用。

| 子 skill | 实际分组 | 提案角色 | 默认依赖 |
|---|---|---|---|
| `arxiv` | 文献检索 | 核心候选 | 无 catalog 默认依赖 |
| `alphaxiv` | 文献检索 | 核心候选 | 无 catalog 默认依赖 |
| `deepxiv` | 文献检索 | 可选 | 无 catalog 默认依赖 |
| `semantic-scholar` | 文献检索 | 核心候选 | 无 catalog 默认依赖 |
| `openalex` | 文献检索 | 核心候选 | 无 catalog 默认依赖 |
| `exa-search` | 文献检索 | 可选 | 无 catalog 默认依赖 |
| `web-debug-search` | 文献检索 | 可选 | 无 catalog 默认依赖 |
| `gemini-search` | 文献检索 | 可选 | 无 catalog 默认依赖 |
| `research-lit` | 文献检索 | 核心候选 | 无 catalog 默认依赖 |
| `comm-lit-review` | 文献检索 | 可选 | 无 catalog 默认依赖 |
| `idea-creator` | 选题与方向 | 核心候选 | 无 catalog 默认依赖 |
| `idea-discovery` | 选题与方向 | 核心候选 | `idea-creator`, `novelty-check`, `research-lit`, `research-review`, `research-refine-pipeline`, `research-refine`, `render-html` |
| `idea-discovery-robot` | 选题与方向 | 可选 | `idea-creator`, `novelty-check`, `research-lit`, `research-review` |
| `novelty-check` | 选题与方向 | 核心候选 | 无 catalog 默认依赖 |
| `research-refine` | 选题与方向 | 核心候选 | 无 catalog 默认依赖 |
| `research-refine-pipeline` | 选题与方向 | 核心候选 | `research-refine`, `experiment-plan` |
| `research-wiki` | 选题与方向 | 核心候选 | 无 catalog 默认依赖 |
| `wiki-enrich` | 选题与方向 | 核心候选 | `research-wiki` |
| `research-pipeline` | 选题与方向 | 核心候选 | `idea-discovery`, `experiment-bridge`, `auto-review-loop`, `render-html` |
| `research-review` | 科研评审 | 核心候选 | 无 catalog 默认依赖 |
| `auto-review-loop` | 科研评审 | 核心候选 | `result-to-claim`, `training-check`, `render-html` |
| `auto-review-loop-llm` | 科研评审 | 可选；配置纠正 | 无 catalog 默认依赖 |
| `auto-review-loop-minimax` | 科研评审 | 可选；配置纠正 | 无 catalog 默认依赖 |
| `kill-argument` | 科研评审 | 核心候选 | `render-html` |
| `formula-derivation` | 公式与证明 | 核心候选 | 无 catalog 默认依赖 |
| `proof-writer` | 公式与证明 | 核心候选 | 无 catalog 默认依赖 |
| `proof-checker` | 公式与证明 | 核心候选 | `render-html` |
| `proof-orchestrator` | 公式与证明 | 核心候选 | 无 catalog 默认依赖 |
| `experiment-plan` | 实验与算力 | 核心候选 | 无 catalog 默认依赖 |
| `experiment-bridge` | 实验与算力 | 核心候选 | `run-experiment`, `experiment-queue`, `monitor-experiment`, `training-check`, `ablation-planner` |
| `research-implement-feature` | 实验与算力 | 核心候选 | 无 catalog 默认依赖 |
| `experiment-queue` | 实验与算力 | 核心候选 | 无 catalog 默认依赖 |
| `run-experiment` | 实验与算力 | 核心候选 | 无 catalog 默认依赖 |
| `monitor-experiment` | 实验与算力 | 核心候选 | 无 catalog 默认依赖 |
| `analyze-results` | 实验与算力 | 核心候选 | 无 catalog 默认依赖 |
| `training-check` | 实验与算力 | 核心候选 | 无 catalog 默认依赖 |
| `system-profile` | 实验与算力 | 核心候选 | 无 catalog 默认依赖 |
| `dse-loop` | 实验与算力 | 可选 | 无 catalog 默认依赖 |
| `qzcli` | 实验与算力 | 可选 | 无 catalog 默认依赖 |
| `vast-gpu` | 实验与算力 | 可选 | 无 catalog 默认依赖 |
| `serverless-modal` | 实验与算力 | 可选 | 无 catalog 默认依赖 |
| `experiment-audit` | 实验与算力 | 核心候选 | 无 catalog 默认依赖 |
| `result-to-claim` | 实验与算力 | 核心候选 | 无 catalog 默认依赖 |
| `ablation-planner` | 实验与算力 | 核心候选 | 无 catalog 默认依赖 |
| `paper-writing` | 论文主线与报告 | 核心候选 | `paper-plan`, `paper-write`, `paper-compile`, `paper-figure`, `figure-spec`, `proof-checker`, `paper-claim-audit`, `citation-audit`, `auto-paper-improvement-loop`, `integrity-forensics`, `kill-argument` |
| `paper-plan` | 论文主线与报告 | 核心候选 | 无 catalog 默认依赖 |
| `paper-write` | 论文主线与报告 | 核心候选 | 无 catalog 默认依赖 |
| `paper-compile` | 论文主线与报告 | 核心候选 | 无 catalog 默认依赖 |
| `paper-figure` | 论文主线与报告 | 核心候选 | 无 catalog 默认依赖 |
| `citation-audit` | 论文主线与报告 | 核心候选 | `render-html` |
| `paper-claim-audit` | 论文主线与报告 | 核心候选 | `render-html` |
| `integrity-forensics` | 论文主线与报告 | 核心候选 | 无 catalog 默认依赖 |
| `auto-paper-improvement-loop` | 论文主线与报告 | 核心候选 | `proof-checker`, `paper-claim-audit`, `kill-argument` |
| `writing-systems-papers` | 论文主线与报告 | 可选 | 无 catalog 默认依赖 |
| `specification-writing` | 专利 | 可选 | `embodiment-description`, `figure-description` |
| `overleaf-sync` | 论文主线与报告 | 可选 | 无 catalog 默认依赖 |
| `render-html` | 论文主线与报告 | 核心候选 | 无 catalog 默认依赖 |
| `paper-illustration` | 配图与展示 | 可选 | 无 catalog 默认依赖 |
| `paper-illustration-image2` | 配图与展示 | 可选；实验性 | 无 catalog 默认依赖 |
| `figure-spec` | 配图与展示 | 核心候选 | 无 catalog 默认依赖 |
| `mermaid-diagram` | 配图与展示 | 可选 | 无 catalog 默认依赖 |
| `pixel-art` | 配图与展示 | 可选 | 无 catalog 默认依赖 |
| `paper-poster` | 配图与展示 | 弃用兼容别名 | `paper-poster-html` |
| `paper-poster-html` | 配图与展示 | 可选 | 无 catalog 默认依赖 |
| `paper-slides` | 配图与展示 | 可选 | 无 catalog 默认依赖 |
| `paper-talk` | 配图与展示 | 可选 | `paper-slides`, `slides-polish` |
| `slides-polish` | 配图与展示 | 可选 | 无 catalog 默认依赖 |
| `rebuttal` | 投稿与基金 | 核心候选 | `render-html` |
| `resubmit-pipeline` | 投稿与基金 | 核心候选 | `auto-paper-improvement-loop`, `proof-checker`, `paper-claim-audit`, `citation-audit`, `kill-argument`, `paper-compile`, `integrity-forensics` |
| `grant-proposal` | 投稿与基金 | 可选 | `research-lit`, `novelty-check`, `research-review` |
| `patent-pipeline` | 专利 | 可选 | `prior-art-search`, `patent-novelty-check`, `invention-structuring`, `claims-drafting`, `specification-writing`, `patent-review`, `jurisdiction-format` |
| `invention-structuring` | 专利 | 可选 | 无 catalog 默认依赖 |
| `claims-drafting` | 专利 | 可选 | 无 catalog 默认依赖 |
| `embodiment-description` | 专利 | 可选 | 无 catalog 默认依赖 |
| `figure-description` | 专利 | 可选 | 无 catalog 默认依赖 |
| `jurisdiction-format` | 专利 | 可选 | 无 catalog 默认依赖 |
| `patent-review` | 专利 | 可选 | 无 catalog 默认依赖 |
| `prior-art-search` | 专利 | 可选 | 无 catalog 默认依赖 |
| `patent-novelty-check` | 专利 | 可选 | 无 catalog 默认依赖 |
| `meta-optimize` | 元工具与杂项 | 可选 | 无 catalog 默认依赖 |
| `meta-apply` | 元工具与杂项 | 可选 | `meta-optimize` |
| `feishu-notify` | 元工具与杂项 | 可选 | 无 catalog 默认依赖 |
| `interview-cheatsheet` | 元工具与杂项 | 可选 | 无 catalog 默认依赖 |
