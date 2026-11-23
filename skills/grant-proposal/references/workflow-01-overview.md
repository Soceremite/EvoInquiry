<!-- EI-WORKFLOW-REFERENCE -->

# Overview

Read this file when the workflow reaches Overview through GENERIC. In commands and examples, interpret relative skill paths from the entrypoint directory.








# Grant Proposal: From Research Ideas to Fundable Application

Draft a grant proposal based on: **$ARGUMENTS**

## Overview

This skill turns validated research ideas into a structured, reviewer-ready grant proposal. It chains sub-skills into a grant-specific pipeline:

```
/research-lit → /novelty-check → [structure design] → [draft] → /research-review → [revise] → GRANT_PROPOSAL.md
  (survey)      (verify gap)     (aims + matrix)     (prose)    (panel review)     (fix)      (done!)
```

**This is a parallel branch, not part of the linear Workflow 1→1.5→2→3 pipeline.** After `/idea-discovery` produces validated ideas, the user can either:
- Go to `/experiment-bridge` → `/auto-review-loop` → `/paper-writing` (implement & publish)
- Go to `/grant-proposal` (write funding application first, then implement after funding)

```
                    ┌→ /experiment-bridge → /auto-review-loop → /paper-writing  (publish track)
/idea-discovery ────┤
                    └→ /grant-proposal → [get funded] → /experiment-bridge → ...  (funding track)
```

Grant proposals argue for **future work** (feasibility + potential), not completed work (results + claims). This skill handles the unique requirements of grant writing: narrative arc design, reviewer-facing structure, budget justification, timeline planning, and agency-specific formatting.

## Constants

- **GRANT_TYPE = `KAKENHI`** — Default grant type. Supported: `KAKENHI`, `NSF`, `NSFC`, `ERC`, `DFG`, `SNSF`, `ARC`, `NWO`, `GENERIC`. Override via argument (e.g., `/grant-proposal "topic — NSF"`).
- **GRANT_SUBTYPE = `auto`** — Sub-type within the grant agency. Examples: KAKENHI `Start-up`/`Wakate`/`Kiban-B`; NSFC `Youth`/`Excellent-Youth`/`Distinguished`/`Overseas`/`Key`; NSF `CAREER`/`CRII`/`Standard`. Auto-detected from argument or defaults to the most common sub-type.
- **REVIEWER_MODEL = `gpt-6-astra`** — Model used via Codex MCP for proposal review. Must be an OpenAI model (e.g., `gpt-6-astra`, `o3`, `gpt-4o`).
- **OUTPUT_FORMAT = `markdown`** — Output format. Supported: `markdown`, `latex`. LaTeX uses grant-specific templates when available.
- **MAX_REVIEW_ROUNDS = 2** — Maximum external review-revise cycles before finalizing.
- **OUTPUT_DIR = `grant-proposal/`** — Directory for generated proposal files.
- **LANGUAGE = `auto`** — Output language. Auto-detected from grant type: KAKENHI→Japanese, NSF→English, NSFC→Chinese, ERC→English, DFG→English (or German), SNSF→English, ARC→English, NWO→English. Override explicitly if needed.
- **AUTO_PROCEED = false** — At each checkpoint, **always wait for explicit user confirmation** before proceeding. Grant proposals require PI-specific judgment at every stage. Set `true` only if user explicitly requests fully autonomous mode.

> 💡 These are defaults. Override by telling the skill, e.g., `/grant-proposal "topic — NSF CAREER, latex output"` or `/grant-proposal "topic — NSFC Youth, language: English"`.

## Optional: Style reference (`— style-ref: <source>`, opt-in)

Lets the PI steer the proposal's **structural** layout (section order tendency, paragraph length, figure density, citation style) toward a successful past proposal or paper they'd like to mirror. **Default OFF — when the user does not pass `— style-ref`, do nothing differently from before.**

Only when `— style-ref: <source>` appears in `$ARGUMENTS`, run the helper FIRST, before drafting:

```bash
# Resolve $STYLE_HELPER via the canonical strict-safe chain (see
# shared-references/integration-contract.md §2). Policy A — gate:
# unresolved helper means --style-ref cannot be satisfied, so abort.
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.ei/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.ei/repo" 2>/dev/null) || true
fi
STYLE_HELPER=".ei/tools/extract_paper_style.py"
[ -f "$STYLE_HELPER" ] || STYLE_HELPER="tools/extract_paper_style.py"
[ -f "$STYLE_HELPER" ] || { [ -n "${ARIS_REPO:-}" ] && STYLE_HELPER="$ARIS_REPO/tools/extract_paper_style.py"; }
[ -f "$STYLE_HELPER" ] || {
  echo "ERROR: extract_paper_style.py not resolved at .ei/tools/, tools/, \$ARIS_REPO/tools/, or via ~/.ei/repo." >&2
  echo "       Fix: rerun bash tools/install_aris.sh or smart_update.sh (refreshes ~/.ei/repo), export ARIS_REPO, or copy the helper to tools/." >&2
  echo "       --style-ref cannot be satisfied; aborting." >&2
  exit 1
}
STYLE_STATUS=0
CACHE=$(python3 "$STYLE_HELPER" --source "<source>") || STYLE_STATUS=$?
case "$STYLE_STATUS" in
  0) ;;                                       # use $CACHE/style_profile.md as structural guidance
  2) echo "warning: style-ref skipped (missing optional dep)" >&2 ;;
  3) echo "error: --style-ref source failed; aborting proposal" >&2 ; exit 1 ;;
  *) echo "error: helper failed unexpectedly; aborting proposal" >&2 ; exit 1 ;;
esac
```

