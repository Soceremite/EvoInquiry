<!-- EI-WORKFLOW-REFERENCE -->

# Phase B: Parse Assessment

Read this file when the workflow reaches Phase B: Parse Assessment through Phase B.5.1: Stop-Evaluation Gate. In commands and examples, interpret relative skill paths from the entrypoint directory.

#### Phase B: Parse Assessment

**CRITICAL: Save the FULL raw response** from the reviewer verbatim (store in a variable for Phase E). For `copilot-native`, this must be the response artifact extracted by the evidence helper, never text copied by the executor. Do NOT discard or summarize — the raw text is the primary record.

Then extract structured fields:
- **Score** (numeric 1-10)
- **Verdict** ("ready" / "almost" / "not ready")
- **Action items** (ranked list of fixes)

#### Phase B.5: Reviewer Memory Update

After parsing the assessment, append to the canonical memory artifact at `review-stage/REVIEWER_MEMORY.md`. Both Copilot backends depend on this file for round-to-round continuity (each native subagent or compatibility subprocess is fresh), so the update runs regardless of `REVIEWER_DIFFICULTY`. No project-root fallback is permitted; create `review-stage/` before the first append:

```markdown
# Reviewer Memory

## Round 1 — Score: X/10

### Raw Reviewer Response (verbatim)
[Paste the COMPLETE raw reviewer response here — never summarized or curated by the executor.]

### Memory Update
[Reviewer's own memory update section, if provided — verbatim.]
- **Suspicion**: [what the reviewer flagged]
- **Unresolved**: [concerns not yet addressed]
- **Patterns**: [recurring issues the reviewer noticed]

---

## Round 2 — Score: X/10

### Raw Reviewer Response (verbatim)
[Paste the COMPLETE raw reviewer response here.]

### Memory Update
- **Previous suspicions addressed?**: [yes/no for each, with reviewer's judgment]
- **New suspicions**: [...]
- **Unresolved**: [carried forward + new]

---
```

**Rules**:
- **Append-only — never delete, never truncate.** The file is a reviewer-owned audit trail. The executor must never summarize, curate, or edit prior rounds' content. Append the reviewer's full raw response for this round verbatim, then append a memory update section if the reviewer provided one.
- Each round's append must be the reviewer's own words — if the reviewer's response includes a "Memory update" section, copy it verbatim as a `## Round N — Memory Update` subsection after the raw response.
- This file is passed back to the reviewer in the next round's Phase A — it is the reviewer's persistent memory.
- **Record the file's SHA-256 hash before each reviewer call** and pass it to `save_trace.sh` via `--memory-hash`. Hash the memory as supplied to the call (pre-call artifact), not the post-append version, so the trace proves which memory was in play for that invocation.
- **If the score REGRESSES round-to-round**, don't just write a new memory line:
  diff the two rounds' raw `.response.md` files in `.ei/traces/` first and find
  the exact criterion that flipped (see `shared-references/review-tracing.md`
  § *Debugging With Traces*). The memory file is a summary; the trace is evidence.

#### Phase B.5.1: Stop-Evaluation Gate

**STOP CONDITION — branch by `round_backend` (the backend that actually ran this round), never by the forward-looking `REVIEWER_BACKEND`. Use the executable transition table in `review_gate.py`; resolve it through the canonical helper chain in `shared-references/integration-contract.md` §2. Its JSON `decision` and `next_backend` fields are authoritative. If the helper cannot be resolved or executed, emit `REVIEW_UNAVAILABLE`; do not improvise a transition.**

Invoke the gate once per completed round. Pass model strings only—the helper
derives families internally and does not accept caller-supplied family labels.
Backend availability must be positively established from the current host's
tool configuration; both finalizers default to unavailable:

