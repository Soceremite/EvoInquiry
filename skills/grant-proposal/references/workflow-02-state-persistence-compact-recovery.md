<!-- EI-WORKFLOW-REFERENCE -->

# State Persistence (Compact Recovery)

Read this file when the workflow reaches State Persistence (Compact Recovery) through Year 2. In commands and examples, interpret relative skill paths from the entrypoint directory.

## State Persistence (Compact Recovery)

Grant proposal drafting is a long task that may trigger context compaction. Persist state to `grant-proposal/GRANT_STATE.json` after each phase:

```json
{
  "phase": 2,
  "grant_type": "KAKENHI",
  "grant_subtype": "Start-up",
  "language": "Japanese",
  "codex_thread_id": "019cfcf4-...",
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
- Has review-stage/AUTO_REVIEW.md → extract reviewer feedback and use it to strengthen the feasibility narrative

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

