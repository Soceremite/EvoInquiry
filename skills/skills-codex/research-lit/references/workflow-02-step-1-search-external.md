<!-- EI-WORKFLOW-REFERENCE -->

# Step 1: Search (external)

Read this file when the workflow reaches Step 1: Search (external). In commands and examples, interpret relative skill paths from the entrypoint directory.

### Step 1: Search (external)
- Use WebSearch to find recent papers on the topic
- Check arXiv, Semantic Scholar, Google Scholar
- Focus on papers from last 2 years unless studying foundational work
- **De-duplicate**: Skip papers already found in Zotero, Obsidian, or local library

**arXiv API search** (only if web/arXiv retrieval is in the resolved source scope; no download by default):

Resolve `$ARXIV_FETCHER` via the canonical strict-safe Codex chain
(see [`shared-references/integration-contract.md`](../../shared-references/integration-contract.md) §2):

```bash
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills-codex.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills-codex.txt 2>/dev/null) || true
fi
ARXIV_FETCHER=""
[ -n "${ARIS_REPO:-}" ] && [ -f "$ARIS_REPO/tools/arxiv_fetch.py" ] && ARXIV_FETCHER="$ARIS_REPO/tools/arxiv_fetch.py"
[ -z "$ARXIV_FETCHER" ] && [ -f tools/arxiv_fetch.py ] && ARXIV_FETCHER="tools/arxiv_fetch.py"
[ -z "$ARXIV_FETCHER" ] && [ -f ~/.codex/skills/arxiv/arxiv_fetch.py ] && ARXIV_FETCHER="$HOME/.codex/skills/arxiv/arxiv_fetch.py"

if [ -n "$ARXIV_FETCHER" ]; then
  # Search arXiv API for structured results (title, abstract, authors, categories).
  if python3 "$ARXIV_FETCHER" search "QUERY" --max 10; then
    echo "D2 contribution: arxiv (helper invocation exit 0)" >&2
  else
    echo "WARN: arxiv_fetch.py invocation failed; D2 aggregate continues with WebSearch results." >&2
  fi
else
  echo "WARN: arxiv_fetch.py not resolved; falling back to WebSearch for arXiv hits." >&2
fi
```

If `$ARXIV_FETCHER` is empty (D2 graceful degradation), fall back to WebSearch for arXiv (same as before).

The arXiv API returns structured metadata (title, abstract, full author list, categories, dates) — richer than WebSearch snippets. Merge these results with WebSearch findings and de-duplicate.

**Semantic Scholar API search** (only when `semantic-scholar` is in sources):

When the resolved source list includes the provider (for example `— sources: semantic-scholar` or `— sources: web, semantic-scholar`), search for published venue papers beyond arXiv:

```bash
# Re-resolve $ARIS_REPO + $S2_FETCHER (SKILL bash blocks may run in separate shells).
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills-codex.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills-codex.txt 2>/dev/null) || true
fi
S2_FETCHER=""
[ -n "${ARIS_REPO:-}" ] && [ -f "$ARIS_REPO/tools/semantic_scholar_fetch.py" ] && S2_FETCHER="$ARIS_REPO/tools/semantic_scholar_fetch.py"
[ -z "$S2_FETCHER" ] && [ -f tools/semantic_scholar_fetch.py ] && S2_FETCHER="tools/semantic_scholar_fetch.py"
[ -z "$S2_FETCHER" ] && [ -f ~/.codex/skills/semantic-scholar/semantic_scholar_fetch.py ] && S2_FETCHER="$HOME/.codex/skills/semantic-scholar/semantic_scholar_fetch.py"

if [ -n "$S2_FETCHER" ]; then
    if python3 "$S2_FETCHER" search "QUERY" --max 10 --fields title,authors,year,venue,citationCount,externalIds,tldr,url; then
      echo "D2 contribution: semantic_scholar (helper invocation exit 0)" >&2
    else
      echo "WARN: semantic_scholar_fetch.py invocation failed; D2 aggregate continues." >&2
    fi
else
    echo "Semantic Scholar unavailable: $S2_FETCHER unresolved; skipping this optional source." >&2
fi
```

