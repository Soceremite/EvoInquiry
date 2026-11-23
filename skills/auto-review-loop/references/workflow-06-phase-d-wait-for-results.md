<!-- EI-WORKFLOW-REFERENCE -->

# Phase D: Wait for Results

Read this file when the workflow reaches Phase D: Wait for Results through Key Rules. In commands and examples, interpret relative skill paths from the entrypoint directory.

#### Phase D: Wait for Results

If experiments were launched:
- Monitor remote sessions for completion
- Collect results from output files and logs
- **Training quality check** — if W&B is configured, invoke `/training-check` to verify training was healthy (no NaN, no divergence, no plateau). If W&B not available, skip silently. Flag any quality issues in the next review round.

#### Phase E: Document Round

Append to `review-stage/AUTO_REVIEW.md`:

```markdown
## Round N (timestamp)

### Assessment (Summary)
- Score: X/10
- Verdict: [ready/almost/not ready]
- Key criticisms: [bullet list]

### Reviewer Raw Response

<details>
<summary>Click to expand full reviewer response</summary>

[Paste the COMPLETE raw response from the reviewer here — verbatim, unedited.
This is the authoritative record. Do NOT truncate or paraphrase.]

</details>

### Debate Transcript (hard + nightmare only)

<details>
<summary>Click to expand debate</summary>

**Executor Rebuttal:**
[paste rebuttal]

**Reviewer Ruling:**
[paste ruling — SUSTAINED / OVERRULED / PARTIALLY SUSTAINED for each]

**Score adjustment**: X/10 → Y/10

</details>

### Actions Taken
- [what was implemented/changed]

### Results
- [experiment outcomes, if any]

### Status
- [continuing to round N+1 / stopping]
- Difficulty: [medium/hard/nightmare]
```

**Write `review-stage/REVIEW_STATE.json`** with current `run_id`, round, threadId, score, verdict, `reviewer_backend`, `requires_external_acquittal`, and any pending experiments. The `run_id` field MUST persist unchanged from initialization; do NOT regenerate it per round.

**Backend labeling for the state file:** The `reviewer_backend` field in `REVIEW_STATE.json` controls the continuation mechanism for the NEXT round (used on resume), not the round just documented. During Phase E:
- Use `round_backend` (snapshotted at round start, step 0) to label the CURRENT round in `AUTO_REVIEW.md` documentation (e.g., "Reviewer backend: copilot-native").
- Use `round_requires_external_acquittal` to decide whether the CURRENT round was a Copilot-triggered finalizer. Write `requires_external_acquittal` in state as the forward-looking obligation for the NEXT round.
- Write `reviewer_backend` in `REVIEW_STATE.json` to the value that should control the NEXT round — this is either (a) unchanged from the current round's backend if no escalation occurred, or (b) the escalation backend set during Phase B.5.1. Never substitute `round_backend` for this forward-looking field.
- When no escalation happened, `round_backend == reviewer_backend` (trivially safe).
- For a native round, persist `native_evidence_id`, `native_evidence_path`, both
  host-event model IDs/sources, `family_relation: different`, and
  `identity_assurance: host_event_verified`. Never copy these fields from prose.

**If `round_backend ∈ {codex, manual}` AND `round_requires_external_acquittal = true` AND score >= 6 AND verdict ∈ {"ready", "almost"}:** append one external-finalizer line to `review-stage/ACQUITTAL_LOG.jsonl`:
```
{"run_id":"<current-run_id>","round":<N>,"backend":"<codex|manual>","effort":"xhigh","verdict":"<ready|almost>","score":<score>,"executor_model":"<from-trace>","executor_model_source":"caller-declared","executor_family":"<derived-from-executor_model>","reviewer_model":"<from-trace-or-manual-Reviewer-Model>","reviewer_model_source":"<requested|backend-reported>","reviewer_family":"<derived-from-reviewer_model>","family_relation":"different","identity_assurance":"caller_declared","independence_verified":"unverified","trace_id":"<skill>/<YYYY-MM-DD>_run<NN>","timestamp":"<ISO8601>"}
```
Use `>>` (append), never `>`. Re-derive both families from model strings and reject unknown/same-family pairs, but copy the model-source and assurance fields without upgrading them. The `trace_id` MUST be the actual trace directory path relative to `.ei/traces/` (e.g., `auto-review-loop/2026-07-13_run01`), matching the RUN_ID format from `save_trace.sh`: `<YYYY-MM-DD>_run<NN>` with the skill-name subdirectory prefix. Do NOT fabricate a synthetic `trace_...` identifier.

**Append to `findings.md`** (when `COMPACT = true`): one-line entry per key finding this round:

```markdown
- [Round N] [positive/negative/unexpected]: [one-sentence finding] (metric: X.XX → Y.YY)
```

