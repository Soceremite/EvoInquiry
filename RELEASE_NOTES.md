# EvoInquiry 1.2.0

**Stable release / 正式版 — Research that evolves through evidence. / 让科研在证据中持续进化。**

EvoInquiry provides **86 Codex skill entrypoints** for literature discovery, research design, theory, experiments, evidence review, papers, presentations, proposals and patents. Start with a concrete task, use a focused skill, or connect stages into a complete research workflow. Project evidence, review decisions and resource constraints guide the next authorized step.

This release promotes the validated **1.1.0-beta.2 runtime** to **1.2.0 stable**. The changes below summarize improvements since the previous stable release, **1.0.0**; the version promotion preserves the validated runtime and existing research workflows.

## New features

- **Project and evidence governance:** Add `project-governance` to track projects, experiment designs, actual executions, reports and environments with distinct identities. Fixed paths and SHA-256 references preserve the evidence behind each result; interrupted report publication and explicitly approved state migrations can be recovered.
- **Independent environment maintenance:** Add `environment-maintenance` to inspect actual interpreters and dependencies, validate independent candidates through metadata, imports, numerical and consumer checks, and select frozen revisions. Queued jobs retain their bindings; active leases and reproduction pins protect environments still needed by research.
- **Reproducible execution records:** Freeze source, expanded configuration, data protocol, evaluator, environment and launch arguments. Give failed attempts, retries and checkpoint restores separate identities, and retain the predeclared rule for aggregating results.
- **Code reuse and documentation checks:** Map source interfaces and method extensions, preserve shared sample/label/split meaning, and identify stale source/documentation relationships that require review before the next implementation.
- **Deployment diagnostics:** Provide a filesystem doctor to check local cross-process exclusion and replacement behavior before governance writes, plus native installer and project-to-report acceptance on both Windows PowerShell variants.

## Bug fixes

- Required method coverage now counts only successful **consumers-layer** receipts. IDs attached to metadata, imports or numerical checks cannot incorrectly satisfy method validation.
- Inspection, all four validation layers and experiment launch use the same validated absolute interpreter entry across working-directory and PATH changes. Virtual-environment entrypoints are preserved instead of being dereferenced to the base Python.
- Import notices, Chinese logs and JSON-like output no longer corrupt the machine fingerprint. `inspect --diagnostics` exposes captured stdout/stderr and actual exit status, while invalid frames, timeouts and failed probes remain failures.
- Fingerprints handle built-in and extension modules and record namespace-package locations and interpreter prefixes. Namespace source drift is detected; historical fingerprints are verified in their original format without rewriting frozen evidence.
- Python source maps honor encoding declarations and UTF-8 BOMs, including valid non-UTF-8 source, while keeping hashes of the original bytes.
- Governance state and evidence reject symlink/Junction traversal, Windows reserved filenames and ambiguous drive-relative references before redirected writes. Case-colliding consumer IDs cannot replace an existing binding on a case-insensitive filesystem.
- Governance CLI output and execution logs use UTF-8 so Chinese paths, results and error messages remain readable under Windows code pages and ASCII output settings.

## Error corrections

- Installation tests compare canonical directory identities on both sides of an assertion, including macOS `/var` and `/private/var` aliases. The installer retains its exact managed-target deletion contract.
- Executable identity comparisons honor platform case rules, including Windows `.EXE`/`.exe`, while preserving the logical virtual-environment entry.
- CI failure annotations retain the actual Unicode assertion, path and line breaks instead of failing during diagnostic output. A failed validation check remains failed and its original receipt remains available.
- Installation links, release status and validation descriptions now match the stable version. Historical GPU, dependency, local-test and behavior results retain their source versions and are not counted as new 1.2.0 executions.

## Practical benefits and existing capabilities

