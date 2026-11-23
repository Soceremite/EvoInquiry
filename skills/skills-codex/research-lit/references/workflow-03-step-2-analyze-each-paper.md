<!-- EI-WORKFLOW-REFERENCE -->

# Step 2: Analyze Each Paper

Read this file when the workflow reaches Step 2: Analyze Each Paper through Key Rules. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Step 2: Analyze Each Paper
For each relevant paper (from all sources), extract:
- **Problem**: What gap does it address?
- **Method**: Core technical contribution (1-2 sentences)
- **Results**: Key numbers/claims
- **Relevance**: How does it relate to our work?
- **Source**: Where we found it (Zotero/Obsidian/local/web) — helps user know what they already have vs what's new

### Step 3: Synthesize
- Group papers by approach/theme
- Identify consensus vs disagreements in the field
- Find gaps that our work could fill
- If Obsidian notes exist, incorporate the user's own insights into the synthesis

### Step 4: Output
Present as a structured literature table:

```
| Paper | Venue | Method | Key Result | Relevance to Us | Source |
|-------|-------|--------|------------|-----------------|--------|
```

Plus a narrative summary of the landscape (3-5 paragraphs).

If Zotero BibTeX was exported, include a `references.bib` snippet for direct use in paper writing.

### Step 5: Save (if requested)
- Save paper PDFs to `literature/` or `papers/`
- Update related work notes in project memory
- If Obsidian is available, optionally create a literature review note in the vault

If `— composed: <canonical-report-path>` is present, return/fold the table,
landscape, and gaps into that report instead of writing a standalone literature
summary. Standalone remains the default; `— standalone` wins and an existing
report never activates composed mode. Keep reusable PDFs/BibTeX and traces. See
[`output-composition.md`](../../shared-references/output-composition.md).

### Step 6: Update Research Wiki

If the project has an active research wiki, update it after producing the literature review:

1. Add or update the topic page with the final paper table, grouped themes, and open gaps.
2. Link each paper to its canonical source and local PDF path if available.
3. Record which sources were used: Zotero, Obsidian, local PDFs, arXiv, Semantic Scholar, DeepXiv, Exa, or broader web.
4. Mark unresolved search gaps and papers requiring follow-up reading.
5. Follow the wiki integration contract in [`shared-references/integration-contract.md`](../../shared-references/integration-contract.md).
6. When the wiki helper is available, rebuild `query_pack.md` after updating literature entries so `/idea-creator` can reuse the latest gaps and failed directions.

If the wiki path or format is unclear, ask before writing. Do not invent a wiki location.

## Key Rules
- Cite verified paper identities and available metadata; do not invent missing authors, years or venues for synthetic or incomplete materials.
- Distinguish between peer-reviewed and preprints
- Be honest about limitations of each paper
- Note if a paper directly competes with or supports our approach
- If a requested source is unavailable, report its status and incomplete coverage; continue useful work that does not depend on it.
- Only unrequested optional sources may be skipped automatically.
- Zotero/Obsidian tools may have different names depending on how the user configured the MCP server (e.g., `mcp__zotero__search` or `mcp__zotero-mcp__search_items`). Try the most common patterns and adapt.
