# 技能表面差异基线

审计基线是 v1.7.0 的 P5 完成快照。已有 Linux 全量测试 1536 项通过、39 项跳过，另有 46 个子测试通过。本地副本保存在 `validation/release-1.7.0/surface-baseline/`，包含各文件 SHA-256 和原始树。

按实际安装路径逐文件比对。相同文件直接复制。工具权限、评审后端、安装定位、恢复说明和主机提示涉及运行时差异。保留原文字节的分歧登记为表面差异，生成测试逐字复核。仅凭行数无法归因的内容不在迁移中删改。

Claude overlay 的八个入口由 `tools/generate_codex_claude_review_overrides.py` 从 Codex 入口转换，支持文件沿用其转换。Gemini overlay 的十五个入口源自现有兼容树，Git 历史显示首次纳入 EvoInquiry 的提交为 `530eb3d`，其后在 `7fa8255`、`6dca674`、`3593c15` 和 `dd57085` 等提交单独维护。迁移保留这些已发布的适配内容。

| 对比结果 | 文件数 |
| --- | ---: |
| 仅 Codex | 25 |
| 仅 主线 | 36 |
| 元数据 | 11 |
| 元数据与正文 | 72 |
| 支持文件内容 | 29 |
| 正文 | 3 |
| 相同 | 37 |