Sources accepted: local TeX dir / file, local PDF, arXiv id, http(s) URL. Overleaf URLs/IDs are rejected — clone the project locally first and pass the local path.

**Strict rules** (full contract in `tools/extract_paper_style.py` docstring):

- Use `style_profile.md` to align paragraph length tendency, figure budget, and citation density. Grant-type-mandated section order (KAKENHI 研究目的 → 研究計画・方法 → 準備状況, NSF Intellectual Merit → Broader Impacts, etc.) **always takes precedence** — the agency template wins, the style ref only refines secondary structure.
- **Never copy proposal prose, claims, vision statements, or budget items** from anything reachable through the cache. The reference might be someone else's funded proposal; reproducing language risks plagiarism.
- **Never pass `— style-ref` (or the cache contents) to the GPT-6-Astra reviewer sub-agent** when it scores the draft — the proposal must be judged on its own merits.

## Grant Type Specifications

### KAKENHI (Japan — JSPS)

| Field | Detail |
|-------|--------|
| **Sections** | 研究目的 (Research Objective), 研究計画・方法 (Plan & Methods), 準備状況 (Preparation Status), 人権の保護 (Ethics, if applicable) |
| **Sub-types** | 基盤研究 A/B/C (Kiban), 若手研究 (Wakate), 研究活動スタート支援 (Start-up), 国際共同研究 (International), 学術変革領域 (Transformative), 挑戦的研究 (Challenging), DC1/DC2 (doctoral) |
| **Language** | Japanese (English technical terms acceptable) |
| **Review criteria** | 学術的重要性 (academic significance), 独創性 (originality), 研究計画の妥当性 (plan feasibility), 研究遂行能力 (PI capability) |
| **Cultural norms** | Explicit yearly milestones (Year 1 / Year 2), budget justification integrated into plan, emphasize 社会的意義 (societal significance), concrete expected outputs (papers, datasets), reference KAKEN database for related funded projects |

### NSF (US)

| Field | Detail |
|-------|--------|
| **Sections** | Project Summary (1p), Project Description (15p max), References Cited, Biographical Sketch, Budget Justification, Data Management Plan |
| **Sub-types** | Standard Grant, CAREER (early career), CRII (research initiation), RAPID, EAGER |
| **Language** | English |
| **Review criteria** | Intellectual Merit, Broader Impacts |
| **Cultural norms** | Aim-based structure (Aim 1/2/3), preliminary data strongly expected, broader impacts must be concrete and specific (not generic "benefit society"), Results from Prior Support section |

### NSFC (China — 国家自然科学基金)

| Field | Detail |
|-------|--------|
| **Sections** | 立项依据 (Rationale & Significance), 研究内容 (Content), 研究目标 (Objectives), 研究方案 (Plan & Methods), 可行性分析 (Feasibility), 创新性 (Innovation Points), 预期成果 (Expected Outcomes), 研究基础 (PI Foundation & Track Record) |
| **Sub-types** | 面上项目 (General Program) — emphasis on scientific problem and research accumulation; 青年基金 (Young Scientists Fund) — age ≤35, emphasis on independence and growth potential; 优秀青年基金/优青 (Excellent Young Scientists) — age ≤38, emphasis on outstanding achievements; 杰出青年基金/杰青 (Distinguished Young Scientists) — age ≤45, emphasis on international-leading level; 海外优青 (Overseas Excellent Young Scientists) — emphasis on overseas experience and return contribution plan; 重点项目 (Key Program) — emphasis on systematic in-depth research |
| **Language** | Chinese |
| **Review criteria** | 科学意义 (scientific significance), 创新性 (innovation), 可行性 (feasibility), 研究队伍 (team qualification) |
| **Cultural norms** | Heavy emphasis on 国际前沿 (international frontier) positioning, detailed feasibility analysis, explicit citation of applicant's prior publications, 研究基础 section is critical for demonstrating PI capability |

### ERC (EU — European Research Council)

| Field | Detail |
|-------|--------|
| **Sections** | Extended Synopsis (5p), Scientific Proposal Part B2 (15p) |
| **Sub-types** | Starting Grant (2-7 years post-PhD), Consolidator Grant (7-12 years), Advanced Grant (established leaders) |
| **Language** | English |
| **Review criteria** | Ground-breaking nature, Methodology, PI track record |
| **Cultural norms** | Emphasis on "high-risk/high-gain", methodology table with WP/deliverables/milestones, Gantt chart expected, strong PI narrative |

### DFG (Germany — Deutsche Forschungsgemeinschaft)

| Field | Detail |
|-------|--------|
| **Sections** | State of the Art, Objectives, Work Programme, Bibliography, CV |
| **Language** | English or German |
| **Review criteria** | Scientific quality, Originality, Feasibility, PI qualification |

### SNSF (Switzerland — Swiss National Science Foundation)

| Field | Detail |
|-------|--------|
| **Sections** | Summary, Research Plan, Timetable, Budget |
| **Language** | English |
| **Review criteria** | Scientific relevance, Originality, Feasibility, Track record |

### ARC (Australia — Australian Research Council)

| Field | Detail |
|-------|--------|
| **Sections** | Project Description, Feasibility, Benefit, Budget |
| **Language** | English |
| **Review criteria** | Research quality, Feasibility, Benefit to Australia |

### NWO (Netherlands — Dutch Research Council)

| Field | Detail |
|-------|--------|
| **Sections** | Summary, Proposed Research, Knowledge Utilisation |
| **Language** | English |
| **Review criteria** | Scientific quality, Innovative character, Knowledge utilisation |

### GENERIC

For any grant not listed above. User provides section names, page limits, and review criteria via argument:

```
/grant-proposal "topic — GENERIC, sections: Background|Methods|Impact, language: English"
```

