<!-- EI-WORKFLOW-REFERENCE -->

# Phase A: Review

Read this file when the workflow reaches Phase A: Review through Instructions. In commands and examples, interpret relative skill paths from the entrypoint directory.

#### Phase A: Review

**Route by REVIEWER_BACKEND and REVIEWER_DIFFICULTY.**

If REVIEWER_BACKEND = `copilot-native`, execute one fresh native cycle:

1. Use NATIVE_CHALLENGE prepared by Step -1. It must be the run-scoped
   `..._ROUND_<round>_REVIEW.challenge.json` artifact created in this round.
   Do not issue a second marker/challenge here.
2. Read the returned nonce. Call the host Task tool with
   `agent_type: rubber-duck`, a fresh name, and a prompt whose first line is
   exactly `ARIS_REVIEW_NONCE=<nonce>`. Supply paths to claims, methods/code,
   raw results, diff/current inputs, and reviewer memory—not an executor
   summary. Require exactly one `Score: X/10` and `Verdict: ready | almost |
   not ready` plus ranked weaknesses/minimum fixes/memory update. Do not pass a
   model override: Copilot's complementary strategy selects it.
3. After Task completes, run `python3 "<resolved-helper>" verify --challenge
   "$NATIVE_CHALLENGE" --output
   "review-stage/COPILOT_NATIVE_<run_id>_ROUND_<round>_REVIEW.evidence.json"
   --response-output
   "review-stage/COPILOT_NATIVE_<run_id>_ROUND_<round>_REVIEW.response.md"` in a new root Bash
   call. Use only the extracted response artifact for Phase B.
4. Exit 10 (same/unknown family), incomplete lifecycle, invalid response, or
   unavailable complementary model is not a review. Apply the opposite-family
   fallback table in `reviewer-routing.md`; if none is positively available,
   emit `REVIEW_UNAVAILABLE`. Never emulate rubber-duck using a slash prompt,
   `copilot --agent rubber-duck`, or generic subagent. Trace a pre-evidence
   dispatch failure as `--backend copilot-native --status error` without
   evidence, then trace the actual fallback separately; this error trace has no
   authority at the stop gate. Before fallback, run
   `copilot_native_evidence.py validate-challenge --challenge
   "$NATIVE_CHALLENGE"` and take EXECUTOR_MODEL only from that output. Then:
   - Anthropic/Google executor + usable Codex → set both REVIEWER_BACKEND and
     `round_backend` to `codex` before the external call.
   - OpenAI executor + manual reviewer reporting a known non-OpenAI model → set
     both values to `manual` before the external call.
   - Set `round_requires_external_acquittal=true` for either fallback, clear
     NATIVE_EVIDENCE, and pass the validated executor model plus the fallback's
     resolved reviewer model to `review_gate.py`. This deliberately uses the
     stricter external-finalizer branch, which re-derives and enforces different
     families. If the external call does not return a usable review, emit
     `REVIEW_UNAVAILABLE`.

If REVIEWER_BACKEND = `copilot`, enforce opposite-family routing from the declared executor identity FIRST:
- Require `--executor-model <model>` parameter. If missing → `REVIEW_UNAVAILABLE`. Stop.
- Derive `executor_family` from `executor_model`:
  - Model names containing `gpt`, `o1`, `o3`, `o4`, `chatgpt` → `openai`
  - Model names containing `claude`, `sonnet`, `opus`, `haiku` → `anthropic`
  - Model names containing `gemini` → `google`
  - Anything else → `unknown`
- If `executor_family` is `unknown` → `REVIEW_UNAVAILABLE` (fail closed). Stop.
- Treat this as route selection, not attestation: persist
  `executor_model_source: caller-declared`; a derived `family_relation:
  different` remains `independence_verified: unverified` unless a future
  stable runtime signal independently proves the parent executor model.
- Router picks opposite-family profile:
  - `openai` → `"aris-reviewer-claude"` (anthropic, forced cross-family)
  - `anthropic` → `"aris-reviewer-openai"` (openai, forced cross-family)
  - `google` → `"aris-reviewer-openai"` (openai default)
- Verify the profile file exists at `.github/agents/<profile>.agent.md`.
  If missing → `REVIEW_UNAVAILABLE`. Stop.
- Read the profile's first frontmatter `model:` value, derive its family, and
  verify it is known and differs from `executor_family`. If not, fail closed.
- Verify `copilot --help` exposes `--model`, `--effort`, and `--allow-tool`.
  Older/unpinned CLIs are `REVIEW_UNAVAILABLE`.