Long-running projects can trace which code, configuration, environment and actual attempt produced a number. Failed attempts remain visible, a moving `current` pointer cannot alter historical evidence, and environment changes can be tested before selected future jobs adopt them. `research-guide` coordinates continuation when the stage is unclear; focused analysis, implementation and writing requests select the corresponding skill. Existing scientific review gates continue to determine whether evidence supports a claim.

The existing experiment storage policy remains available: retain two valid full recovery points during training, a validation-selected best model and required final outputs; account for concurrent save peaks before launching. When training finishes or is explicitly ended, validate retained weights before releasing unused recovery states. Completed comparisons prefer the validation-selected winner while preserving every run's evidence and models required by future work.

## 中文更新日志

**1.2.0 是正式版**，将 1.1.0-beta.2 已验收的运行时正式发布。以下新增能力以此前正式版 1.0.0 为基准；正式版共提供 **86 个 Codex skill 入口**，覆盖文献、选题、研究设计、理论、实验、证据审查、论文、展示、项目申请与专利。

### 新增功能

- **项目与证据治理：**新增 `project-governance`，分别记录项目、实验设计、实际执行、报告和环境身份，以固定路径和摘要连接结果与来源，并支持中断报告发布恢复及经过授权的状态迁移。
- **独立环境维护：**新增 `environment-maintenance`，检查实际解释器和依赖，通过元数据、导入、数值及方法接口四层回执验证独立候选环境。排队任务保持原环境绑定，运行租约与复现保护继续保留。
- **可复现实验记录：**固定代码、展开后的配置、数据协议、评价器、环境与启动参数，分别记录失败、重试和断点恢复，保留实验开始前声明的统计纳入规则。
- **代码复用与文档检查：**梳理已有接口和方法扩展点，保护样本、标签及划分语义，识别代码与说明之间需要重新审查的变化。
- **部署诊断与原生验收：**提供文件系统 doctor，检查跨进程锁和文件替换行为；补充两种 Windows PowerShell 的原生安装与项目到报告流程验收。

### Bug 修复

- 修复方法覆盖误判：仅成功的 consumers 层回执计入要求的覆盖，其他验证层的消费者 ID 不能代替方法接口测试。
- 修复工作目录或 PATH 变化后使用错误解释器的问题：探测、四层验证和实验启动固定同一绝对入口，保留虚拟环境。
- 修复导入通知、中文日志或输出中的 JSON 污染指纹的问题；诊断可以查看真实日志和退出码，非法结果及超时仍拒绝通过。
- 修复内建模块来源处理及 namespace 来源遗漏，新增解释器 prefix、模块类型和搜索位置记录；旧冻结记录按原格式核验。
- 修复源码默认编码假设，正确处理 Python 编码声明和 BOM，同时保留原始字节摘要。
- 修复 NTFS Junction 路径保护缺口，并拒绝保留文件名、盘符相对引用及会覆盖既有绑定的大小写冲突。
- 修复 Windows 代码页或 ASCII 输出设置下的中文 CLI、实验日志及错误输出问题。

### 错误修正

- 修正安装测试把目录别名当作不同目录的断言，覆盖 macOS `/var` 与 `/private/var`；安装器管理目标的删除校验继续保留。
- 修正 Windows `.EXE`/`.exe` 的字符串比较，按平台路径规则判断解释器身份，同时保留 venv 的逻辑入口。
- 修正 CI 中文失败报告自身的编码错误，保留实际断言、路径与换行，失败检查和原始回执不会被改记为成功。
- 修正安装链接、正式版状态及验证描述；GPU、依赖冲突、本地测试和行为试点保留历史来源，不冒充本次新执行。

### 能力与优点

课题可以持续追踪“哪个实验设计、哪次实际执行、哪份代码配置和环境产生了这个结果”，在方案修订、任务重试和多人协作中复用已有证据。明确任务直接进入相关 skill，阶段不明确时由 `research-guide` 协调下一步；科研结论仍经过原有独立审查和证据门槛。

