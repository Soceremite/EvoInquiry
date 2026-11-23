<!-- EI-WORKFLOW-REFERENCE -->

# Step 1: Search (external)

Read this file when the workflow reaches Step 1: Search (external). In commands and examples, interpret relative skill paths from the entrypoint directory.

### Step 1: Search (external)
- Use WebSearch to find recent papers on the topic
- Check arXiv, Semantic Scholar, Google Scholar
- Focus on papers from last 2 years unless studying foundational work
- **De-duplicate**: Skip papers already found in Zotero, Obsidian, or local library

**arXiv API search** (runs when `— sources:` is unset, contains `web` or `all`; no download by default — arXiv API is part of the Priority-4 Web tier, see Source Table above):

**Policy D2 tracking discipline (orchestrator-managed)**: the
executor (you, the LLM) maintains an in-context list of contributing
sources. For **helper-backed bash sources** (arxiv, semantic-scholar,
deepxiv, exa, openalex), a source contributes iff its bash block
ran its helper successfully (helper resolved AND invocation exited 0;
note: the helper exiting 0 with an empty result list still counts as
"ran" — downstream relevance ranking is what decides whether the user
actually sees content). For **non-helper sources** (zotero / obsidian /
local PDF / WebSearch / Gemini), the contribution rule is stated in
the Step-1 finalization block below — these are tracked separately
because they don't emit `D2 contribution:` log lines from bash. Sources
that were not requested via `— sources:` do not count. At the end of
Step 1 (before "Optional PDF download"), if zero sources contributed,
surface a D2 empty-aggregate error and stop. (See
integration-contract.md §2 Policy D2 — the in-context tracking
replaces a shared bash accumulator because SKILL bash blocks are
executed as separate shells; state does not survive.)

Resolve `$ARXIV_FETCHER` via the canonical chain (Policy D2 — this
source contributes to the multi-source aggregate; warn-and-continue
on failure, never abort the whole aggregate):

```bash
# Canonical strict-safe resolver (see shared-references/integration-contract.md §2).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.ei/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.ei/repo" 2>/dev/null) || true
fi
ARXIV_FETCHER=".ei/tools/arxiv_fetch.py"
[ -f "$ARXIV_FETCHER" ] || ARXIV_FETCHER="tools/arxiv_fetch.py"
[ -f "$ARXIV_FETCHER" ] || { [ -n "${ARIS_REPO:-}" ] && ARXIV_FETCHER="$ARIS_REPO/tools/arxiv_fetch.py"; }
[ -f "$ARXIV_FETCHER" ] || ARXIV_FETCHER=""

if [ -n "$ARXIV_FETCHER" ]; then
  # Search arXiv API for structured results (title, abstract, authors, categories).
  # Wrap with if/then/else so set -e doesn't abort the SKILL.
  if python3 "$ARXIV_FETCHER" search "QUERY" --max 10; then
    echo "D2 contribution: arxiv (helper invocation exit 0)" >&2
  else
    echo "WARN: arxiv_fetch.py invocation failed; D2 aggregate continues with WebSearch results." >&2
  fi
else
  echo "WARN: arxiv_fetch.py not resolved; falling back to WebSearch for arXiv hits." >&2
fi
```

> **Record-keeping**: track the `D2 contribution: …` lines emitted by
> each source's bash block. They form the contributing-source list
> the orchestrator uses for the Step-1 finalization gate below.
> WebSearch (Priority 4) is treated as having contributed iff
> WebSearch was requested (no `— sources:` filter, or the list
> contains `web` or `all`) AND was actually invoked; the orchestrator
> records that separately. (The finalization block below restates
> this rule canonically — both lines must stay in sync.)

If `$ARXIV_FETCHER` is empty (D2 graceful degradation), fall back to WebSearch for arXiv (same as before).

The arXiv API returns structured metadata (title, abstract, full author list, categories, dates) — richer than WebSearch snippets. Merge these results with WebSearch findings and de-duplicate.

**Semantic Scholar API search** (only when `semantic-scholar` is in sources):

When the resolved source list includes the provider (for example `— sources: semantic-scholar` (or `— sources: web, semantic-scholar`)), search for published venue papers beyond arXiv:

