<!-- EI-WORKFLOW-REFERENCE -->

# Context: $ARGUMENTS

Read this file when the workflow reaches Context: $ARGUMENTS through Phase B: Parse Assessment. In commands and examples, interpret relative skill paths from the entrypoint directory.





# Auto Review Loop: Autonomous Research Improvement

> **Codex assurance:** every base reviewer result records
> `review_independence: same-family` and `acceptance_status: provisional` in its
> trace/state artifact. A positive provisional verdict may drive fixes and stop
> the loop, but is never cross-family accepted. Reviewer failure emits BLOCKED.

Autonomously iterate: review → implement fixes → re-review, until the external reviewer gives a positive assessment or MAX_ROUNDS is reached.

## Context: $ARGUMENTS

## Shared cycle and recovery

Read [research-review-cycle](../../shared-references/research-review-cycle.md)
before iterating or resuming. It owns material-issue closure, cumulative budgets,
state preservation and the common cycle. The backend routing, reviewer memory,
acquittal gate and single receipt append site below remain authoritative.

## Constants

- MAX_ROUNDS = 4
- POSITIVE_THRESHOLD: score >= 6/10 AND verdict ∈ {"ready", "almost"} — both must hold, matching the operative STOP CONDITION below. Verdict vocabulary is {"ready", "almost", "not ready"}. (Earlier wording used "or" + a stale verdict set; the AND form is authoritative.)
- REVIEW_DOC: `review-stage/AUTO_REVIEW.md` (cumulative log) *(fall back to `./AUTO_REVIEW.md` for legacy projects)*
- **OUTPUT_DIR = `review-stage/`** — All review-stage outputs go here. Create the directory if it doesn't exist.
- REVIEWER_MODEL = `gpt-6-astra` — Model used via a secondary Codex agent. Must be an OpenAI model (e.g., `gpt-6-astra`, `o3`, `gpt-4o`)
- **REVIEWER_BACKEND = `codex`** — Default: Codex reviewer agent at xhigh reasoning. Override with `--reviewer: oracle-pro` only when the user explicitly requests Oracle; if Oracle is unavailable, warn and fall back to Codex xhigh. **Same-family note:** this default reviewer is a second Codex/GPT agent — valid for Type-A completeness/drive review, but not a cross-family Type-B verdict; install a `skills-codex-claude-review` / `skills-codex-gemini-review` overlay for a cross-family acquittal (see `shared-references/reviewer-routing.md`).
- **HUMAN_CHECKPOINT = false** — When `true`, pause after each round's review (Phase B) and present the score + weaknesses to the user. Wait for user input before proceeding to Phase C. The user can: approve the suggested fixes, provide custom modification instructions, skip specific fixes, or stop the loop early. When `false` (default), the loop runs fully autonomously.
- **COMPACT = false** — When `true`, (1) read `EXPERIMENT_LOG.md` and `findings.md` instead of parsing full logs on session recovery, (2) append key findings to `findings.md` after each round.
- **REVIEWER_DIFFICULTY = medium** — Controls adversarial depth: `medium` uses normal Codex xhigh review through `spawn_agent` / `send_input`; `hard` adds Reviewer Memory and Debate Protocol; `nightmare` adds direct repository-reading adversarial verification by an independent reviewer.
- **RENDER_HTML = true** — When `true` (default), auto-render `review-stage/AUTO_REVIEW.md` to HTML on loop termination via `/render-html`. Uses `--no-review` for structural conversion of the recorded assessment; rendering does not add or change review acceptance. Preserve unavailable or incomplete reviews as BLOCKED. Set `false` to skip.

> 💡 Override: `/auto-review-loop "topic" — compact: true, human checkpoint: true, difficulty: hard`

## Claude-Aligned Reviewer Memory and Debate

Maintain `review-stage/REVIEWER_MEMORY.md` in all difficulty modes. Phase B.5 appends the reviewer's raw response and memory update regardless of `REVIEWER_DIFFICULTY`.

