<!-- EI-WORKFLOW-REFERENCE -->

# Overview

Read this file when the workflow reaches Overview through Phase 0: Input Parsing & Context Gathering. In commands and examples, interpret relative skill paths from the entrypoint directory.




> Override for Codex users who want **Gemini**, not a second Codex agent, to act as the reviewer. Install this package **after** `skills/skills-codex/*`.

# Grant Proposal: From Research Ideas to Fundable Application

> **Gemini overlay assurance:** verify the actual different-family reviewer before recording `review_independence: cross-family`; `acceptance_status: accepted` requires a positive disposition and the workflow's evidence closure. Negative, unavailable and budget-stop outcomes grant no phase acceptance; same-family responses retain the base provisional contract.

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
- **REVIEWER_MODEL = `gemini-review`** — Gemini reviewer invoked through the local `gemini-review` MCP bridge for proposal review. Set `GEMINI_REVIEW_MODEL` if you need a specific Gemini model override.
- **OUTPUT_FORMAT = `markdown`** — Output format. Supported: `markdown`, `latex`. LaTeX uses grant-specific templates when available.
- **MAX_REVIEW_ROUNDS = 2** — Maximum external review-revise cycles before finalizing.
- **OUTPUT_DIR = `grant-proposal/`** — Directory for generated proposal files.
- **LANGUAGE = `auto`** — Output language. Auto-detected from grant type: KAKENHI→Japanese, NSF→English, NSFC→Chinese, ERC→English, DFG→English (or German), SNSF→English, ARC→English, NWO→English. Override explicitly if needed.
- **AUTO_PROCEED = false** — At each checkpoint, **always wait for explicit user confirmation** before proceeding. Grant proposals require PI-specific judgment at every stage. Set `true` only if user explicitly requests fully autonomous mode.

> 💡 These are defaults. Override by telling the skill, e.g., `/grant-proposal "topic — NSF CAREER, latex output"` or `/grant-proposal "topic — NSFC Youth, language: English"`.

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

## State Persistence (Compact Recovery)

Grant proposal drafting is a long task that may trigger context compaction. Persist state to `grant-proposal/GRANT_STATE.json` after each phase:

```json
{
  "phase": 2,
  "grant_type": "KAKENHI",
  "grant_subtype": "Start-up",
  "language": "Japanese",
  "thread_id": "019cfcf4-...",
  "gap_statement": "...",
  "aims_count": 3,
  "status": "in_progress",
  "timestamp": "2026-03-18T15:00:00"
}
```

**Write this file at the end of every phase.** On invocation, check for this file:
- If absent or `status: "completed"` → fresh start
- If `status: "in_progress"` and within 24h → **resume** from saved phase (read `GRANT_PROPOSAL.md` and `GRANT_REVIEW.md` to restore context)
- If older than 24h → fresh start (stale state)

On completion, set `"status": "completed"`.

## Workflow

### Phase 0: Input Parsing & Context Gathering

Parse `$ARGUMENTS` to extract:

1. **Research direction/idea** — may reference existing files or be a freeform description
2. **Grant type** — detect from keywords (e.g., "科研費"→KAKENHI, "NSF"→NSF, "国自然"→NSFC, "基金"→NSFC)
3. **Grant sub-type** — detect from keywords (e.g., "Start-up", "若手", "青年", "CAREER", "优青", "海外优青")
4. **Overrides** — output format, language, review rounds

Then gather context from the project directory:

1. Read `idea-stage/IDEA_REPORT.md` if it exists (from `/idea-discovery`); fall back to `./IDEA_REPORT.md` if not found
2. Read `refine-logs/FINAL_PROPOSAL.md` if it exists (from `/research-refine`)
3. Read `refine-logs/EXPERIMENT_PLAN.md` if it exists (from `/experiment-plan`)
4. Read `review-stage/AUTO_REVIEW.md` if it exists (from `/auto-review-loop` — prior review feedback is gold for grants); fall back to `./AUTO_REVIEW.md` if not found
5. Read `NARRATIVE_REPORT.md` or `STORY.md` if they exist
6. Read any existing literature notes or survey documents
7. Scan for the user's publication list (e.g., `publications.md`, `cv.md`, `bio.md`, `CV.pdf`)
8. Check for `grant-proposal/GRANT_STATE.json` (resume from prior interrupted run)

If insufficient context exists:
- No research idea at all → suggest running `/idea-discovery` first
- No literature survey → will invoke `/research-lit` inline in Phase 1
- No publication list → leave PI qualification section with `[TODO: Add publications]` placeholders
- Has `review-stage/AUTO_REVIEW.md` → extract reviewer feedback and use it to strengthen the feasibility narrative

