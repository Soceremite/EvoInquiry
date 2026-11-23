<!-- EI-WORKFLOW-REFERENCE -->

# Review Tracing

Read this file when the workflow reaches Review Tracing through Test 4: Append-Only Integrity. In commands and examples, interpret relative skill paths from the entrypoint directory.

#### Review Tracing

## Review Tracing

After every `mcp__claude-review__review_start`, `mcp__claude-review__review_reply_start`, `oracle-pro`, or nightmare adversarial verification call, save a trace following `../shared-references/review-tracing.md`. Include prompt summary, reviewer route, saved threadId, raw response path, score/verdict, accepted fixes, rejected rebuttals, and the `Reviewer Memory` update if present.

### Termination

When the loop ends (evidence-backed positive assessment, budget, stall or user stop):

1. Update `review-stage/REVIEW_STATE.json` with `"status": "completed"`
2. Write final summary to `review-stage/AUTO_REVIEW.md`
3. Update project notes with conclusions
4. **Write method/pipeline description** to `review-stage/AUTO_REVIEW.md` under a `## Method Description` section — a concise 1-2 paragraph summary of the final method, architecture, and data flow. This serves as direct input for `/paper-illustration`.
5. **Generate claims from results** — invoke `/result-to-claim` to convert experiment results from `review-stage/AUTO_REVIEW.md` into structured paper claims. Output: `CLAIMS_FROM_RESULTS.md`. If `/result-to-claim` is not installed, skip this step (no `CLAIMS_FROM_RESULTS.md` is produced; `/paper-plan` extracts claims from the narrative as before) — but NEVER fabricate the file or its verdict. If it ran but its output starts with `verdict: REVIEW_UNAVAILABLE`, keep that file AS-IS (do not overwrite or paraphrase it) and record in `AUTO_REVIEW.md` that claims are UNADJUDICATED — downstream paper stages must not treat them as validated.
6. If stopped for budget, stall or user instruction without evidence closure:
   - List remaining blockers
   - Estimate effort needed for each
   - Suggest whether to continue manually or pivot
7. **Feishu notification** (if configured): Send `pipeline_done` with final score progression table
8. **Render HTML view** (if `RENDER_HTML = true`, default): invoke `/render-html` on the cumulative review log:
   ```
   /render-html "review-stage/AUTO_REVIEW.md" --no-review --state review-stage/REVIEW_STATE.json
   ```
   Pass `--state` explicitly when `REVIEW_STATE.json` exists (the helper does not auto-discover the sidecar). HTML lands at `review-stage/AUTO_REVIEW.html` with embedded source SHA256. **Non-blocking**: if `/render-html` fails, log the error and continue — the HTML is a convenience, not a termination prerequisite.

## Output Protocols

> Follow these shared protocols for all output files:
> - **[Output Versioning Protocol](../../shared-references/output-versioning.md)** — write timestamped file first, then copy to fixed name
> - **[Output Manifest Protocol](../../shared-references/output-manifest.md)** — log every output to MANIFEST.md
> - **[Output Language Protocol](../../shared-references/output-language.md)** — respect the project's language setting

## Key Rules

- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.

- Always ask the Claude reviewer for strict, high-rigor feedback.
- Save the completed `threadId` from the first `mcp__claude-review__review_status` result, then use `mcp__claude-review__review_reply_start` plus `mcp__claude-review__review_status` for subsequent rounds
- Be honest — include negative results and failed experiments
- Do NOT hide weaknesses to game a positive score
- Implement fixes BEFORE re-reviewing (don't just promise to fix)
- If an experiment takes > 30 minutes, launch it and continue with other fixes while waiting
- Document EVERYTHING — the review log should be self-contained
- Update project notes after each round, not just at the end

## Prompt Template for Round 2+

```
mcp__claude-review__review_reply_start:
  # the bridge grants the reviewer no tools by default; this prompt passes
  # artifact paths, so it has to ask for read-only access explicitly
  tools: "Read,Grep,Glob"
  threadId: [saved from round 1]
  # inherits the agent's model/effort — do not re-send
  prompt: |
    [Round N update]

    Since your last review these files changed — read them yourself; do not
    take my word for what changed or whether it worked:
    - Changed files: <paths>
    - Raw diff: <path to a saved diff file — you can read files but cannot run `git diff`>
    - Updated raw results: <result-file paths> (verbatim files, not a pasted table)

    Please re-score and re-assess. Are the remaining concerns addressed?
    Same format: Score, Verdict, Remaining Weaknesses, Minimum Fixes.

    === REVIEW SCOPE ===
    Evaluate the actual research question, requested deliverable and applicable
    disciplinary standards. Locate strengths and defects in the supplied evidence;
    do not presume acceptance, rejection or a particular threat model. Distinguish
    observed errors, unsupported claims and optional extensions. Propose the smallest
    adequate correction, citing its failing path, evidence or preserved invariant.
    Keep hypotheses, speculation and unperformed checks explicit. A real boundary
    or reproducibility defect is in scope when it affects this work; unrelated
    infrastructure and speculative redesign are not automatically required.
    Say plainly when something is correct. Do not manufacture findings.
```

After this start call, immediately save the returned `jobId` and poll `mcp__claude-review__review_status` with a bounded `waitSeconds` until `done=true`. Treat the completed status payload's `response` as the reviewer output, and save the completed `threadId` for any follow-up round.

## Acquittal Gate Test Specifications

The following test cases validate the `run_id` + append-only acquittal receipt mechanism.

### Test 1: Fresh Start — Codex Acquits

**Setup:** Delete `review-stage/REVIEW_STATE.json` and `review-stage/ACQUITTAL_LOG.jsonl`. Run review.

**Action:** Codex round 1 returns score=7, verdict="ready".

**Expected:** Phase E writes acquittal line to `ACQUITTAL_LOG.jsonl` with current `run_id`. Loop stops.

### Test 2: Stale Completed State — Old Run's Acquittal Does NOT Satisfy New Run

**Setup:** Run 1 (run_id=`run_20260713_aaaaaaaa`) completes with `status: "completed"` and writes acquittal: `{"run_id":"run_20260713_aaaaaaaa","backend":"claude-review","verdict":"ready","score":7}` to `ACQUITTAL_LOG.jsonl`. Then a fresh-start invocation generates run_id=`run_20260713_bbbbbbbb`.

**Action:** Run 2 round 1 returns score=5, verdict="not ready". Continue to round 2, score=8, verdict="ready".

**Expected:** Run 2's acquittal line has `run_id=run_20260713_bbbbbbbb`. The old acquittal with `run_id=run_20260713_aaaaaaaa` is an audit artifact only. The stop gate for run 2 uses the current-run acquittal.

### Test 3: Legacy State File — No run_id Field

**Setup:** Create a `REVIEW_STATE.json` with `status: "in_progress"`, a fresh timestamp, but NO `run_id` field. Resume.

**Expected:** Initialization detects missing `run_id` and generates one. Log: "No run_id in legacy state file; assigned run_<...> for this resume."

### Test 4: Append-Only Integrity

**Setup:** Run 1 reaches a positive verdict, appends one receipt, and stops. Start Run 2 with a new `run_id`; it also reaches a positive verdict and appends one receipt.

**Action:** After the loop, inspect `ACQUITTAL_LOG.jsonl`.

**Expected:** File contains exactly 2 lines with different run IDs. Run 1's line remains unchanged after Run 2 appends; a stopped loop cannot continue to a later positive round.
