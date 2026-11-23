# EvoInquiry 优化大纲与实施方案

> 版本：草案 v0.3（2026-11-23，新增资源自适应规划）
> EvoInquiry v1.7.0 的实施对应 §3–§10，验收材料索引见 §11。
> 范围：`skills/` 多表面树结构、SKILL.md 内容组织、评审变体 skill、rebuttal skill 替换（§9）、硬件资源自适应配置（§10）。
> 本方案基于对仓库的实测数据，非泛泛建议；所有结论均可复现验证。行数统计时点为 2026-11-23，P4 后须重测，不把旧行数当作后续验收基线。

## 1. 现状实测（优化依据）

| 检查项 | 实测结果 | 含义 |
| --- | --- | --- |
| 表面结构 | **2 套全量树 + 2 套局部 overlay**：主线 `skills/` 88 个；`skills/skills-codex/` 89 个（多 `research-guide`）；Claude overlay 8 个，已有 `tools/generate_codex_claude_review_overrides.py`；Gemini overlay 15 个，暂未找到专用生成器，维护方式由 P0 核实 | 核心负担是**主线/Codex 全量双写**；overlay 不是全量副本，问题是生成规则分散且不统一，不能笼统说“4 棵树都靠人工维护” |
| 主线/Codex 抽样差异 | `analyze-results`：110 vs 108 行，frontmatter 与措辞不同；`auto-review-loop`：**1093 vs 488 行**，为当前抽样到的最大行数差 | **行数差不自动等于漂移**：可能是运行时差异，也可能是内容漏同步；必须由 P0 分类后再定性 |
| 治理块占比 | 主线全部 SKILL.md 共 29250 行，`EVO-INQUIRY`/`EI-GOVERNANCE` 标记块合计 1076 行，**仅 4%** | “注入模板过重”不成立，治理块保持原样，不作为优化对象 |
| 超长入口文件 | 10 个 skill 超过 300 行，最大 1093 行（清单见 §5） | 入口全量加载带来 token 与导航成本；行数是筛查指标，最终收益以 token 和行为测试共同验收 |
| 模型变体 | 仅 2 个：`auto-review-loop-llm`、`auto-review-loop-minimax`，各 63 行，diff 主要是后端 MCP 名称与 description | 可低成本共享正文 |
| 已有保护网 | `tests/test_codex_skill_mirror.py`、`tools/check_skills_inventory.py`、`tools/skill-contracts.json`、`tests/test_skill_behavior_harness.py`、`tests/test_trigger_eval.py` | 优化必须复用并加强这些测试，而不是另起炉灶 |
| 已有生成器先例 | `tools/convert_skills_to_llm_chat.py`（支持 `--dry-run`）与 Claude overlay 专用生成器 | “单源 + 生成”已有局部实践；P1 是统一与扩展现有机制，不是从零发明 |
| 资源机制现状 | `tools/resource_budget.py` 已支持 NVIDIA/CPU/RAM/磁盘探测、用户上限、plan/launch 两次检查；但 `skills/experiment-queue/scripts/build_manifest.py:79-80` 默认 `gpus=0..7`、`max_parallel=8`，`queue_manager.py:567` 也有 8 卡回退；准入工具只判断单个完整请求，不生成替代配置 | 不能误称当前完全没有硬件自适应；真正缺口是**默认配置硬编码、动态并发与候选配置规划**，由 P5 处理 |

## 2. 优化目标、统一原则与非目标

**目标**

1. **P1：统一源树与表面生成**。`skills/<name>/` 成为唯一人工维护源；Codex 全量树由生成器产出；Claude/Gemini overlay 纳入同一套声明式规则与 CI 校验，复用或迁移已有生成逻辑。
2. **P2：超长 SKILL.md 渐进式拆分**。§5 清单内入口控制在 200 行以内，细节下沉到 `references/` 按需加载；研究流程、产物与安全语义不变。
3. **P3：评审变体共享正文**。消除 `-llm` / `-minimax` 的重复正文，保留 skill 名与触发词。
4. **P4：rebuttal 基座替换**。以 awesome-rebuttal 替换旧实现并移植 EvoInquiry 独有优势。
5. **P5：硬件资源自适应规划**。在现有会话资源表与准入门之上增加候选配置规划和动态并发，消除资源绑定路径中的 8 卡/8 并发硬编码；用户上限始终优先于可用硬件。

**行为变更边界**：P4 允许 rebuttal 研究行为与产物升级；P5 只允许资源调度与配置选择行为变化，不得借此改变科学目标、公平比较条件或冻结中的实验输入。其余阶段保持研究行为与产物契约。

**统一判定原则（避免双重标准）**

- **差异先审计，后定性**：1093 vs 488 只称“最大行数差”，未经 P0 分类不得称为漂移或删除某侧内容。
- **内容变更先于表面归并**：rebuttal、auto-review-loop、两个模型变体以及 P5 涉及的资源相关 skill 分别先完成 P4/P2/P3/P5，再进入 P1；其余稳定 skill 可先试点生成器。
- **阻断与降级分开**：证据、venue 权限或安全条件缺失时必须阻断；可选外部工具不可用时允许降级，但必须在产物中披露验证范围，不能把 in-context 彩排伪装成跨族外部验证。
- **资源灵活性有边界**：有效资源 = 实际可用硬件 ∩ 用户授权上限 ∩ scheduler/lease 约束。动态规划可以降并发、换设备、等待或提出替代配置，但不能突破用户上限、杀死别人的任务、把未知遥测当作空闲，或静默降低科学要求。
- **兼容分两层**：P0–P3 保持研究行为与产物契约；P4 保持 skill 名、命名空间和触发兼容，但产物/状态格式变化必须写入 CHANGELOG 与迁移说明；P5 的资源行为变化须保留原授权与审计语义。

**非目标（明确不做）**

- 不增删对外可用 skill，不改变 `evo-inquiry:` 命名空间与其他 skill 的路由语义。P1 把 Codex 已有的 `research-guide` 纳入源树只是统一维护入口，不是新增能力；P4 只替换 rebuttal 内部实现。
- 不改动 `EVO-INQUIRY` / `EI-GOVERNANCE` 治理块内容；P4 新基座需保留同等治理约定。
- 不改动 `mcp-servers/`、`tools/` 中与本方案无关的运行时逻辑。
- 不改变发布流程的门禁语义，只增强检查。