```bash
# Re-resolve $ARIS_REPO (SKILL bash blocks may run in separate shells).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.ei/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.ei/repo" 2>/dev/null) || true
fi
# Resolve $S2_FETCHER (Policy D2 — warn-and-skip on missing).
S2_FETCHER=".ei/tools/semantic_scholar_fetch.py"
[ -f "$S2_FETCHER" ] || S2_FETCHER="tools/semantic_scholar_fetch.py"
[ -f "$S2_FETCHER" ] || { [ -n "${ARIS_REPO:-}" ] && S2_FETCHER="$ARIS_REPO/tools/semantic_scholar_fetch.py"; }
[ -f "$S2_FETCHER" ] || S2_FETCHER=""

if [ -n "$S2_FETCHER" ]; then
  # Search for published CS/Engineering papers with quality filters.
  # Wrap with if/then/else so set -e doesn't abort the SKILL.
  if python3 "$S2_FETCHER" search "QUERY" --max 10 \
      --fields-of-study "Computer Science,Engineering" \
      --publication-types "JournalArticle,Conference"; then
    echo "D2 contribution: semantic_scholar (helper invocation exit 0)" >&2
  else
    echo "WARN: semantic_scholar_fetch.py invocation failed; D2 aggregate continues with remaining sources." >&2
  fi
fi
```

If `$S2_FETCHER` is empty (canonical chain exhausted), skip silently — D2 multi-source aggregate continues with the remaining resolved sources.

**Why use Semantic Scholar?** Many IEEE/ACM journal papers are NOT on arXiv. S2 fills the gap for published venue-only papers with citation counts and venue metadata.

**De-duplication between arXiv and S2**: Match by arXiv ID (S2 returns `externalIds.ArXiv`):
- If a paper appears in both: check S2's `venue`/`publicationVenue` — if it has been published in a journal/conference (e.g. IEEE TWC, JSAC), use S2's metadata (venue, citationCount, DOI) as the authoritative version, since the published version supersedes the preprint. Keep the arXiv PDF link for download.
- If the S2 match has no venue (still just a preprint indexed by S2): keep the arXiv version as-is.
- S2 results without `externalIds.ArXiv` are **venue-only papers** not on arXiv — these are the unique value of this source.

**DeepXiv search** (only when `deepxiv` is in sources):

When the resolved source list includes the provider (for example `— sources: deepxiv` (or includes `deepxiv` in a combined source list)), use the DeepXiv adapter for progressive retrieval:

```bash
# Re-resolve $ARIS_REPO (SKILL bash blocks may run in separate shells).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.ei/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.ei/repo" 2>/dev/null) || true
fi
# Resolve $DEEPXIV_FETCHER (Policy D2 — warn-and-skip on missing).
DEEPXIV_FETCHER=".ei/tools/deepxiv_fetch.py"
[ -f "$DEEPXIV_FETCHER" ] || DEEPXIV_FETCHER="tools/deepxiv_fetch.py"
[ -f "$DEEPXIV_FETCHER" ] || { [ -n "${ARIS_REPO:-}" ] && DEEPXIV_FETCHER="$ARIS_REPO/tools/deepxiv_fetch.py"; }
[ -f "$DEEPXIV_FETCHER" ] || DEEPXIV_FETCHER=""

if [ -n "$DEEPXIV_FETCHER" ] && command -v deepxiv >/dev/null 2>&1; then
  # Wrap each adapter call so set -e doesn't abort the SKILL.
  if python3 "$DEEPXIV_FETCHER" search "QUERY" --max 10; then
    echo "D2 contribution: deepxiv (helper invocation exit 0)" >&2

    # Then deepen only for the most relevant papers (sub-calls don't change D2 aggregate count):
    python3 "$DEEPXIV_FETCHER" paper-brief ARXIV_ID \
      || echo "WARN: deepxiv_fetch.py paper-brief failed; skipping deepen step." >&2
    python3 "$DEEPXIV_FETCHER" paper-head ARXIV_ID \
      || echo "WARN: deepxiv_fetch.py paper-head failed; skipping deepen step." >&2
    python3 "$DEEPXIV_FETCHER" paper-section ARXIV_ID "Experiments" \
      || echo "WARN: deepxiv_fetch.py paper-section failed; skipping deepen step." >&2
  else
    echo "WARN: deepxiv_fetch.py search invocation failed; D2 aggregate continues with remaining sources." >&2
  fi
fi
```

If `$DEEPXIV_FETCHER` is empty or the `deepxiv` CLI is unavailable, skip this source gracefully and continue with the remaining requested sources (Policy D2 graceful degradation).

**Why use DeepXiv?** It is useful when a broad search should be followed by staged reading rather than immediate full-paper loading. This reduces unnecessary context while still surfacing structure, TLDRs, and the most relevant sections.

