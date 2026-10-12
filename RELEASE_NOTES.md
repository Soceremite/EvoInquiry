# EvoInquiry 1.0.0

**Research that evolves through evidence. / 让科研在证据中持续进化。**

EvoInquiry 1.0.0 is the first stable release of a research workflow toolkit for Codex. It provides **84 skill entrypoints** to help researchers explore a direction, develop a method, run and interpret experiments, examine the evidence, and prepare research outputs. Start with a focused task or connect the steps into a longer workflow; existing project materials, resource limits, and the requested stopping point guide what happens next.

## Research capabilities

| Area | What EvoInquiry helps you do |
| --- | --- |
| Literature and knowledge | Search and understand papers, organize related work, check novelty, and maintain a persistent research knowledge base. |
| Ideas and method design | Generate research directions, refine a proposal, and design baselines, controls, ablations, metrics, and an experiment roadmap. |
| Theory and proofs | Organize assumptions and derivations, draft mathematical proofs, and review gaps in an argument. |
| Experiments and analysis | Build research prototypes, execute and queue experiments, monitor training, analyze multiple seeds, and compare results. |
| Evidence and review | Audit experiment integrity, assess which claims the results support, check citations, and revise work through bounded review cycles. |
| Papers and figures | Plan and draft a manuscript, produce plots and editable diagrams, compile LaTeX, and improve an existing paper. |
| Talks and submissions | Prepare slides and posters, write a rebuttal, and adapt an existing paper for a new venue. |
| Proposals and patents | Structure funding proposals and invention disclosures, then draft and review patent application materials. |
| Project continuation | Use `research-guide` to inspect existing work and coordinate the next authorized step; use `research-pipeline` for a requested full research workflow. |

The [skill catalog](https://github.com/Soceremite/EvoInquiry/blob/v1.0.0/docs/SKILLS_CATALOG.md) lists the actual entrypoints and their setup requirements. The inventory includes focused tasks, orchestrators, optional provider adapters, and a retained compatibility redirect.

## Why use EvoInquiry

- **Choose the right amount of workflow.** Natural requests can select the relevant skill directly. Project continuation coordinates several steps when needed, and explicit skill names remain available for precise control.
- **Keep conclusions connected to evidence.** Plans connect research questions with tests; analysis preserves numerical caveats; formal claim checks, experiment audits, and citation checks help expose unsupported conclusions and missing evidence.
- **Continue from concrete project artifacts.** Proposals, experiment trackers, results, review reports, knowledge pages, and workflow state provide inputs for the next stage and support resuming an interrupted project.
- **Plan for limited resources.** Experiment guidance accounts for compute, time, storage, concurrent saves, and completed runs. Active training defaults to the latest two valid full recovery points and a validation-selected best model, with required final outputs and dependencies protected.
- **Archive completed experiments deliberately.** After training completes or is explicitly ended, validate retained weights before releasing unused recovery states. Finished comparison groups prefer the validation-selected winner while preserving all runs' evidence and models needed by future work; unresolved retention choices are presented to the user.
- **Keep supervision configurable.** Workflow checkpoints, review limits, budgets, and stopping conditions let researchers control how work proceeds. Optional search, reviewer, compute, and rendering integrations can be configured for the project's needs.

Version 1.0.0 brings together project coordination, clearer natural-request routing, bounded checkpoint retention, and completed-run archiving. Existing workflow bodies and the protected runtime/reference contract remain preserved.

## Install and start

Download and extract `evo-inquiry-1.0.0.tar.gz` or `evo-inquiry-1.0.0.zip`, then run these commands from the extracted root directory:

```sh
cd /path/to/evo-inquiry-1.0.0
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

Start a new Codex session. Describe your research goal and constraints, or name a skill such as `evo-inquiry:research-refine`, `evo-inquiry:experiment-plan`, or `evo-inquiry:analyze-results`. Keep the extracted source directory available for the local marketplace. The [English guide](https://github.com/Soceremite/EvoInquiry/blob/v1.0.0/README.md) and [中文说明](https://github.com/Soceremite/EvoInquiry/blob/v1.0.0/README_CN.md) include usage examples, setup, and update instructions.

## Validation and scope

Release publication is gated by the complete Linux and macOS regression suites. Checkpoint validation includes capacity limits, failed saves, corruption fallback, dependency protection, interrupted cleanup, concurrent access, and real CPU training continuation with optimizer, scheduler, and random state. Source archives include `SHA256SUMS` and `release-manifest.json`, which identifies the source commit and skill inventory. Private test records, local build outputs, credentials, and Git history are excluded from these archives.

The toolkit primarily targets ML, AI, and related engineering research. External services, GPU platforms, image tools, and LaTeX require their own setup. Storage guidance must be implemented and verified in the actual trainer; the optional local checkpoint helper requires a project-specific writer and loader validator. GPU/distributed recovery, live providers, complete research projects, and broad discipline coverage have not been verified end to end. Scoped behavior checks include an inconclusive storage-implementation case and do not establish general research correctness or improved research outcomes. See [validation scope](https://github.com/Soceremite/EvoInquiry/blob/v1.0.0/docs/BETA_VALIDATION.md) and the [machine-readable record](https://github.com/Soceremite/EvoInquiry/blob/v1.0.0/release-validation.json) for the evidence and limits.

## 中文介绍

EvoInquiry 1.0.0 是首个正式版，提供 **84 个 Codex skill 入口**，覆盖文献检索与知识积累、选题与方法设计、理论推导、实验实施与分析、证据审查、论文写作、展示与投稿，以及基金申请和专利材料。可以直接完成一个具体任务，也可以按目标衔接多个科研阶段。

它的主要优势是：按任务调用相关能力，利用已有材料继续课题，把结论与实验和引用证据关联起来，并在计算、时间和存储预算内推进工作。计划、结果、评审报告和工作流状态会成为后续工作的输入；用户可以通过检查点、预算和停止条件控制执行范围。

长时间训练默认保留最近两个有效的完整恢复点和按验证指标选出的最佳模型，同时保护必要的最终输出与后续模型依赖。训练完成或用户明确结束训练后，验证保留权重，再清理不再需要的恢复状态。已完成的对比实验优先仅保留验证集最优模型，保护后续实验需要的其他模型，并保留所有实验的指标、配置和记录；存在未解决的保留选择时，由用户决定。

正式版发布经过 Linux 和 macOS 完整回归门槛，下载包附有校验和及源码提交记录。84 个入口包含单步任务、流程协调和可选后端；外部服务与实验平台按需配置。当前验证主要覆盖 ML、AI 与相关工程科研，具体测试范围和未覆盖场景见上面的验证说明。

MIT licensed. See [LICENSE](https://github.com/Soceremite/EvoInquiry/blob/v1.0.0/LICENSE) and [NOTICE](https://github.com/Soceremite/EvoInquiry/blob/v1.0.0/NOTICE) for license and attribution.
