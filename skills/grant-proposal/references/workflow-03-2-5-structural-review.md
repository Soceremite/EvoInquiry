<!-- EI-WORKFLOW-REFERENCE -->

# 2.5 Structural Review

Read this file when the workflow reaches 2.5 Structural Review through Phase 4: External Review. In commands and examples, interpret relative skill paths from the entrypoint directory.

#### 2.5 Structural Review

Invoke `/research-review` to get critical feedback on the proposal structure before drafting:

```
/research-review "[GRANT_TYPE] [GRANT_SUBTYPE] proposal structure:
Gap: [gap statement]
Aims: [aims list with claims-evidence matrix]
Timeline: [timeline]
— reviewer persona: [GRANT_TYPE] review panelist"
```

**What this does:**
- GPT-6-Astra xhigh acts as a grant review panelist (not a paper reviewer)
- Evaluates aims independence, narrative arc, risk identification, timeline realism
- Identifies the single biggest reviewer concern
- Provides actionable fixes ranked by severity

Apply structural feedback before proceeding to drafting.

**🚦 Checkpoint:** Present the proposal structure to the user:

```
🏗️ Proposal structure designed:
- Gap: [gap statement]
- Aim 1: [title] — Risk: LOW
- Aim 2: [title] — Risk: MEDIUM
- Aim 3: [title] — Risk: LOW
- Timeline: [summary]
- Reviewer feedback: [key points from GPT-6-Astra]

Proceed to section drafting? Or adjust the structure?
```

**⛔ STOP HERE. This is the most critical checkpoint — the proposal structure determines everything downstream.**

Options for the user:
- Reply **"go"** or **"ok"** → proceed to Phase 3 (section drafting)
- Reply with **structural changes** (e.g., "merge Aim 2 and 3", "add an aim about X", "reduce to 2 aims") → redesign and re-present
- Reply **"back"** → return to Phase 1 to adjust the gap/positioning
- Reply **"stop"** → save current structure to `grant-proposal/DRAFT_NOTES.md`

**State**: Write `GRANT_STATE.json` with `phase: 2`, aims summary, and Codex threadId.

### Phase 3: Section Drafting

Draft each section according to the grant type template. Write **complete prose**, not outlines or placeholders.

**What this does:**
- Writes all required sections in the agency-specific language and tone
- Pulls content from idea-stage/IDEA_REPORT.md, FINAL_PROPOSAL.md, and literature notes
- Uses `/paper-illustration` for figure generation (if user requests)
- Leaves `[TODO]` only for PI-specific information, `[AMOUNT]` for budget figures
- Outputs `grant-proposal/GRANT_PROPOSAL.md`

#### Drafting Order (optimized for narrative coherence)

1. **Specific Aims / Research Objective** — the "abstract" of the grant. Write first, refine last.
2. **Background / Significance / State of the Art** — establish the problem and gap.
3. **Research Plan / Methods** — per aim, with feasibility arguments.
4. **Figures** — generate key diagrams (see below).
5. **Timeline & Milestones** — year-by-year deliverables.
6. **PI Qualification / Preparation Status** — track record, team, infrastructure.
7. **Budget Justification** — narrative only (leave dollar/yen amounts as `[AMOUNT]` placeholders).
8. **Broader Impacts / Societal Significance** — if required by the grant type.

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

1. **Pull relevant content** from idea-stage/IDEA_REPORT.md, FINAL_PROPOSAL.md, literature notes
2. **Write complete prose** — no `[TODO]` except for PI-specific information
3. **Include figure/table placeholders** where appropriate (e.g., `[Figure 1: System architecture]`)
4. **Cite references properly** — use citation keys, will build bibliography later
5. **Match the agency's tone and style** — formal Japanese for KAKENHI, direct English for NSF, etc.

### Phase 4: External Review

Invoke `/research-review` on the complete draft for grant-type-specific evaluation:

```
/research-review "Read the grant review bundle at grant-proposal/codex_panel_review_bundle_round_1.md and evaluate it as a [GRANT_TYPE] [GRANT_SUBTYPE] review panelist using the official criteria."
```

**What this does:**
- GPT-6-Astra xhigh acts as a grant review panelist
- Scores each section 1-5 using agency-specific criteria
- Identifies fatal flaws and recommends funding/revisions/rejection
- Provides ranked action items for improvement
- All feedback saved to `grant-proposal/GRANT_REVIEW.md`

> ⚠️ **Codex MCP fallback**: If `mcp__codex__codex` is not available (no OpenAI API key), skip external review. Note "External review skipped — no Codex MCP available. Consider running `/auto-review-loop-llm` separately." in GRANT_REVIEW.md. The proposal is still usable without external review.

If `/research-review` is invoked (preferred), it handles the Codex call internally. If calling Codex directly (e.g., to maintain thread context from Phase 2):