- Before each reviewer call, prepend the full `REVIEWER_MEMORY.md` contents under `## Your Reviewer Memory (persistent across rounds)`.
- Tell the reviewer to check whether prior suspicions were genuinely addressed or merely sidestepped.
- Require a `Memory update` section in the reviewer response.
- After Phase B, copy the `Memory update` into `REVIEWER_MEMORY.md` before writing `REVIEW_STATE.json`.
- For `difficulty: hard` and `difficulty: nightmare`, additionally use the **Debate Protocol** after a critical review.
- In `nightmare`, launch an additional fresh adversarial reviewer with direct repository/file-reading instructions. It should read `NARRATIVE_REPORT.md` or `review-stage/AUTO_REVIEW.md` for the author's claims, then verify those claims against code, logs, result files, and paper drafts instead of trusting executor summaries.

## Instructions

In hard and nightmare modes, the reviewer must actively look for omissions, unsupported claims, cherry-picked evidence, metric mistakes, and weaknesses the executor may have downplayed.

For `difficulty: hard` and `nightmare`, use the **Debate Protocol** after a critical review:

1. Codex writes a concise rebuttal with evidence, not spin.
2. Send the rebuttal to the same reviewer via `send_input`.
3. The reviewer rules which objections are resolved, unresolved, or newly discovered.
4. Only mark a concern resolved when the reviewer accepts the rebuttal.

## State Persistence (Compact Recovery)

Long-running loops may hit the context window limit, triggering automatic compaction. To survive this, persist state to `review-stage/REVIEW_STATE.json` after each round:

```json
{
  "run_id": "run_20260713_a1b2c3d4",
  "round": 2,
  "agent_id": "019cd392-...",
  "status": "in_progress",
  "last_score": 5.0,
  "last_verdict": "not ready",
  "pending_experiments": ["screen_name_1"],
  "timestamp": "2026-03-13T21:00:00"
}
```

- **`run_id`** — Globally unique per invocation. Generated on fresh start as `run_<YYYYMMDD>_<8-char-hex>` (e.g., `run_20260713_a1b2c3d4`). Preserved across round writes. On resume, read from state file unchanged. This binds all round state and acquittal receipts to one run.

**Write this file at the end of every Phase E** (after documenting the round). Overwrite each time — only the latest round's state matters. The `run_id` field MUST persist unchanged across overwrites within the same run.

**On completion** (positive assessment or max rounds), set `"status": "completed"` so future invocations don't accidentally resume a finished loop.

### Append-Only Acquittal Receipt

In addition to the overwritable state file, maintain an **append-only** acquittal log at `review-stage/ACQUITTAL_LOG.jsonl`. Each line is a standalone JSON object recording an acquitting positive verdict:

```jsonl
{"run_id":"run_20260713_a1b2c3d4","round":3,"backend":"codex","effort":"xhigh","verdict":"ready","score":7.5,"trace_id":"trace_20260713_run03","timestamp":"2026-07-13T14:22:00Z"}
```

**Rules (non-negotiable):**

| Rule | Detail |
|------|--------|
| **Append-only** | Never delete, never truncate, never overwrite lines. Only `>>`. |
| **When to write** | At the end of Phase E, after a positive verdict (score >= 6 AND verdict ∈ {"ready", "almost"}) AND verified material-issue closure. |
| **`run_id` binding** | Every acquittal line carries the current `run_id`. Only entries whose `run_id` matches the current run are valid acquittals for stop decisions. |
| **Trace linkage** | `trace_id` MUST reference a trace artifact in `.ei/traces/`. |
| **No overwrite** | `REVIEW_STATE.json` is overwritten each round. `ACQUITTAL_LOG.jsonl` is NEVER overwritten — it is the permanent, cumulative record.

## Workflow

### Initialization

