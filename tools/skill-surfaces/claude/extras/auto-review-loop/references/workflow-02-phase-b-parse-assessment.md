<!-- EI-WORKFLOW-REFERENCE -->

# Phase B: Parse Assessment

Read this file when the workflow reaches Phase B: Parse Assessment through Status. In commands and examples, interpret relative skill paths from the entrypoint directory.

#### Phase B: Parse Assessment

**CRITICAL: Save the FULL raw response** from the external reviewer verbatim (store in a variable for Phase E). Do NOT discard or summarize — the raw text is the primary record.

Then extract structured fields:
- **Score** (numeric 1-10)
- **Verdict** ("ready" / "almost" / "not ready")
- **Action items** (ranked list of fixes)

#### Phase B.5: Reviewer Memory Update

After parsing the assessment, update `review-stage/REVIEWER_MEMORY.md`. Copilot backend depends on this file for round-to-round continuity (every round is a fresh process), so the update runs regardless of `REVIEWER_DIFFICULTY`:

## Your Reviewer Memory (persistent across rounds)

Pass this file back to the reviewer in the next round so it can track its own suspicions.

```markdown
# Reviewer Memory

## Round 1 — Score: X/10
- **Suspicion**: [what the reviewer flagged]
- **Unresolved**: [concerns not yet addressed]
- **Patterns**: [recurring issues the reviewer noticed]

## Round 2 — Score: X/10
- **Previous suspicions addressed?**: [yes/no for each, with reviewer judgment]
- **New suspicions**: [...]
- **Unresolved**: [carried forward + new]
```

Rules:
- Append each round; never delete prior rounds.
- If the reviewer response includes a `Memory update` section, copy it verbatim.
- If the score REGRESSES round-to-round, don't just write a new memory line:
  diff the two rounds' raw `.response.md` files in `.ei/traces/` first and
  find the exact criterion that flipped (see `shared-references/review-tracing.md`
  § *Debugging With Traces*). The memory file is a summary; the trace is evidence.
- This file is passed back to the reviewer in the next round's Phase A.

#### Phase B.5.1: Stop-Evaluation Gate

**STOP CONDITION**: If score >= 6 AND verdict ∈ {"ready", "almost"} (exact match — "not ready" does NOT qualify), decide to stop and continue through Phase E. **Do not write a receipt here**; Phase E is the single append site.

This evaluation runs AFTER Phase B.5 so the terminal-round memory is always appended to REVIEWER_MEMORY.md before exit.

#### Phase B.6: Debate Protocol (hard + nightmare only)

Skip entirely if `REVIEWER_DIFFICULTY = medium`.

After parsing the review, Codex writes a structured rebuttal for up to three high-impact weaknesses:

```markdown
### Rebuttal to Weakness #1: [title]
- **Accept / Partially Accept / Reject**
- **Argument**: [why this criticism is valid, invalid, already addressed, or out of scope]
- **Evidence**: [specific code, result file, log, prior-round fix, or paper section]
```

Send the rebuttal to the same reviewer via `mcp__claude-review__review_reply_start`:

```
mcp__claude-review__review_reply_start:
  threadId: [saved reviewer id]
  prompt: |
    Please rule on the author's rebuttal below.
    For each contested weakness, decide: accepted / partially accepted / rejected.
    If rejected, state the minimum evidence or change required.

    [paste rebuttal + evidence]
```

After this start call, immediately save the returned `jobId` and poll `mcp__claude-review__review_status` with a bounded `waitSeconds` until `done=true`. Treat the completed status payload's `response` as the reviewer output, and save the completed `threadId` for any follow-up round.

Record a `### Debate Transcript (hard + nightmare only)` section in `review-stage/AUTO_REVIEW.md`. Only mark a weakness resolved if the reviewer accepts the rebuttal.

### Debate Transcript (hard + nightmare only)

In the round log, preserve the rebuttal, reviewer ruling, accepted objections, rejected objections, and any required follow-up evidence.