Why use Semantic Scholar? Many IEEE/ACM journal papers are not on arXiv. S2 fills the gap for published venue-only papers with citation counts and venue metadata.

De-duplication between arXiv and S2:
- Match by arXiv ID (`externalIds.ArXiv`) or DOI. Similar normalized titles only flag candidates; do not merge them automatically.
- If a paper appears in both and S2 has venue / DOI / citation metadata, use S2 as authoritative metadata while keeping the arXiv PDF link.
- S2 results without `externalIds.ArXiv` are venue-only papers and should be preserved as unique value.

**DeepXiv search** (only when `deepxiv` is in sources):

When the resolved source list includes the provider (for example `— sources: deepxiv` (or includes `deepxiv` in a combined source list)), use the DeepXiv adapter for progressive retrieval:

```bash
# Re-resolve $ARIS_REPO + $DEEPXIV_FETCHER (SKILL bash blocks may run in separate shells).
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills-codex.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills-codex.txt 2>/dev/null) || true
fi
DEEPXIV_FETCHER=""
[ -n "${ARIS_REPO:-}" ] && [ -f "$ARIS_REPO/tools/deepxiv_fetch.py" ] && DEEPXIV_FETCHER="$ARIS_REPO/tools/deepxiv_fetch.py"
[ -z "$DEEPXIV_FETCHER" ] && [ -f tools/deepxiv_fetch.py ] && DEEPXIV_FETCHER="tools/deepxiv_fetch.py"
[ -z "$DEEPXIV_FETCHER" ] && [ -f ~/.codex/skills/deepxiv/deepxiv_fetch.py ] && DEEPXIV_FETCHER="$HOME/.codex/skills/deepxiv/deepxiv_fetch.py"

if [ -n "$DEEPXIV_FETCHER" ]; then
    if python3 "$DEEPXIV_FETCHER" search "QUERY" --max 10; then
      echo "D2 contribution: deepxiv (helper invocation exit 0)" >&2
      python3 "$DEEPXIV_FETCHER" paper-brief ARXIV_ID || echo "WARN: deepxiv paper-brief failed" >&2
      python3 "$DEEPXIV_FETCHER" paper-head ARXIV_ID || echo "WARN: deepxiv paper-head failed" >&2
      python3 "$DEEPXIV_FETCHER" paper-section ARXIV_ID "Experiments" || echo "WARN: deepxiv paper-section failed" >&2
    else
      echo "WARN: deepxiv_fetch.py search invocation failed; D2 aggregate continues." >&2
    fi
elif command -v deepxiv >/dev/null 2>&1; then
    deepxiv search "QUERY" --limit 10 --format json
    deepxiv paper ARXIV_ID --brief --format json
    deepxiv paper ARXIV_ID --head --format json
    deepxiv paper ARXIV_ID --section "Experiments" --format json
    echo "D2 contribution: deepxiv (CLI fallback)" >&2
else
    echo "DeepXiv unavailable: $DEEPXIV_FETCHER unresolved and no deepxiv CLI; skipping this optional source." >&2
fi
```

If `deepxiv_fetch.py` or the `deepxiv` CLI is unavailable, report that this requested source is unavailable and continue independent work with incomplete coverage.

**De-duplication against other sources**:
- Match by arXiv ID first
- Flag similar normalized titles for manual identity review; do not automatically merge them
- Keep one canonical paper entry and record `deepxiv` as an additional source when it overlaps with web/arXiv findings

**Exa search** (only when `exa` is in sources):

When the resolved source list includes the provider (for example `— sources: exa` (or includes `exa` in a combined source list)), use the Exa tool for broad AI-powered web search with content extraction:

```bash
# Re-resolve $ARIS_REPO + $EXA_FETCHER (SKILL bash blocks may run in separate shells).
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills-codex.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills-codex.txt 2>/dev/null) || true
fi
EXA_FETCHER=""
[ -n "${ARIS_REPO:-}" ] && [ -f "$ARIS_REPO/tools/exa_search.py" ] && EXA_FETCHER="$ARIS_REPO/tools/exa_search.py"
[ -z "$EXA_FETCHER" ] && [ -f tools/exa_search.py ] && EXA_FETCHER="tools/exa_search.py"
[ -z "$EXA_FETCHER" ] && [ -f ~/.codex/skills/exa-search/exa_search.py ] && EXA_FETCHER="$HOME/.codex/skills/exa-search/exa_search.py"

if [ -n "$EXA_FETCHER" ]; then
  exa_contributed=false
  # Search for research papers with highlights.
  if python3 "$EXA_FETCHER" search "QUERY" --max 10 --category "research paper" --content highlights; then
    exa_contributed=true
  else
    echo "WARN: exa_search.py research-paper invocation failed; D2 aggregate continues." >&2
  fi
  # Search for broader web content (blogs, docs, news).
  if python3 "$EXA_FETCHER" search "QUERY" --max 10 --content highlights; then
    exa_contributed=true
  else
    echo "WARN: exa_search.py broad-web invocation failed; D2 aggregate continues." >&2
  fi
  [ "$exa_contributed" = "true" ] && echo "D2 contribution: exa (at least one invocation exit 0)" >&2
else
  echo "Exa unavailable: \$EXA_FETCHER unresolved; skipping this optional source." >&2
fi
```

If `exa_search.py` or the `exa-py` SDK is unavailable, report that this requested source is unavailable and continue independent work with incomplete coverage.

**De-duplication against other sources**:
- Use a verified canonical paper URL or strong ID; similar titles only flag possible matches
- If Exa returns an arXiv paper already found by other sources, prefer structured metadata from arXiv/S2
- Exa results from non-academic domains (blogs, docs, news) are unique value not covered by other sources

**Gemini search** (only when `gemini` is in sources):

When the resolved source list includes the provider (for example `— sources: gemini` (or includes `gemini` in a combined source list)), use Gemini for AI-powered broad literature discovery.

**Priority 1 — Gemini MCP** (preferred): Call `mcp__gemini-cli__ask-gemini` with the search prompt:

```
mcp__gemini-cli__ask-gemini({
  prompt: 'You are a research literature scout. Search comprehensively for papers on: "QUERY"

IMPORTANT CONSTRAINTS:
1. Search from MULTIPLE angles — decompose the topic into sub-problems, aliases, neighboring tasks, and common benchmark/settings variants.
2. Prefer papers that are genuinely relevant, not merely keyword-adjacent.
3. Include top venues, journals, surveys, recent preprints, and papers with code when available.
4. Choose a date range appropriate to the question and current date; include relevant foundational work.

For EACH paper found, provide ALL of the following:
- Title: [exact title]
- Authors: [full author list]
- Year: [publication year]
- Venue: [exact conference/journal name + year, or "arXiv preprint"]
- arXiv ID: [format 2401.12345, or "N/A"]
- DOI: [if available, or "N/A"]
- Code URL: [GitHub/GitLab link if available, or "No code"]
- Summary: [one-sentence core contribution]

Return relevant traceable candidates within the requested search budget; do not pad a fixed count.',
  model: 'auto-gemini-3'
})
```

**Priority 2 — Gemini CLI fallback** (if MCP unavailable): Use `gemini -p "...same prompt..." 2>/dev/null` via Bash (timeout: 120s).

If both MCP and CLI are unavailable, report that this requested source is unavailable and continue independent work with incomplete coverage.

**Why use Gemini?** Gemini provides AI-driven discovery that goes beyond keyword matching — it decomposes topics, explores naming variants, and surfaces papers that traditional API-based searches may miss. It fills a different retrieval niche from structured database queries.