## 3. P0：基线审计与保护网（0.5–1 天）

目的：在任何 P1–P4 修改前固定基线，确保后续每一步可对比、可回滚。

1. 跑全量测试记录基线（不用 `-x`，避免首个失败后丢失完整基线）：
   ```sh
   python -m pytest tests/ -q | tee /tmp/ei-baseline.txt
   ```
2. 生成主线/Codex 差异报告，按“frontmatter 差异 / 正文差异 / 文件缺失”分类：
   ```sh
   diff -rq skills/ skills/skills-codex/ --exclude=skills-codex --exclude=skills-codex-claude-review --exclude=skills-codex-gemini-review > /tmp/ei-drift.txt
   ```
3. 人工把每处差异标注为「刻意（运行时差异）」「漂移（bug）」或 `pending_review`，产出 `docs/SURFACE_DIFF_AUDIT.md`。
   - 刻意差异 → 进入生成器的声明式规则（见 P1）。
   - 漂移 → 单独提 PR 修复，**不与生成器改造混在同一 PR**。
   - 只有行数不同但语义尚未核对的条目标为 `pending_review`；该 skill 在核对完成前不得进入 P1 迁移。
4. 核实两套 overlay 的维护链：Claude 记录现有生成器的输入/输出与覆盖 8 个 skill 的规则；Gemini 核实 15 个 skill 的来源，并把未自动化的差异写入同一审计报告。
5. 固定 P4 旧版 rebuttal 基线：保存 394 行入口、产物清单与硬安全门行为，建立旧行为到上游 `tests_or_checks` 的对照，供替换后回归。
6. 输出超长文件清单（§5 表格即为初版），确定 P2 处理顺序；入口 token 数与行数同时记录。

**验收**：基线测试结果已记录；主线/Codex 差异均有分类或 `pending_review`；两套 overlay 的来源链已写清；P4 旧行为有可重放的对照材料。

## 4. P1：单一源树 + 表面生成器（核心，约 2–3 周）

### 4.1 设计

采用「**共享正文 + 表面标记段**」方案，源文件仍是每个 skill 一个 `skills/<name>/SKILL.md`：

- 所有表面共享的内容：保持现状，直接书写。
- 表面特有内容：用标记包裹，例如
  ```md
  <!-- SURFACE:codex -->
  This is the Codex-native entrypoint. Use the exact discovered ...
  <!-- /SURFACE -->
  <!-- SURFACE:mainline -->
  When a Codex plugin session is active, use its exact discovered ...
  <!-- /SURFACE -->
  ```
- frontmatter 差异（如 Codex 树去掉 `argument-hint`、`allowed-tools`，`name` 加引号）做成生成器的**声明式规则**，写在 `tools/surface_rules.json`，不写死在代码里。
- `research-guide` 仅存在于 Codex 树：在源树为其建立 `skills/research-guide/`，用 frontmatter 加 `surfaces: [codex]` 声明只生成到指定表面。

新增工具 `tools/generate_skill_surfaces.py`（参照 `convert_skills_to_llm_chat.py` 的 CLI 风格）：

```sh
# 生成全部表面树（写入 skills/skills-codex/ 等）
python tools/generate_skill_surfaces.py --surface all
# CI 校验模式：不写入，生成结果与已提交内容不一致则退出码非零
python tools/generate_skill_surfaces.py --surface all --check
# 单 skill 试点
python tools/generate_skill_surfaces.py --surface codex --skill analyze-results --dry-run
```

### 4.2 生成物的管理决策

**推荐：生成树继续提交到 git**，理由：插件直接从仓库发现 `skills/skills-codex/`，Release 打包与 `codex plugin marketplace add "$PWD"` 都依赖它存在；用 `--check` 模式进 CI 防止手改生成树。不建议改为 `.gitignore` + 安装时生成（会改变安装契约，风险大）。

同时在所有纳管生成产物的文件头部生成一行注释：
`<!-- GENERATED from skills/<name>/SKILL.md — do not edit directly -->`。

### 4.3 分批迁移步骤

1. **试点批（5 个）**：选差异小且**不在 P2/P3/P4/P5 内容变更清单中**的稳定 skill（首个候选 `analyze-results`，其余由 P0 报告确定），验证标记语法与 frontmatter 规则足以表达现有刻意差异。两个模型变体不再作为试点，避免与 P3 重复改造。
2. **普通批（每批约 15 个）**：按审计报告逐批归并。特殊 skill 遵循“内容先行”：`auto-review-loop` 先 P2、`rebuttal` 先 P4、两个模型变体先 P3、`experiment-plan` / `experiment-queue` / `idea-discovery` / `idea-creator` 先 P5，完成后再进入对应 P1 批次。
3. **overlay 批**：Claude overlay 复用 `tools/generate_codex_claude_review_overrides.py` 的现有规则并迁入统一配置；Gemini overlay 按 P0 核实的来源链迁移。旧脚本须等新路径产物对齐、测试通过后再废弃，不能先删后补。
4. **切换 CI**：`tests/test_codex_skill_mirror.py` 中的人工一致性断言逐步替换为「生成器 `--check` 全量通过」。集合断言改为由 frontmatter `surfaces` 驱动：源树纳入 `research-guide` 后为 89 个，Codex 生成集合等于声明包含 `codex` 的 skill 集合，不再硬编码“88 + 1”。

每批必跑：

```sh
python -m pytest tests/test_codex_skill_mirror.py tests/test_plugin_manifest.py \
  tests/test_skill_behavior_harness.py tests/test_trigger_eval.py \
  tests/test_llm_chat_converter.py -q
```

### 4.4 风险与回滚

| 风险 | 缓解 |
| --- | --- |
| 刻意差异被误判为漂移而误删 | P0 的人工分类报告是生成规则的唯一依据；试点批先验证表达能力 |
| 生成器 bug 影响全部 89 个 skill | 分批迁移，每批独立 PR；未迁移的 skill 维持主线/Codex 双写，Claude overlay 沿用现有生成器，Gemini 按 P0 核实的旧链维护 |
| 社区有人直接编辑生成产物 | 头部 GENERATED 注释 + CI `--check` 双重拦截；`CONTRIBUTING.md` 更新说明 |
| 回滚 | 每批独立 PR，revert 即可；源树始终是唯一事实来源，生成产物可随时重建 |