#### Human Checkpoint (if enabled)

**Skip this step entirely if `HUMAN_CHECKPOINT = false`.**

When `HUMAN_CHECKPOINT = true`, present the review results and wait for user input:

```
📋 Round N/MAX_ROUNDS review complete.

Score: X/10 — [verdict]
Top weaknesses:
1. [weakness 1]
2. [weakness 2]
3. [weakness 3]

Suggested fixes:
1. [fix 1]
2. [fix 2]
3. [fix 3]

Options:
- Reply "go" or "continue" → implement all suggested fixes
- Reply with custom instructions → implement your modifications instead
- Reply "skip 2" → skip fix #2, implement the rest
- Reply "stop" → end the loop, document current state
```

Wait for the user's response. Parse their input:
- **Approval** ("go", "continue", "ok", "proceed"): proceed to Phase C with all suggested fixes
- **Custom instructions** (any other text): treat as additional/replacement guidance for Phase C. Merge with reviewer suggestions where appropriate
- **Skip specific fixes** ("skip 1,3"): remove those fixes from the action list
- **Stop** ("stop", "enough", "done"): terminate the loop, jump to Termination

#### Feishu Notification (if configured)

After parsing the score, check if `~/.codex/feishu.json` exists and mode is not `"off"`:
- Send a `review_scored` notification: "Round N: X/10 — [verdict]" with top 3 weaknesses
- If **interactive** mode and verdict is "almost": send as checkpoint, wait for user reply on whether to continue or stop
- If config absent or mode off: skip entirely (no-op)

#### Phase C: Implement Fixes (if not stopping)

For each action item (highest priority first):

1. **Code changes**: Write/modify experiment scripts, model code, analysis scripts
2. **Run experiments**: Deploy to GPU server via SSH + screen/tmux
3. **Analysis**: Run evaluation, collect results, update figures/tables
4. **Documentation**: Update project notes and review document

Prioritization rules:
- Skip fixes requiring excessive compute (flag for manual follow-up)
- Skip fixes requiring external data/models not available
- Prefer reframing/analysis over new experiments when both address the concern
- Add a metric only when it resolves a material question within authorization and budget; retain original primary outcomes

#### Phase D: Wait for Results

If experiments were launched:
- Monitor remote sessions for completion
- Collect results from output files and logs
- **Training quality check** — if W&B is configured, invoke `/training-check` to verify training was healthy (no NaN, no divergence, no plateau). If W&B is not available, skip silently.

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

[Paste the COMPLETE raw response from the external reviewer here — verbatim, unedited.
This is the authoritative record. Do NOT truncate or paraphrase.]

</details>

### Actions Taken
- [what was implemented/changed]

### Results
- [experiment outcomes, if any]

### Status
- [continuing to round N+1 / stopping]
```

**Write `review-stage/REVIEW_STATE.json`** with current `run_id`, round, completed threadId, score, verdict, and any pending experiments. The `run_id` field MUST persist unchanged from initialization; do NOT regenerate it per round.

**If score >= 6 AND verdict ∈ {"ready", "almost"} AND material-issue closure is verified:** append an acquittal line to `review-stage/ACQUITTAL_LOG.jsonl`:
```
{"run_id":"<current-run_id>","round":<N>,"backend":"claude-review","effort":"high-rigor","verdict":"<ready|almost>","score":<score>,"trace_id":"<skill>/<YYYY-MM-DD>_run<NN>","timestamp":"<ISO8601>"}
```
Use `>>` (append), never `>`. The `trace_id` must be the actual trace directory relative to `.ei/traces/` (for example `auto-review-loop/2026-07-13_run01`), not a fabricated `trace_...` identifier.

**Append to `findings.md`** (when `COMPACT = true`): one-line entry per key finding this round.

```markdown
- [Round N] [positive/negative/unexpected]: [one-sentence finding] (metric: X.XX → Y.YY)
```

Increment round counter → back to Phase A.