1. **Check for `review-stage/REVIEW_STATE.json`** *(fall back to `./REVIEW_STATE.json` if not found — legacy path)*:
   - If neither path exists: **fresh start** (normal case, identical to behavior before this feature existed)
     - **Generate `run_id`**: `run_<YYYYMMDD>_<8-char-hex>` (e.g., `run_20260713_a1b2c3d4`). This run_id persists across all round writes and binds acquittal receipts to this invocation.
   - If it exists AND `status` is `"completed"`: **fresh start** (previous loop finished normally — but its `ACQUITTAL_LOG.jsonl` entries are retained as an audit trail with their own `run_id`, and are NOT valid for the current run's stop gate)
     - **Generate a new `run_id`** for this invocation.
   - If `status` is `"in_progress"`: reconcile pending jobs and evidence, then resume the same run regardless of timestamp age. Apply the shared cycle's recovery rules; never delete state or reset original limits because it is old.
     - Read the saved `run_id`, round, reviewer session and pending work unchanged. If a legacy state lacks `run_id`, assign it once and record the migration; old unrelated receipts remain invalid.
     - Read the existing cumulative review log and actual pending-job records before choosing the next round. Preserve unfinished work until its outcome is verified.
   - Malformed or conflicting state: preserve it and report the specific recovery issue; do not silently begin a replacement run.
2. Read project narrative documents, memory files, and any prior review documents. When `COMPACT = true` and compact files exist, prefer `findings.md` + `EXPERIMENT_LOG.md` over full raw logs.
3. Read recent experiment results (check output directories, logs)
4. Identify current weaknesses and open TODOs from prior reviews
5. Initialize round counter = 1 (unless recovered from state file)
6. Create/update `review-stage/AUTO_REVIEW.md` with header and timestamp

### Loop (repeat up to MAX_ROUNDS)

#### Phase A: Review

**Route by REVIEWER_DIFFICULTY:**

##### Medium (default) — Codex Review

Send comprehensive context to the external reviewer:

```
spawn_agent:
  model: gpt-6-astra
  reasoning_effort: xhigh
  message: |
    [Round N/MAX_ROUNDS of autonomous review loop]

    Review the work directly from its artifacts — executor notes are not
    evidence, so read the files yourself rather than trusting my framing:
    - Claims / paper draft: <path>
    - Methods / code under review: <path(s)>
    - Raw results (verbatim files, not a summary): <path(s)>
    - Changed since last round: <changed-file paths> — read the diff, not my description

    Please review the work against its question, evidence and intended use.
    Verify consequential claims against actual artifacts. Identify supported
    strengths, material weaknesses, alternative explanations and missing evidence.
    Apply the same evidential standard to favorable and unfavorable conclusions.

    1. Score this work 1-10 for a top venue
    2. List remaining critical weaknesses (ranked by severity)
    3. For each weakness, specify the MINIMUM fix (experiment, analysis, or reframing)
    4. State clearly: is this READY for submission? Yes/No/Almost

    Be brutally honest. If, after genuinely trying to break it, the work holds
    up and is ready, say so clearly.

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

If this is round 2+, use `send_input` with the saved agent id to maintain continuity.

##### Hard — Codex Review + Reviewer Memory

Use the same `spawn_agent` / `send_input` route as medium, but prepend the full `review-stage/REVIEWER_MEMORY.md` contents under `## Your Reviewer Memory (persistent across rounds)` and require a `Memory update` section in the reviewer response.

##### Nightmare — Independent Repository Review

Use everything in hard mode, then ask an additional fresh adversarial reviewer to verify claims against repository files, logs, result files, and paper drafts instead of trusting executor summaries. Preserve the fresh review as a separate raw response and trace. That reviewer is fresh, so it does not inherit the scope limits from the medium/hard prompt — repeat the block from [`review-scope-limits.md`](../../shared-references/review-scope-limits.md) in its prompt. This is the mode with the widest repository access and the one most likely to propose defensive scaffolding.

#### Phase B: Parse Assessment

**CRITICAL: Save the FULL raw response** from the external reviewer verbatim (store in a variable for Phase E). Do NOT discard or summarize — the raw text is the primary record.

Then extract structured fields:
- **Score** (numeric 1-10)
- **Verdict** ("ready" / "almost" / "not ready")
- **Action items** (ranked list of fixes)