Increment round counter → back to Phase A.

### Termination

When the loop ends (evidence-backed positive assessment, budget, stall or user stop):

1. Update `review-stage/REVIEW_STATE.json` with `"status": "completed"`
2. Write final summary to `review-stage/AUTO_REVIEW.md`
3. Update project notes with conclusions
4. **Write method/pipeline description** to `review-stage/AUTO_REVIEW.md` under a `## Method Description` section — a concise 1-2 paragraph description of the final method, its architecture, and data flow. This serves as input for `/paper-illustration` in Workflow 3 (so it can generate architecture diagrams automatically).
5. **Generate claims from results** — invoke `/result-to-claim` to convert experiment results from `review-stage/AUTO_REVIEW.md` into structured paper claims. Output: `CLAIMS_FROM_RESULTS.md`. This bridges Workflow 2 → Workflow 3 so `/paper-plan` can directly use validated claims instead of extracting them from scratch. If `/result-to-claim` is not installed, skip this step (no `CLAIMS_FROM_RESULTS.md` is produced; `/paper-plan` extracts claims from the narrative as before) — but NEVER fabricate the file or its verdict. If it ran but its output starts with `verdict: REVIEW_UNAVAILABLE`, keep that file AS-IS (do not overwrite or paraphrase it) and record in `AUTO_REVIEW.md` that claims are UNADJUDICATED — downstream paper stages must not treat them as validated.
6. If stopped for budget, stall or user instruction without evidence closure:
   - List remaining blockers
   - Estimate effort needed for each
   - Suggest whether to continue manually or pivot
7. **Feishu notification** (if configured): Send `pipeline_done` with final score progression table
8. **Render HTML view** (if `RENDER_HTML = true`, default): invoke `/render-html` on the cumulative review log:
   ```
   /render-html "review-stage/AUTO_REVIEW.md" --no-review --state review-stage/REVIEW_STATE.json
   ```
   Pass `--state` explicitly (the helper does not auto-discover the sidecar). Drop the `--state` flag if `REVIEW_STATE.json` doesn't exist. HTML lands at `review-stage/AUTO_REVIEW.html` with embedded source SHA256. **Non-blocking**: if `/render-html` fails, log the error and continue — the HTML is a convenience, not a termination prerequisite. Skip if `RENDER_HTML = false`.

## Key Rules

- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.

- **Codex backend:** pin `model: gpt-6-astra` + `config: {"model_reasoning_effort": "xhigh"}` on the first call of every thread. `xhigh` is this loop's **regular tier** per [`reviewer-routing.md`](../../shared-references/reviewer-routing.md), not the maximum — `ultra` belongs to the one-shot deep-audit skills and is slower and costlier per round. Do not raise this loop's tier; replies inherit the thread's pair, so changing it means a new thread. Follow the capability-fallback chain only for explicit capability errors.
- **Native Copilot is an evidence-gated acceptance backend.** It never pins a
  reviewer model: Copilot selects the complementary rubber-duck model, and the
  helper verifies the actual cross-family pair from host events. A native
  positive needs no external finalizer.
- **Explicit compatibility Copilot remains drive-only.** Its `copilot --agent`
  calls pin profile model/xhigh/read-only access and require a traced
  Codex/manual finalizer; caller-declared identity remains unverified.
- Save `threadId` (codex/manual), fresh evidence path/ID (`copilot-native`), or `reviewer_profile` (compatibility copilot); use the appropriate continuation mechanism
- **Anti-hallucination citations**: When adding references during fixes, NEVER fabricate BibTeX. Use the same DBLP → CrossRef → `[VERIFY]` chain as `/paper-write`: (1) `curl -s "https://dblp.org/search/publ/api?q=TITLE&format=json"` → get key → `curl -s "https://dblp.org/rec/{key}.bib"`, (2) if not found, `curl -sLH "Accept: application/x-bibtex" "https://doi.org/{doi}"`, (3) if both fail, mark with `% [VERIFY]`. Do NOT generate BibTeX from memory.
- Be honest — include negative results and failed experiments
- Do NOT hide weaknesses to game a positive score
- Implement fixes BEFORE re-reviewing (don't just promise to fix)
- **Exhaust before surrendering** — before marking any reviewer concern as "cannot address": (1) try at least 2 different solution paths, (2) for experiment issues, adjust hyperparameters or try an alternative baseline, (3) for theory issues, provide a weaker version of the result or an alternative argument, (4) only then concede narrowly and bound the damage. Never give up on the first attempt.
- If an experiment takes > 30 minutes, launch it and continue with other fixes while waiting
- Document EVERYTHING — the review log should be self-contained
- Update project notes after each round, not just at the end

