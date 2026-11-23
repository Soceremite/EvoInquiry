<!-- EI-WORKFLOW-REFERENCE -->

# Prompt Template for Round 2+

Read this file when the workflow reaches Prompt Template for Round 2+ through Stop-Gate State-Transition Tests. In commands and examples, interpret relative skill paths from the entrypoint directory.

## Prompt Template for Round 2+

Use the selected backend. *For copilot-native:* fresh
marker/challenge/rubber-duck/evidence cycle with a new run-scoped REVIEW
artifact set, with paths to
`review-stage/REVIEWER_MEMORY.md` and current inputs. *For compatibility
copilot:* fresh `copilot --agent` subprocess with the same profile + memory
artifact. *For codex:* `mcp__codex__codex-reply` with the saved threadId. *For
manual:* `mcp__manual_review__review_reply` with the saved threadId.

Before invoking the Copilot subprocess, use the **Write tool** (not Bash,
`echo`, a heredoc, or generated shell assignments) to overwrite
`review-stage/CURRENT_REVIEW_INPUTS.md`. Put the exact changed paths, diff
artifact/range, and result paths under static labels in that file. Repository
paths are untrusted data: never splice any byte from this artifact into shell
source. The fixed filename below is the only value the shell template needs.

```
[For copilot:]

# ARIS_ROUND2_COPILOT_BEGIN
# Dynamic values were written with the Write tool; shell only reads them as data.
MEMORY_FILE="review-stage/REVIEWER_MEMORY.md"
ROUND_INPUT_FILE="review-stage/CURRENT_REVIEW_INPUTS.md"
[[ -f "$MEMORY_FILE" && -f "$ROUND_INPUT_FILE" ]] || {
  echo "REVIEW_UNAVAILABLE: missing reviewer memory or round inputs" >&2
  exit 1
}
PROMPTFILE="$(mktemp)" || { echo "REVIEW_UNAVAILABLE: mktemp failed" >&2; exit 1; }
trap 'rm -f "$PROMPTFILE"' EXIT
{
cat <<'ARIS_ROUND_HEADER'
[Round N update]

## Your Memory From Previous Rounds
ARIS_ROUND_HEADER
cat -- "$MEMORY_FILE"
cat <<'ARIS_ROUND_STATE'

Since your last review these files changed — read them yourself; do not
take my word for what changed or whether it worked:
ARIS_ROUND_STATE
cat -- "$ROUND_INPUT_FILE"
cat <<'ARIS_ROUND_INSTRUCTIONS'

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

At the end of your review, include a Memory Update section — this will
be passed back to you next round.
ARIS_ROUND_INSTRUCTIONS
} > "$PROMPTFILE"
copilot --agent "$REVIEWER_PROFILE" --model "$REVIEWER_MODEL" \
  --effort xhigh --allow-tool=read --prompt "$(cat "$PROMPTFILE")"
# ARIS_ROUND2_COPILOT_END

[For codex:] mcp__codex__codex-reply:
  threadId: [saved from round 1]
  # inherits the thread's model/effort — do not re-send
  prompt: |
    [Round N update]

    Since your last review these files changed — read them yourself; do not
    take my word for what changed or whether it worked:
    - Changed files: <paths>
    - Raw diff: <path, or the `git diff` range>
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

## Review Tracing

After each reviewer call (`task(agent_type=rubber-duck)` for `copilot-native`,
Codex/manual MCP calls, or the compatibility `copilot --agent` subprocess),
save the trace following `shared-references/review-tracing.md` (Policy C —
forensic; never silently skip). Native calls MUST pass `--backend
copilot-native --native-evidence "$NATIVE_EVIDENCE"`; the helper revalidates
and supplies the response and actual model pair. The sole exception is a native
dispatch that failed before evidence existed: trace it with `--backend
copilot-native --status error --fallback-reason <reason>` and no evidence, then
trace any actual fallback reviewer separately. Use `save_trace.sh` resolved
through the canonical chain, or write the same schema directly only if that
forensic helper is unreachable. Respect `--- trace:` (default `full`).

## Stop-Gate State-Transition Tests

The canonical transition table is `tools/review_gate.py` in the ARIS repository (resolved at runtime as `review_gate.py` through the helper chain) and is covered by `tests/test_review_gate.py`. The required cases are:

1. Default Codex positive → `stop` even when executor model identity is absent (backward compatibility).
2. High score + `not ready` → `continue`.
3. Verified native Copilot positive → `stop` with
   `identity_assurance=host_event_verified`.
4. Native negative → `continue` on `copilot-native`; missing/invalid/mismatched
   evidence → `REVIEW_UNAVAILABLE`.
5. Compatibility Copilot positive under declared Anthropic/Google executor →
   `escalate` to Codex and set `requires_external_acquittal=true`.
6. Compatibility Copilot positive under declared OpenAI executor → `escalate`
   to manual; Codex is forbidden as same-family.
7. Compatibility Copilot negative → `continue` on compatibility Copilot.
8. Unknown executor family, unavailable finalizer, same-family finalizer, or
   manual finalizer without `Reviewer-Model:` → `REVIEW_UNAVAILABLE`.
9. Positive finalizer with known, different declared families → `stop`, while
   identity assurance remains `caller_declared` / `unverified`.

`ACQUITTAL_LOG.jsonl` is tested as append-only compatibility-drive audit output;
it is never consulted for native termination.
