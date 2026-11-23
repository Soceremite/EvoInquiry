<!-- EI-WORKFLOW-REFERENCE -->

# Figure Generation

Read this file when the workflow reaches Figure Generation through 5.2 Generate Output. In commands and examples, interpret relative skill paths from the entrypoint directory.

#### Figure Generation

Grant proposals benefit greatly from clear diagrams. Generate the following figures using SVG or matplotlib (save to `grant-proposal/figures/`):

1. **全体構成図 / Overview Diagram** — Show the relationship between aims (Aim 1 → Aim 2 → Aim 3), shared resources (participants, stimuli, pipeline), and outputs. This is the single most important figure.
2. **実験パラダイム図 / Experimental Paradigm** — Visual schematic of each paradigm (stimulus timing, conditions, EEG recording).
3. **年次計画 / Timeline Gantt Chart** — Year-by-year (or H1/H2) milestones with deliverables.

For AI-generated publication-quality figures, invoke `/paper-illustration`:

```
/paper-illustration "Overview diagram showing [aims relationship + shared resources] for grant proposal"
```

For simpler diagrams (flowcharts, Gantt charts), generate clean SVG or matplotlib directly via code.

**🚦 Figure Checkpoint:** Before generating, ask which figures the user wants:

```
🎨 The following figures would strengthen this proposal:
1. 全体構成図 / Overview — aims relationship + shared resources
2. 実験パラダイム図 / Paradigm — stimulus timing + conditions
3. 年次計画 / Gantt — timeline with milestones

Which should I generate? (e.g., "1 and 3", "all", "skip")
```

**⛔ Wait for user response.** Generate only the requested figures.

#### Grant-Specific Drafting Guidelines

**KAKENHI:**
- Write in formal Japanese academic style (である調, not です/ます調)
- Use 「」for Japanese quotations, bold for emphasis
- Structure: 研究の学術的背景 → 研究期間内に何をどこまで明らかにするか → 本研究の学術的な特色・独創性
- Include explicit 年次計画 (yearly plan) with concrete milestones
- Emphasize 社会的意義 (societal significance)
- Reference related KAKEN-funded projects to show awareness of the field

**NSF:**
- Write in clear, direct English
- Use Aim-based structure with bold headings
- Preliminary data paragraphs for each Aim (with figure references)
- Broader Impacts must be concrete: specific outreach activities, broadening participation plans
- Include Results from Prior Support (if PI has prior NSF funding)

**NSFC:**
- Write in formal Chinese academic style
- 立项依据 must position work at 国际前沿 (international frontier)
- 创新性 section must list numbered innovation points (创新点)
- 研究基础 must cite PI's own publications (with IF and citations if possible)
- 可行性分析 must address: technical feasibility, team capability, time feasibility, equipment/conditions

**ERC:**
- Write a compelling "high-risk/high-gain" narrative
- Extended Synopsis must be self-contained and compelling
- Include Work Package table with deliverables and milestones
- Gantt chart (describe in text, or generate as figure)

#### For Each Section

1. **Pull relevant content** from `idea-stage/IDEA_REPORT.md`, FINAL_PROPOSAL.md, literature notes
2. **Write complete prose** — no `[TODO]` except for PI-specific information
3. **Include figure/table placeholders** where appropriate (e.g., `[Figure 1: System architecture]`)
4. **Cite references properly** — use citation keys, will build bibliography later
5. **Match the agency's tone and style** — formal Japanese for KAKENHI, direct English for NSF, etc.

### Phase 4: External Review

Invoke `/research-review` on the complete draft for grant-type-specific evaluation:

```
/research-review "Complete [GRANT_TYPE] [GRANT_SUBTYPE] proposal draft. Evaluate as a [GRANT_TYPE] review panelist using official criteria. [PASTE FULL PROPOSAL TEXT]"
```

**What this does:**
- Gemini acts as a grant review panelist
- Scores each section 1-5 using agency-specific criteria
- Identifies fatal flaws and recommends funding/revisions/rejection
- Provides ranked action items for improvement
- All feedback saved to `grant-proposal/GRANT_REVIEW.md`