| 路径 | 基线观察 | 迁移处理 |
| --- | --- | --- |
| `README.md` | 仅 Codex | 保留对应目标表面 |
| `README_CN.md` | 仅 Codex | 保留对应目标表面 |
| `ablation-planner/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `alphaxiv/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `analyze-results/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `arxiv/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `auto-paper-improvement-loop/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `auto-review-loop-llm/SKILL.md` | 元数据 | 保留两侧原文，形成可重建的表面差异 |
| `auto-review-loop-minimax/SKILL.md` | 元数据 | 保留两侧原文，形成可重建的表面差异 |
| `auto-review-loop/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `citation-audit/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `claims-drafting/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `comm-lit-review/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `comm-lit-review/references/domain-taxonomy.md` | 仅 Codex | 保留对应目标表面 |
| `comm-lit-review/references/output-template.md` | 仅 Codex | 保留对应目标表面 |
| `comm-lit-review/references/source-policy.md` | 仅 Codex | 保留对应目标表面 |
| `comm-lit-review/references/venue-tiering.md` | 仅 Codex | 保留对应目标表面 |
| `deepxiv/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `dse-loop/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `embodiment-description/SKILL.md` | 元数据 | 保留两侧原文，形成可重建的表面差异 |
| `environment-maintenance/SKILL.md` | 正文 | 保留两侧原文，形成可重建的表面差异 |
| `exa-search/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `experiment-audit/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `experiment-bridge/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `experiment-plan/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `experiment-queue/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `experiment-queue/scripts/build_manifest.py` | 仅 主线 | 保留对应目标表面 |
| `experiment-queue/scripts/queue_manager.py` | 仅 主线 | 保留对应目标表面 |
| `feishu-notify/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `figure-description/SKILL.md` | 元数据 | 保留两侧原文，形成可重建的表面差异 |
| `figure-spec/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `figure-spec/scripts/figure_renderer.py` | 仅 主线 | 保留对应目标表面 |
| `formula-derivation/SKILL.md` | 元数据 | 保留两侧原文，形成可重建的表面差异 |
| `gemini-search/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `grant-proposal/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `idea-creator/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `idea-discovery-robot/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `idea-discovery/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `integrity-forensics/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `interview-cheatsheet/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `invention-structuring/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `jurisdiction-format/SKILL.md` | 元数据 | 保留两侧原文，形成可重建的表面差异 |
| `kill-argument/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `mermaid-diagram/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `meta-apply/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `meta-optimize/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `monitor-experiment/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `novelty-check/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `openalex/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `overleaf-sync/SKILL.md` | 元数据 | 保留两侧原文，形成可重建的表面差异 |
| `paper-claim-audit/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `paper-compile/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `paper-figure/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `paper-illustration-image2/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `paper-illustration/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `paper-plan/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `paper-poster-html/DESIGN_FINAL.md` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/IMPLEMENTATION_CONVENTIONS.md` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/LICENSES/posterly-MIT.txt` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/NOTICE.md` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `paper-poster-html/scripts/_posterly/__init__.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/scripts/_posterly/canvas.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/scripts/_posterly/measure.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/scripts/_posterly/polish.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/scripts/_posterly/preflight.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/scripts/_posterly/render.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/scripts/_posterly/textutil.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/scripts/_posterly/verify_final.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/scripts/asset_check.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/scripts/extract_pdf_figures.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/scripts/poster_check.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/scripts/preprocess_figures.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/scripts/render_preview.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/scripts/run_gates.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/scripts/style_check.py` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/templates/COMPONENTS.md` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/templates/README.md` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/templates/landscape_4col.html` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/templates/landscape_hero.html` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/templates/portrait_2col.html` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/templates/tokens/acl.json` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/templates/tokens/cvpr.json` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/templates/tokens/generic.json` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/templates/tokens/iclr.json` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/templates/tokens/icml.json` | 仅 主线 | 保留对应目标表面 |
| `paper-poster-html/templates/tokens/neurips.json` | 仅 主线 | 保留对应目标表面 |
| `paper-poster/SKILL.md` | 元数据 | 保留两侧原文，形成可重建的表面差异 |
| `paper-slides/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `paper-talk/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `paper-write/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `paper-write/templates/aaai2026.bst` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/aaai2026.sty` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/aaai2026.tex` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/acl.sty` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/acl2026.tex` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/acl_natbib.bst` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/acm.bst` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/acm_mm2026.tex` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/acmart.cls` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/cvpr.bst` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/cvpr.sty` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/cvpr2026.tex` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/iclr2026_conference.bst` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/iclr2026_conference.sty` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/icml2025.tex` | 仅 主线 | 保留对应目标表面 |
| `paper-write/templates/icml2026.sty` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/icml2026.tex` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/neurips2025.tex` | 仅 主线 | 保留对应目标表面 |
| `paper-write/templates/neurips2026.tex` | 仅 Codex | 保留对应目标表面 |
| `paper-write/templates/neurips_2026.sty` | 仅 Codex | 保留对应目标表面 |
| `paper-writing/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `patent-novelty-check/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `patent-pipeline/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `patent-review/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `pixel-art/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `prior-art-search/SKILL.md` | 元数据 | 保留两侧原文，形成可重建的表面差异 |
| `project-governance/SKILL.md` | 正文 | 保留两侧原文，形成可重建的表面差异 |
| `proof-checker/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `proof-orchestrator/NOTICE.md` | 仅 主线 | 保留对应目标表面 |
| `proof-orchestrator/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `proof-orchestrator/references/deepseek-routing.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `proof-orchestrator/references/dispatch-prompts.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `proof-orchestrator/references/stress-tests.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `proof-writer/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `qzcli/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `rebuttal/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `render-html/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `render-html/scripts/render_html.py` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `render-html/scripts/templates/academic.html` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `research-guide/SKILL.md` | 仅 Codex | 保留对应目标表面 |
| `research-implement-feature/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `research-lit/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `research-manager/SKILL.md` | 正文 | 保留两侧原文，形成可重建的表面差异 |
| `research-pipeline/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `research-refine-pipeline/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `research-refine/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `research-refine/references/full-workflow.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `research-review/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `research-wiki/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `resubmit-pipeline/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `result-to-claim/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `run-experiment/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `semantic-scholar/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `serverless-modal/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/acceptance-gate.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/assurance-contract.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/capture-antipatterns.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/citation-discipline.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/compute-env-contract.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/effort-contract.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/evidence-precheck.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/evo-inquiry.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/external-cadence.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/fan-out-pattern.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/injection-hygiene.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/integration-contract.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/output-composition.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/output-language.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/output-manifest.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/resumable-runs.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/review-tracing.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/reviewer-independence.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/reviewer-routing.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/skill-governance.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/taste-calibration.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/venue-checklists.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `shared-references/wiki-helper-resolution.md` | 支持文件内容 | 保留两侧原文，形成可重建的表面差异 |
| `slides-polish/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `specification-writing/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `system-profile/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `training-check/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `vast-gpu/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `web-debug-search/SKILL.md` | 元数据 | 保留两侧原文，形成可重建的表面差异 |
| `wiki-enrich/SKILL.md` | 元数据与正文 | 保留两侧原文，形成可重建的表面差异 |
| `writing-systems-papers/SKILL.md` | 元数据 | 保留两侧原文，形成可重建的表面差异 |

## Rebuttal 旧版基线

两个旧入口见 `docs/archive/rebuttal-legacy/`，基线标签为 `rebuttal-legacy`。上游与旧版的产物和安全门对照见 `docs/REBUTTAL_UPSTREAM_SYNC.md`。

## 入口拆分的加载量

使用 o200k_base 对原入口和生成后的入口计数。参考文档按需加载。

| Skill | 主线行数 | 主线 token | Codex 行数 | Codex token |
| --- | ---: | ---: | ---: | ---: |
| auto-paper-improvement-loop | 710 → 36 | 10189 → 478 | 626 → 29 | 8545 → 378 |
| auto-review-loop | 1093 → 41 | 15906 → 623 | 488 → 28 | 6628 → 342 |
| grant-proposal | 715 → 37 | 8810 → 576 | 636 → 27 | 7503 → 348 |
| idea-creator | 594 → 36 | 8234 → 482 | 441 → 26 | 5702 → 340 |
| paper-illustration | 753 → 37 | 8002 → 551 | 700 → 28 | 7066 → 437 |
| paper-slides | 652 → 36 | 6620 → 500 | 581 → 29 | 5487 → 372 |
| paper-write | 691 → 38 | 9290 → 555 | 490 → 28 | 6406 → 373 |
| paper-writing | 933 → 39 | 12836 → 612 | 755 → 31 | 9240 → 432 |
| proof-checker | 884 → 39 | 13860 → 636 | 566 → 30 | 7347 → 394 |
| research-lit | 781 → 36 | 12086 → 448 | 483 → 26 | 7671 → 295 |

主线、Codex 和相关评审 overlay 总计 30 个入口。最长 41 行，token 降幅最小为 87.8%。
每段原始指令保留在对应参考文档，涉及 Markdown 相对引用时同步修正路径。

## 生成路径

安装树按主线正文、声明的元数据规则和保留的宿主差异生成。宿主差异实体位于 `tools/skill-surfaces/`，避免普通主线安装读取其他宿主的例程。发生冲突时生成器提示对应文件。Codex 专用 research-guide 的源使用 `SKILL.source.md`，生成时才投影为 `SKILL.md`。

试点覆盖 analyze-results、arxiv、monitor-experiment、research-wiki 和 wiki-enrich。合并前逐字对比全部三个表面的目标文件，确认除生成标记外与完成 P2/P3/P4/P5 后的原文件一致。Claude 生成沿用已有转换，并把保留的差异应用于转换结果。Gemini 在对应 Codex 文件上应用差异。
