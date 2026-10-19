# EvoInquiry 1.5.0

EvoInquiry helps turn a rough research direction into a sequence of testable questions, fair experiments and evidence-based decisions. Version 1.5.0 strengthens sustained research: continue within the original resource budget, recover without blindly repeating work, and finish each investigation with results, concrete cases and a verifiable handoff. The package retains **88 Codex entrypoints**; these capabilities extend existing workflows rather than add another layer of skills.

## New capabilities

**Research that continues within its limits.** Optional continuation controls attach to existing project runs and preserve the original authorized clock, resource reservations, retry bounds and closeout time. Each new wave addresses an unresolved question using the remaining resources. Negative results, a supported pivot and a justified stop remain valid outcomes; exhausting a budget does not become scientific success.

**Recovery tied to actual execution.** Repeated action requests reuse their original identity. Interrupted work is reconciled against process and terminal evidence before a retry. Registered executions can settle against their frozen source/configuration snapshot without relaunching the experiment or changing a research-review verdict. Handoff receipts check selected present or missing files against current sources, making stale handoffs visible.

**Useful memory from existing research records.** Read-only retrieval locates prior decisions, evidence, deferred alternatives and revisit conditions in existing Markdown or wiki records. It returns source identities for inspection rather than treating a search match as truth or permission. Authorized continuation reuses valid code, environments and scoped reviews while preserving methodological changes and negative evidence.

**Traceable activity and toolkit evaluation.** Explicit Codex JSONL imports retain source-bound observations while omitting raw prompts, commands, outputs and credentials from normalized events. Candidate comparisons bind actual requests, fixtures, model settings and budgets, retaining failed and timed-out attempts. Toolkit optimization stages proposals for the existing human-selected landing process; it does not rewrite installed skills automatically.

## Bug fixes

- Allow authorized CPU-only work when the GPU allowance is zero; distinguish an exhausted resource from an actual overrun.
- Preserve original clocks, unresolved reservations and real observed costs across stopping and recovery; reject corrupted accounting and mismatched execution identities.
- Publish each event import as one atomic batch, avoiding repeated whole-source reads and log rewrites. Reimports are idempotent; failed publication preserves earlier history, and changed or truncated sources are rejected.
- Separate a skill-path reference from verified invocation or compliance, a completed turn from a completed workflow, and a terminal process from a supported scientific claim.
- Correct the Codex self-optimization path to use the existing native behavior harness and separate proposal generation from reviewed landing.
- Include bounded-research and handoff regressions in both native Windows shell gates for development and release CI.
- Retry short Windows file-sharing contention during old-checkpoint cleanup. Persistent sharing errors remain visible after a bounded wait; access-denied errors are not treated as temporary. The deletion journal and newest recovery points remain available after interrupted cleanup.

## Improved research guidance

Scientific interfaces explain parameters, tensor/array axes, returned values and relevant constraints beside the changed routine. A check before the first consumer or handoff helps catch missing or stale contracts without requiring documentation of every trivial helper. Shared changes retain representative consumer checks.

Reviews are sized to the pending decision and remaining budget. They reuse valid scoped evidence, save incomplete findings progressively and finish once required coverage is met. Splitting a review leaves cross-interface checks and uncovered requirements pending. Partial prose, a timed-out call or a same-family review cannot become independent scientific acceptance.

Completed waves save available metrics, compact sample evidence and decisions before further dispatch. Existing fair-comparison, multi-seed, case-study, checkpoint-retention and storage-recovery guidance remains available. Small edits, numerical questions and advice-only requests retain their requested scope. Plan and Goal are optional host features; EvoInquiry does not create a Goal or a background service merely because it is installed.

## Practical validation and limits

Local practical use includes a **36-minute, four-wave continuation with 21 new CPU fits**. Separate parent programs reconstructed **376,272 saved prediction records**, checked metrics and paired contrasts, and verified 24 proactive case entries. These are repeated prediction records over fixed samples, models and draws—not 376,272 independent observations. The investigation preserved robustness tradeoffs and stopped with unused resources rather than repeatedly tuning exposed evaluation data.

