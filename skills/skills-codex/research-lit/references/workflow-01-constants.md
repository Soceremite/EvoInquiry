<!-- EI-WORKFLOW-REFERENCE -->

# Constants

Read this file when the workflow reaches Constants through Step 0c: Scan Local Paper Library. In commands and examples, interpret relative skill paths from the entrypoint directory.





# Research Literature Review

Research topic: $ARGUMENTS

## Constants

- **PAPER_LIBRARY** — Local directory containing user's paper collection (PDFs). Check these paths in order:
  1. `papers/` in the current project directory
  2. `literature/` in the current project directory
  3. Custom path specified by user in `AGENTS.md` under `## Paper Library`
- **MAX_LOCAL_PAPERS = 20** — Maximum number of local PDFs to scan (read first 3 pages each). If more are found, prioritize by filename relevance to the topic.
- **SOURCES = `auto`** — Which literature sources to search. Options: `zotero`, `obsidian`, `local`, `web`, `semantic-scholar`, `deepxiv`, `exa`, `gemini`, `openalex`, `all`, `auto`. Full source table and selection rules: see `## Data Sources` below.
- **ARXIV_DOWNLOAD = false** — When `true`, download top 3-5 most relevant arXiv PDFs to PAPER_LIBRARY after search. When `false` (default), only fetch metadata (title, abstract, authors) via arXiv API — no files are downloaded.
- **ARXIV_MAX_DOWNLOAD = 5** — Maximum number of PDFs to download when `ARXIV_DOWNLOAD = true`.
- **REVIEWER_BACKEND = `codex`** — Default reviewer route for optional literature synthesis cross-checks. Use `--reviewer: oracle-pro` only when explicitly requested; if Oracle is unavailable, warn and continue with Codex xhigh or local synthesis.

> 💡 Overrides:
> - `/research-lit "topic" — paper library: ~/my_papers/` — custom local PDF path
> - `/research-lit "topic" — sources: zotero, local` — only search Zotero + local PDFs
> - `/research-lit "topic" — sources: web` — only search the web (skip all local)
> - `/research-lit "topic" — sources: web, semantic-scholar` — also search Semantic Scholar for published venue papers
> - `/research-lit "topic" — sources: all, deepxiv` — use default sources plus DeepXiv
> - `/research-lit "topic" — arxiv download: true` — download top relevant arXiv PDFs
> - `/research-lit "topic" — arxiv download: true, max download: 10` — download up to 10 PDFs

## Data Sources

This skill checks multiple sources **in priority order**.

### Optional external capabilities

`nature-academic-search` was audited as an optional candidate. It is not bundled
or enabled as a validated EvoInquiry provider in 1.4.0. Its dependencies and
multi-index/remote-relay behavior are not required by this skill. Use an already
available connector only after checking its actual interface and requested scope;
otherwise use the existing providers and record unavailable coverage. Never
claim that this audit establishes all providers working end to end.

### Source Selection

Parse `$ARGUMENTS` for a `— sources:` directive. For `auto`, resolve an explicit list of relevant available providers first; the conditional provider steps below apply to that resolved list as well as user-named lists:
- **If `— sources:` is specified**: Only search the listed sources (comma-separated). Valid values: `zotero`, `obsidian`, `local`, `web`, `semantic-scholar`, `deepxiv`, `exa`, `gemini`, `openalex`, `all`, `auto`.
- **If not specified**: Use `auto`: choose relevant available sources for the question, local materials and primary academic sources as appropriate. Record actual sources and limitations. Legacy `all` retains its local/Zotero/Obsidian/web bundle; optional named providers are not silently added to that alias. Explicit lists constrain the search. Load [literature-evidence](../../shared-references/literature-evidence.md) for coverage, reading and identity records.