**验收**：Codex 全量树 100% 由新生成器产出；Claude/Gemini overlay 均纳入统一规则、可重复生成并通过 `--check`；CI 全绿；修改源文件后，相关表面产物一次生成同步。

## 5. P2：超长 SKILL.md 渐进式拆分（1–2 周，内容先行，与 P1 按 skill 错峰）

### 5.1 拆分对象（实测行数，主线树）

| 顺序 | skill | 行数 |
| --- | --- | --- |
| 1 | auto-review-loop | 1093 |
| 2 | paper-writing | 933 |
| 3 | proof-checker | 884 |
| 4 | research-lit | 781 |
| 5 | paper-illustration | 753 |
| 6 | grant-proposal | 715 |
| 7 | auto-paper-improvement-loop | 710 |
| 8 | paper-write | 691 |
| 9 | paper-slides | 652 |
| 10 | idea-creator | 593 |

### 5.2 拆分规范

- **入口 ≤ 200 行**，只保留：frontmatter、何时使用（触发条件）、主流程摘要（步骤清单）、references 索引、停止条件。
- 详细流程、检查清单、模板、示例移至 `skills/<name>/references/<topic>.md`，入口用相对链接引用；与现有 `shared-references/` 的引用方式保持一致。
- 每个 reference 文件在开头注明「何时需要读本文件」，避免 agent 无差别加载。
- **不改研究行为**：拆分是纯内容搬移 + 索引，禁止顺手改写研究流程、产物或安全语义；从“入口全量阅读”变为“按需读取 references”是本阶段唯一有意的加载策略变化。如需改研究语义，另提 PR。
- 拆分后同步更新 Codex 对应树（P1 完成后由生成器处理）；若该 skill 同时有 Claude/Gemini overlay，则用对应生成链重建，不能只改主线。

### 5.3 验收

- 研究行为不退化：`tests/behavior/`、`tests/test_skill_behavior_harness.py`、`tests/test_trigger_eval.py` 全绿。
- 契约检查：`tools/check_skills_inventory.py` 与 `tools/skill-contracts.json` 中若引用了被搬移的段落位置，同步更新。
- 量化收益：记录每个 skill 拆分前后入口文件的行数/token 数，写入 PR 描述；以入口默认加载 token 下降 60% 以上为目标，不把按需读取的 references 计入默认加载量。

## 6. P3：评审变体共享正文（2–3 天，在变体进入 P1 前完成）

对象：`auto-review-loop-llm` 与 `auto-review-loop-minimax`（各 63 行，diff 仅为后端 MCP 名称、description、触发词）。

**推荐方案：共享正文 + 薄入口**，而非直接删目录：

1. 新建 `skills/shared-references/external-review-loop.md`，承载两者共同的流程正文，并同步 Codex 对应 shared-references；避免让 minimax 反向依赖 llm 的目录。
2. 两个 SKILL.md 缩减为约 20 行：各自 frontmatter（保留 `"llm review"` / `"minimax review"` 触发词）+ 后端配置段 + 指向共享正文的链接。
3. 不删除任何 skill、不改 `description` 触发语义，因此无需新增 catalog/group 条目；但镜像、引用路径、契约中相关段落与测试仍须同步，**不宣称“零改动”**。
4. 若未来确需减目录，再评估合并为 `auto-review-loop-external` + backend 参数；届时需保留旧名称 alias 一个版本，并同步 `tests/test_review_loop_adapters.py`、`tests/test_llm_chat_converter.py`。

**验收**：两个变体正文零重复；`tests/test_review_loop_adapters.py`、`tests/test_minimax_integration.py`、`tests/test_llm_chat_review_fallback.py` 全绿。

## 7. 里程碑汇总

| 阶段 | 内容 | 预估工作量 | 关键交付物 |
| --- | --- | --- | --- |
| P0 | 全量基线 + 主线/Codex 差异审计 + overlay 来源链 + rebuttal 对照材料 | 0.5–1 天 | `docs/SURFACE_DIFF_AUDIT.md` |
| P4 | rebuttal 以 awesome-rebuttal 为基座替换（方案 B） | **2–3 天** | 新 `skills/rebuttal/` + 3 项独有优势移植 + 归档旧版 |
| P5 | 用户约束 + 实时硬件的候选配置规划与动态并发 | **3–5 天** | `tools/resource_planner.py`、`RESOURCE_PLAN.md`、去除资源绑定路径的 8 卡/8 并发硬编码 |
| P2 | 10 个超长入口拆分，auto-review-loop 优先 | 1–2 周 | 各 skill `references/`、入口 ≤200 行 |
| P3 | 2 个评审变体共享正文 | 2–3 天 | 共享 reference + 薄入口 |
| P1 | 统一生成器 + Codex 全量树迁移 + 2 套 overlay 纳管 | 2–3 周 | `tools/generate_skill_surfaces.py`、`tools/surface_rules.json`、CI `--check` |

**推荐落地顺序**：P0 → P4/P5 → P2/P3 → P1 全量迁移。P4 与 P5 相互独立，可按人力并行。P1 的生成器开发和 5 个稳定 skill 试点可在 P0 后立即并行，但试点不得包含任何 P2/P3/P4/P5 目标 skill；这些特殊 skill 必须先完成各自内容阶段，再进入 P1，避免“先归并、后重写”的重复工作。P4 后 rebuttal 不再进入 P2，其新入口按自身 token 实测验收，不机械套用 P2 的 200 行门槛。

## 8. 给维护者的执行建议

- 每个阶段独立 PR，PR 描述附实测数据（漂移数、行数变化、token 变化），便于评审。
- P1 迁移期间在 `CONTRIBUTING.md` 顶部加临时公告：Codex 生成树及已纳管 overlay 禁止手改；未迁移部分仍按各自现行维护链操作。
- 全部完成后，把 `AGENT_GUIDE.md` 的维护说明改为“源树 + 生成产物”；但**运行时不得混用不同引用树的约束仍保留**，因为它保护的是一次会话内的引用一致性，不只是防止人工双写漂移。

## 9. P4：rebuttal skill 替换——以 awesome-rebuttal 为基座（方案 B，约 2–3 天）