Two fresh gpt-6.1-sol/high follow-up sessions exercised the final interface and scoped-review guidance in about 142 and 111 seconds. They completed their native turns, passed their bounded artifact checks, and retained an adverse result and missing integration coverage. The validation record also preserves earlier review timeouts, an external interruption, failed probes and a comparison that found no clear general gain.

These are limited public development cases and same-family assessments, not proof of general superiority over 1.4.0, independent scientific discovery, unattended operation over hours or days, or complete recursive self-improvement. Optional providers, distributed training, network filesystems and power-loss recovery retain their own setup and validation requirements. Final commit checks and native CI are recorded separately in the [validation record](https://github.com/Soceremite/EvoInquiry/blob/v1.5.0/docs/VALIDATION_1_5_0.md) and [machine-readable summary](https://github.com/Soceremite/EvoInquiry/blob/v1.5.0/release-validation.json); earlier commit receipts do not certify later source changes. The original 83-workflow and 450-resource preservation baselines remain frozen, with directed adaptations recorded separately.

## 中文说明

EvoInquiry 1.5.0 的重点是：**让已授权的科研任务能够在明确边界内持续推进，并可靠收尾。** 保留 88 个 Codex 入口，在原有工作流中增加预算、恢复、决策复用和交接能力，不增加一套平行科研流程。

**新增能力：** 保留原始任务时钟、资源预留和收尾窗口，依据上一轮证据决定下一轮；核对中断任务的实际终态再重试；将执行身份与固定的源码、配置和结果绑定；检查交接所选来源是否仍然有效。从已有决策文档检索证据、备选方案和重新考虑的条件；显式导入来源绑定的操作记录，并在相同任务与预算下比较工具修改。

**修复问题：** 零 GPU 预算不再误拦允许的 CPU 工作；实际超支、未决预留和原始截止时间不会被恢复操作掩盖。日志按批原子写入，避免反复扫描和重写，保留失败发布前的历史。纠正“提到了 skill 路径就等于执行”“会话完成就等于科研完成”和自优化直接改写已安装技能等错误边界；补齐两种 Windows Shell 的发布回归范围。

Windows 监控读取旧断点时，清理操作现在会对短暂的文件共享占用进行有时限的重试；持久占用和其他权限错误仍会报告，删除日志及最新恢复点得到保留。

**规范改进：** 新改科研函数在代码旁说明参数、shape、返回值和约束，并在首次调用或交接前核对。评审围绕待决定的问题与剩余预算展开，拆分后保留跨接口和未覆盖检查；超时文本不能关闭门槛。每轮先保存结果、样例与决策，保留正面发现、退化和未知；负结果与有依据的停止同样有效。

**实际体验：** 完成约 36 分钟、四轮、21 次新增 CPU 拟合的研究推进；使用独立代码重算保存的预测，检查指标、对比和主动案例。后续两个新会话分别在约 142 秒与 111 秒内完成接口实现和限定范围审查。所有结论均有适用范围，旧超时与失败不改判通过；不据此宣传普遍优于旧版、完全无人值守或完整 RSI。详见验证记录。

## Install and upgrade

Download the published `evo-inquiry-1.5.0.tar.gz` or `.zip`, or use the source at tag `v1.5.0` once available. For an upgrade or source-directory change, replace the existing marketplace registration before installing from the extracted directory:

```sh
cd /path/to/evo-inquiry-1.5.0
codex plugin marketplace remove evo-inquiry
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

Omit removal on a first installation. Start a **new Codex session** and keep the source directory available. Installing the package does not migrate research state or add persistent routing preferences automatically. See the [English README](https://github.com/Soceremite/EvoInquiry/blob/v1.5.0/README.md), [中文说明](https://github.com/Soceremite/EvoInquiry/blob/v1.5.0/README_CN.md), [bounded-research guide](https://github.com/Soceremite/EvoInquiry/blob/v1.5.0/docs/BOUNDED_RESEARCH_CN.md) and [deployment guide](https://github.com/Soceremite/EvoInquiry/blob/v1.5.0/docs/DEPLOYMENT_GUIDE.md).
