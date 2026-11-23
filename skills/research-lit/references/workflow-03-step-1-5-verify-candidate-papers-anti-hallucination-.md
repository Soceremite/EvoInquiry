<!-- EI-WORKFLOW-REFERENCE -->

# Step 1.5: Verify Candidate Papers (anti-hallucination, mandatory)

Read this file when the workflow reaches Step 1.5: Verify Candidate Papers (anti-hallucination, mandatory) through Step 5: Save (if requested). In commands and examples, interpret relative skill paths from the entrypoint directory.

### Step 1.5: Verify Candidate Papers (anti-hallucination, mandatory)

Before analysis, run pre-search verification on **all** candidate papers
collected from Steps 0a-1 to filter out LLM-fabricated arXiv IDs / DOIs /
titles. Helper: `verify_papers.py` (canonical name; resolved per
[`shared-references/integration-contract.md`](../../shared-references/integration-contract.md) §2,
Policy D1 — primary helper with degraded-output fallback). If the
helper is unresolved on this machine, the SKILL emits a fallback
`verified_papers.json` tagging every candidate `[UNVERIFIED]` so
downstream analysis proceeds with audit-visible degraded output
rather than silently dropping candidates.

```bash
# 1. Resolve $VERIFY_PAPERS via the canonical strict-safe chain (§2).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.ei/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.ei/repo" 2>/dev/null) || true
fi
VERIFY_PAPERS=".ei/tools/verify_papers.py"
[ -f "$VERIFY_PAPERS" ] || VERIFY_PAPERS="tools/verify_papers.py"
[ -f "$VERIFY_PAPERS" ] || { [ -n "${ARIS_REPO:-}" ] && VERIFY_PAPERS="$ARIS_REPO/tools/verify_papers.py"; }
[ -f "$VERIFY_PAPERS" ] || VERIFY_PAPERS=""

# 2. Emit candidates as JSON. Verification scratch lives under .ei/
#    (NOT under research-wiki/ — Step 6's wiki ingest predicate is
#    "research-wiki/ exists", and we must not trip it from Step 1.5).
mkdir -p .ei/verify-papers
cat > .ei/verify-papers/candidate_papers.json <<'JSON'
[
  {"id": "p1", "arxiv_id": "2307.03172", "doi": null, "title": "Lost in the Middle"},
  {"id": "p2", "arxiv_id": null, "doi": "10.1145/...", "title": "..."},
  {"id": "p3", "arxiv_id": null, "doi": null, "title": "Some Paper Title"}
]
JSON

# 3. Run 3-layer verification (arXiv batch → CrossRef → Semantic Scholar fuzzy).
#    Policy D1: when the helper is unresolved OR its invocation fails, emit
#    a degraded verified set tagging everything [UNVERIFIED] so the user
#    can audit search quality. If python3 itself is missing, we BLOCK
#    rather than hand-roll JSON in shell.
verify_ok=false
if [ -n "$VERIFY_PAPERS" ]; then
  if python3 "$VERIFY_PAPERS" \
        --input  .ei/verify-papers/candidate_papers.json \
        --output .ei/verify-papers/verified_papers.json; then
    verify_ok=true
  else
    echo "WARN: verify_papers.py invocation failed (resolved at $VERIFY_PAPERS); falling back to [UNVERIFIED] tagging." >&2
  fi
else
  echo "WARN: verify_papers.py not resolved at .ei/tools/, tools/, \$ARIS_REPO/tools/, or via ~/.ei/repo." >&2
  echo "      Fix: rerun bash tools/install_aris.sh or smart_update.sh (refreshes ~/.ei/repo), export ARIS_REPO, or copy the helper to tools/." >&2
fi
if [ "$verify_ok" = "false" ]; then
  if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 unavailable; cannot emit fallback verified_papers.json." >&2
    echo "       Status: BLOCKED. Install python3 or restore the helper to proceed." >&2
    exit 1
  fi
  echo "      Emitting unverified candidate set with [UNVERIFIED] tags." >&2
  python3 - <<'PY'
import json
cands = json.load(open('.ei/verify-papers/candidate_papers.json'))
out = {
  'verdict': 'WARN',
  'reason_code': 'verify_papers_unavailable',
  'summary': 'verify_papers.py helper unresolved or invocation failed; all candidates tagged [UNVERIFIED] for audit visibility.',
  'papers': [dict(p, status='unverified', method='none') for p in cands],
}
with open('.ei/verify-papers/verified_papers.json', 'w') as f:
  json.dump(out, f, indent=2)
PY
fi

# 4. Read verdict + per-paper status from .ei/verify-papers/verified_papers.json;
#    surface warnings to the user.
```