> 决策：不并存、不做增量吸收，直接以 [`xiongqi123123/awesome-rebuttal`](https://github.com/xiongqi123123/awesome-rebuttal)（MIT）为基座**替换**现有 `skills/rebuttal/`，把 EvoInquiry 独有的三项能力移植过去，旧版归档保留一个版本。
> 依据（已读双方实际文件核实）：新基座无 MCP 硬依赖、结构化问卷交互、6 种回复格式（含 one-page PDF）、入口 182 行 + 20 个能力文件按需加载、带策略库/11 个模板/3 个完整示例/验收清单；旧版 394 行单文件、Phase 6 压测强依赖 Codex/manual-review MCP 且硬编码审稿模型，非 Codex 环境走不完流程。

### 9.0 对比与增量清单（决策背景）

双方都具有 provenance/commitment/coverage 三类安全门，不能再把这三者称为 EvoInquiry 独有优势。旧版真正需要保留的是：**REVISION_PLAN 承诺双向追踪、跨模型族外部压力测试与身份约束、review tracing**，以及 consistency/thread-local/adversarial-design 三项额外检查。awesome-rebuttal 自带以下 6 个增量，方案 B 落地后由新基座直接提供；9.3 负责保留旧版的额外能力：

| awesome-rebuttal 的能力 | EvoInquiry 现状 | 可吸收的增量 |
| --- | --- | --- |
| AC summary writer（面向 Area Chair 的决策摘要） | 只有 meta-reviewer closing 一句话规则 | 新增 AC_SUMMARY 产物：决策事实清单，服务最终定稿 |
| 实验四级分诊（must-do / 高价值可选 / 不建议 / 不可行 + EXP-* 编号） | Phase 3.5 只有 mini plan + GPU 估算 | 实验计划加分诊 taxonomy，避免为不值得的实验烧预算 |
| 多 persona 彩排（原审稿人 / 独立审稿人 / AC 三种角色 + 现成 prompt + anticipated answer bank） | Phase 6 只有单一外部审稿人压测 | 增加 AC persona 压测；answer bank 产物直接喂给多轮讨论的 delta 回复，跨轮复用 |
| 审稿人参与度/分数追踪器（跨轮次） | Phase 8 只有 FOLLOWUP_LOG 原文记录 | 每轮 stance 变化追踪，支撑「何时停止争论」决策 |
| one-page PDF rebuttal + 内置 LaTeX 模板 | 明确不做 PDF，仅 text-only / per-reviewer | 新增输出格式，覆盖 CVPR/ICCV 等一页 PDF 会议（真实能力空白） |
| JSON memory schemas + 快照/版本管理 + 渲染脚本 | 全部 Markdown 状态文件 | 状态文件加 schema 校验，多轮 diff 可机器检查 |

**架构层面的启发更重要**：awesome-rebuttal 的「薄 SKILL.md 入口 + `references/capabilities/` 20 个原子能力文件 + 按生命周期分组」正是本方案 **P2 渐进式拆分的参考实现**。旧版 rebuttal（394 行）不再先拆后换，而是由 P4 直接采用该结构替换，并通过 9.2/9.3 保留旧版额外检查与追踪能力。

### 9.1 目标结构

```
skills/rebuttal/                     # skill 名保持 rebuttal，触发词与路由不变
├── SKILL.md                         # 上游 182 行入口 + EI 适配段（见 9.4）
├── references/
│   ├── capabilities/00..19_*.md     # 上游 20 个能力文件；移植后合计 21 个
│   ├── capabilities/20_revision_commitment_tracker.md   # 移植①，新增
│   ├── core/user_questionnaire_protocol.md
│   ├── strategy-library/            # concern/posture taxonomy、实验决策规则等
│   ├── templates/                   # 上游 11 个模板 + revision_plan.md（移植①）
│   └── examples/                    # 上游 3 个完整示例，兼作验收夹具
├── assets/one-page-rebuttal-template/
├── scripts/render_snapshot.py
└── tests_or_checks/                 # 上游验收/安全回归清单，接入 EvoInquiry 行为测试
```

许可：上游 MIT，复制时在 `NOTICE` 增加署名与来源 commit SHA；新建 `docs/REBUTTAL_UPSTREAM_SYNC.md` 记录基座版本，**所有 EvoInquiry 本地改动用 `<!-- EI-LOCAL:BEGIN/END -->` 标记包裹**，便于以后 rebase 上游更新。

### 9.2 旧能力映射与取舍

| 旧版（394 行，Phase 0–9） | 去向 |
| --- | --- |
| Phase 0–2 初始化/审稿归一化/原子化 | 上游 00/01/05/06/07 能力文件替代；`ISSUE_BOARD.md` → atomic concern ledger（JSON + 模板） |
| Phase 3 策略计划 | 上游 08 strategy planner + 策略库替代；`STRATEGY_PLAN.md` → response strategy matrix |
| Phase 3.5 证据冲刺（AUTO_EXPERIMENT） | 保留为 EI-LOCAL 段，挂入上游 `10_experiment_triage.md`：用户批准的 must-do `EXP-*` 可交接 `/experiment-bridge`，默认 false 不变 |
| Phase 4 起草 + 防守性写法启发式 | 上游 11/12/13 替代；旧版独有的 reviewer-defensive moves（最小充分证据、预注册校准措辞、structural_distinction 等 5 条）**是真实增量**，迁入上游 `strategy-library/tone_and_safety.md` 的 EI-LOCAL 段 |
| `REVISION_PLAN.md` 承诺追踪 | 移植①，见 9.3 |
| Phase 5 八道 lint | 上游 14 safety checker 已有五道 gate（provenance/commitment/coverage/venue/tone）；旧版独有的 **consistency 跨回复一致性、thread-local context、adversarial design-choice scan** 三项以 EI-LOCAL 段补入 14 |
| Phase 6 外部压测 | 移植②，改造上游 18 rehearsal |
| Phase 7 双版本产物（PASTE_READY + rich） | `PASTE_READY.txt` 精确字符数要求以 EI-LOCAL 段保留进 11；`REBUTTAL_DRAFT_rich.md` 保留为**可选**扩展产物，不再默认强制，变化写入 CHANGELOG，不能未核实就宣称上游已覆盖 |
| Phase 8 多轮跟进 | 上游 19 discussion handler 替代（自带 engagement/score tracker 与 delta-only 起草，优于旧版） |
| Phase 9 render-html | **不移植**。新基座有快照渲染与 PDF 产物，HTML 渲染非核心；如需保留走通用 `/render-html` skill，不写在 rebuttal 流程里 |
| QUICK_MODE（只出分析不起草） | 保留：SKILL.md 注明 narrow run = 只读 00–08 能力文件，输出分析后停止 |
| Review tracing | 移植③，见 9.3 |

### 9.3 三项独有优势的移植设计

**移植① REVISION_PLAN 承诺双向追踪**（新增能力文件 `20_revision_commitment_tracker.md` + 模板 `templates/revision_plan.md`）：
- 产物保持 `REVISION_PLAN.md`：扁平 checklist（每项原子、带 issue_id、commitment 分类 `already_done`/`approved_for_rebuttal`/`future_work_only`）+ 按章节/severity 分组视图 + 承诺统计 + out-of-scope log。
- 在上游 `14_safety_rule_checker.md` 的 commitment gate 中加 EI-LOCAL 双向校验：**草稿中每个隐含论文修改的承诺必须在 REVISION_PLAN 有条目，且计划中无孤儿条目**；19 discussion handler 每轮更新 checkbox 状态而非重新生成。

**移植② 跨模型族外部压测（改为可选后端）**，改造上游 `18_rebuttal_rehearsal.md`：
- **默认保持上游原样**：in-context persona 彩排（原审稿人/独立审稿人/AC），零依赖，任何环境可完成。
- 新增 EI-LOCAL 可选段 `reviewer_backend: codex | manual`：启用时沿用旧版身份规则——`Reviewer-Model: <exact-model-id>` 开头、`executor_model` 如实传递、同族模型不能 acquit、无法确认身份输出 `REVIEW_UNAVAILABLE`；轮次沿用 base 1 轮 + pivotal 聚焦轮、硬上限 5。
- 后端不可用**不再阻塞流程**：降级为 in-context 彩排并在报告中显式标注“未做跨族外部验证”，这正是旧版最大的可用性痛点。

**移植③ Review tracing 取证**：外部后端启用时遵循 `shared-references/review-tracing.md`（Policy C），用 `tools/save_trace.sh` 落盘 `.ei/traces/rebuttal/`；in-context 彩排无外部调用，不强制 trace。

### 9.4 EvoInquiry 集成适配

- `SKILL.md`：name 保持 `rebuttal`；description 合并旧触发词（"rebuttal"/"reply to reviewers"/"ICML rebuttal"/"OpenReview response"）与新增 PDF 场景；顶部保留 `EVO-INQUIRY` / `EI-GOVERNANCE` 块。默认 frontmatter 不再声明 MCP 为必需工具；可选外部后端的工具授权与身份要求写在 18 号能力文件的 EI-LOCAL 段。
- 状态目录：上游 `.awesome-rebuttal/` 改为经 `tools/state_paths.py` 解析的 `.ei/rebuttal/`（memory/drafts/snapshots/templates/logs/cache 子结构不变）；运行时状态绝不写入 skill 安装目录。
- 语言政策与 venue rules 运行时确认（user-provided 或 AI-searched + user-confirmed）保留上游设计：先通过问卷补齐，仍缺失则阻断起草；这与“可选外部工具缺失可降级”是两个不同维度，不冲突。
- Overleaf/LeafLink：保留为可选能力且默认沉默；其链接不得出现在任何投稿面向文本（上游已有此安全规则，保留）。

### 9.5 受影响文件清单（已 grep 核实）

- 替换：`skills/rebuttal/**`；同步：`skills/skills-codex/rebuttal/**`（P1 未完成前按现行方式同步）。当前 Claude overlay 8 个、Gemini overlay 15 个 skill 清单中**均不含 rebuttal**，因此本阶段不新增 overlay；未来若支持，另按 P1 规则处理。
- 契约/目录：`tools/skill-contracts.json`、`tools/skill-groups.tsv`、`docs/SKILLS_CATALOG.md`、`AGENT_GUIDE.md`（Workflow 4 描述更新）。
- 既有测试：`tests/test_codex_skill_mirror.py`、`tests/test_copilot_install.py`、`tests/test_http_reviewer_fallback_contract.py`（外部后端可选化后需改断言：MCP 缺失不再 stop，而是降级 + 标注）。
- 新增测试：`tests/test_rebuttal_contract.py`——REVISION_PLAN 双向校验、venue 未确认不起草、外部后端缺失时 in-context 彩排可完成、legacy 状态导入提示。
- 合规/发布：`NOTICE`（署名）、`CHANGELOG.md`（替换说明 + 旧版归档位置）。

### 9.6 旧版归档与迁移

- 替换前打 git tag `rebuttal-legacy`；旧版完整复制到 `docs/archive/rebuttal-legacy/`（**不放 `skills/` 树下**，避免被插件发现成第二个 skill）。
- 用户已有旧版 `rebuttal/` 工作目录时：新 01 intake gate 增加 EI-LOCAL 检测——发现 `REBUTTAL_STATE.md` 则提示「导入为新 JSON memory」或「只读查看旧记录」，不静默覆盖；进行中的多轮讨论允许用旧记录人工接续。
- 触发词、skill 名、`evo-inquiry:rebuttal` 命名空间不变，**触发层面无迁移成本**；状态格式、默认产物和可选 rich/HTML 行为的变化必须写入 CHANGELOG，进行中的项目按上条导入或只读接续。

### 9.7 验收标准

1. 上游 `tests_or_checks/` 三份清单（manual_acceptance_cases / memory_schema_checklist / safety_regression_checklist）全部通过，并固化为 EvoInquiry 行为测试。
2. 旧版硬门回归：编造证据被 provenance gate 拦截、未批准承诺被 commitment gate 拦截、审稿意见零遗漏（coverage）、超字符限制被拦截。
3. 移植①往返测试：草稿增删承诺 → REVISION_PLAN 同步增删，孤儿条目报警。
4. 移植②降级测试：无 MCP 环境完整跑通 rehearsal 并输出“未做跨族外部验证”标注。
5. 用上游 3 个 synthetic 示例（openreview / one-page / hybrid）各跑一次端到端，产物齐全。
6. `python -m pytest tests/test_codex_skill_mirror.py tests/test_copilot_install.py tests/test_http_reviewer_fallback_contract.py tests/test_rebuttal_contract.py tests/test_trigger_eval.py -q` 全绿。
7. 兼容验收：旧触发词仍路由到 `rebuttal`；rich 改可选、Phase 9 不内嵌 render-html、状态目录变化均有迁移说明，不以“行为完全不变”作为 P4 验收口径。

### 9.8 执行步骤与工作量

| 步骤 | 内容 | 预估 |
| --- | --- | --- |
| B0 | 固定上游 commit、复制基座、NOTICE 署名、打 `rebuttal-legacy` tag | 0.5 小时 |
| B1 | EI 适配：状态目录、frontmatter、治理块、QUICK_MODE、旧 lint 三项补入、rich 可选化与迁移说明 | 0.5 天 |
| B2 | 三项移植（20 号能力文件、18 号可选后端、tracing） | 0.5–1 天 |
| B3 | 镜像树/契约/目录/既有测试更新 + 新增契约测试 | 0.5 天 |
| B4 | 三示例端到端验收、旧版归档、CHANGELOG | 0.5 天 |

### 9.9 风险与回滚

| 风险 | 缓解 |
| --- | --- |
| 上游更新后难同步 | EI-LOCAL 标记 + `docs/REBUTTAL_UPSTREAM_SYNC.md` 记录基座 SHA，本地改动可机械重放 |
| 旧版隐性行为丢失 | 9.2 映射表逐项核对，验收第 2 条做硬门回归；旧版归档可随时查阅 |
| 既有测试假设 MCP 必需 | 9.5 已定位 `test_http_reviewer_fallback_contract.py`，改为断言降级行为 |
| 整体不满意需回退 | `rebuttal-legacy` tag + 归档目录，单次 revert 恢复 |

## 10. P5：硬件资源自适应规划（约 3–5 天）

> 目标：根据**用户给定限制、当前实际可用硬件和任务峰值需求**生成资源配置与并发度，而不是假设固定的 8 卡/8 并发。灵活性只作用于资源层，不突破授权、不改变科学目标。

### 10.1 保留现有能力，只补真实缺口

| 已有能力（保留，不重写） | 真实缺口（P5 处理） |
| --- | --- |
| `resource_budget.py` 已读取 NVIDIA GPU、CPU affinity/cgroup、RAM 与磁盘；支持用户 custom 上限、GPU allowlist/sharing、plan/launch 两次实时检查 | `build_manifest.py:79-80` 缺省写入 `gpus=list(range(8))` 和 `max_parallel=8`；`queue_manager.py:567` 也有 8 卡回退 |
| 会话资源表 `.ei/resource-sessions/<session-id>.json` 是唯一策略源；硬件变化刷新观测但保留用户选择 | 用户限制、任务需求与当前硬件之间缺少统一的候选配置规划产物 |
| `evaluate()` 已区分 `AUTO_APPROVED` / `WAIT_RESOURCE` / `REPLAN_REQUIRED` / `NEEDS_ESTIMATE` / `NEEDS_APPROVAL` | 当前只评估一个完整请求；资源不足时不自动给出“降并发/换设备/等待/替代配置”的可执行候选 |
| 队列已能把 `max_parallel` 当上限并只启动 admitted subset | 省略并发度时没有按整个并发批次的 GPU/RAM/磁盘叠加峰值动态计算；`queue_manager.py:645-647` 还阻止自己的任务共用设备，即使会话允许 sharing |

明确不重复建设：不再做第二份资源策略文件，不绕过首次用户选择，不取消启动前准入，不把旧的 `gpu_free_threshold_mib` 兼容参数重新变成主调度逻辑。首版沿用现有 NVIDIA/CPU/RAM/磁盘探测能力，不在本阶段承诺 AMD/Apple 等新遥测后端。

### 10.2 统一配置规则

1. **有效容量**：`effective = observed_available ∩ user_policy ∩ scheduler/lease`。
   - 用户指定 GPU IDs、RAM/磁盘/时长/花费/并发上限时，均为硬边界。
   - `all_visible` 只跟随当前被允许可见的设备；显式 allowlist 不因发现新卡而扩大。
   - 遥测未知保持 `NEEDS_ESTIMATE`，不得当作空闲或零占用。
2. **最大可用不等于默认用满**：未设上限时仍采用满足任务的最小充分资源；默认偏好 `balanced`，用户可选 `fastest` 或 `lowest_resource`。
3. **用户已在任务中明确给出等价限制时**，直接映射到现有 `select --preset custom` 并记录用户选择引用，不重复询问；只有冲突或缺失的关键授权才提问。
4. **规划可自动，科学变更不可静默**：降并发、换同权限设备、等待属于资源层；修改 batch/effective batch、精度、模型、数据、种子或冻结配置属于实验层，必须另列影响并按规定确认。

示例：用户限定“只用 GPU 0/1、最多 2 并发、RAM 64 GiB、时间不限”，即使机器有 8 张卡，规划也只能在 0/1 中选择；若两任务叠加峰值只能容纳 1 个，则先启动 1 个，另一个保持 pending，而不是报 8 卡配置或抢占其他任务。

### 10.3 新增候选配置规划器

新增 `tools/resource_planner.py`，复用 `resource_budget.probe()`、`hardware_state()` 与 `evaluate()`，**不新建调度器或策略存储**。

输入为任务资源模板，而非要求调用者预先写死 GPU ID：

- `gpu_options`：每个候选包含 GPU 数量和每卡额外峰值，允许显式 CPU-only 候选。
- `cpu_cores`、`ram_bytes`、`job_seconds`、`storage`、`new_spend`：沿用现有请求字段和单位。
- `max_parallel_jobs`：用户并发硬上限，可空；空不等于无限，由可 admitted 的任务数决定。
- `preference`：`balanced`（默认）/ `fastest` / `lowest_resource`。
- 科学要求只作为冻结约束的引用，规划器不得自行改写。

规划器行为：

1. 在实际目标 host 重新探测硬件，只枚举用户允许的设备；按“满足峰值后的余量”排序，以 UUID 做稳定 tie-breaker，生成完整现有 schema 的候选 request。
2. 用现有 `evaluate()` 验证候选；启动前仍必须再经 `check_launch()`，规划结果不能替代准入。
3. 对并发 N，按**整个同时运行批次**叠加每卡 VRAM、RAM 与各真实文件系统存储峰值，计算可接纳的最大 N，再取 `min(N_admitted, 用户上限, pending任务数)`。
4. 输出 `<experiment-output>/RESOURCE_PLAN.md` 与 `resource-request.json`：列出用户上限、实测硬件、有效容量、选择理由、被否决候选及原因、并发计算、共享/公平性注意事项和下次复查点。它们是规划产物，不是第二份会话策略。
5. 冻结配置继续绑定现有 `configuration.resource_budget`；运行中不得 live-edit，硬件变化时在下一启动/恢复点重新规划。

建议 CLI：

```sh
python tools/resource_planner.py --root <project> --session <id> \
  --task <task-resource.json> --preference balanced --output-dir <experiment-output> --markdown
python tools/resource_budget.py --root <project> --session <id> \
  check --stage launch --request <experiment-output>/resource-request.json --markdown
```

### 10.4 队列默认值与动态并发改造

- `build_manifest.py`：资源绑定任务省略 `gpus` 时，不再生成 `0..7`，而是由规划器在准入后确定设备；省略 `max_parallel` 时不在 manifest 中写入 8，由每个调度步按当前峰值动态计算。
- `queue_manager.py`：资源绑定路径使用规划器的 admitted assignments 和动态 slots；用户显式 `gpus`/`max_parallel` 始终作为额外硬上限。会话允许 sharing 时，自己的多个资源绑定任务也可在每卡叠加峰值与 lease 允许的前提下共享设备；exclusive 或 legacy 路径继续一任务一设备，所有共享均记录。
- **旧未绑定 legacy 任务不自动接管**：旧 manifest 可继续走既有兼容路径，但新 manifest 若缺少资源绑定，必须显式给出设备/并发或先绑定会话，不能一边无准入一边声称已动态安全调度。
- 资源等待保持原实验身份、不消耗 OOM 重试；不得为释放资源停止其他任务。

### 10.5 资源不足时的统一决策矩阵

| 情况 | 自动允许的动作 | 必须额外确认/禁止 |
| --- | --- | --- |
| 当前空闲不足，但物理总容量足够 | 降并发、选择其他允许设备、保持 pending 等待 | 不得杀死或暂停别人的任务 |
| 单任务峰值超过所有允许设备的物理容量 | 返回 `REPLAN_REQUIRED`，列出已评估候选 | 不得无限等待；不得静默降 batch/精度/模型或修改冻结输入 |
| 共享被允许且峰值可容纳 | 可共享，并记录并发与共享条件 | 公平计时比较需单独披露，不能把显存足够当作计算隔离 |
| 用户策略上限被超过 | 指出具体超限项 | 只有用户可修改策略或批准例外；规划器不得自授权 |
| 遥测失败/硬件在启动前变化 | `NEEDS_ESTIMATE` 或重新规划、重新准入 | 不得把未知当空闲，不得沿用旧设备分配 |
| 新花费超过授权 | 阻止该候选 | 不得把“有可用硬件”解释为新购买授权 |

### 10.6 受影响文件

- 新增：`tools/resource_planner.py`、`tests/test_resource_planner.py`。
- 队列：`skills/experiment-queue/scripts/build_manifest.py`、`skills/experiment-queue/scripts/queue_manager.py`、`skills/experiment-queue/SKILL.md`。
- 资源约定：`skills/shared-references/resource-budget.md`、`skills/experiment-plan/SKILL.md`、`skills/idea-discovery/SKILL.md`、`skills/idea-creator/SKILL.md`。
- 同步：上述文件的 Codex 镜像；若 P1 已落地则改源后生成。
- 既有测试：`tests/test_resource_budget.py`、`tests/test_governed_queue.py`、`tests/test_execution_governance.py`、`tests/test_dispatch_monitor_repairs.py`、`tests/test_training_budget_clock.py`；不改变训练计时与停止授权语义。
- 文档：`docs/CUSTOMIZATION.md`、`docs/CUSTOMIZATION_CN.md` 与 `CHANGELOG.md`，说明省略 `gpus`/`max_parallel` 时的新行为及 legacy 边界。

### 10.7 验收用例

1. 8 卡可见但用户只允许 0/1：规划与启动都不得出现其他设备。
2. 资源绑定任务省略 `gpus`/`max_parallel`：产物中不得再出现默认 `0..7` 或固定 8 并发。
3. 用户并发上限为 1，即使硬件可容纳更多也只能启动 1 个。
4. 4 个候选并发因 VRAM/RAM/磁盘叠加只能容纳 2 个：先启动 2 个，其余 pending；资源释放后重新计算，不消耗失败重试。
5. 多路径位于同一文件系统时按合并峰值计算，不重复计算空闲空间。
6. 物理容量不足时返回 `REPLAN_REQUIRED` 与候选解释，科学配置不被静默修改。
7. 共享允许且两个自有任务叠加峰值可容纳时可共卡；exclusive 或 legacy 路径仍一任务一设备；共享条件进入比较记录。
8. 启动前设备消失、UUID 变化、遥测失败时旧分配失效，重新检查且不伪造容量。
9. 未绑定 legacy 任务保持明确边界，新 manifest 缺配置时给出绑定/显式配置提示。
10. 上述相关 pytest 全绿，并验证未突破花费、停止、用户授权与公平比较约束。

### 10.8 执行步骤、风险与回滚

| 步骤 | 内容 | 预估 |
| --- | --- | --- |
| R0 | 固定现有资源表、队列与准入门回归基线 | 0.5 天 |
| R1 | 实现候选规划器、规划产物与单任务/并发峰值计算 | 1–2 天 |
| R2 | 改造资源绑定队列默认值和动态 slots，保留 legacy 明确边界 | 1 天 |
| R3 | 更新资源约定、相关 skill/镜像、文档与测试 | 1 天 |

| 风险 | 缓解与回滚 |
| --- | --- |
| 规划器把估算当成真实容量 | 启动前 `check_launch()` 仍是唯一准入；峰值未知即 `NEEDS_ESTIMATE` |
| 动态并发破坏公平比较 | 共享/并发条件写入比较记录；资源调度不改变预先声明的训练预算与种子 |
| 为“灵活”而引入第二份策略 | 会话资源表保持唯一策略源，RESOURCE_PLAN 只是可重建的规划视图 |
| 队列行为变化影响旧任务 | 新旧路径分开验收；按阶段独立 PR，资源绑定新逻辑可单独 revert，旧会话表保留 |

### 10.9 v1.7.0 实施记录

规划器逐个放置待运行作业，按所选偏好比较已声明的可互换配置。启动器复核队列保存的
设备 UUID、会话策略和租约。队列按已启动作业的完整声明峰值保守核算，因为主机遥测
无法可靠区分各作业已经消耗的 RAM、显存和磁盘空间。并发上限由当前队列执行，独立队列
之间使用外部调度器分配容量。启动收据中的实际分配和重叠作业可引用到比较日志。

旧队列沿用明确的 GPU 配置。未指定设备的历史 manifest 补充显式设备清单后可继续走
旧入口。计划产物、命令和迁移说明见[资源配置](CUSTOMIZATION_CN.md#自适应资源配置)。

## 11. v1.7.0 本地实施与验收

| 阶段 | 实施 |
| --- | --- |
| P0 | 固定原始技能树、文件摘要和回归结果。登记评审覆盖树的来源与差异 |
| P1 | 从主线源和宿主差异生成 Codex、Claude 与 Gemini 安装文件。原 Claude 生成命令继续可用 |
| P2 | 十个长入口把完整流程移入阶段文档。实测 30 个相关入口最长 41 行，默认加载 token 至少减少 87.8% |
| P3 | 两个外部 API 评审技能复用评审流程，各自维护后端接入及恢复方式 |
| P4 | 引入固定版本的 awesome-rebuttal，保留旧版入口归档和作者承诺检查 |
| P5 | 以会话策略、目标主机遥测和任务峰值生成资源计划。启动前重新校验设备与容量 |

宿主差异保存在独立源文件中，以便主线正文直接安装到其他宿主。Codex 专用的
`research-guide` 在生成时投影成可发现的入口。具体规则与路径见[技能差异审计](SURFACE_DIFF_AUDIT.md)。

测试结果、合成审稿场景和隔离安装记录见[本地验收记录](../release-validation.json)。
Rebuttal 上游来源和旧项目接续方式见[迁移说明](REBUTTAL_UPSTREAM_SYNC.md)。

## 12. 按优先级派发与训练期间的 CPU 工作

### 12.1 优先级派发和资源利用

- 在现有队列记录任务优先级。依赖满足后，按优先级、同级入队顺序派发。旧任务使用默认优先级。训练、评测、工程和可视化共用会话资源表、目标主机遥测、容量核算及已有租约。
- 优先为已就绪或有可信就绪时间的高优先级任务安排所需资源。低优先级任务可使用其余容量。需要共用预留设备时，用已有运行记录验证低优先级任务能在预约前结束。估算不足时使用与该预约无冲突的资源。高优先级任务新到达时，重新安排待启动任务，运行中的任务沿用现有的中断授权规则。
- 在现有评测入口声明可替换的执行配置，例如增大推理 batch size 或使用多卡分片。根据实测吞吐量、单卡显存峰值和全部 GPU 的总成本选配置。先验证样本覆盖、逐样本结果和聚合指标达到项目设定的一致性要求。多卡评测按样本 ID 检查重复和遗漏，并按指标定义合并原始记录。速度对比记录 GPU、batch size、精度和并发条件，统一对比口径。
- `experiment-queue` 维护持久化任务、排序及其启动记录。派发子代理可根据同一份队列快照提出优先级或放置建议，并沿用会话的模型偏好。实际派发由队列和现有准入执行。宿主提供 agent 时可以启用建议路径，派发规则本身可独立运行。

### 12.2 长任务期间主动推进 CPU 工作

- `training-check` 保持对训练或评测的监听。对于当前目标已有授权的工作，`research-guide` 从待办中选择能推动下一项决策的 CPU 任务，例如代码审查、小型回归、数据覆盖和泄漏检查、预处理或数据读取性能分析、可视化、推导和方案比较。监控发现异常或主任务产出新结果时，重新检查待办优先级。
- CPU 任务按核数、内存、磁盘和 I/O 需求准入。数据构造、代码修改和优化草稿使用独立版本，引用当前运行的固定输入。评测吞吐量等依赖资源隔离的跑次保留独立测量条件。将有证据的结论交给对应 skill 和既有项目记录。
- 普通执行与 Goal 会话可以并行推进授权范围内的工作。仅观察的 Plan 会话可继续监控、读代码和拟定下一轮方案。各模式复用同一监控记录，并按宿主支持情况恢复任务。

### 12.3 验收

1. 用受控遥测验证高优先级先派发、同级顺序稳定、等待多卡的任务保住预约、剩余设备可运行低优先级任务。
2. 覆盖跨阶段依赖、GPU 共享、资源动态变化和进程运行中加入高优先级任务。验证同一任务无重复派发，当前任务按既有授权处理。
3. 在同一固定评测集复测单卡、多卡和不同批大小。用逐样例和汇总指标核对等价性，并记录吞吐量、完成时间与各资源峰值。
4. 在实际训练或评测期间并行执行授权的 CPU 工作，验证监控按期运行、异常及时接管当前注意力，以及发现可以交接到下一轮的证据。额外观察主任务吞吐量和文件系统压力。
5. 用普通、Goal 和 Plan 会话复测任务接续。模拟派发代理不可用及会话重启，验证队列和监控可由既有状态恢复。

### 12.4 实施

`experiment-queue` 支持在下次轮询读取追加的待运行任务与优先级。预约沿用会话
准入与已记录的峰值。预留设备和共享的 CPU、内存、并发、存储、I/O 容量按
队列状态检查。需要借用未来预约的任务附上同类运行的时长证据。

评测配置从固定样本、测量记录与执行身份生成。启动时锁定当次选择的 batch size
和 CUDA UUID。主任务的健康记录供 CPU 任务派发和只读观察复用。执行配置、样本
汇总命令和监控用法见[优先级派发规范](../skills/experiment-queue/references/priority-dispatch.md)。