**De-duplication against arXiv and S2**:
- Match by arXiv ID or DOI; title similarity only flags a possible match
- If DeepXiv and arXiv refer to the same preprint, keep one canonical paper row and record `deepxiv` as an additional source
- If DeepXiv overlaps with S2 on a published paper, prefer S2 venue/citation metadata in the final table, but keep DeepXiv-derived section notes when they add value

**Exa search** (only when `exa` is in sources):

When the resolved source list includes the provider (for example `— sources: exa` (or includes `exa` in a combined source list)), use the Exa tool for broad AI-powered web search with content extraction:

```bash
# Re-resolve $ARIS_REPO (SKILL bash blocks may run in separate shells).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.ei/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.ei/repo" 2>/dev/null) || true
fi
# Resolve $EXA_FETCHER (Policy D2 — warn-and-skip on missing).
EXA_FETCHER=".ei/tools/exa_search.py"
[ -f "$EXA_FETCHER" ] || EXA_FETCHER="tools/exa_search.py"
[ -f "$EXA_FETCHER" ] || { [ -n "${ARIS_REPO:-}" ] && EXA_FETCHER="$ARIS_REPO/tools/exa_search.py"; }
[ -f "$EXA_FETCHER" ] || EXA_FETCHER=""

if [ -n "$EXA_FETCHER" ]; then
  # Search for research papers with highlights.
  # Wrap with if/then/else so set -e doesn't abort the SKILL.
  exa_contributed=false
  if python3 "$EXA_FETCHER" search "QUERY" --max 10 --category "research paper" --content highlights; then
    exa_contributed=true
  else
    echo "WARN: exa_search.py research-paper invocation failed; D2 aggregate continues." >&2
  fi
  # Search for broader web content (blogs, docs, news)
  if python3 "$EXA_FETCHER" search "QUERY" --max 10 --content highlights; then
    exa_contributed=true
  else
    echo "WARN: exa_search.py broad-web invocation failed; D2 aggregate continues." >&2
  fi
  [ "$exa_contributed" = "true" ] && echo "D2 contribution: exa (at least one invocation exit 0)" >&2
fi
```

If `$EXA_FETCHER` is empty or the `exa-py` SDK is unavailable, skip this source gracefully and continue with the remaining requested sources (Policy D2 graceful degradation).

**Why use Exa?** Exa provides AI-powered search across the broader web (blogs, documentation, news, company pages) with built-in content extraction. It fills a gap between academic databases (arXiv, S2) and generic WebSearch by returning richer content with each result.

**De-duplication against arXiv, S2, and DeepXiv**:
- Use a verified canonical paper URL or strong ID; similar titles only flag possible matches
- If Exa returns an arXiv paper already found by arXiv/S2, prefer the structured metadata from those sources
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

**Why use Gemini?** Gemini provides AI-driven discovery that goes beyond keyword matching — it decomposes topics, explores naming variants, and surfaces papers that traditional API-based searches (arXiv, S2) may miss. It fills a different retrieval niche from structured database queries.

**De-duplication against arXiv, S2, DeepXiv, and Exa**:
- Match by arXiv ID or DOI; title similarity only flags a possible match
- If Gemini returns a paper already found by S2, prefer S2's citation count and venue metadata
- If Gemini returns a paper already found by arXiv, prefer arXiv's structured metadata
- Gemini's unique value is discovering papers that other keyword-based indexes did not surface
- **Do not use Gemini-reported citation counts** — they may be inaccurate. Use S2 for authoritative citation data.

**OpenAlex search** (only when `openalex` is in sources):

When the resolved source list includes the provider (for example `— sources: openalex` (or includes `openalex` in a combined source list), use OpenAlex API for comprehensive academic metadata):

```bash
# Re-resolve $ARIS_REPO (SKILL bash blocks may run in separate shells).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.ei/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.ei/repo" 2>/dev/null) || true
fi
# Resolve $OPENALEX_FETCHER (Policy D2 — warn-and-skip on missing).
OPENALEX_FETCHER=".ei/tools/openalex_fetch.py"
[ -f "$OPENALEX_FETCHER" ] || OPENALEX_FETCHER="tools/openalex_fetch.py"
[ -f "$OPENALEX_FETCHER" ] || { [ -n "${ARIS_REPO:-}" ] && OPENALEX_FETCHER="$ARIS_REPO/tools/openalex_fetch.py"; }
[ -f "$OPENALEX_FETCHER" ] || OPENALEX_FETCHER=""

# Preflight: skip OpenAlex silently if the helper is unresolved OR the
# `requests` Python package is missing. Both checks must pass before
# the script is invoked, so users without `requests` installed never see
# a stack trace from a default `/research-lit` run.
if [ -z "$OPENALEX_FETCHER" ] || ! python3 -c "import requests" >/dev/null 2>&1; then
  echo "OpenAlex source not available (openalex_fetch.py unresolved or 'requests' module missing); skipping." >&2
else
  # Search for papers with comprehensive metadata.
  # Wrap with if/then/else so set -e doesn't abort the SKILL.
  if python3 "$OPENALEX_FETCHER" search "QUERY" --max 10 \
      --type article \
      --sort relevance; then
    echo "D2 contribution: openalex (helper invocation exit 0)" >&2
  else
    echo "WARN: openalex_fetch.py invocation failed; D2 aggregate continues with remaining sources." >&2
  fi
fi
```

