<!-- EI-WORKFLOW-REFERENCE -->

# Phase B.6: Debate Protocol (hard + nightmare only)

Read this file when the workflow reaches Phase B.6: Debate Protocol (hard + nightmare only) through Phase C: Implement Fixes (if not stopping). In commands and examples, interpret relative skill paths from the entrypoint directory.

#### Phase B.6: Debate Protocol (hard + nightmare only)

**Skip entirely if `REVIEWER_DIFFICULTY = medium`.**

After parsing the review, the executor gets a chance to **rebut**:

**Step 1 — Executor Rebuttal:**

For each weakness the reviewer identified, the executor writes a structured response:

```markdown
### Rebuttal to Weakness #1: [title]
- **Accept / Partially Accept / Reject**
- **Argument**: [why this criticism is invalid, already addressed, or based on a misunderstanding]
- **Evidence**: [point to specific code, results, or prior round fixes]
```

Rules for the executor's rebuttal:
- Must be honest — do NOT fabricate evidence or misrepresent results
- Can point out factual errors in the review (reviewer misread code, wrong metric, etc.)
- Can argue a weakness is out of scope or would require unreasonable effort
- Maximum 3 rebuttals per round (pick the most impactful to contest)

**Step 2 — Reviewer Rules on Rebuttal:**

Send the executor's rebuttal back to the reviewer for a ruling:

*Hard mode — use the selected backend for the rebuttal step:*

*For copilot-native:* run a fresh marker/challenge and invoke a fresh native
`rubber-duck` Task. Give it paths to `review-stage/REVIEWER_MEMORY.md`, the raw
review response, and `review-stage/ROUND_${ROUND}_REBUTTAL.md`; require it to
verify the cited files itself and return its updated Score/Verdict. Verify this
verdict-bearing ruling with distinct run-scoped
`..._ROUND_<round>_REBUTTAL.challenge.json`, `.evidence.json`, and
`.response.md` artifacts. Use that evidence (not the pre-debate evidence) in
the stop gate and trace.

*For compatibility copilot:* fresh `copilot --agent` subprocess with the same profile + `review-stage/REVIEWER_MEMORY.md` context:
```bash
# Store the generated rebuttal as data; never paste memory/rebuttal text into
# a heredoc body, because either may contain a line matching its delimiter.
MEMORY_FILE="review-stage/REVIEWER_MEMORY.md"
REBUTTAL_FILE="review-stage/ROUND_${ROUND}_REBUTTAL.md"
[[ -f "$MEMORY_FILE" && -f "$REBUTTAL_FILE" ]] || {
  echo "REVIEW_UNAVAILABLE: missing memory or rebuttal artifact" >&2
  exit 1
}
PROMPTFILE="$(mktemp)" || { echo "REVIEW_UNAVAILABLE: mktemp failed" >&2; exit 1; }
trap 'rm -f "$PROMPTFILE"' EXIT
{
cat <<'ARIS_REBUTTAL_HEADER'
[Rebuttal ruling — same reviewer]

## Your Memory From Previous Rounds
ARIS_REBUTTAL_HEADER
cat -- "$MEMORY_FILE"
cat <<'ARIS_REBUTTAL_MIDDLE'

The author rebuts your review:
ARIS_REBUTTAL_MIDDLE
cat -- "$REBUTTAL_FILE"
cat <<'ARIS_REBUTTAL_FOOTER'

For each rebuttal, rule:
- SUSTAINED (author's argument is valid, withdraw this weakness)
- OVERRULED (your original criticism stands, explain why)
- PARTIALLY SUSTAINED (revise the weakness to a narrower scope)

Then update your score if any weaknesses were withdrawn.
Include a Memory Update section at the end of your response.
ARIS_REBUTTAL_FOOTER
} > "$PROMPTFILE"
copilot --agent "$REVIEWER_PROFILE" --model "$REVIEWER_MODEL" \
  --effort xhigh --allow-tool=read --prompt "$(cat "$PROMPTFILE")"
```

*For codex:*
```
mcp__codex__codex-reply:
  threadId: [saved]
  # inherits the thread's model/effort — do not re-send
  prompt: |
    The author rebuts your review:
```

*For manual:* use `mcp__manual_review__review_reply` with the same `threadId` and prompt.

The prompt content:

```
    The author rebuts your review:

    [paste executor's rebuttal]

    For each rebuttal, rule:
    - SUSTAINED (author's argument is valid, withdraw this weakness)
    - OVERRULED (your original criticism stands, explain why)
    - PARTIALLY SUSTAINED (revise the weakness to a narrower scope)

    Then update your score if any weaknesses were withdrawn.
```

*Nightmare mode (codex exec):*
```bash
codex exec "$(cat <<'PROMPT'
You are the same adversarial reviewer. The author rebuts your review:

[paste executor's rebuttal]

VERIFY the author's evidence claims yourself — read the files they reference.
Do NOT take their word for it.

For each rebuttal, rule:
- SUSTAINED (verified and valid)
- OVERRULED (evidence doesn't check out or argument is weak)
- PARTIALLY SUSTAINED (partially valid, narrow the weakness)

Update your score. Update your memory.
PROMPT
)" --skip-git-repo-check 2>&1
```

**Step 3 — Update score and action items** based on the ruling:
- SUSTAINED weaknesses: remove from action items
- OVERRULED: keep as-is
- PARTIALLY SUSTAINED: revise scope

Append the full debate transcript to `review-stage/AUTO_REVIEW.md` under the round's entry.

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

After parsing the score, check if `~/.claude/feishu.json` exists and mode is not `"off"`:
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