Examples:
```
/research-lit "diffusion models"                        → auto (default)
/research-lit "diffusion models" — sources: auto        → question-appropriate available sources
/research-lit "diffusion models" — sources: all         → legacy local/Zotero/Obsidian/web bundle
/research-lit "diffusion models" — sources: zotero      → Zotero only
/research-lit "diffusion models" — sources: zotero, web → Zotero + web
/research-lit "diffusion models" — sources: local       → local PDFs only
/research-lit "topic" — sources: obsidian, local, web   → skip Zotero
/research-lit "topic" — sources: web, semantic-scholar  → web + Semantic Scholar API
/research-lit "topic" — sources: deepxiv                → DeepXiv only
/research-lit "topic" — sources: all, deepxiv           → default sources + DeepXiv
/research-lit "topic" — sources: all, semantic-scholar  → default sources + Semantic Scholar API
/research-lit "topic" — sources: exa                    → Exa only (broad web + content extraction)
/research-lit "topic" — sources: all, exa               → default sources + Exa web search
/research-lit "topic" — sources: gemini                 → Gemini only (AI-powered broad discovery)
/research-lit "topic" — sources: all, gemini            → default sources + Gemini discovery
/research-lit "topic" — sources: openalex               → OpenAlex only (open citation graph + institutions)
/research-lit "topic" — sources: all, openalex          → default sources + OpenAlex citation graph
```

### Source Table

| Priority | Source | ID | How to detect | What it provides |
|----------|--------|----|---------------|-----------------|
| 1 | **Zotero** (via MCP) | `zotero` | Try calling any `mcp__zotero__*` tool — if unavailable, skip | Collections, tags, annotations, PDF highlights, BibTeX, semantic search |
| 2 | **Obsidian** (via MCP) | `obsidian` | Try calling any `mcp__obsidian-vault__*` tool — if unavailable, skip | Research notes, paper summaries, tagged references, wikilinks |
| 3 | **Local PDFs** | `local` | `Glob: papers/**/*.pdf, literature/**/*.pdf` | Raw PDF content (first 3 pages) |
| 4 | **Web search** | `web` | Check available search/browse tooling; report unavailable access | arXiv, Semantic Scholar, Google Scholar |
| 5 | **Semantic Scholar API** | `semantic-scholar` | `$S2_FETCHER` resolves (canonical name `semantic_scholar_fetch.py`, per integration-contract §2 Codex chain) | Published venue papers (IEEE, ACM, Springer) with structured metadata: citation counts, venue info, TLDR. **Runs when included in the resolved source list** |
| 6 | **DeepXiv CLI** | `deepxiv` | `$DEEPXIV_FETCHER` resolves (canonical name `deepxiv_fetch.py`, per integration-contract §2) **and** `deepxiv` CLI present | Progressive paper retrieval: search, brief, head, section, trending, web search. **Runs when included in the resolved source list** |
| 7 | **Exa Search** | `exa` | `$EXA_FETCHER` resolves (canonical name `exa_search.py`, per integration-contract §2); fetcher handles `exa-py` SDK + API key internally | AI-powered broad web search with content extraction (highlights, text, summaries). Covers blogs, docs, news, companies, and research papers beyond arXiv/S2. **Runs when included in the resolved source list** |
| 8 | **Gemini** (MCP / CLI) | `gemini` | `mcp__gemini-cli__ask-gemini` is available, or `gemini` CLI is installed | AI-powered broad literature discovery that decomposes topics into sub-problems, aliases, and variants. **Runs when included in the resolved source list** |
| 9 | **OpenAlex** | `openalex` | `$OPENALEX_FETCHER` resolves (canonical name `openalex_fetch.py`, per integration-contract §2 Codex chain) and Python `requests` is importable | Open citation graph with institutional affiliations, funding data, and broad work metadata. **Runs when included in the resolved source list** |

> If the user explicitly requests Zotero or Obsidian and that source is not configured, report it as unavailable and explain setup; continue work independent of that source with coverage marked incomplete. Only sources that were not requested may be omitted when irrelevant; summarize material coverage limitations.

