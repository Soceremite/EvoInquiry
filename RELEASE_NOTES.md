# EvoInquiry 1.3.0

EvoInquiry is a research workflow toolkit with **86 Codex skills**, covering literature discovery, method design, experiments, evidence review, mathematical proofs, papers, figures, presentations and research proposals. Version 1.3.0 strengthens comparative experiment design and keeps the evidence needed to understand a result after large training artifacts are released. It preserves the existing workflow entrypoints and review gates.

## New capabilities

**Fair comparisons across the experiment lifecycle.** Eight existing skills now share a comparison protocol covering dataset identity and leakage, baseline quality, training and hyperparameter-search budgets, input access, independent seeds, failures, validation selection and fixed evaluation. The protocol distinguishes a controlled contribution test, performance under an equal resource cap, and reasonably tuned system performance. It allows justified method-specific recipes and keeps each conclusion tied to the question actually tested.

**More informative result analysis.** Comparison guidance calls for individual runs, inclusion and exclusion reasons, failed or missing slots, appropriate aggregates, variability and effect uncertainty. Replication follows the expected effect, precision and budget; three seeds remains a starting estimate rather than a universal adequacy guarantee. Matched independent units are required for paired inference, and a model's many evaluation examples are distinguished from independent training runs.

**Evidence before winner-only weight archival.** The optional checkpoint helper now requires a fixed comparison evidence index before releasing another run's weights into the selected winner. It checks all declared method/run/seed slots and all recorded execution attempts, including failures and retries; verifies protocol, configuration, log and result references; and binds the validation selection to the surviving store. Logs must remain outside disposable checkpoint artifacts. Interrupted cleanup rechecks both the winner and the bound evidence. Existing model-dependency pins remain protected.

**Opt-in persistent research routing.** `tools/configure_research_guidance.py` can install the managed research preference in a project or the Codex global instruction file. Relevant research requests and short follow-ups prefer suitable installed EvoInquiry skills, while direct execution tasks retain their scope. The helper supports preview, check and removal; preserves unrelated instructions; respects active override files; and rejects ambiguous managed blocks or concurrent edits. Plugin installation alone does not change those preferences, and routing instructions do not guarantee activation on every turn.

## Bug fixes

Comparison consolidation previously verified the surviving model without checking that comparison records were complete. Destructive consolidation now stops when evidence is missing, declared runs or recorded failures are omitted, references change, selection names another store, or evidence would be lost inside a checkpoint artifact. The same guard applies when an interrupted deletion journal is resumed.

Legacy comparison receipts remain inspectable. Further destructive cleanup requires binding complete evidence to the same recorded winner, rather than silently treating the older receipt as sufficient. Ordinary single-run completion, standalone single-file trainers and bounded active recovery retain their existing behaviour. Permanently stopped, evaluated winners remain eligible for retention; unstarted slots use cancellation records rather than fabricated attempts.

Windows checkpoint saves now flush files through a writable, non-truncating handle, as required by the native file-sync API. File-flush failures preserve the previous recovery points and manifest. Manifest reads and atomic replacement retry temporary native sharing/access errors for at most one second per operation, including CRT-backed read errors, while preserving the old manifest; persistent and unrelated errors and corruption still propagate. Both Windows shell gates additionally run the checkpoint-retention suite. Long public CI annotations preserve the test identity and final exception within a bounded UTF-8 excerpt, and expose actual JUnit counts without changing pytest's exit status.

## Corrected guidance

Fairness is expressed relative to the comparison question, with justified differences in learning rates, optimisers and epochs. Comparison analysis qualifies relative gains when a baseline is zero or the metric scale makes ratios inappropriate, distinguishes standard deviation from uncertainty of an effect, and prevents a best seed or retry from replacing the full comparison. OOM-related recipe changes are visible protocol deviations. Test scores cannot select the archived winner.

## Compatibility and validation