**Mandatory output rules** (see
[`shared-references/citation-discipline.md`](../../shared-references/citation-discipline.md)
§ Pre-Search Verification Protocol for the full contract):

- Tag every paper in the analyzed list with its status: `✅ verified (via
  arxiv|crossref|s2)` or `⚠️ UNVERIFIED (reason)` or `… verify_pending`.
- **Never silently drop unverified papers** — keep them in the output with the
  `[UNVERIFIED]` marker so the user can audit the search quality.
- Never fabricate a DOI or arXiv ID from memory. If a field is unknown, leave
  it `null` in `candidate_papers.json` — the helper will fall through to title
  search.
- If the helper returns `WARN` with `high_hallucination_rate`, surface the
  warning verbatim and recommend re-running with narrower queries.
- For papers tagged `verify_pending`, do not promote them to `verified` —
  show the pending state to the user and retry on the next session.

Optional: set `ARIS_VERIFY_EMAIL=you@institution.edu` in your shell to lift
CrossRef rate limits to the polite pool.

### Step 2: Analyze Each Paper

> **Fan-out (Tier-aware).** Per-paper extraction is pure breadth — each paper
> is independent — so it parallelizes cleanly. **Tier 1** (Workflow): spawn
> one Claude subagent per paper (or per small batch) to extract the fields
> below. **Tier 2** (Agent tool, no Workflow): the same per-paper subagents
> via the Agent tool. **Tier 3**: iterate sequentially. This follows the
> *extraction* shard schema from
> [`shared-references/fan-out-pattern.md`](../../shared-references/fan-out-pattern.md)
> — `{shard_id: "<paper-or-batch id>", entries: [{dedup_key: "<canonical
> arXiv-id / DOI / title-hash, already assigned upstream in Step 1.5>",
> problem, method, results, relevance, source, verification_status}]}`.
>
> The "jury" here is **not a model** — it is the **deterministic**
> `verify_papers.py` gate already run in Step 1.5 (3-layer arXiv / CrossRef /
> Semantic Scholar cross-check). Because the acceptance gate is a deterministic
> verifier, not a model verdict, the cross-model-family rule is automatically
> satisfied (a process is not a model family — see
> [`acceptance-gate.md`](../../shared-references/acceptance-gate.md)), so this is
> the **near-zero-risk** corner of the fan-out design space. The per-paper work
> is **extraction, not adjudication**: shards report what each paper says and
> its verification status verbatim; they do **not** decide which papers
> "count" (Step 1.5 already did, mechanically) and they do **not** drop a paper
> for any status other than `verified`. Synthesis (Step 3) is *interpretive*
> aggregation — grouping by theme, spotting gaps our work could fill — over an
> already-admitted set; it is the executor's normal job, NOT an accept/reject
> verdict on whether a paper *counts*. The cross-model-family rule governs
> admission verdicts, and here admission is the deterministic Step-1.5 gate, so
> the invariant is satisfied without a model jury.

For **every** paper in `.ei/verify-papers/verified_papers.json`
(verified, unverified, `verify_pending`, and `error` alike — see
Retention rule above), extract:
- **Problem**: What gap does it address?
- **Method**: Core technical contribution (1-2 sentences)
- **Results**: Key numbers/claims
- **Relevance**: How does it relate to our work?
- **Source**: Where we found it (Zotero/Obsidian/local/web) — helps user know what they already have vs what's new
- **Verification status** (one of):
  - `✅ verified (via arxiv|crossref|s2)`
  - `⚠️ UNVERIFIED (verification unavailable: helper unresolved or invocation failed)`
  - `⚠️ UNVERIFIED (searched: not found in any source)`
  - `… VERIFY_PENDING (transient API failure — retry next session)`
  - `❌ ERROR (malformed input: no arxiv, no DOI, no title)`

  Show the status in the analyzed table — never silently drop a
  paper because its status is anything other than `verified`.

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

> **Composed mode** — if invoked with `— composed: <canonical-report-path>` (an
> orchestrator like `/idea-discovery` passes this), do **not** write a standalone
> landscape `.md`. Return the structured table + narrative summary for the orchestrator
> to fold into its canonical report as a "Literature Landscape" section; the report
> links any saved PDFs/`references.bib`, it does not get a duplicate landscape file.
> Step 6 (research-wiki ingest) still runs — the wiki is a separate persistent store,
> not a duplicate of the report. **Default (no `— composed:` directive): behave exactly
> as above — standalone, write files as documented.** Never infer composed mode from a
> report file merely existing on disk. Full rules:
> [`shared-references/output-composition.md`](../../shared-references/output-composition.md).