已有实验存储策略继续适用：训练中保留最近两个有效恢复点、验证指标选出的最佳模型及必要最终结果；启动前计算并发保存峰值，结束训练后验证保留权重再释放恢复状态。完成的对比实验优先保留最优模型，同时保护所有实验记录及长期计划需要的模型。

## Installation, upgrades and rollback / 安装、升级与回滚

Download and extract `evo-inquiry-1.2.0.tar.gz` or `.zip`. Use the clean extracted directory as the source. For a first installation, omit the remove command; for an upgrade, replace the previously registered source.

下载并解压 `evo-inquiry-1.2.0.tar.gz` 或 `.zip`，从干净的解压目录安装。首次安装省略 remove 命令；升级时先替换已登记的旧来源。

```sh
cd /path/to/evo-inquiry-1.2.0
codex plugin marketplace remove evo-inquiry
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

Start a new Codex session and keep the source directory available. Rollback uses the same commands from a preserved prior release directory. Plugin switching does not migrate research project state. 安装后新开 Codex 会话，并保留来源目录；回滚时从保留的旧版目录执行相同命令，插件切换不会自动迁移科研项目状态。

See the [skill catalog](https://github.com/Soceremite/EvoInquiry/blob/v1.2.0/docs/SKILLS_CATALOG.md), [usage guide](https://github.com/Soceremite/EvoInquiry/blob/v1.2.0/docs/GOVERNANCE_USAGE_CN.md), [English README](https://github.com/Soceremite/EvoInquiry/blob/v1.2.0/README.md) and [中文说明](https://github.com/Soceremite/EvoInquiry/blob/v1.2.0/README_CN.md).

## Validation and supported scope / 验证与适用范围

The promoted beta.2 source passed the Linux/macOS full suites and both native Windows gates in its [main CI](https://github.com/Soceremite/EvoInquiry/actions/runs/38359883402) and [release CI](https://github.com/Soceremite/EvoInquiry/actions/runs/38360526301). Stable publication requires the same four platform gates on the actual 1.2.0 tag; Linux installs the interactive-test dependency so those cases execute. All 83 original workflow bodies and checkpoint helper bytes remain protected. Source assets contain `SHA256SUMS` and a fixed-commit `release-manifest.json`; private plans, logs, credentials, build outputs and Git history are excluded.

升级来源已实际通过 Linux/macOS 完整回归及两种 Windows PowerShell 原生验收；1.2.0 发布仍要求对应标签的四组门禁全部通过。既有 83 个工作流主体与检查点工具字节保持原有契约，下载包附校验摘要和固定提交清单。具体范围见[发布验收](https://github.com/Soceremite/EvoInquiry/blob/v1.2.0/docs/UPGRADE_VALIDATION_CN.md)、[兼容性验收](https://github.com/Soceremite/EvoInquiry/blob/v1.2.0/docs/PORTABILITY_VALIDATION_CN.md)及[机器可读记录](https://github.com/Soceremite/EvoInquiry/blob/v1.2.0/release-validation.json)。

Governance requires a persistent project volume with verified local locking and replacement semantics. Multi-host/network-filesystem concurrency, power-loss behavior, SSH/screen deployment, distributed or large-scale GPU training and optional live reviewer backends need deployment-specific acceptance. Windows directory fsync and the POSIX checkpoint helper are not certified; use the trainer's native checkpoint facilities there. The [deployment guide](https://github.com/Soceremite/EvoInquiry/blob/v1.2.0/docs/DEPLOYMENT_GUIDE.md) explains the measured storage scope. 正式治理使用持久项目存储并验证真实锁与文件替换行为；多机、网络文件系统、大规模训练及可选外部服务按实际部署单独验收。

MIT licensed. See [LICENSE](https://github.com/Soceremite/EvoInquiry/blob/v1.2.0/LICENSE) and [NOTICE](https://github.com/Soceremite/EvoInquiry/blob/v1.2.0/NOTICE).