The release keeps **86 Codex entrypoints** and the original **83 workflow bodies**. Additions are scoped instruction hooks, shared references, supporting tools and tests. The checkpoint helper changes deliberately to add the evidence gate; older release hashes are not reused as proof of its current behaviour. Linux/macOS full-suite and both native Windows shell workflows include the relevant checks. An earlier local Linux full suite passed **1053 tests**, with 35 skips and no failures; the corrected runtime additionally passed 140 focused tests and [full Linux/macOS CI plus both native Windows shell gates](https://github.com/Soceremite/EvoInquiry/actions/runs/38519743173). The actual scopes and separate receipts are recorded in [1.3.0 validation](https://github.com/Soceremite/EvoInquiry/blob/v1.3.0/docs/VALIDATION_1_3_0.md) and [release-validation.json](https://github.com/Soceremite/EvoInquiry/blob/v1.3.0/release-validation.json).

A coverage or file-integrity PASS is not a scientific fairness certificate. Evidence writers must be stopped during local consolidation; distributed training, object stores, network filesystems and power-loss behaviour need backend-specific acceptance. Existing formal research review gates continue to determine claim support.

## 中文说明

EvoInquiry 1.3.0 保留 **86 个 Codex skill** 和既有科研流程，重点提高对比实验的可解释性与证据完整性。文献、方法设计、实验、审查、证明、论文和展示能力继续可按任务单独使用，也可组成更长的工作流。

**新增功能：** 将公平比较规范接入八个现有实验 skill，覆盖数据集与划分、数据泄漏、强基线、训练与调参成本、输入权限、多种子、失败重试和统一评测。区分机制贡献、等资源预算和充分调优性能，允许有理由的方法差异。增加可选的全局或项目科研路由设置工具，让相关请求与短追问更容易继续采用合适的已安装 skill，保留原有指令与任务范围。

**修复问题：** 非最优权重归档前，新增对比证据检查。缺少实验或失败尝试、日志摘要发生变化、保留模型身份不匹配，或证据位于将被清理的断点目录中，都会阻止删除；中断清理后重试也会重新验证。旧归档记录仍可查看，但继续删除前必须补齐并绑定证据。后续实验需要的模型依赖继续受到保护。

Windows 断点文件使用可写但不截断内容的句柄刷盘，兼容系统落盘要求；刷盘失败继续保留此前的恢复点和清单。清单读取与原子替换仅对系统临时共享或访问错误进行每次操作最多一秒的重试，兼容读取接口只提供 errno 的情况，期间保留旧清单，持续权限错误、其他错误及清单损坏照常上报。两种 Windows Shell 验收均加入完整断点保留测试。较长的 CI 失败注释保留测试身份与末尾异常，避免公开注释截断时丢失真正原因，同时展示原始 JUnit 统计，不改变测试退出状态。

**修正规范：** 明确不以相同学习率、优化器或训练轮数作为通用公平标准；不把固定三个种子当成充分性保证；不以最优种子或最优重试替代完整比较。分析区分跨运行波动与效果不确定性，避免零基线或不适合比值的指标产生误导性相对提升。验证集决定模型与阈值，测试结果不能参与归档最优模型的选择。

完整记录与原始证据在释放大权重后继续保留。文件完整性通过仅代表记录覆盖和字节一致，科研公平性、计算正确性及结论支持程度仍由实际证据和既有审查门禁判断。

## Install and upgrade

Use a clean extracted `evo-inquiry-1.3.0.tar.gz` or `.zip` source package. Replace an existing marketplace registration before installing from the new directory; omit removal on a first installation.

```sh
cd /path/to/evo-inquiry-1.3.0
codex plugin marketplace remove evo-inquiry
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

Start a new Codex session and keep the selected source directory available. For persistent research routing, review and apply `python tools/configure_research_guidance.py --global`, or use `--project /path/to/project` for a project-specific preference. Plugin switching does not migrate research state. See the [English README](https://github.com/Soceremite/EvoInquiry/blob/v1.3.0/README.md), [中文说明](https://github.com/Soceremite/EvoInquiry/blob/v1.3.0/README_CN.md), [skill catalog](https://github.com/Soceremite/EvoInquiry/blob/v1.3.0/docs/SKILLS_CATALOG.md), [evidence format](https://github.com/Soceremite/EvoInquiry/blob/v1.3.0/docs/COMPARISON_EVIDENCE.md) and [deployment guide](https://github.com/Soceremite/EvoInquiry/blob/v1.3.0/docs/DEPLOYMENT_GUIDE.md).