```bash
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.ei/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.ei/repo" 2>/dev/null) || true
fi
REVIEW_GATE=".ei/tools/review_gate.py"
[ -f "$REVIEW_GATE" ] || REVIEW_GATE="tools/review_gate.py"
[ -f "$REVIEW_GATE" ] || { [ -n "${ARIS_REPO:-}" ] && REVIEW_GATE="$ARIS_REPO/tools/review_gate.py"; }
[ -f "$REVIEW_GATE" ] || REVIEW_GATE=""
[ -n "$REVIEW_GATE" ] || { echo "REVIEW_UNAVAILABLE: review_gate.py not resolved" >&2; exit 1; }

GATE_REVIEWER_MODEL="${REPORTED_REVIEWER_MODEL:-${REQUESTED_REVIEWER_MODEL:-${REVIEWER_MODEL:-}}}"
GATE_ARGS=(
  --round-backend "$round_backend"
  --score "$SCORE"
  --verdict "$VERDICT"
  --executor-model "${EXECUTOR_MODEL:-}"
  --reviewer-model "$GATE_REVIEWER_MODEL"
)
if [[ "$round_backend" == "copilot-native" ]]; then
  [[ -n "${NATIVE_EVIDENCE:-}" ]] || {
    echo "REVIEW_UNAVAILABLE: native round has no evidence artifact" >&2
    exit 1
  }
  GATE_ARGS+=(--native-evidence "$NATIVE_EVIDENCE")
fi
if [[ "$round_requires_external_acquittal" == "true" ]]; then
  GATE_ARGS+=(--requires-external-acquittal)
fi
if [[ "${CODEX_AVAILABLE:-false}" == "true" ]]; then
  GATE_ARGS+=(--codex-available)
fi
if [[ "${MANUAL_AVAILABLE:-false}" == "true" ]]; then
  GATE_ARGS+=(--manual-available)
fi
if [[ "${MANUAL_IDENTITY_REPORTED:-false}" == "true" ]]; then
  GATE_ARGS+=(--manual-identity-reported)
fi
GATE_JSON=$(python3 "$REVIEW_GATE" "${GATE_ARGS[@]}") || {
  echo "REVIEW_UNAVAILABLE: review gate execution failed" >&2
  exit 1
}
```

Parse `GATE_JSON` as JSON; never infer a transition from the helper's prose
`reason`. A `review_unavailable` decision is terminal. Copy `next_backend` and
`requires_external_acquittal` into forward-looking state for `escalate` or
`continue`; only `stop` enters the successful termination path.

- **Default Codex compatibility (`round_backend = codex`, `round_requires_external_acquittal = false`):** score >= 6 AND verdict ∈ {"ready", "almost"} stops exactly as it did before this Copilot integration. Executor identity is advisory trace metadata and may be absent; do not turn a valid default-Codex positive verdict into `REVIEW_UNAVAILABLE`. This path does not write an external-finalizer receipt.
- **Existing Oracle/Agy routes:** when explicitly selected outside a Copilot-finalizer state, their qualifying positive verdicts retain the same pre-Copilot stop behavior. They are not valid substitutes once `requires_external_acquittal=true`; that state permits only Codex/manual.
- **Explicit manual backend:** a positive verdict still requires the response's exact `Reviewer-Model:` header. Missing identity is `REVIEW_UNAVAILABLE`.
- **Native Copilot round (`round_backend = copilot-native`):** the evidence
  artifact is mandatory and revalidated by the gate. Its response-derived
  Score/Verdict must equal the CLI fields. A qualifying positive returns
  `decision: stop` with `identity_assurance: host_event_verified`; a negative
  returns `continue` on `copilot-native`. No external-finalizer state is set.
- **Compatibility Copilot drive round (`round_backend = copilot`):** this path never stops the loop. A negative verdict continues on compatibility Copilot. A positive verdict returns `decision: escalate`, sets `requires_external_acquittal: true`, and chooses the next backend from the caller-declared executor family:
  - `anthropic` or `google` → Codex when available, otherwise manual;
  - `openai` → manual only (Codex would be same-family);
  - `unknown` or no policy-approved finalizer → `REVIEW_UNAVAILABLE`.
- **External-finalizer round (`round_requires_external_acquittal = true`):** Codex/manual may stop on a qualifying positive verdict only when the model strings derive to known, different families; manual also requires its reported model header. This is fail-closed route consistency, not independent executor attestation. Record `identity_assurance: caller_declared` and `independence_verified: "unverified"`. A negative finalizer verdict continues on the same finalizer backend with the obligation still true.

On compatibility Copilot escalation, update the forward-looking `reviewer_backend` and `requires_external_acquittal` in `REVIEW_STATE.json`; keep `round_backend` and `round_requires_external_acquittal` unchanged for Phase E. Once a finalizer returns a qualifying positive verdict, set the forward flag to false and stop. `ACQUITTAL_LOG.jsonl` is an append-only audit receipt, never an input that lets a later compatibility Copilot verdict stop the loop. Native evidence is evaluated directly and never consults that log.

This evaluation runs AFTER Phase B.5 so the terminal-round memory is always appended to `review-stage/REVIEWER_MEMORY.md` before exit.

