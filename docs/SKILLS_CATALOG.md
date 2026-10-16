# EvoInquiry skill catalog

[README](../README.md) · [中文介绍](../README_CN.md)

The development tree provides **88 skills**: 83 retained workflow entrypoints,
research-guide, project-governance, environment-maintenance, scientific-brainstorming
and research-manager. Invoke a skill with the `evo-inquiry:`
namespace; each link below opens the Codex implementation actually installed.
The table describes capabilities and setup categories. Read the selected
`SKILL.md` for exact inputs, dependencies, outputs, and checkpoints.

Base Codex review uses a fresh agent from the same model family and remains
provisional. Optional reviewer overlays have separate setup requirements.
Provider availability must be checked in the running session; a listed skill
or dependency does not establish that an integration is configured.

## Workflow Orchestrators

| Skill | Capability | Setup |
| --- | --- | --- |
| [`/research-guide`](../skills/skills-codex/research-guide/SKILL.md) | Resume a project or choose the next evidence-based step; reads and executes the appropriate skill within the task's scope | Dependencies of the selected step |
| [`/project-governance`](../skills/skills-codex/project-governance/SKILL.md) | Project identities, fixed artifact references, read-only audits and controlled .ei migration/recovery | Python, jsonschema; local filesystem |
| [`/environment-maintenance`](../skills/skills-codex/environment-maintenance/SKILL.md) | Frozen environment reuse, independent candidate validation, consumer leases/pins and retirement planning | Python, jsonschema; existing conda/uv as needed |
| [`/research-pipeline`](../skills/skills-codex/research-pipeline/SKILL.md) | **Full chain** — Workflow 1 → 1.5 → 2 → 3, from research direction to submission-ready paper | Native Codex review, LaTeX, GPU |
| [`/idea-discovery`](../skills/skills-codex/idea-discovery/SKILL.md) | **Workflow 1** — research-lit → idea-creator → novelty-check → research-review → research-refine-pipeline | Native Codex review |
| [`/idea-discovery-robot`](../skills/skills-codex/idea-discovery-robot/SKILL.md) | Workflow 1 adapter for robotics / embodied AI — robotics-aware literature survey + benchmark-anchored ideation | Native Codex review |
| [`/experiment-bridge`](../skills/skills-codex/experiment-bridge/SKILL.md) | **Workflow 1.5** — read experiment plan → implement code → sanity check → deploy to GPU → collect initial results | GPU (local / remote / Vast / Modal) |
| [`/auto-review-loop`](../skills/skills-codex/auto-review-loop/SKILL.md) | **Workflow 2** — bounded review → revision → re-review, governed by issue closure, stagnation and resource limits; stopping grants no acceptance | Native Codex review |
| [`/auto-review-loop-llm`](../skills/skills-codex/auto-review-loop-llm/SKILL.md) | Same as Workflow 2 but uses any OpenAI-compatible LLM via [`llm-chat`](../mcp-servers/llm-chat/) MCP server | llm-chat MCP |
| [`/auto-review-loop-minimax`](../skills/skills-codex/auto-review-loop-minimax/SKILL.md) | Workflow 2 variant pinned to MiniMax API | MiniMax API key |
| [`/paper-writing`](../skills/skills-codex/paper-writing/SKILL.md) | **Workflow 3** — paper-plan → paper-figure → illustration → paper-write → paper-compile → auto-paper-improvement-loop | Native Codex review, LaTeX |
| [`/rebuttal`](../skills/skills-codex/rebuttal/SKILL.md) | **Workflow 4** — parse reviews → atomize → strategy → draft → safety check → stress test → 2-version output → follow-ups | Native Codex review |
| [`/resubmit-pipeline`](../skills/skills-codex/resubmit-pipeline/SKILL.md) | **Workflow 5** — text-only port across venues (no new experiments, no bib edits) — isolation → anonymity → audits `--soft-only` → microedit → kill-argument gate → compile + push | Native Codex review, LaTeX |
| [`/paper-talk`](../skills/skills-codex/paper-talk/SKILL.md) | **Workflow 6** — paper → slide outline → Beamer + PPTX → per-page polish → assurance audits → final report | Native Codex review, LaTeX, python-pptx |
| [`/research-refine-pipeline`](../skills/skills-codex/research-refine-pipeline/SKILL.md) | Sub-pipeline used by `/idea-discovery` — refine method + plan experiments in one chain | Native Codex review |
| [`/patent-pipeline`](../skills/skills-codex/patent-pipeline/SKILL.md) | Full patent drafting — invention → claims → spec → jurisdiction format (CN / US / EP) | Native Codex review |
| [`/dse-loop`](../skills/skills-codex/dse-loop/SKILL.md) | Autonomous design-space exploration loop for computer architecture / EDA — run → analyze → tune → iterate until objective met | Domain-specific tools |
| [`/meta-optimize`](../skills/skills-codex/meta-optimize/SKILL.md) | **Workflow M** — analyze the toolkit usage logs and propose SKILL.md / prompt / default-parameter improvements (outer-loop self-evolution) | Native Codex review, hook logging |
| [`/meta-apply`](../skills/skills-codex/meta-apply/SKILL.md) | **Privileged landing gate** — the only skill allowed to mutate the skill corpus; lands `/meta-optimize` patches the human approved, after a fresh reviewer jury PASS on the staged diff (read-only producer ≠ privileged applier) | Native Codex review, human-in-loop |