If `openalex_fetch.py` is not found or `requests` module is missing, report that this requested source is unavailable and continue independent work with incomplete coverage.

**Why use OpenAlex?** Fully open citation graph (no API key required), institutional affiliations, funding data (NSF, NIH), comprehensive topic/keyword metadata, and coverage across all disciplines (not just CS).

**De-duplication against arXiv, S2, DeepXiv, Exa, and Gemini**:
- Match by DOI first (OpenAlex has DOI for most works), then arXiv ID, then normalized title
- If OpenAlex and S2 both have the same paper:
  - Prefer S2 for citation counts (more up-to-date)
  - Prefer S2 for venue metadata (more accurate for CS/AI papers)
  - Use OpenAlex for institutional affiliations and funding data (unique value)
  - Merge both into a richer record
- If OpenAlex and arXiv overlap, prefer arXiv's PDF link and metadata, but keep OpenAlex's citation/institution data
- OpenAlex's unique value: institutional affiliations, funding sources, comprehensive topic classification, and cross-discipline coverage

**D2 aggregate finalization** (per integration-contract §2 Policy D2):

The orchestrator (you, the LLM) maintains an in-context list of
contributing sources by reading the `D2 contribution: <name>` log
lines emitted by each source's bash block above, plus:

- `zotero` if Step 0a returned non-empty Zotero hits.
- `obsidian` if Step 0b returned non-empty Obsidian hits.
- `local` if Step 0c found at least one relevant local PDF.
- `web` if WebSearch (Priority 4) was requested (either no `— sources:`
  filter, or the list contains `web` or `all`) AND was actually invoked.
  Note: `— sources: all` covers the default-on tier (zotero, obsidian,
  local, web) — it does **NOT** include the opt-in fetchers
  (semantic-scholar, deepxiv, exa, gemini, openalex). To enable those,
  add them explicitly (e.g. `— sources: all, semantic-scholar, openalex`),
  matching the existing convention at L42-43 / L51-63 of this SKILL.
- `gemini` if Gemini MCP / CLI returned at least one paper.

If the resulting contributing-source list has zero entries, surface:

> **ERROR**: D2 aggregate empty — every requested source either was
> unresolved, not invoked, failed, or (for MCP / local PDF / Gemini
> sources) returned no usable result. (Note: WebSearch contributes
> when requested and invoked, even if the result set is empty.) The
> multi-source aggregate cannot proceed. Suggest the user retry with
> a wider `— sources:` list (e.g. `web, local`) or check helper
> resolution and SDK installation.

Then stop before Step 1.5. Otherwise log the contributing-source
list to the user (e.g. "Sources contributed: arxiv, semantic_scholar,
web") and proceed.

**Optional PDF download** (only when `ARXIV_DOWNLOAD = true`):

After all sources are searched and papers are ranked by relevance:
```bash
# Re-resolve $ARXIV_FETCHER (SKILL bash blocks may run in separate shells).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.ei/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.ei/repo" 2>/dev/null) || true
fi
ARXIV_FETCHER=".ei/tools/arxiv_fetch.py"
[ -f "$ARXIV_FETCHER" ] || ARXIV_FETCHER="tools/arxiv_fetch.py"
[ -f "$ARXIV_FETCHER" ] || { [ -n "${ARIS_REPO:-}" ] && ARXIV_FETCHER="$ARIS_REPO/tools/arxiv_fetch.py"; }
[ -f "$ARXIV_FETCHER" ] || ARXIV_FETCHER=""

# Download requested relevant arXiv papers; report unresolved helper and missing downloads.
[ -n "$ARXIV_FETCHER" ] && python3 "$ARXIV_FETCHER" download ARXIV_ID --dir papers/
```
- Only download papers ranked in the top ARXIV_MAX_DOWNLOAD by relevance
- Skip papers already in the local library
- 1-second delay between downloads (rate limiting)
- Verify each PDF > 10 KB

