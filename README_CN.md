# EvoInquiry

**让科研在证据中持续进化。**

[English](README.md) · [科研原则](skills/skills-codex/shared-references/evo-inquiry.md) · [子 skill 审计](SKILL_AUDIT_CN.md) · [版本记录](CHANGELOG.md)

**1.0 Beta — `v1.0.0-beta.1`**

EvoInquiry 将继承自 [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)
的 **83 个 Codex skill** 与六条共享科研原则结合，覆盖文献、选题、实验、
评审、证明和论文写作，让结论的范围与证据相匹配。

六条原则是：独立判断、扎根问题与证据、解释上的简洁、能区分解释的研究、
诚实结论、反思与进展。各 skill 按任务读取相关原则，并将它们带入子任务与
评审简报。项目自身的约束仍然适用；原则不规定通用算力预算，也不授权额外行动。

## 安装 beta

当前在 Linux 上验证过 Codex CLI **0.162.1**。请使用提供 `codex plugin`
命令的 Codex 版本。

克隆 beta 标签，再将目录注册为本地 marketplace：

```sh
git clone --branch v1.0.0-beta.1 https://github.com/Soceremite/EvoInquiry.git evo-inquiry
cd evo-inquiry
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

也可以下载并解压 Release 归档，进入解压后的根目录，执行上面两个
`codex plugin` 命令。启动新的 Codex 会话，目录中应出现
`evo-inquiry:research-refine` 等入口。

已有 ARIS 或旧版 Lyd's Compass 的用户，启用 EvoInquiry 时应停用旧插件，
保留旧包以便回退。Codex 加载的是安装后的缓存副本；修改源码后需要重新安装
或刷新插件，并开启新会话。

## 使用

可以直接要求 Codex 使用对应的命名空间入口，例如：

> 使用 `evo-inquiry:research-refine` 打磨这个科研方向，区分假设、现有证据
> 和尚未解决的问题。

> 使用 `evo-inquiry:result-to-claim` 分析这些原始结果能支持哪些结论，
> 还存在哪些替代解释。

流程检查点设置沿用原有含义：`AUTO_PROCEED=true` 时，报告选定路径后继续
在同一轮执行已获授权的工作；显式阻塞的检查点仍需用户回复。
请按项目的监督需求选择模式。

本 beta 安装全部 83 个入口。[审计清单](SKILL_AUDIT_CN.md)给出了
“45 个核心候选＋38 个可选入口”的提案，目前没有按该提案裁剪安装。
其中既有总流程，也有单步工具和可替换后端，不能仅凭名称相近就删除。
`paper-poster` 是保留的弃用跳转入口，新海报任务使用 `paper-poster-html`。

## 后端与 beta 范围

安装插件会提供 skill 和随包辅助工具。检索服务、第三方评审、GPU 平台、
图像渲染器和 LaTeX 工具需要各自的依赖与必要凭据。按实际需求配置后端；
使用通用/MiniMax 评审或 image2 前，请阅读[Codex 后端兼容说明](compatibility/codex-backends.md)。

继承的执行流程主要面向 ML/AI 与相关工程科研。原则可跨项目使用，但尚未验证
所有学科方法。保留的 Claude Code 等客户端包沿用上游实现，本 beta 不为它们
加入 EvoInquiry 原则层。

开发阶段完成了 **777 项测试通过、20 项跳过**，新会话成功发现全部入口，
带空格的目录迁移验证也通过。详见[验证范围](docs/BETA_VALIDATION.md)。
真实第三方服务、完整科研流程和所有操作系统尚未逐一验证。
自动评审分数不能证明科研结论成立。

## 参与和维护

见[贡献说明](CONTRIBUTING_CN.md)。本地检查：

```sh
python -m pip install -r requirements-dev.txt
python tools/verify_evo_inquiry.py
python tools/check_skills_inventory.py
python -m pytest tests/ -q
```

请按 EvoInquiry 标签更新。保留的 ARIS 安装与更新脚本面向上游 ARIS，
直接用于更新本定制版可能丢失原则层。整合新的上游快照时，应在独立分支
重新应用定制层，并通过兼容与回归检查。

## 来源和许可证

基于 wanshuiyin 的 ARIS 快照 `3b19a22dc5a64c983d2eafd6c2c94000fadc4f8d`，
EvoInquiry 定制由 lyd 完成。保留原有 skill 正文、MIT 许可证及作者署名；
见 [NOTICE](NOTICE) 和 [LICENSE](LICENSE)。原版文档保存在
[README_ARIS.md](README_ARIS.md) 与 [README_CN_ARIS.md](README_CN_ARIS.md)。
