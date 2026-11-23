<!-- EI-WORKFLOW-REFERENCE -->

# State Persistence (Compact Recovery)

Read this file when the workflow reaches State Persistence (Compact Recovery) through Loop (repeat up to MAX_ROUNDS). In commands and examples, interpret relative skill paths from the entrypoint directory.

## State Persistence (Compact Recovery)

Long-running loops may hit the context window limit, triggering automatic compaction. To survive this, persist state to `review-stage/REVIEW_STATE.json` after each round:

```json
{
  "run_id": "run_20260713_a1b2c3d4",
  "round": 2,
  "threadId": null,
  "reviewer_profile": "rubber-duck",
  "reviewer_backend": "copilot-native",
  "executor_model": "claude-sonnet-4.6",
  "executor_model_source": "host-session-event",
  "executor_family": "anthropic",
  "requested_reviewer_model": null,
  "reported_reviewer_model": "gpt-5.5",
  "reviewer_model_source": "host-session-event",
  "reviewer_family": "openai",
  "family_relation": "different",
  "identity_assurance": "host_event_verified",
  "independence_verified": true,
  "native_evidence_id": "cne_0123456789abcdef0123456789abcdef",
  "native_evidence_path": "review-stage/COPILOT_NATIVE_run_20260713_a1b2c3d4_ROUND_2_REVIEW.evidence.json",
  "requires_external_acquittal": false,
  "status": "in_progress",
  "difficulty": "medium",
  "last_score": 5.0,
  "last_verdict": "not ready",
  "pending_experiments": ["screen_name_1"],
  "timestamp": "2026-03-13T21:00:00"
}
```

- **`run_id`** — Globally unique per invocation. Generated on fresh start as `run_<YYYYMMDD>_<8-char-hex>` (e.g., `run_20260713_a1b2c3d4`). Preserved across round writes. On resume, read from state file unchanged. This binds all round state, reviewer-memory appends, and acquittal receipts to one run so a stale completed state from a previous invocation cannot leak into the current run's acquittal check.

When REVIEWER_BACKEND = `copilot-native`, save the evidence ID/path and the
host-event executor/reviewer models, derived families, and sources. Each round
is a fresh rubber-duck subagent and therefore gets a fresh evidence artifact;
there is no persistent child handle. When REVIEWER_BACKEND = compatibility
`copilot`, retain `reviewer_profile`, requested model, caller-declared executor
model, `independence_verified: "unverified"`, and the external-finalizer
obligation. For `codex` save its MCP `threadId`; for `manual` save `threadId`
and the reported reviewer identity. On resume, use `reviewer_backend` to select
the continuation mechanism and preserve `requires_external_acquittal`.

**Write this file at the end of every Phase E** (after documenting the round). Overwrite each time — only the latest round's state matters. The `run_id` field MUST persist unchanged across overwrites within the same run.

**On completion** (positive assessment or max rounds), set `"status": "completed"` so future invocations don't accidentally resume a finished loop.

### Append-Only External-Finalizer Receipt

Whenever a Copilot path hands the verdict to an external backend—after a
positive compatibility-drive review or after a pre-verdict native dispatch
failure—maintain an **append-only** finalizer log at
`review-stage/ACQUITTAL_LOG.jsonl`. Each line records the Codex/manual reviewer
that completed that run. A successful native rubber-duck round never needs or
writes this receipt; its evidence sidecar is the acceptance record. The
historical filename is retained for compatibility:

```jsonl
{"run_id":"run_20260713_a1b2c3d4","round":3,"backend":"codex","effort":"xhigh","verdict":"ready","score":7.5,"executor_model":"claude-sonnet-4-5","executor_model_source":"caller-declared","executor_family":"anthropic","reviewer_model":"gpt-6-astra","reviewer_model_source":"requested","reviewer_family":"openai","family_relation":"different","identity_assurance":"caller_declared","independence_verified":"unverified","trace_id":"auto-review-loop/2026-07-13_run03","timestamp":"2026-07-13T14:22:00Z"}
```

**Rules (non-negotiable):**

| Rule | Detail |
|------|--------|
| **Append-only** | Never delete, never truncate, never overwrite lines. Only `>>`. |
| **Who writes** | Only a `codex` or `manual` round at `xhigh` effort when `round_requires_external_acquittal` was `true`. A Copilot review/dispatch never writes a finalizer line itself. |
| **When to write** | At the end of Phase E, after the policy-approved finalizer returns score >= 6 AND verdict ∈ {"ready", "almost"}. A normal default-Codex run does not need this sidecar. |
| **`run_id` binding** | Every line carries the current `run_id` and round so the Copilot → finalizer transition is auditable. |
| **Trace linkage** | `trace_id` MUST reference the real trace artifact in `.ei/traces/`; source and family fields in the receipt must exactly match that trace. |
| **Identity honesty** | Re-derive `family_relation` from the model strings, but preserve their sources. With the current caller-declared executor identity, write `identity_assurance: "caller_declared"` and `independence_verified: "unverified"`; never promote different strings to independent attestation. |
| **No overwrite** | `REVIEW_STATE.json` is overwritten each round (only latest state). `ACQUITTAL_LOG.jsonl` is NEVER overwritten — it is the permanent, cumulative record. |