> ⚠️ **External review fallback**: If `gemini-review` MCP is unavailable or Gemini credentials are missing, skip external review. Note "External review skipped — gemini-review unavailable." in `GRANT_REVIEW.md`. The proposal is still usable without external review.

If `/research-review` is invoked (preferred), it handles the external review internally. If you run the reviewer directly, use `mcp__gemini-review__review_start` for Round 1 and `mcp__gemini-review__review_reply_start` for follow-up rounds.

#### Round 1 (full draft review):

```
mcp__gemini-review__review_start:
  prompt: |
    Review this complete [GRANT_TYPE] [GRANT_SUBTYPE] proposal draft.

    Act as a [GRANT_TYPE] review panelist. Evaluate using the official criteria:

    [INSERT GRANT-TYPE-SPECIFIC CRITERIA — see Grant Type Specifications above]

    For each section:
    1. Score 1-5 (5 = excellent)
    2. Strongest aspect
    3. Most critical weakness
    4. Specific fix suggestion (actionable, not vague)

    Overall assessment:
    - Would you recommend funding? (Yes / Yes with revisions / No)
    - Single most impactful change to improve funding chances?
    - Any fatal flaws?

    [PASTE FULL PROPOSAL TEXT]
```

After this start call, immediately save the returned `jobId` and poll `mcp__gemini-review__review_status` with a bounded `waitSeconds` until `done=true`. Treat the completed status payload's `response` as the review output, and save the completed `threadId` in `GRANT_STATE.json` if you want to continue the same dialogue in Round 2.

#### Round 2+ (after revisions):

If MAX_REVIEW_ROUNDS > 1 and revisions were applied:

```
mcp__gemini-review__review_reply_start:
  threadId: [saved completed threadId from Round 1]
  prompt: |
    [Round N review of revised [GRANT_TYPE] [GRANT_SUBTYPE] proposal]

    Since your last review, I have applied the following changes:
    1. [Change 1]: [what was done]
    2. [Change 2]: [what was done]
    3. [Change 3]: [what was done]

    Please re-evaluate. Same format: section scores, overall assessment, remaining weaknesses.
    Focus on whether the CRITICAL and MAJOR issues from Round 1 have been adequately addressed.

    [PASTE REVISED PROPOSAL TEXT]
```

After this start call, immediately save the returned `jobId` and poll `mcp__gemini-review__review_status` with a bounded `waitSeconds` until `done=true`. Treat the completed status payload's `response` as the updated review output.

### Phase 5: Revision & Output

#### 5.1 Apply Reviewer Feedback

Parse reviewer feedback into severity levels:
- **CRITICAL** — fatal flaws that would lead to rejection. Fix immediately.
- **MAJOR** — significant weaknesses. Fix before submission.
- **MINOR** — suggestions for improvement. Fix if time allows.

Implement CRITICAL and MAJOR fixes. If MAX_REVIEW_ROUNDS > 1, re-submit for another round via `send_input`.

#### 5.2 Generate Output

**Markdown output** (default):

```
grant-proposal/
├── GRANT_PROPOSAL.md          # Complete proposal, all sections
├── GRANT_REVIEW.md            # Review history and reviewer feedback
├── GRANT_STATE.json           # State persistence file
├── figures/                   # Generated diagrams (if any)
└── references.bib             # Bibliography (if citations were used)
```

**LaTeX output** (when OUTPUT_FORMAT = latex):

```
grant-proposal/
├── main.tex                   # Master file
├── sections/
│   ├── aims.tex               # Specific Aims / Research Objective
│   ├── background.tex         # Background / Significance
│   ├── research_plan.tex      # Research Plan / Methods
│   ├── timeline.tex           # Timeline & Milestones
│   ├── pi_qualification.tex   # PI Qualification / Track Record
│   └── budget.tex             # Budget Justification (if applicable)
├── references.bib
└── figures/                   # Any generated diagrams
```