## Literature & Search

| Skill | Capability | Setup |
| --- | --- | --- |
| [`/research-lit`](../skills/skills-codex/research-lit/SKILL.md) | Multi-source literature search — Zotero / Obsidian / local PDFs / web / arXiv / S2 / DeepXiv / Exa / Gemini / OpenAlex with cross-source dedup | Task-dependent; see skill |
| [`/arxiv`](../skills/skills-codex/arxiv/SKILL.md) | Search, download, summarize arXiv papers; multi-result table + per-paper detail | Task-dependent; see skill |
| [`/semantic-scholar`](../skills/skills-codex/semantic-scholar/SKILL.md) | Published-venue paper search (IEEE / ACM / Springer) — citation counts, venue metadata, TLDR | Task-dependent; see skill |
| [`/deepxiv`](../skills/skills-codex/deepxiv/SKILL.md) | Progressive paper reading — search → brief → head → section → trending → web search | `pip install deepxiv-sdk` |
| [`/exa-search`](../skills/skills-codex/exa-search/SKILL.md) | AI-powered broad web search with content extraction — blogs, docs, news, papers | `pip install exa-py` + `EXA_API_KEY` |
| [`/web-debug-search`](../skills/skills-codex/web-debug-search/SKILL.md) | Multi-source debugging search across GitHub, Stack Exchange, Chinese technical communities, and general web — routing, compatibility, and discovery-only results | Task-dependent; see skill |
| [`/openalex`](../skills/skills-codex/openalex/SKILL.md) | OpenAlex API search — open citation graph, institutional affiliations, funding data | `pip install requests` |
| [`/gemini-search`](../skills/skills-codex/gemini-search/SKILL.md) | Gemini-driven literature discovery — decomposes topics into sub-problems, aliases, variants | Gemini CLI |
| [`/alphaxiv`](../skills/skills-codex/alphaxiv/SKILL.md) | Quick single-paper lookup via [AlphaXiv](https://www.alphaxiv.org) — three-tier fallback (overview → markdown → LaTeX source) | Task-dependent; see skill |
| [`/comm-lit-review`](../skills/skills-codex/comm-lit-review/SKILL.md) | Communications-domain literature review with Claude-style knowledge-base-first retrieval — wireless / networking / satellite / Wi-Fi / cellular | Task-dependent; see skill |
| [`/novelty-check`](../skills/skills-codex/novelty-check/SKILL.md) | Verify a research idea is novel against recent literature — multi-source search + reviewer verification + closest-prior-work table | Native Codex review |

## Ideation & Method Design

| Skill | Capability | Setup |
| --- | --- | --- |
| [`/scientific-brainstorming`](../skills/skills-codex/scientific-brainstorming/SKILL.md) | Frame vague directions into testable questions, alternatives and discriminating inquiries | No mandatory external service |
| [`/research-manager`](../skills/skills-codex/research-manager/SKILL.md) | Evidence-linked decisions, pivots and handoffs using the existing authoritative record | Existing documents; wiki optional |
| [`/idea-creator`](../skills/skills-codex/idea-creator/SKILL.md) | Generate mechanism candidates for a bounded question; assess novelty, informativeness and feasibility | Pilots only within authorized resources |
| [`/research-refine`](../skills/skills-codex/research-refine/SKILL.md) | Iterative method refinement — problem anchor → up to 5 review rounds → the skill’s stopping conditions | Native Codex review |
| [`/experiment-plan`](../skills/skills-codex/experiment-plan/SKILL.md) | Turn a refined proposal into a claim-driven experiment roadmap — ablations, budgets, run order | Task-dependent; see skill |
| [`/ablation-planner`](../skills/skills-codex/ablation-planner/SKILL.md) | Design ablation studies from a reviewer's perspective (after main results pass `/result-to-claim`) | Native Codex review |
| [`/formula-derivation`](../skills/skills-codex/formula-derivation/SKILL.md) | Structure theory derivations — organize assumptions, build derivation chains, turn scattered equations into coherent narrative | Task-dependent; see skill |

## Proof Engineering

| Skill | Capability | Setup |
| --- | --- | --- |
| [`/proof-orchestrator`](../skills/skills-codex/proof-orchestrator/SKILL.md) | Stateful proof-run orchestration: run directories, cross-run continuation, manual GPT Pro handoff packages, optional DeepSeek second opinion (additional evidence only — `/proof-writer` drafts proofs, `/proof-checker` owns verification and submission acceptance) | Task-dependent; see skill |

## Experiments & Infrastructure

| Skill | Capability | Setup |
| --- | --- | --- |
| [`/research-implement-feature`](../skills/skills-codex/research-implement-feature/SKILL.md) | Build from a plain "implement X" request — runnable spine first, then one feature per rung; every under-determined decision declared in an assumption ledger before the code depends on it, plus a reviewer sweep for the ones that slipped through undeclared | Native Codex review |
| [`/run-experiment`](../skills/skills-codex/run-experiment/SKILL.md) | Deploy experiments to local / remote / Vast.ai / Modal GPU | GPU (configurable) |
| [`/monitor-experiment`](../skills/skills-codex/monitor-experiment/SKILL.md) | Monitor running experiments, check progress, collect results | Task-dependent; see skill |
| [`/analyze-results`](../skills/skills-codex/analyze-results/SKILL.md) | Interpret metrics and proactively diagnose available sample outputs: paired case studies, errors, improvements, regressions and coverage limits | Task-dependent; see skill |
| [`/experiment-queue`](../skills/skills-codex/experiment-queue/SKILL.md) | SSH job queue for multi-seed / multi-config sweeps — OOM retry, stale-screen cleanup, wave gating, crash-safe state | SSH access |
| [`/vast-gpu`](../skills/skills-codex/vast-gpu/SKILL.md) | Rent, manage, destroy on-demand GPU on [Vast.ai](https://vast.ai) | Vast.ai account + `vast-cli` |
| [`/serverless-modal`](../skills/skills-codex/serverless-modal/SKILL.md) | Run GPU workloads on [Modal](https://modal.com) — zero-config serverless, auto scale-to-zero | `pip install modal` + Modal account |
| [`/qzcli`](../skills/skills-codex/qzcli/SKILL.md) | Manage GPU compute jobs on the Qizhi (启智) platform via `qzcli` (kubectl-style CLI) | `qzcli` installed |
| [`/training-check`](../skills/skills-codex/training-check/SKILL.md) | Periodically poll W&B metrics during training — catch NaN, loss divergence, idle GPUs early | W&B account |
| [`/system-profile`](../skills/skills-codex/system-profile/SKILL.md) | Profile a target (script / process / GPU / memory / interconnect) with external tools + code instrumentation; produce actionable report | Profiling tools |

## Review, Audit & Assurance

| Skill | Capability | Setup |
| --- | --- | --- |
| [`/research-review`](../skills/skills-codex/research-review/SKILL.md) | One fresh evidence-based review of a proposal, paper or results, preserving supported findings and unresolved limitations | Native Codex review (or configured optional reviewer) |
| [`/experiment-audit`](../skills/skills-codex/experiment-audit/SKILL.md) | Audit experiment code, results and fairness; distinguish supplied-record support, direct execution verification and independent review | Native Codex review |
| [`/result-to-claim`](../skills/skills-codex/result-to-claim/SKILL.md) | Map experimental results to intended claims — judges what's supported, what's not, what's missing; routes to next action | Native Codex review |
| [`/paper-claim-audit`](../skills/skills-codex/paper-claim-audit/SKILL.md) | Check manuscript numbers, comparisons and scope claims against raw result files in a fresh review | Native Codex review |
| [`/citation-audit`](../skills/skills-codex/citation-audit/SKILL.md) | Bibliography audit — existence + metadata correctness + context appropriateness for every `\cite{}`; `--soft-only` mode for frozen-bib resubmits | Native Codex review, web access |
| [`/proof-checker`](../skills/skills-codex/proof-checker/SKILL.md) | Rigorous mathematical proof verification — 20-category issue taxonomy, two-axis severity, side-condition checklists, counterexample red team, proof-obligation ledger | Native Codex review |
| [`/kill-argument`](../skills/skills-codex/kill-argument/SKILL.md) | Two-thread adversarial review — Thread 1 writes the strongest 200-word rejection memo; Thread 2 (independent) defends point-by-point and surfaces still-unresolved issues | Native Codex review |
| [`/integrity-forensics`](../skills/skills-codex/integrity-forensics/SKILL.md) | SHA-pinned thin launcher for [Anti-Autoresearch](https://github.com/wanshuiyin/Anti-Autoresearch) — evidence-ledger forensic sweep (46 patterns, deterministic adjudicator) → typed BLOCK/WARN/NO_NEW_BLOCKER gate + append-only obligations ledger; default pre-submission self-audit in `/paper-writing` | git, Native Codex review (via upstream) |

## Paper Writing & Figures

| Skill | Capability | Setup |
| --- | --- | --- |
| [`/paper-plan`](../skills/skills-codex/paper-plan/SKILL.md) | Generate a structured paper outline from review conclusions + experiment results — claims-evidence matrix, section structure, figure plan, citation scaffolding | Task-dependent; see skill |
| [`/paper-write`](../skills/skills-codex/paper-write/SKILL.md) | Section-by-section LaTeX generation (ICLR / NeurIPS / ICML / IEEE / ACL / AAAI / CVPR / ACM MM). Anti-hallucination BibTeX via DBLP / CrossRef | Task-dependent; see skill |
| [`/paper-figure`](../skills/skills-codex/paper-figure/SKILL.md) | Publication-quality matplotlib / seaborn plots + LaTeX comparison tables from experiment results | matplotlib / seaborn |
| [`/figure-spec`](../skills/skills-codex/figure-spec/SKILL.md) | Deterministic JSON → SVG renderer for architecture / workflow / pipeline / audit-cascade diagrams. Shape-aware edge clipping, self-loops, CJK width estimation | Task-dependent; see skill |
| [`/paper-illustration`](../skills/skills-codex/paper-illustration/SKILL.md) | AI architecture + method illustrations via Gemini image generation, with Claude-supervised iterative refinement | `GEMINI_API_KEY` |
| [`/paper-illustration-image2`](../skills/skills-codex/paper-illustration-image2/SKILL.md) | Codex-native image generation alternative — uses ChatGPT Plus / Pro quota via local Codex app-server bridge (no Gemini key) | Codex app-server + `codex-image2` MCP bridge |
| [`/mermaid-diagram`](../skills/skills-codex/mermaid-diagram/SKILL.md) | Generate Mermaid diagrams from requirements — flowcharts, sequence, class, ER, Gantt, with syntax verification | Task-dependent; see skill |
| [`/pixel-art`](../skills/skills-codex/pixel-art/SKILL.md) | Generate pixel-art SVG illustrations for READMEs, docs, slides | Task-dependent; see skill |
| [`/paper-compile`](../skills/skills-codex/paper-compile/SKILL.md) | Compile LaTeX paper to PDF — auto-fix errors, submission readiness checks | LaTeX (`latexmk`, `pdfinfo`) |
| [`/auto-paper-improvement-loop`](../skills/skills-codex/auto-paper-improvement-loop/SKILL.md) | Bounded content-review, revision, and format-check rounds. `--edit-whitelist` mode for resubmits | Native Codex review |
| [`/proof-writer`](../skills/skills-codex/proof-writer/SKILL.md) | Draft rigorous mathematical proofs for ML / AI theory — theorems, lemmas, propositions, corollaries; fill in missing steps; formalize sketches | Task-dependent; see skill |
| [`/writing-systems-papers`](../skills/skills-codex/writing-systems-papers/SKILL.md) | Paragraph-level structural blueprint for 10-12 page systems papers — page allocation, paragraph templates, writing patterns for OSDI / SOSP / ASPLOS / NSDI / EuroSys | Task-dependent; see skill |
| [`/grant-proposal`](../skills/skills-codex/grant-proposal/SKILL.md) | Structured grant proposal drafting — KAKENHI (JP), NSF (US), NSFC (CN including 面上 / 青年 / 优青 / 杰青 / 海优 / 重点), ERC (EU), DFG (DE), more | Task-dependent; see skill |

## Talks, Posters & Resubmission

| Skill | Capability | Setup |
| --- | --- | --- |
| [`/paper-slides`](../skills/skills-codex/paper-slides/SKILL.md) | Conference presentation — Beamer LaTeX → PDF + editable PPTX + speaker notes + full talk script | LaTeX, python-pptx |
| [`/slides-polish`](../skills/skills-codex/slides-polish/SKILL.md) | Per-page Codex review + targeted python-pptx / Beamer fixes (font scaling, frame resize, banner-as-tcolorbox, italic leak guard, em-dash spacing, CJK font hint, anonymity placeholder discipline) | Native Codex review, python-pptx |
| [`/paper-poster-html`](../skills/skills-codex/paper-poster-html/SKILL.md) | **Default** conference poster — single HTML/CSS file with measurement-driven hard gates (two-hue tokens, real paper figures with provenance, anti-patch-loop fix vocabulary) → print-ready PDF via headless Chromium | Playwright (Chromium), PyMuPDF |
| [`/paper-poster`](../skills/skills-codex/paper-poster/SKILL.md) | DEPRECATED — redirect stub to `/paper-poster-html` (legacy LaTeX pipeline retired; in git history) | — |

## Patents

| Skill | Capability | Setup |
| --- | --- | --- |
| [`/invention-structuring`](../skills/skills-codex/invention-structuring/SKILL.md) | Structure a raw invention idea into a formal invention disclosure | Task-dependent; see skill |
| [`/claims-drafting`](../skills/skills-codex/claims-drafting/SKILL.md) | Draft patent claims — independent + dependent, with anti-pattern checks | Task-dependent; see skill |
| [`/embodiment-description`](../skills/skills-codex/embodiment-description/SKILL.md) | Write detailed embodiment descriptions for the patent specification | Task-dependent; see skill |
| [`/specification-writing`](../skills/skills-codex/specification-writing/SKILL.md) | Full patent specification from claims + invention disclosure | Task-dependent; see skill |
| [`/figure-description`](../skills/skills-codex/figure-description/SKILL.md) | Generate formal drawing descriptions for patent figures | Task-dependent; see skill |
| [`/prior-art-search`](../skills/skills-codex/prior-art-search/SKILL.md) | Search patent databases + academic literature for prior art relevant to an invention | Task-dependent; see skill |
| [`/patent-novelty-check`](../skills/skills-codex/patent-novelty-check/SKILL.md) | Assess patent novelty and non-obviousness against prior art (patentability evaluation) | Native Codex review |
| [`/patent-review`](../skills/skills-codex/patent-review/SKILL.md) | External patent-examiner-style critical review of a patent application | Native Codex review |
| [`/jurisdiction-format`](../skills/skills-codex/jurisdiction-format/SKILL.md) | Compile patent application into jurisdiction-specific filing format (CN / US / EP) | Task-dependent; see skill |

## Meta, Utilities & Integrations

| Skill | Capability | Setup |
| --- | --- | --- |
| [`/research-wiki`](../skills/skills-codex/research-wiki/SKILL.md) | Persistent research knowledge base — papers / ideas / experiments / claims with typed relationships. Workflow hooks auto-ingest across the research lifecycle | Task-dependent; see skill |
| [`/wiki-enrich`](../skills/skills-codex/wiki-enrich/SKILL.md) | Fill the per-paper TODO sections that `ingest_paper` leaves as scaffolds (Karpathy LLM-wiki principle). Fetch chain alphaxiv → deepxiv → arXiv → page abstract; idempotent by default, `--force` to rewrite | Python stdlib + WebFetch |
| [`/render-html`](../skills/skills-codex/render-html/SKILL.md) | Render the toolkit Markdown / JSON artifacts into reviewed single-file HTML views for human reading | Python stdlib; Native Codex review for review gate |
| [`/overleaf-sync`](../skills/skills-codex/overleaf-sync/SKILL.md) | Two-way sync between local paper directory and Overleaf project via Overleaf Git bridge (Premium) — `setup` / `pull` (diff protocol) / `push` (confirmation gate) / `status` | Overleaf Premium + macOS Keychain |
| [`/feishu-notify`](../skills/skills-codex/feishu-notify/SKILL.md) | Send notifications to Feishu / Lark — push-only (webhook) or interactive (bidirectional) modes. Off by default | Feishu webhook URL |
| [`/interview-cheatsheet`](../skills/skills-codex/interview-cheatsheet/SKILL.md) | Generate long-form Chinese ML / LLM interview-prep cheat sheets with formulas, code, Q&A, review, and HTML output | Native Codex review, Python |

## Compatibility notes

- `paper-poster` is a retained redirect. Use `paper-poster-html` for new posters.
- `auto-review-loop-llm` and `auto-review-loop-minimax` require their selected
  provider; see [Codex backend compatibility](../compatibility/codex-backends.md).
- `paper-illustration-image2` is experimental and requires a working renderer.
- Claude/Gemini reviewer overlays are optional compatibility resources; the
  standard EvoInquiry plugin discovers the base Codex directory.
- Topic and platform skills serve specialized workflows. The beta ships all
  84 entries; select the ones appropriate to the task.