## Workflow

### Per-source/per-paper fan-out

Retrieval and extraction are breadth-bound. Use fresh `spawn_agent` shards when
delegation is available, or the same work sequentially otherwise. Every shard
is read-only and returns
`{"shard_id": ..., "entries": [{"payload": ..., "dedup_key": "<DOI/arXiv/id>"}]}`.
The parent invokes every resolved source, unions results, mechanically dedups on
canonical IDs, and writes once. Shards do not rank paper quality. Source
verification remains deterministic; optional Codex synthesis review is
same-family provisional. See
[`fan-out-pattern.md`](../../shared-references/fan-out-pattern.md).

### Step 0a: Search Zotero Library (if available)

**Run only if Zotero is in the resolved source list. If unavailable, record the missing configuration and continue independent work; do not claim its library was searched.**

Try calling a Zotero MCP tool (e.g., search). If it succeeds:

1. **Search by topic**: Use the Zotero search tool to find papers matching the research topic
2. **Read collections**: Check if the user has a relevant collection/folder for this topic
3. **Extract annotations**: For highly relevant papers, pull PDF highlights and notes — these represent what the user found important
4. **Export BibTeX**: Get citation data for relevant papers (useful for `/paper-write` later)
5. **Compile results**: For each relevant Zotero entry, extract:
   - Title, authors, year, venue
   - User's annotations/highlights (if any)
   - Tags the user assigned
   - Which collection it belongs to

> 📚 Zotero annotations are gold — they show what the user personally highlighted as important, which is far more valuable than generic summaries.

### Step 0b: Search Obsidian Vault (if available)

**Run only if Obsidian is in the resolved source list. If unavailable, record the missing configuration and continue independent work; do not claim its vault was searched.**

Try calling an Obsidian MCP tool (e.g., search). If it succeeds:

1. **Search vault**: Search for notes related to the research topic
2. **Check tags**: Look for notes tagged with relevant topics (e.g., `#diffusion-models`, `#paper-review`)
3. **Read research notes**: For relevant notes, extract the user's own summaries and insights
4. **Follow links**: If notes link to other relevant notes (wikilinks), follow them for additional context
5. **Compile results**: For each relevant note:
   - Note title and path
   - User's summary/insights
   - Links to other notes (research graph)
   - Any frontmatter metadata (paper URL, status, rating)

> 📝 Obsidian notes represent the user's **processed understanding** — more valuable than raw paper content for understanding their perspective.

### Step 0c: Scan Local Paper Library

Before searching online, check if the user already has relevant papers locally:

1. **Locate library**: Check PAPER_LIBRARY paths for PDF files
   ```
   Glob: papers/**/*.pdf, literature/**/*.pdf
   ```

2. **De-duplicate against Zotero**: If Step 0a found papers, skip any local PDFs already covered by Zotero results (match by filename or title).

3. **Filter by relevance**: Match filenames and first-page content against the research topic. Skip clearly unrelated papers.

4. **Summarize relevant papers**: For each relevant local PDF (up to MAX_LOCAL_PAPERS):
   - Read first 3 pages (title, abstract, intro)
   - Extract: title, authors, year, core contribution, relevance to topic
   - Flag papers that are directly related vs tangentially related

5. **Build local knowledge base**: Compile summaries into a "papers you already have" section. This becomes the starting point — external search fills the gaps.

> 📚 If the user has a comprehensive local collection, the external search can be more targeted (focus on what's missing).
>
> ⚠️ **If all three PAPER_LIBRARY paths miss, say so before moving on** — do not skip silently. A user whose PDFs live in a reference manager (Zotero, Mendeley, ...) otherwise assumes `— sources: all` covered them. Emit:
>
> `WARN: local contributed nothing — no PDFs found in papers/, literature/, or a configured paper library. To include yours, add a "## Paper Library" heading to AGENTS.md followed by the directory path.`
>
> Then continue to Step 1.

