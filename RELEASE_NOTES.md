# EvoInquiry 1.6.0

EvoInquiry helps turn a rough research direction into testable questions, fair experiments and evidence-based decisions. **Version 1.6.0 adds a practical brake for sustained research:** step back at meaningful boundaries, test whether several problems share a cause, revise the plan when evidence warrants it, and stop owned training when continuing is unnecessary. The package provides **89 Codex entrypoints and 88 mainline skills**, including one new skill, `problem-synthesis`. Existing planning, execution, review and writing workflows retain their responsibilities.

## New capabilities

**Review the trajectory before spending the next budget.** Comparison blocks, tuning batches, major milestones and direction changes become natural review boundaries. The existing controller supports optional boundaries by settled action count or elapsed time, observed by the existing monitor or before dispatch. Opening a gate requests an actual judgment; it does not select CONTINUE, REPLAN or STOP for the model. Evidence, remaining resources, alternatives and counterexamples determine the next useful action.

**Look for a shared cause without forcing one.** The new `problem-synthesis` skill compares a common explanation with keeping problems separate or changing the level of abstraction. It records observations, competing hypotheses, counterevidence, joint predictions and discriminating checks. A single problem stays with its active workflow owner, and fairness drift routes to the existing experiment audit. A proposed merge remains a testable hypothesis, not an accepted scientific claim.

**Make a changed direction a concrete handoff.** Gate-bound reflection records retain blockers and keep dependent dispatch paused until the owner hands off a fixed revised plan. Later routine reviews preserve that plan's identity. Recovery checks the original evidence, pending work, resource limits and clock instead of treating a new action key or an old status as permission to continue.

**Deliver STOP to a running local experiment.** The bound local launcher observes workflow STOP and snapshot/process-bound cancellation requests, stops its owned process group on POSIX and records actual termination before settlement. Its effective execution limit is capped by the explicit timeout, experiment attempt budget and original remaining dispatch time. A cooperative trainer can save its latest recovery state and exit cleanly while the execution remains correctly classified as stopped. Ordinary reflection leaves healthy training running.

## Bug fixes

- Prevent stale or unrelated reflections from clearing a later gate; bind each record to its gate, kind and phase.
- Keep DEFER and BLOCKED decisions paused, and require a revised-plan handoff after REPLAN or a synthesis pivot.
- Preserve revised-plan identity across later routine reviews; changed evidence requires reconciliation.
- Recover a ledger append interrupted before coordination updates without duplicating the reflection entry or resetting stale-progress counters.
- Preserve original limits, late unreviewed results and resource accounting through review and recovery; cancelled attempts do not count as completed comparison evidence.
- Correct zero-exit cancellation classification in both the local launcher and explicit independent-observer recovery receipts. Stopped attempts stay out of successful aggregation.
- Preserve legacy review-backend defaults, send reviewer text through the documented MCP `prompt` argument, and retain external-timer boundaries during state recovery.
- Use the existing portable file lock for iteration-ledger writes and cover reflection and execution-governance regressions in both native Windows shell gates.

## Clearer collaboration between skills

The three review-loop entrypoints share their cycle and recovery guidance while preserving backend adapters and stricter acceptance gates. An old timestamp prompts reconciliation of existing work rather than deletion and a fresh round budget. The deprecated `paper-poster` entrypoint forwards unchanged arguments to `paper-poster-html`. Routing and composition reuse valid child artifacts, with one owner responsible for each requested output. **No existing skill is removed**, and the original 83-workflow and 450-resource preservation baselines remain frozen with explicit adaptations recorded separately.

## Practical validation and limits

The final local Linux regression passed **1,349 tests**, with 36 skipped and 46 passing subtests, including all 19 execution-governance checks. The three existing deprecation warnings remain. Separate real-process checks exercised owned-child termination, survival of an unrelated process, ordinary review during healthy work and cooperative save/exit-zero cancellation.

An earlier real CUDA engineering run completed **3,600.004 seconds and 2,145,720 optimizer steps**, with 30 full-state publications, the latest two recovery points retained, injected numerical failure and full-state replay. Its milestone decisions were programmed engineering checks, not model research judgments.

