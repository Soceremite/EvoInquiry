# EvoInquiry 1.4.0

EvoInquiry connects research exploration, literature, method design, experiments, evidence review and paper preparation through **88 Codex skills**. Version 1.4.0 helps turn an uncertain direction into testable questions, keep research decisions connected to evidence, and explain results using both measurements and concrete cases. Focused tasks remain focused; longer workflows are available when requested.

## New capabilities

**Problem framing before implementation.** The new `scientific-brainstorming` skill explores plausible questions, competing explanations, prior-work overlap and inexpensive discriminating tests. It makes assumptions and resource constraints explicit before committing to a method or launching experiments.

**Research decisions that survive a handoff.** The new `research-manager` skill records decisions, supporting evidence, alternatives, blockers and authorized next steps in existing project records. It helps resume work across sessions without creating a parallel project registry or treating a completed planning document as scientific acceptance.

**Proactive case studies alongside metrics.** Substantive result analysis now inspects available sample-level outputs by default: classification errors, regression residuals, generated images or timestamped video evidence. Selection records preserve pairing, improvements, regressions and missing coverage; the same evidence can feed figure panels and paper outlines. Narrow numerical questions stay concise. Missing predictions or media are reported, and new inference is not launched automatically.

**Traceable literature and figures.** Literature helpers retain source identity, versions, reading scope, conflicts and export order while selecting relevant available search sources. Figure receipts connect actual input data, editable source, rendered output and captions. Existing search providers, plotting tools and optional illustration backends remain separate capabilities with their own setup requirements.

## Bug fixes

- Correct runtime-relative guidance links, verify loaded plugin variants and preserve noncanonical reads as separate runtime findings.
- Stop completed framing from becoming the resume target again; bind its completion to a nonempty artifact without bypassing later scientific review.
- Give generated Claude reviewers read-only access to the supplied artifacts, and keep primary and material negative results visible during paper improvement.
- Preserve interrupted decision history and Unicode output, stabilize literature exports, and reject figure path aliases or invalid geometry.
- Preserve supplied weights and resource quantities in experiment plans; produce the requested blocked-run tracker even when cumulative storage makes execution infeasible.
- Add literature, decision, workflow-version and figure-evidence tests to both native Windows release gates, with a regression that detects omitted publication coverage.

## Corrected analysis and review

Observed ranking, effect size, uncertainty and practical value are reported separately. A challenge triggers evidence checking rather than automatic agreement or criticism. Positive results, regressions, missing populations and alternative explanations remain visible, and repeated findings are consolidated to keep reports proportionate to the question.

Local assessment of supplied records no longer forces a full execution-certification workflow. Formal claim acceptance retains its independent review requirements: unavailable, stopped or incomplete review grants no acceptance. Metric normalization is judged against its definition, comparison protocol and actual claim. Valid precision/F1/IoU formulas and disclosed display scaling are not failures by themselves; a rescaled display score cannot establish absolute accuracy, calibration or relative improvement.

## Compatibility and validation

The package contains **88 Codex entrypoints** and **87 mainline entries**. Frozen preservation baselines cover the original **83 workflows and 450 resources**, with directed adaptations pinned separately. Existing fair-comparison, checkpoint-retention, evidence-archival and scientific-review gates remain in place. Old project records keep their versioned contracts; switching the plugin does not migrate project state.

