<!-- EI-WORKFLOW-REFERENCE -->

# 5.3 Final Checks

Read this file when the workflow reaches 5.3 Final Checks through Publish Track (skip this skill). In commands and examples, interpret relative skill paths from the entrypoint directory.

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
- Review score: [summary from Gemini]
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

## Output Protocols

> Follow these shared protocols for all output files:
> - **[Output Versioning Protocol](../../shared-references/output-versioning.md)** — write timestamped file first, then copy to fixed name
> - **[Output Manifest Protocol](../../shared-references/output-manifest.md)** — log every output to MANIFEST.md
> - **[Output Language Protocol](../../shared-references/output-language.md)** — respect the project's language setting

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
- **Feishu notifications are optional.** If `~/.codex/feishu.json` exists, send `checkpoint` at each phase transition and `pipeline_done` at final output. If absent, skip silently.

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
| `reviewer model` | gemini-review | Gemini reviewer bridge | → reviewer thread |
| `auto proceed` | false | Skip checkpoints | — |

## Composing with Other Skills

### Sub-skills used by this skill

| Sub-skill | Phase | Purpose |
|-----------|:-----:|---------|
| `/research-lit` | 1 | Literature survey (if not already done) |
| `/novelty-check` | 1 | Verify the gap is real |
| `/research-review` | 2, 4 | Structural review + full draft review |
| `/paper-illustration` | 3 | Generate proposal figures (optional) |

### Funding Track (this skill's primary use case)

```
/idea-discovery "direction"              ← Workflow 1: find validated ideas
/research-refine "idea"                  ← sharpen the method
/grant-proposal "idea — KAKENHI"         ← this skill: write the grant proposal
                                          ← [submit & get funded]
/experiment-bridge                       ← implement experiments with funding
/auto-review-loop "results"              ← Workflow 2: iterate until submission-ready
/paper-writing                           ← Workflow 3: write the paper
```

### Publish Track (skip this skill)

```
/idea-discovery → /experiment-bridge → /auto-review-loop → /paper-writing → submit
```