**De-duplication against other sources**:
- Match by arXiv ID or DOI; title similarity only flags a possible match
- If Gemini returns a paper already found by Semantic Scholar, prefer S2's citation count and venue metadata
- If Gemini returns a paper already found by arXiv, prefer arXiv's structured metadata
- Do not use Gemini-reported citation counts; they may be inaccurate

**OpenAlex search** (only when `openalex` is in sources):

When the resolved source list includes the provider (for example `— sources: openalex` (or includes `openalex` in a combined source list), use OpenAlex API for comprehensive academic metadata):

```bash
# Re-resolve $ARIS_REPO + $OPENALEX_FETCHER (SKILL bash blocks may run in separate shells).
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills-codex.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills-codex.txt 2>/dev/null) || true
fi
OPENALEX_FETCHER=""
[ -n "${ARIS_REPO:-}" ] && [ -f "$ARIS_REPO/tools/openalex_fetch.py" ] && OPENALEX_FETCHER="$ARIS_REPO/tools/openalex_fetch.py"
[ -z "$OPENALEX_FETCHER" ] && [ -f tools/openalex_fetch.py ] && OPENALEX_FETCHER="tools/openalex_fetch.py"
[ -z "$OPENALEX_FETCHER" ] && [ -f ~/.codex/skills/openalex/openalex_fetch.py ] && OPENALEX_FETCHER="$HOME/.codex/skills/openalex/openalex_fetch.py"

# Skip OpenAlex when the helper or its optional dependency is unavailable.
if [ -z "$OPENALEX_FETCHER" ] || ! python3 -c "import requests" >/dev/null 2>&1; then
  echo "OpenAlex source not available (openalex_fetch.py unresolved or 'requests' module missing); skipping." >&2
else
  if python3 "$OPENALEX_FETCHER" search "QUERY" --max 10 \
      --type article \
      --sort relevance; then
    echo "D2 contribution: openalex (helper invocation exit 0)" >&2
  else
    echo "WARN: openalex_fetch.py invocation failed; D2 aggregate continues with remaining sources." >&2
  fi
fi
```

If `openalex_fetch.py` is not found or the `requests` module is missing, report that this requested source is unavailable and continue independent work with incomplete coverage.

**Why use OpenAlex?** OpenAlex provides an open citation graph, institutional affiliations, funding data, and broad work metadata across disciplines.

**De-duplication against other sources**:
- Match by DOI or arXiv ID; title similarity only flags a possible match
- If OpenAlex and Semantic Scholar overlap, prefer S2 for citation counts and venue metadata
- If OpenAlex and arXiv overlap, prefer arXiv's PDF link and metadata while retaining OpenAlex's citation and institution data

**Optional PDF download** (only when `ARXIV_DOWNLOAD = true`):

After all sources are searched and papers are ranked by relevance:
```bash
# Re-resolve $ARXIV_FETCHER (SKILL bash blocks may run in separate shells).
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills-codex.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills-codex.txt 2>/dev/null) || true
fi
ARXIV_FETCHER=""
[ -n "${ARIS_REPO:-}" ] && [ -f "$ARIS_REPO/tools/arxiv_fetch.py" ] && ARXIV_FETCHER="$ARIS_REPO/tools/arxiv_fetch.py"
[ -z "$ARXIV_FETCHER" ] && [ -f tools/arxiv_fetch.py ] && ARXIV_FETCHER="tools/arxiv_fetch.py"
[ -z "$ARXIV_FETCHER" ] && [ -f ~/.codex/skills/arxiv/arxiv_fetch.py ] && ARXIV_FETCHER="$HOME/.codex/skills/arxiv/arxiv_fetch.py"

# Download requested relevant arXiv papers; report unresolved helper and missing downloads.
[ -n "$ARXIV_FETCHER" ] && python3 "$ARXIV_FETCHER" download ARXIV_ID --dir papers/
```
- Only download papers ranked in the top ARXIV_MAX_DOWNLOAD by relevance
- Skip papers already in the local library
- 1-second delay between downloads (rate limiting)
- Verify each PDF > 10 KB