A supplemental native-model observation retained its original one-hour cap and closed after **43 minutes 52 seconds**. A real model reviewed fixed outputs and paired cases, identified a shared representational obstruction and chose REPLAN. A matched-duration followup supported that explanation. A later real review chose STOP; the bound CUDA worker saved and exited about **3.505 seconds** after stop intent. Two three-step replays from the latest checkpoint produced identical complete-state hashes and the verification process completed normally. Control regressions and both harness mistakes remain recorded: one wrongly lengthened run was excluded from fair comparison, and a first recovery process timeout was preserved before a bounded successful retry.

These are constructed, explicitly guided local cases and **same-family provisional assessments**. They do not establish independent scientific acceptance, protection against every local optimum, an always-on universal watchdog, implicit skill-selection frequency or autonomous discovery over hours or days. Existing monitoring must observe the configured boundary; local execution must be bound to its owner. SSH, schedulers, distributed training and Windows descendant trees retain their own execution and validation requirements. Native release CI is a separate gate, not inferred from local results. See the [1.6.0 validation record](https://github.com/Soceremite/EvoInquiry/blob/v1.6.0/docs/VALIDATION_1_6_0.md), [boundary assessment](https://github.com/Soceremite/EvoInquiry/blob/v1.6.0/docs/AUDIT_1_6_0_BOUNDARIES_AND_BRAKES_CN.md) and [machine-readable summary](https://github.com/Soceremite/EvoInquiry/blob/v1.6.0/release-validation.json).

## 中文说明

**EvoInquiry 1.6.0：让长期推进的科研，能够适时回顾、有据转向、真正停下来。** 保留 89 个 Codex 入口和 88 个主线 skill，仅新增 `problem-synthesis`，在已有工作流中补齐回顾和刹车能力。

**新增能力：** 在对比实验块、调参批次、重要里程碑和方向变化处回顾原研究问题；按已结算任务数或经过时间请求真实判断。多个问题可能来自共同原因时，比较共因、保持分离和改变抽象层级，提出能够区分解释的检查。改变方向后等待具体修订计划交接，保留原始预算、负结果和阻断原因。模型或用户决定 STOP 后，绑定的本地启动器核实停止所属训练，保存终止回执并保留恢复状态。

**修复问题：** 旧回顾不能解除新门槛；DEFER、BLOCKED 和待交接的转向不会误放行；后续普通回顾不会丢失有效计划绑定；日志中断恢复不重复记账、不重置预算。训练保存后以 0 退出仍正确归类取消，既有启动与独立终止恢复路径均有回归覆盖。修复评审后端兼容、MCP 正文参数与旧状态恢复边界，并补齐两种 Windows Shell 的相关检查。

**协作改进：** 三个评审循环复用共享规范，保留各自后端和更严格的门槛；旧海报入口仅作兼容转发。选题、问题合成、规划、执行、分析与科研裁决各自负责明确产出，组合流程复用已有有效证据，不另建调度器或科研数据库。

**实际检验：** 最新本地回归 1,349 项通过。真实一小时 CUDA 工程长跑验证有界断点保存、数值故障处理和恢复；另一段保留原时钟、约 44 分钟的模型观察，实际出现 REPLAN、STOP、训练保存退出和一致的完整状态重放。停止意图到终止回执约 3.505 秒。两次测试驱动问题和对照组退步样例完整保留，不改判为全部成功。这些证据不代表默认常驻急停、普遍避免局部最优或完整无人值守科研；远程平台、多机及 Windows 子进程树仍需对应验收。

## Install and upgrade

Download `evo-inquiry-1.6.0.tar.gz` or `.zip`, or use source at tag `v1.6.0`. For an upgrade or source-directory change, replace the existing marketplace registration before installing from the extracted directory:

```sh
cd /path/to/evo-inquiry-1.6.0
codex plugin marketplace remove evo-inquiry
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

Omit removal on a first installation. Start a **new Codex session** and keep the clean source directory available. Installation does not migrate research state, change training environments or add persistent routing preferences automatically. See the [English README](https://github.com/Soceremite/EvoInquiry/blob/v1.6.0/README.md), [中文说明](https://github.com/Soceremite/EvoInquiry/blob/v1.6.0/README_CN.md) and [bounded-research guide](https://github.com/Soceremite/EvoInquiry/blob/v1.6.0/docs/BOUNDED_RESEARCH_CN.md).