**Why this exists:** `REVIEW_STATE.json` is overwritten each round. The log
preserves evidence that a compatibility drive verdict or failed native attempt
did not terminate by itself. A successful `copilot-native` verdict instead
uses its host-event evidence sidecar.

## Output Protocols

> Follow these shared protocols for all output files:
> - **[Output Versioning Protocol](../../shared-references/output-versioning.md)** — write timestamped file first, then copy to fixed name
> - **[Output Manifest Protocol](../../shared-references/output-manifest.md)** — log every output to MANIFEST.md
> - **[Output Language Protocol](../../shared-references/output-language.md)** — respect the project's language setting

## Workflow

### Initialization

1. **Check for `review-stage/REVIEW_STATE.json`** *(fall back to `./REVIEW_STATE.json` if not found — legacy path)*:
   - If neither path exists: **fresh start** (normal case, identical to behavior before this feature existed)
     - **Generate `run_id`**: `run_<YYYYMMDD>_<8-char-hex>` (e.g., `run_20260713_a1b2c3d4`). Use `date +%Y%m%d` and 8 random hex characters. This run_id persists across all round writes and binds acquittal receipts to this invocation.
   - If it exists AND `status` is `"completed"`: **fresh start** (previous loop finished normally — but its `ACQUITTAL_LOG.jsonl` entries are retained as an audit trail with their own `run_id`, and are NOT valid for the current run's stop gate)
     - **Generate a new `run_id`** for this invocation.
   - If `status` is `"in_progress"`: reconcile pending jobs and evidence, then resume the same run regardless of timestamp age. Apply the shared cycle's recovery rules; never delete state or reset original limits because it is old.
     - Read the saved `run_id`, round, reviewer session and pending work unchanged. If a legacy state lacks `run_id`, assign it once and record the migration; old unrelated receipts remain invalid.
     - **Legacy backend migration:** when `reviewer_backend` is absent, retain the pre-Copilot default `codex`; when `requires_external_acquittal` is absent, retain `false`. Record these defaults without running fresh-start backend detection. Continue through the saved backend's existing reply/evidence mechanism.
     - Read the existing cumulative review log and actual pending-job records before choosing the next round. Preserve unfinished work until its outcome is verified.
   - Malformed or conflicting state: preserve it and report the specific recovery issue; do not silently begin a replacement run.
2. Read project narrative documents, memory files, and any prior review documents. **When `COMPACT = true` and compact files exist**: read `findings.md` + `EXPERIMENT_LOG.md` instead of full `review-stage/AUTO_REVIEW.md` and raw logs — saves context window.
3. Read recent experiment results (check output directories, logs)
4. Identify current weaknesses and open TODOs from prior reviews
5. Initialize round counter = 1 (unless recovered from state file)
6. Create/update `review-stage/AUTO_REVIEW.md` with header and timestamp
7. If this is a fresh run with no explicit reviewer directive, initialize
   REVIEWER_BACKEND to `auto`. Step -1 of Round 1 performs activation and uses
   that same challenge for the review. Explicit reviewer directives initialize
   their selected backend and bypass activation. Do not use environment
   heuristics.

### Loop (repeat up to MAX_ROUNDS)

**Step -1 — Resolve the automatic backend and prepare one native challenge:**

- If REVIEWER_BACKEND is `auto`, resolve the native helper and run one root
  `marker` call followed by one root `challenge` call. Use binding
  `<run_id>_r<round>_review_<8-random-hex>` and output
  `review-stage/COPILOT_NATIVE_<run_id>_ROUND_<round>_REVIEW.challenge.json`.
  A bound challenge sets REVIEWER_BACKEND to `copilot-native` and
  NATIVE_CHALLENGE to that path. Exit 3/unbound sets REVIEWER_BACKEND to
  `codex`. Any other failure follows the fail-closed capability rules.
- If REVIEWER_BACKEND is already `copilot-native` (a later round or a resumed
  run), create one fresh marker/challenge pair with the same run-scoped naming
  pattern and set NATIVE_CHALLENGE. An unbound or invalid challenge cannot be
  treated as a verdict or silently relabeled.
- Explicit external or compatibility backends do nothing in this step.

The challenge created here is the challenge consumed by Phase A. **Do not run
another marker/challenge for the same review.** Run-scoped filenames are
append-only audit identities; never pass `--replace` to reuse evidence from an
older invocation.

**Step 0 — Snapshot current-round state:** After Step -1 resolves `auto`, set `round_backend = <current REVIEWER_BACKEND>` and `round_requires_external_acquittal = <current requires_external_acquittal, default false>`. These variables label the backend and obligation that actually governed the CURRENT round. If compatibility-drive escalation occurs later in Phase B.5.1 (`copilot` → codex/manual), the snapshots retain their pre-escalation values while the forward-looking state is updated for the NEXT round. A native dispatch failure is different because no review occurred: replace both snapshots with the external fallback values before that reviewer call, as specified in Phase A. A successful native call never sets the finalizer obligation. Phase E uses only the resulting snapshots when documenting or writing a finalizer receipt.