- Adapt the Codex MCP calls below to use the **`copilot --agent`** subprocess
  (documented Copilot CLI form):
  - Replace `mcp__codex__codex` with `copilot --agent "<profile>" --model "<parsed-model>" --effort xhigh --allow-tool=read --prompt "..."`
  - Each round is a fresh `copilot --agent` call with the same profile +
    `review-stage/REVIEWER_MEMORY.md` artifact carrying round-to-round state.
  - The prompt text and Review Tracing are identical to the Codex path.
  - If `copilot` CLI is unavailable → `REVIEW_UNAVAILABLE` (no MCP fallback).
  - If `REVIEWER_DIFFICULTY = nightmare`, skip Copilot (nightmare requires Codex
    exec): emit `REVIEW_UNAVAILABLE`.
  See `shared-references/reviewer-routing.md`.

**If REVIEWER_BACKEND ∈ {codex, manual}:** use the backend-specific MCP call per the
Reviewer Calling Convention above. The prompt text is the same regardless of backend.

##### Medium (default) — MCP Review

Send comprehensive context to the independent reviewer using the selected backend.

*For codex backend:*

```
mcp__codex__codex:
  model: gpt-6-astra
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
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

*For manual backend:* use `mcp__manual_review__review` with the `prompt` text above and `config: {"model_reasoning_effort": "xhigh", "executor_model": "<actual executor model>", "require_reviewer_model": true}`. Save the returned `threadId`.

If this is round 2+, use `mcp__codex__codex-reply` (codex) or `mcp__manual_review__review_reply` (manual) with the saved threadId.

##### Hard — MCP Review + Reviewer Memory

Same as medium, but **prepend Reviewer Memory** to the prompt. Use the selected backend.

*For codex backend:*

```
mcp__codex__codex:
  model: gpt-6-astra
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    [Round N/MAX_ROUNDS of autonomous review loop]

    ## Your Reviewer Memory (persistent across rounds)
    [Paste full contents of review-stage/REVIEWER_MEMORY.md here]

    IMPORTANT: You have memory from prior rounds. Check whether your
    previous suspicions were genuinely addressed or merely sidestepped.
    The author (the executor model) controls what context you see — be skeptical
    of convenient omissions.

    Review directly from the artifacts (paths below) — read the files yourself:
    - Claims / methods / code: <path(s)>
    - Raw results: <path(s)>
    - Changed since last round: <changed-file paths> (read the raw diff)

    Please act as a senior ML reviewer (NeurIPS/ICML level).
    1. Score this work 1-10 for a top venue
    2. List remaining critical weaknesses (ranked by severity)
    3. For each weakness, specify the MINIMUM fix
    4. State clearly: is this READY for submission? Yes/No/Almost
    5. **Memory update**: List any new suspicions, unresolved concerns,
       or patterns you want to track in future rounds.

    Be brutally honest. Actively look for things the author might be hiding.

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

##### Nightmare — Codex Exec (GPT reads repo directly)

**Do NOT use MCP.** Instead, let GPT access the repo autonomously via `codex exec`:

```bash
codex exec "$(cat <<'PROMPT'
You are an adversarial senior ML reviewer (NeurIPS/ICML level).
This is Round N/MAX_ROUNDS of an autonomous review loop.

## Your Reviewer Memory (persistent across rounds)
[Paste full contents of review-stage/REVIEWER_MEMORY.md]

## Instructions
You have FULL READ ACCESS to this repository. The author (the executor model) does NOT
control what you see — explore freely. Your job is to find problems the
author might hide or downplay.

DO THE FOLLOWING:
1. Read the experiment code, results files (JSON/CSV), and logs YOURSELF
2. Verify that reported numbers match what's actually in the output files
3. Check if evaluation metrics are computed correctly (ground truth, not model output)
4. Look for cherry-picked results, missing ablations, or suspicious hyperparameter choices
5. Read NARRATIVE_REPORT.md or review-stage/AUTO_REVIEW.md for the author's claims — then verify each against code

OUTPUT FORMAT:
- Score: X/10
- Verdict: ready / almost / not ready
- Verified claims: [which claims you independently confirmed]
- Unverified/false claims: [which claims don't match the code or results]
- Weaknesses (ranked): [with MINIMUM fix for each]
- Memory update: [new suspicions and patterns to track next round]

Be adversarial. Trust nothing the author tells you — verify everything yourself.

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
PROMPT
)" --skip-git-repo-check 2>&1
```

**Key difference**: In nightmare mode, GPT independently reads code, result files, and logs. Claude cannot filter or curate what GPT sees. This is the closest analog to a real hostile reviewer who reads your actual paper + supplementary materials.

