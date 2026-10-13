# EvoInquiry 1.1.0-beta.2

**Research that evolves through evidence. / 让科研在证据中持续进化。**

EvoInquiry provides **86 Codex skill entrypoints** for literature discovery, research design, theory, experiments, evidence review, papers, presentations, proposals and patents. This update strengthens project and environment governance for research that needs to continue across many experiments, failures, revisions and collaborators. You can still start with a focused request; the workflow follows the project's evidence, constraints and authorized stopping point.

## Capabilities

| Capability | What it helps you do |
| --- | --- |
| Project and evidence governance | Give projects, experiment designs, real executions, reports and environments distinct identities. Use fixed paths and SHA-256 references for evidence; recover interrupted publication and explicitly planned state migrations. |
| Reproducible execution | Freeze the source, expanded configuration, data protocol, evaluator, environment and launch arguments. Preserve failed attempts, record retry or checkpoint-restoration parents, and aggregate according to a rule declared before results exist. |
| Environment maintenance | Inspect the real interpreter and imports, build an independent candidate, and preserve actual metadata/import/numerical/consumer checks. Keep queued tasks bound to their environment and protect active leases or reproduction pins. |
| Code reuse and documentation | Find existing interfaces and method extensions, preserve shared sample/label/split meaning, and identify source/documentation changes that require another review. |
| Storage and deployment | Probe local cross-process locks and atomic publication requirements before governance writes; distinguish temporary test storage from a durable project deployment. Verify plugin source switching and rollback. |

The focused skills `project-governance` and `environment-maintenance`, join the existing research workflows. `research-guide` continues to coordinate unclear or multi-stage requests; a clear analysis, implementation or writing task goes directly to its relevant skill. Ordinary reading and small edits do not require project initialization. Schema validity and file identity do not replace independent scientific review or turn a claim into an accepted result.

## Why this matters

Long-running projects can answer which code, configuration, environment and actual attempt produced a number. Failed attempts remain visible, report revisions retain their inputs, and a moving `current` pointer cannot silently change historical evidence. Environment changes can be tested before selected future tasks adopt them, while existing queued work and reproduction dependencies remain protected.

The existing storage policy remains available: retain two valid full recovery points during training, a validation-selected best model and required final outputs; account for the complete-save peak before launching. When training ends, validate retained weights before releasing unused recovery states. Finished comparisons prefer the validation-selected winner while preserving every run's evidence and models needed by future work.

## Reliability improvements in beta.2

Required method coverage now comes only from successful consumers-layer checks. Inspection, all four validation layers and experiment launch use the same validated absolute interpreter entry across working-directory and PATH changes, preserving the virtual environment and its dependencies. Import notices no longer corrupt the fingerprint JSON; inspect --diagnostics exposes the captured logs and exit code. New fingerprints include namespace package locations and interpreter prefixes, while historical fingerprints continue using their original format without rewritten evidence.

Source maps honor Python encoding declarations and BOMs, and keep hashes of the original bytes. Governance paths reject NTFS Junctions, reserved filenames and ambiguous drive-relative references before redirected writes; case-colliding consumer IDs cannot replace an existing binding. Dedicated alias tests exercise installation, reconciliation and managed deletion. Existing installer-managed skill links remain supported.