The validated implementation passed **1,150 local tests, with 38 skips**, and [Ubuntu, macOS and both native Windows shell CI jobs](https://github.com/Soceremite/EvoInquiry/actions/runs/38991160599). A separate publication-coverage regression reproduced the missing Windows modules before the fix and passed afterward. The final release tag must pass its own Linux/macOS full suites and both Windows gates before GitHub publishes the archives.

Natural-request validation includes objective interpretation, routing, literature, figures, storage, handoffs and legacy workflows. Original timeouts, noncanonical reads, blocked scientific reviews and the user's case-specific acceptance of J05 remain recorded. Targeted repairs have their own prospective receipts; they do not erase earlier failures or prove a general advantage over 1.3.0. Same-family implementation reviews and synthetic cases do not certify research correctness or image-understanding quality. See the [validation record](https://github.com/Soceremite/EvoInquiry/blob/v1.4.0/docs/VALIDATION_1_4_0.md) and [machine-readable summary](https://github.com/Soceremite/EvoInquiry/blob/v1.4.0/release-validation.json) for exact sources, scopes and limitations.

Optional provider integrations require configuration and are not all verified end to end. Checkpoint cleanup and governance depend on supported filesystem operations; a failed lock probe remains a blocker. No new distributed-training, network-filesystem or power-loss guarantee is added.

## 中文说明

EvoInquiry 1.4.0 提供 **88 个 Codex skill**，覆盖选题、文献、方法、实验、审查、证明、论文和展示。本次升级让模糊研究方向更容易落到可检验的问题，让决策能够追溯到证据，也让实验分析主动关注真实样例中的改善与失败。

**新增功能：** `scientific-brainstorming` 用于问题界定、竞争解释和低成本区分性验证；`research-manager` 在已有项目记录中保存决策、备选方案、阻碍和交接。完整结果分析主动开展案例研究，按分类、回归、图像生成和视频理解任务选择合适证据，保留配对、选样理由、退化与覆盖缺口。文献记录区分元数据、摘要和实际阅读内容；图件关联真实输入、可编辑源文件、输出与图注。

**修复问题：** 修正安装变体的相对引用和完成阶段的恢复定位，保留中断决策与 Unicode 输出，稳定文献导出，拒绝图件路径别名和无效几何。实验计划保留用户给出的权重大小等资源信息，即使预算不可行也交付明确阻塞的任务表。两个 Windows 发布门禁补齐文献、决策、流程版本和图件测试，防止普通 CI 已测而发布 CI 漏测。

**修正规范：** 客观报告指标排序、效果大小、不确定性和实际价值，用户质疑后回看证据，避免迎合或无依据地否定结果。局部材料分析与正式实验认证区分处理；正式结论依然需要原有独立审查。正常指标公式和已声明的显示归一化不再被一概判错，但显示分数不能被用于推导绝对准确率、校准性或相对提升。简短问题保持简短，没有逐样本输出时说明缺口，不编造案例，也不擅自新增推理。

**验证范围：** 当前实现本地全套测试为 1,150 项通过、38 项跳过，Linux、macOS 和两种原生 Windows Shell CI 全部通过。最终标签另行执行发布门禁。行为验收保留原始超时、运行路径偏差、不可用审查和 J05 的用户接受记录；修复后验证单独记账，不据此宣称每次调用都完美或普遍优于旧版。详细范围见验证文档，外部服务、视觉理解和真实科研项目仍需按实际环境验收。

## Install and upgrade

Download and extract `evo-inquiry-1.4.0.tar.gz` or `.zip` from this release. For an upgrade or source-directory change, replace the existing marketplace registration before installing from the clean extracted directory:

```sh
cd /path/to/evo-inquiry-1.4.0
codex plugin marketplace remove evo-inquiry
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

Omit removal on a first installation. Start a **new Codex session** and keep the selected source directory available. Existing persistent research-routing preferences remain applicable; installing a plugin alone does not add them. To configure the optional preference, preview `python tools/configure_research_guidance.py --global --dry-run`, then apply `--global`, or use `--project /path/to/project` for one project. Explicit user instructions and task boundaries continue to take priority.

See the [English README](https://github.com/Soceremite/EvoInquiry/blob/v1.4.0/README.md), [中文说明](https://github.com/Soceremite/EvoInquiry/blob/v1.4.0/README_CN.md), [skill catalog](https://github.com/Soceremite/EvoInquiry/blob/v1.4.0/docs/SKILLS_CATALOG.md) and [deployment guide](https://github.com/Soceremite/EvoInquiry/blob/v1.4.0/docs/DEPLOYMENT_GUIDE.md).
