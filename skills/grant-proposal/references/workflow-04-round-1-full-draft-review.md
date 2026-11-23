<!-- EI-WORKFLOW-REFERENCE -->

# Round 1 (full draft review):

Read this file when the workflow reaches Round 1 (full draft review): through Composing with Other Skills. In commands and examples, interpret relative skill paths from the entrypoint directory.

#### Round 1 (full draft review):

Write `grant-proposal/codex_panel_review_bundle_round_1.md` containing the
criteria below plus the absolute path to `grant-proposal/GRANT_PROPOSAL.md`,
then keep the Codex MCP prompt short:

```
mcp__codex__codex-reply:
  threadId: [from Phase 2]
  # inherits the thread's model/effort — do not re-send
  prompt: |
    Read the grant review bundle at <absolute path to
    grant-proposal/codex_panel_review_bundle_round_1.md> and follow all
    instructions in it.
```

Bundle contents:

```
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

    Proposal draft path (read this file yourself): <absolute path to
    grant-proposal/GRANT_PROPOSAL.md>
```

#### Round 2+ (after revisions):

If MAX_REVIEW_ROUNDS > 1 and revisions were applied:

Write `grant-proposal/codex_panel_review_bundle_round_N.md` containing the
change log, any raw diff / changed-file paths worth inspecting, and the
absolute path to the current `grant-proposal/GRANT_PROPOSAL.md`, then reuse the
same short MCP prompt pattern:

```
mcp__codex__codex-reply:
  threadId: [saved from Round 1]
  # inherits the thread's model/effort — do not re-send
  prompt: |
    Read the grant review bundle at <absolute path to
    grant-proposal/codex_panel_review_bundle_round_N.md> and follow all
    instructions in it.
```

Bundle contents:

```
    [Round N review of revised [GRANT_TYPE] [GRANT_SUBTYPE] proposal]

    Since your last review, I have applied the following changes:
    1. [Change 1]: [what was done]
    2. [Change 2]: [what was done]
    3. [Change 3]: [what was done]

    Please re-evaluate. Same format: section scores, overall assessment, remaining weaknesses.
    Focus on whether the CRITICAL and MAJOR issues from Round 1 have been adequately addressed.

    Revised proposal path (read this file yourself): <absolute path to
    grant-proposal/GRANT_PROPOSAL.md>
```

### Phase 5: Revision & Output

#### 5.1 Apply Reviewer Feedback

Parse reviewer feedback into severity levels:
- **CRITICAL** — fatal flaws that would lead to rejection. Fix immediately.
- **MAJOR** — significant weaknesses. Fix before submission.
- **MINOR** — suggestions for improvement. Fix if time allows.

Implement CRITICAL and MAJOR fixes. If MAX_REVIEW_ROUNDS > 1, re-submit for another round via `mcp__codex__codex-reply`.

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

#### 5.3 Final Checks

Before declaring done:

- [ ] All sections required by the grant type are present and complete
- [ ] Gap statement is clear and appears early in the proposal
- [ ] Each aim is independently valuable and logically connected
- [ ] Timeline includes concrete yearly milestones and deliverables
- [ ] PI qualification section has content (or clear `[TODO]` placeholders)
- [ ] Budget justification uses `[AMOUNT]` placeholders (no fabricated numbers)
- [ ] Language matches the grant type (Japanese for KAKENHI, Chinese for NSFC, etc.)
- [ ] No leftover `[TODO]` markers except for PI-specific information
- [ ] References are real (no hallucinated citations)
- [ ] Review feedback has been addressed (CRITICAL and MAJOR items)

**🚦 Final Checkpoint:** Present the completed proposal summary:

```
📝 Grant proposal draft complete:
- Type: [GRANT_TYPE] [GRANT_SUBTYPE]
- Language: [language]
- Aims: [N] aims covering [summary]
- Timeline: [N] years
- Review score: [summary from GPT-6-Astra]
- Output: grant-proposal/GRANT_PROPOSAL.md

Files saved to grant-proposal/. Please review and customize:
1. PI qualification section (add your publications and track record)
2. Budget amounts (replace [AMOUNT] placeholders)
3. Any [TODO] markers for personal information

What would you like to do next?
- "figures" → generate proposal diagrams
- "review again" → run another round of external review
- "latex" → convert to LaTeX format
- "done" → finalize
```

## Key Rules

- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.

- **Do NOT fabricate budget amounts.** Generate narrative budget justification only. Leave specific dollar/yen/yuan/euro amounts as `[AMOUNT]` placeholders for the user to fill in.
- **Do NOT fabricate PI information.** If no publication list is available, leave `[TODO: Add publications]` placeholders. Never invent papers, grants, or credentials.
- **Do NOT hallucinate citations.** Use references from literature survey. Mark uncertain citations with `[VERIFY]`.
- **Grant ≠ paper.** A grant argues for future work (feasibility + potential). A paper argues for completed work (results + claims). Write accordingly — emphasize "what we will do" and "why it will work", not "what we found."
- **Aims must be independently valuable.** If Aim 2 fails, Aim 1 and Aim 3 should still produce publishable results.
- **Preliminary data de-risks.** Include any pilot results, existing datasets, or prior publications that demonstrate feasibility.
- **Reviewer-facing structure.** Bold key sentences. Use numbered lists for clarity. Make the reviewer's job easy.
- **Cultural norms matter.** KAKENHI expects 社会的意義; NSF expects Broader Impacts; NSFC expects 国际前沿 positioning. Missing these is a red flag for reviewers.
- **Feishu notifications are optional.** If `~/.claude/feishu.json` exists, send `checkpoint` at each phase transition and `pipeline_done` at final output. If absent, skip silently.

## Parameter Pass-Through

Parameters can be passed inline with `—` separator. They flow to sub-skills when invoked:

```
/grant-proposal "topic — KAKENHI Start-up, sources: zotero, arxiv download: true"
```

| Parameter | Default | Description | Passed to |
|-----------|---------|-------------|-----------|
| `grant type` | KAKENHI | Agency (KAKENHI/NSF/NSFC/ERC/DFG/SNSF/ARC/NWO/GENERIC) | — |
| `grant subtype` | auto | Sub-type (Start-up/Wakate/CAREER/Youth/etc.) | — |
| `output format` | markdown | `markdown` or `latex` | — |
| `language` | auto | Output language override | — |
| `max review rounds` | 2 | External review cycles | — |
| `sources` | all | Literature sources | → `/research-lit` |
| `arxiv download` | false | Download arXiv PDFs | → `/research-lit` |
| `reviewer model` | gpt-6-astra | Codex review model | → Codex MCP |
| `auto proceed` | false | Skip checkpoints | — |

## Composing with Other Skills

