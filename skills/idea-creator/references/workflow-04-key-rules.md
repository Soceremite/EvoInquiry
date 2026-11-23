<!-- EI-WORKFLOW-REFERENCE -->

# Key Rules

Read this file when the workflow reaches Key Rules through Review Tracing. In commands and examples, interpret relative skill paths from the entrypoint directory.

## Key Rules

- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.

- The user provides a DIRECTION, not an idea. Your job is to generate the ideas.
- Quantity first, quality second: brainstorm broadly, then narrow only to allocate pilot budget — annotate the rest, don't paper-kill them.
- A good negative result is just as publishable as a positive one. Prioritize ideas where the answer matters regardless of direction.
- Don't fall in love with any idea before validating it — but let evidence do the killing, not anticipated objections.
- Always estimate compute cost. An idea that needs 1000 GPU-hours is not actionable for most researchers.
- "Apply X to Y" is legitimate when Y can reveal a non-obvious interaction, failure mode, or finding — judge the revelation, not the template.
- Include eliminated ideas in the report — they save future time by documenting dead ends.
- **If the user's direction is broad (e.g., "NLP"), use Phase 1 to derive 2-3 concrete frames and generate across them — ask the user only when a missing constraint would materially change the pilot slate.** A good direction is 1-2 sentences specifying the problem, domain, and constraint — e.g., "factorized gap in discrete diffusion LMs" or "sample efficiency of offline RL with image observations". Without sufficient specificity, generated ideas will be too vague to run experiments on.
- **Anti-hallucination for cited papers.** When the landscape survey or novelty justification cites specific papers, every cited paper must pass pre-search verification (`verify_papers.py`, canonical name resolved per [`shared-references/integration-contract.md`](../../shared-references/integration-contract.md) §2; 3-layer arXiv / CrossRef / S2 fallback inside the helper itself). Policy D1 (primary + degraded-output fallback): if the helper is unresolved **or** its invocation fails, mark candidates `[UNVERIFIED]` and continue rather than dropping or guessing. Never fabricate arXiv IDs, DOIs, or titles from memory. Full protocol in [`shared-references/citation-discipline.md`](../../shared-references/citation-discipline.md) § Pre-Search Verification Protocol.

## Composing with Other Skills

After this skill produces the ranked report:
```
/idea-creator "direction"     → ranked ideas
/novelty-check "top idea"     → deep novelty verification (already done in Phase 4, but user can re-run)
/research-review "top idea"   → external critical feedback
implement                     → write code
/run-experiment               → deploy to GPU
/auto-review-loop             → iterate until submission-ready
```

## Review Tracing

After each reviewer call (`mcp__codex__codex`, `mcp__codex__codex-reply`, `mcp__manual_review__review`, or `mcp__manual_review__review_reply`), save the trace following `shared-references/review-tracing.md` (Policy C — forensic; never silently skip). Use `save_trace.sh` (resolved per the chain in `shared-references/integration-contract.md` §2) or write files directly to `.ei/traces/<skill>/<date>_run<NN>/`. Respect the `--- trace:` parameter (default: `full`).
