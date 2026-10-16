---
name: "novelty-check"
description: "Verify research idea novelty against recent literature. Use when user says \"查新\", \"novelty check\", \"有没有人做过\", \"check novelty\", or wants to verify a research idea is novel before implementing."
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
<!-- EVO-INQUIRY:END -->

> Override for Codex users who want **Gemini**, not a second Codex agent, to act as the reviewer. Install this package **after** `skills/skills-codex/*`.

# Novelty Check Skill

> **Gemini overlay assurance:** verify the actual different-family reviewer before recording `review_independence: cross-family`; `acceptance_status: accepted` requires a positive disposition and the workflow's evidence closure. Negative, unavailable and budget-stop outcomes grant no phase acceptance; same-family responses retain the base provisional contract.

Check whether a proposed method/idea has already been done in the literature: **$ARGUMENTS**

## Constants

- **REVIEWER_MODEL = `gemini-review`** — Gemini reviewer invoked through the local `gemini-review` MCP bridge. Set `GEMINI_REVIEW_MODEL` if you need a specific Gemini model override.

## Instructions

Given a method description, systematically verify its novelty:

### Phase A: Extract Key Claims
1. Read the user's method description
2. Identify 3-5 core technical claims that carry the claimed delta:
   - What is the method?
   - What problem does it solve?
   - What is the mechanism?
   - What makes it different from obvious baselines?

### Phase B: Multi-Source Literature Search
For each core claim, choose sources and search variants appropriate to its discipline and required coverage. Use the literature-evidence reference and record actual coverage:

1. **Web Search** (via `WebSearch`):
   - Search arXiv, Google Scholar, Semantic Scholar
   - Use specific technical terms from the claim
   - Try at least 3 different query formulations per claim
   - Use a current, question-appropriate time window and include relevant foundational work

2. **Known paper databases**: Check against:
   - Relevant journals, conference proceedings and primary-source archives for this field
   - Recent preprints and subsequent versions or corrections where relevant

3. **Read abstracts**: For each potentially overlapping paper, WebFetch its abstract and related work section

### Phase C: Cross-Model Verification
Call REVIEWER_MODEL via `mcp__gemini-review__review_start` with high-rigor review:
```
mcp__gemini-review__review_start:
  prompt: |
    [Full novelty briefing + prior work list + specific novelty questions]
```

After this start call, immediately save the returned `jobId` and poll `mcp__gemini-review__review_status` with a bounded `waitSeconds` until `done=true`. Treat the completed status payload's `response` as the reviewer output, and save the completed `threadId` for any follow-up round.
Prompt should include:
- The proposed method description
- All papers found in Phase B
- Ask: "Is this method novel? What is the closest prior work? What is the delta?"
- The NOVELTY VERDICT LIMITS block below, verbatim — the reviewer judges under it

### The verdict limits

Copy this block **verbatim** into the reviewer's briefing; the report in
Phase D is judged under it too.

```
=== NOVELTY VERDICT LIMITS (these bound how you judge, never how widely you search) ===
Search within the question and declared resource boundary; report coverage.
1. Assess closest work and the concrete difference using verified sources.
   Proximity is not duplication; unfamiliarity is not novelty.
2. Report search_coverage: adequate | partial | unavailable and
   overlap_assessment: direct | partial | none_located | unknown.
3. ABANDON for duplication requires a named, checked work containing the
   claimed contribution. Explain the actual overlap, not only similar keywords.
4. PROCEED means an evidenced difference warrants further investigation;
   it is not proof of novelty or validity. If search or the difference is
   unresolved, use PROCEED WITH CAUTION and identify the missing check.
5. Keep the evidence assessment separate from the decision to spend resources.
   A limited next search can be worthwhile with novelty unknown. Do not mark
   incomplete coverage as an affirmative novelty verification.
6. Do not invent overlap or a favorable difference to satisfy a gate. Preserve
   the actual review source and unresolved issues; continuing exploration is
   not scientific acceptance.
Say plainly when an idea clears the check. Do not manufacture overlap.
```

### Phase D: Novelty Report
Output a structured report:

```markdown
## Novelty Check Report

### Proposed Method
[1-2 sentence description]

### Core Claims
1. [Claim 1] — Closest: [paper] — What stays unknown or different: [delta]
2. [Claim 2] — Closest: [paper] — What stays unknown or different: [delta]
...

### Closest Prior Work
| Paper | Year | Venue | Overlap | Key Difference |
|-------|------|-------|---------|----------------|

### Overall Novelty Assessment
- Score: X/10 (anchor: 5/10 = has clear neighbors but a defensible delta worth
  a pilot; reserve 1-3 for results a named published paper already contains)
- Recommendation: PROCEED / PROCEED WITH CAUTION / ABANDON (per the verdict
  limits: PROCEED requires a checked difference; uncertain coverage is CAUTION; duplication requires a checked paper)
- Key differentiator: [what makes this unique, if anything]
- Risk: [what a reviewer would cite as prior work]

### Suggested Positioning
[State the delta honestly in one sentence a reviewer could verify]
```

### Important Rules
- Two failures waste months equally: a false novelty claim, and a viable idea
  abandoned because the territory has neighbors. Be brutally honest in both
  directions — and when an idea clears the check, say so plainly.
- Novelty can live in the combination or the finding even when every
  individual claim rates LOW — judge the idea, not each claim in isolation.
  Known parts may yield a novel finding only when that finding and its difference from checked prior work are verified; a new arrangement alone is insufficient.
- "Applying X to Y" earns novelty by what the application reveals — a
  non-obvious interaction, failure mode, or insight. Judge the revelation, not
  the template.
- Check both the method AND the experimental setting for novelty
- If the method is not novel but the FINDING would be, say so explicitly
- Always check the most recent 6 months of arXiv — the field moves fast
