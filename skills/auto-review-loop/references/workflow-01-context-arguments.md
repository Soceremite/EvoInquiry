<!-- EI-WORKFLOW-REFERENCE -->

# Context: $ARGUMENTS

Read this file when the workflow reaches Context: $ARGUMENTS through Reviewer Calling Convention. In commands and examples, interpret relative skill paths from the entrypoint directory.








# Auto Review Loop: Autonomous Research Improvement

> 🔒 **Do not wrap this skill in `/loop`, `/schedule`, or `CronCreate`.** It
> already loops internally (review → fix → re-review) and the reviewer carries
> round-to-round memory in one `threadId` (`codex-reply`). An external timer
> re-enters from the top each tick — fresh `threadId`, reviewer memory reset —
> firing the verdict on wall-clock time instead of on artifact change: zero new
> signal, full token cost. If you want to schedule something, schedule the
> *external wait that precedes it* (experiments done → then run this once). See
> [`shared-references/external-cadence.md`](../../shared-references/external-cadence.md).

Autonomously iterate: review → implement fixes → re-review, until an independent reviewer gives a policy-approved positive assessment or MAX_ROUNDS is reached.

## Context: $ARGUMENTS

## Shared cycle and recovery

Read [research-review-cycle](../../shared-references/research-review-cycle.md)
before iterating or resuming. It owns material-issue closure, cumulative budgets,
state preservation and the common cycle. The backend routing, reviewer memory,
acquittal gate and single receipt append site below remain authoritative.

## Constants

- MAX_ROUNDS = 4
- POSITIVE_THRESHOLD: score >= 6/10 **AND** verdict ∈ {"ready", "almost"} — **both** must hold. This matches the operative Phase-E STOP CONDITION exactly; the verdict vocabulary is {"ready", "almost", "not ready"} (a high score with a "not ready" verdict does NOT stop the loop). Earlier wording here used `or` and a stale verdict set ("accept"/"sufficient"/"ready for submission") — that was an internal inconsistency; the `AND` form is authoritative.
- REVIEW_DOC: `review-stage/AUTO_REVIEW.md` (cumulative log) *(fall back to `./AUTO_REVIEW.md` for legacy projects)*
- REVIEWER_MODEL = `gpt-6-astra` — Default model for the Codex backend. Must be an OpenAI model (e.g., `gpt-6-astra`, `o3`, `gpt-4o`). Manual backend uses a model the user chooses — it must be a recognized model from a different family (OpenAI, Anthropic, Google, DeepSeek, Moonshot/Kimi, Qwen).
- **REVIEWER_BACKEND** — With no reviewer directive, start as `auto`; Step -1 runs exactly one two-call native marker/challenge probe for the first review. A bound Copilot CLI root session uses `copilot-native` (built-in complementary `rubber-duck` subagent); an unbound/non-Copilot host keeps the existing `codex` default. Explicit `— reviewer: codex`, `oracle-pro`, `agy`, or `manual` bypasses the probe and selects that external backend. Explicit `— reviewer: copilot` retains the compatibility `copilot --agent` drive mode and its later Codex/manual finalizer. The native path gets both actual model IDs from host session events; it never needs `COPILOT_CLI` or caller-provided `--executor-model`. See `shared-references/reviewer-routing.md`.
- **OUTPUT_DIR = `review-stage/`** — All review-stage outputs go here. Create the directory if it doesn't exist.
- **HUMAN_CHECKPOINT = false** — When `true`, pause after each round's review (Phase B) and present the score + weaknesses to the user. Wait for user input before proceeding to Phase C. The user can: approve the suggested fixes, provide custom modification instructions, skip specific fixes, or stop the loop early. When `false` (default), the loop runs fully autonomously.
- **COMPACT = false** — When `true`, (1) read `EXPERIMENT_LOG.md` and `findings.md` instead of parsing full logs on session recovery, (2) append key findings to `findings.md` after each round.
- **REVIEWER_DIFFICULTY = medium** — Controls how adversarial the reviewer is. Three levels:
  - `medium` (default): Current behavior — MCP-based review, the executor controls what context the reviewer sees.
  - `hard`: Adds **Reviewer Memory** (the reviewer tracks its own suspicions across rounds) + **Debate Protocol** (the executor can rebut, the reviewer rules).
  - `nightmare`: Everything in `hard` + **Codex exec reviewer reads the repo directly** via `codex exec` (the executor cannot filter what the reviewer sees) + **Adversarial Verification** (the reviewer independently checks if code matches claims).
- **RENDER_HTML = true** — When `true` (default), auto-render `review-stage/AUTO_REVIEW.md` to HTML on loop termination via `/render-html`. Uses `--no-review` for structural conversion of the recorded assessment; rendering does not add or change review acceptance. Preserve unavailable or incomplete reviews as BLOCKED. Set `false` to skip, or pass `— render html: false`.

> ⚠️ **Nightmare + Manual incompatibility**: If `REVIEWER_BACKEND = manual` and `REVIEWER_DIFFICULTY = nightmare`, STOP with:
> "difficulty: nightmare requires Codex CLI / codex exec and is not compatible with --reviewer: manual. Use difficulty: hard, or switch reviewer to codex."

> 💡 Override: `/auto-review-loop "topic" — compact: true, human checkpoint: true, difficulty: hard`

## Reviewer Calling Convention

When calling the reviewer, branch on REVIEWER_BACKEND:

**If no `--reviewer:` directive was supplied:**
  Set REVIEWER_BACKEND to `auto`. At Step -1 of the first round, resolve
  `copilot_native_evidence.py` using the canonical four-layer helper chain.
  Generate a fresh binding `<run_id>_r<round>_review_<8-random-hex>` and invoke
  `marker`, wait, then invoke `challenge` as **two distinct root Bash calls**.
  Put the literal binding and concrete resolved helper path in both calls;
  Copilot Bash calls do not share variables. If the challenge binds, set
  REVIEWER_BACKEND to `copilot-native` and use that same challenge for the
  first review. Do not issue a second activation challenge in Phase A. If it
  exits 3 because no current Copilot root session is bound, use `codex`.
  Explicit reviewer directives bypass this probe. If the helper is missing,
  native acceptance is unavailable; use Codex only if that external backend
  is positively available, otherwise emit `REVIEW_UNAVAILABLE`.

**If REVIEWER_BACKEND = `copilot-native`:**
  Read the challenge nonce and host-reported executor model. Invoke the host's
  native `task` tool with `agent_type: rubber-duck`; do not start a subprocess
  and do not specify a reviewer model. The prompt contains the exact standalone
  `ARIS_REVIEW_NONCE=<nonce>` line, artifact/diff paths, the output contract,
  and (round 2+) `review-stage/REVIEWER_MEMORY.md`. It contains no executor
  summary or fix narrative. After the task completes, invoke
  `copilot_native_evidence.py verify` to create the evidence and raw-response
  artifacts. The verifier must observe one successful linked rubber-duck
  lifecycle and known, different host-reported model families.

  Pass the evidence to both `review_gate.py --native-evidence` and
  `save_trace.sh --backend copilot-native --native-evidence`. A qualifying
  native positive may stop directly; no external finalizer is needed. A native
  negative continues with a fresh marker/challenge/subagent next round. Every
  verdict-bearing native call—including a hard-mode rebuttal ruling—gets one
  unique `<run_id, round, purpose>` artifact set and exactly one challenge.
  Missing, same/unknown-family, malformed, stale, or mismatched evidence is
  never a verdict. If native complementary dispatch is unavailable, fall back
  only to a positively available opposite-family backend: Anthropic/Google
  executor → Codex; OpenAI executor → manual with a reported non-OpenAI model.
  Otherwise emit `REVIEW_UNAVAILABLE`. Full protocol:
  `shared-references/reviewer-routing.md`.

**If REVIEWER_BACKEND = `copilot`:**
  **Require `--executor-model`:** if not provided → emit `REVIEW_UNAVAILABLE`.
  **Determine executor family** from `--executor-model` (see reviewer-routing.md).
  **Router picks opposite-family profile:**
  - executor_family=openai → profile="aris-reviewer-claude" (anthropic)
  - executor_family=anthropic → profile="aris-reviewer-openai" (openai)
  - executor_family=google → profile="aris-reviewer-openai" (openai, default cross)
  - executor_family=unknown → `REVIEW_UNAVAILABLE` (fail closed).
  **Verify the profile file** exists at `.github/agents/<profile>.agent.md`.
  If missing → `REVIEW_UNAVAILABLE`.
  **Read its `model:` field** into `REVIEWER_MODEL`, derive `reviewer_family`
  from that model string, and verify it differs from `executor_family`. Pass
  the same value through subprocess `--model`; never trust a caller-supplied
  family label or profile-only pinning under an Auto session.
  **Identity assurance:** `--executor-model` is caller-declared routing input,
  not runtime attestation. Record `executor_model_source: caller-declared`, the
  derived `family_relation`, and `independence_verified: unverified`. A pair of
  different model strings must never be promoted to independently verified.
  **Capability gate:** `copilot --help` must advertise `--model`, `--effort`,
  and `--allow-tool`; otherwise emit `REVIEW_UNAVAILABLE`.
  **Use the `copilot --agent` subprocess** (documented Copilot CLI form)
  with the selected profile, `--model "$REVIEWER_MODEL"`, `--effort xhigh`,
  and `--allow-tool=read` for each review call.
  **Multi-round:** each round is a fresh `copilot --agent` call with the same
  profile; reviewer memory is carried via `review-stage/REVIEWER_MEMORY.md` artifact.
  If `copilot` CLI is unavailable → `REVIEW_UNAVAILABLE` for that drive round;
  do not silently substitute another transport. A later positive Copilot
  verdict still requires the separately documented Codex/manual finalizer.
  See `shared-references/reviewer-routing.md` for the full copilot contract.

**If REVIEWER_BACKEND = `codex`:**
  Use `mcp__codex__codex` for new review threads.
  Use `mcp__codex__codex-reply` for follow-up rounds (reuse threadId).

**If REVIEWER_BACKEND = `manual`:**
  Use `mcp__manual_review__review` for new review threads with:
    prompt: [exact same prompt that would go to Codex]
    config: {"model_reasoning_effort": "xhigh", "executor_model": "<actual executor model>", "require_reviewer_model": true}
  Save the returned `threadId`.
  Use `mcp__manual_review__review_reply` for follow-up rounds with:
    threadId: [saved manual-review threadId]
    prompt: [follow-up prompt]
    config: {"model_reasoning_effort": "xhigh", "executor_model": "<actual executor model>", "require_reviewer_model": true}
  A verdict-bearing manual response MUST begin with
  `Reviewer-Model: <exact-model-id>`. Derive `reviewer_family` from that model
  identity. Missing, unknown, or same-family identity cannot acquit; for a
  mandatory escalation, emit `REVIEW_UNAVAILABLE` rather than guessing.

Prompt fidelity: the manual review task must be exactly the same text that Codex would receive; the transport may add only the required `Reviewer-Model:` response-format instruction.
Review tracing applies to every backend. Native traces are populated from the
revalidated host-event artifact rather than caller model declarations.

