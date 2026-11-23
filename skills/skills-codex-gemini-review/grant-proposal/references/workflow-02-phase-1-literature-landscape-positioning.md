<!-- EI-WORKFLOW-REFERENCE -->

# Phase 1: Literature & Landscape Positioning

Read this file when the workflow reaches Phase 1: Literature & Landscape Positioning through Drafting Order (optimized for narrative coherence). In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 1: Literature & Landscape Positioning

Invoke `/research-lit` to ground the proposal in real literature, then search for competing funded projects:

```
/research-lit "$ARGUMENTS"
```

**What this does:**
- Reuse existing surveys if `/research-lit` was already run and notes exist
- Otherwise invoke `/research-lit` for multi-source literature search (arXiv, Scholar, Zotero, local PDFs)
- Search for **funded projects** in the same area via WebSearch:
  - KAKENHI → KAKEN database (https://kaken.nii.ac.jp/)
  - NSF → NSF Award Search (https://www.nsf.gov/awardsearch/)
  - NSFC → NSFC funded projects
  - Other agencies → general web search
- Identify competing groups and their recent publications
- Run `/novelty-check` on the proposed research direction to verify the gap is real:
  ```
  /novelty-check "[proposed gap statement]"
  ```
- Build the **gap statement** — the single most important sentence in the proposal:
  ```
  "Despite progress in [X], [specific gap] remains unaddressed because [reason].
  This proposal addresses this by [approach], which will [expected impact]."
  ```

**🚦 Checkpoint:** Present the landscape summary and gap statement to the user:

```
📚 Literature & landscape analysis complete:
- [key findings from literature]
- [competing funded projects found]
- Gap statement: "[the gap statement]"

Does this accurately capture the positioning? Should I adjust before designing the proposal structure?
```

**⛔ STOP HERE and wait for user response.** Do NOT auto-proceed unless AUTO_PROCEED=true was explicitly set by the user.

Options for the user:
- Reply **"go"** or **"ok"** → proceed to Phase 2 with current positioning
- Reply with **adjustments** (e.g., "focus more on X", "the gap should emphasize Y") → refine and re-present
- Reply **"stop"** → end the skill, save current progress to `grant-proposal/DRAFT_NOTES.md`

**State**: Write `GRANT_STATE.json` with `phase: 1` and the gap statement.

### Phase 2: Narrative Structure & Aims Design

Design the proposal's logical architecture before writing any prose.

#### 2.1 Define Specific Aims (2-4)

Each aim must satisfy:
- **Independently valuable** — if one aim fails, others still produce publishable results
- **Logically connected** — Aim 1 enables Aim 2, Aim 2 informs Aim 3
- **Concrete deliverables** — each aim maps to specific outputs (papers, datasets, tools, benchmarks)
- **Feasible within budget and timeline**

#### 2.2 Build Claims-Aims-Evidence Matrix

```markdown
| Aim | Key Claim | Preliminary Evidence | Proposed Validation | Risk Level | Deliverable |
|-----|-----------|---------------------|--------------------|-----------:|-------------|
| Aim 1 | [claim] | [pilot data, prior work] | [experiments] | LOW | [paper, dataset] |
| Aim 2 | [claim] | [theoretical basis] | [experiments] | MEDIUM | [paper, tool] |
```

#### 2.3 Design the Narrative Arc

Grant proposals follow a fundamentally different arc from papers:

```
Problem → Why Now → What We Propose → Why It Will Work → What We Will Deliver
         (not: Problem → Method → Results → Implications)
```

- **Problem**: What gap exists and why it matters (scientific + societal)
- **Why Now**: What recent developments make this the right time (new data, new methods, new need)
- **What We Propose**: The specific aims and approach
- **Why It Will Work**: Preliminary data, PI track record, team expertise, feasibility arguments
- **What We Will Deliver**: Concrete outputs, timeline, expected publications

#### 2.4 Timeline & Milestones

Design year-by-year (or quarter-by-quarter) plan:

```markdown
### Year 1
- Q1-Q2: [Aim 1 tasks]
- Q3-Q4: [Aim 1 completion + Aim 2 start]
- Expected outputs: [papers, datasets]

### Year 2
- Q1-Q2: [Aim 2 completion + Aim 3]
- Q3-Q4: [Aim 3 completion + synthesis]
- Expected outputs: [papers, tools, final report]
```

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
- Gemini acts as a grant review panelist (not a paper reviewer)
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
- Reviewer feedback: [key points from Gemini]

Proceed to section drafting? Or adjust the structure?
```

**⛔ STOP HERE. This is the most critical checkpoint — the proposal structure determines everything downstream.**

Options for the user:
- Reply **"go"** or **"ok"** → proceed to Phase 3 (section drafting)
- Reply with **structural changes** (e.g., "merge Aim 2 and 3", "add an aim about X", "reduce to 2 aims") → redesign and re-present
- Reply **"back"** → return to Phase 1 to adjust the gap/positioning
- Reply **"stop"** → save current structure to `grant-proposal/DRAFT_NOTES.md`

**State**: Write `GRANT_STATE.json` with `phase: 2`, aims summary, and the completed reviewer `thread_id` if you ran the reviewer directly.

### Phase 3: Section Drafting

Draft each section according to the grant type template. Write **complete prose**, not outlines or placeholders.

**What this does:**
- Writes all required sections in the agency-specific language and tone
- Pulls content from `idea-stage/IDEA_REPORT.md`, FINAL_PROPOSAL.md, and literature notes
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