These fixes add actual interpreter and filesystem regressions to the Linux/macOS full suites and both native Windows gates. See [portability coverage](https://github.com/Soceremite/EvoInquiry/blob/v1.1.0-beta.2/docs/PORTABILITY_VALIDATION_CN.md) for compatibility details and the scope of each check.

## Installation, upgrades and rollback

Download and extract `evo-inquiry-1.1.0-beta.2.tar.gz` or `.zip`. Use the clean extracted directory as the plugin source, keeping local validation folders and Git history outside it:

```sh
cd /path/to/evo-inquiry-1.1.0-beta.2
# For an upgrade, remove the previously registered source first:
codex plugin marketplace remove evo-inquiry
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

For a first installation, omit the remove command. Start a new Codex session and keep the selected source directory available. Rollback uses the same commands from a preserved prior release directory. Plugin switching does not migrate research project state. See the [skill catalog](https://github.com/Soceremite/EvoInquiry/blob/v1.1.0-beta.2/docs/SKILLS_CATALOG.md), [usage guide](https://github.com/Soceremite/EvoInquiry/blob/v1.1.0-beta.2/docs/GOVERNANCE_USAGE_CN.md), [deployment guide](https://github.com/Soceremite/EvoInquiry/blob/v1.1.0-beta.2/docs/DEPLOYMENT_GUIDE.md), [English README](https://github.com/Soceremite/EvoInquiry/blob/v1.1.0-beta.2/README.md) and [中文说明](https://github.com/Soceremite/EvoInquiry/blob/v1.1.0-beta.2/README_CN.md).

## Validation and scope

The preceding beta.1 acceptance includes a real H100 training pilot: two methods and three seeds, one preserved interruption and an independent restored execution, plus a separately declared continuous-training control. Model, optimizer, scheduler and Python/CPU/device random states matched exactly between restoration and continuous training. The pilot used 24 optimizer steps, a 512 KB checkpoint budget and approximately 63 KB measured save peak. Both available GPUs also passed small numerical probes; this does not establish distributed-training correctness or large-run performance.

The preceding offline pip pilot created two independent virtual environments, recorded an actual dependency-resolution conflict and a consumer interface failure, and verified that the frozen old environment and queued binding stayed unchanged. Native Codex discovery, complete installed-source bytes, version-source alignment and rollback were checked. Original research workflow bodies and checkpoint policy remain protected by the preservation contract. Natural-request checks are scoped behavior evidence, not proof of general autonomy or improved research outcomes.

The local complete host regression passed 955 tests with 35 scoped skips (506.46 seconds). The final UTF-8 probe-stream and Chinese import-log follow-up passed 17 tests with one Windows-only skip; The subsequent pinned-validation and environment follow-up passed 47 tests with 12 Windows-only skips, and Unicode CI diagnostics passed two checks; the platform gates execute the final committed source. Earlier restricted-sandbox failures were retained and resolved by running the same owner-preserving copy and local HTTP tests on the actual host runtime.

Publication requires the Linux and macOS full regression suites plus native Windows installer/local-governance checks. Linux also installs the interactive-test dependency so those cases execute on its runner. Source archives include `SHA256SUMS` and a committed-source `release-manifest.json`; private plans, test logs, credentials, build folders and Git history are excluded.

Governance writes require verified local locking and rename/fsync behavior on an operator-confirmed persistent project volume. The acceptance host's QuarkFS mount failed lock exclusion, and its passing overlay/emptyDir test storage was not confirmed durable; the toolkit rejects unsupported writes. Multi-host/network-filesystem operation, power-loss recovery, SSH/screen queues, live optional reviewer APIs and large-scale or distributed GPU training still need deployment-specific validation. This is a **beta release**; version 1.0.0 remains the stable option.

## 中文介绍

1.1.0-beta.2 提供 **86 个 Codex skill 入口**及项目与环境治理，帮助长周期科研保留“哪个实验设计、哪次实际执行、哪份代码配置和环境产生了这个结果”的完整联系。报告使用固定版本与摘要引用，中断发布、失败重试和断点恢复保留独立身份；环境变更先在独立候选中验证，排队任务和论文复现依赖继续受到保护。

本次修复方法覆盖误判、工作目录/PATH 改变后的 venv 启动、导入日志干扰、namespace 来源缺失、源码编码与目录别名断言，并为 Junction、保留文件名和大小写冲突增加原生 Windows 验收。旧格式指纹按原格式核验，不改写历史证据。

使用时仍从具体任务开始：文献、方案、实验、分析、审查、论文和展示按需衔接。明确任务直接使用相关 skill，普通阅读和小型修改无需先初始化项目。原有科研审查门禁及有界断点策略保留，文件登记完整不等于科研结论已经被接受。

前一版验收实际完成 H100 短训练与全状态断点恢复、两张 GPU 的小型数值探测、独立环境的 pip 依赖冲突和接口失败、插件安装来源核对及回滚。发布流程增加 Windows 原生安装与本地治理验收，Linux 执行交互终端用例。临时容器目录不能当作长期科研存储，不支持可靠文件锁的挂载会被拒绝写入；多机、网络文件系统、大规模训练与可选外部评审仍需单独验收。具体证据和范围见[升级验收记录](https://github.com/Soceremite/EvoInquiry/blob/v1.1.0-beta.2/docs/UPGRADE_VALIDATION_CN.md)及[机器可读记录](https://github.com/Soceremite/EvoInquiry/blob/v1.1.0-beta.2/release-validation.json)。

MIT licensed. See [LICENSE](https://github.com/Soceremite/EvoInquiry/blob/v1.1.0-beta.2/LICENSE) and [NOTICE](https://github.com/Soceremite/EvoInquiry/blob/v1.1.0-beta.2/NOTICE).
