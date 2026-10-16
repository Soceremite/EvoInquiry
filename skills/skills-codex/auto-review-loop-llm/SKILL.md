---
name: "auto-review-loop-llm"
description: "Run iterative research review and revision with an OpenAI-compatible LLM API. Use when that reviewer backend is requested; requires llm-chat or API setup."
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
<!-- EVO-INQUIRY:END -->


# Auto Review Loop (Generic LLM): Autonomous Research Improvement

Autonomously iterate: review → implement fixes → re-review, until the external reviewer gives a positive assessment or MAX_ROUNDS is reached.

## Context: $ARGUMENTS

## Evidence closure and bounded stopping

Scores and verdicts remain required interface fields. A positive threshold is
necessary, and every material issue must also have a checked disposition: fixed
with evidence, or excluded with a specific, evidenced scope reason. Reviewer
agreement alone does not resolve an issue. Keep strengths that the evidence
supports; do not invent objections to make another round appear useful.

Apply this closure condition at every positive stop and acquittal append below.
An unresolved critical issue prevents a positive receipt even when the score is
high. Preserve existing independent-review requirements and same-family
provisional status. File checks do not establish scientific support.

Before iterating, use the authorized round, time, experiment and cost budgets.
Track which decision-relevant uncertainty each action can resolve. Stop when a
budget is reached or successive rounds produce no new evidence or actionable
change; record the reason and remaining unknowns. A budget/stall/user stop is
completion of the loop, not research acceptance, and grants no acquittal.
Never hide an unfavorable primary result by adding a favorable metric or by
renaming the original hypothesis. Label any exploratory reframing explicitly.

## Constants

- MAX_ROUNDS = 4
- POSITIVE_THRESHOLD: score >= 6/10 AND verdict ∈ {"ready", "almost"} — both must hold, matching the operative STOP CONDITION below. Verdict vocabulary is {"ready", "almost", "not ready"}. (Earlier wording used "or" + a stale verdict set; the AND form is authoritative.)
- REVIEW_DOC: `review-stage/AUTO_REVIEW.md` (cumulative log) *(fall back to `./AUTO_REVIEW.md` for legacy projects)*

## LLM Configuration

This skill uses **any OpenAI-compatible API** for external review via the `llm-chat` MCP server.

### Configuration via MCP Server (Recommended)

Add to `~/.codex/settings.json`:

```json
{
  "mcpServers": {
    "llm-chat": {
      "command": "/usr/bin/python3",
      "args": ["/Users/yourname/.codex/mcp-servers/llm-chat/server.py"],
      "env": {
        "LLM_API_KEY": "your-api-key",
        "LLM_BASE_URL": "https://api.deepseek.com/v1",
        "LLM_MODEL": "deepseek-chat"
      }
    }
  }
}
```

### Supported Providers

| Provider | LLM_BASE_URL | LLM_MODEL |
|----------|--------------|-----------|
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o`, `o3` |
| **DeepSeek** | `https://api.deepseek.com/v1` | `deepseek-chat`, `deepseek-reasoner` |
| **MiniMax** | `https://api.minimax.io/v1` | `MiniMax-M3` |
| **Kimi (Moonshot)** | `https://api.moonshot.cn/v1` | `moonshot-v1-8k`, `moonshot-v1-32k` |
| **ZhiPu (GLM)** | `https://open.bigmodel.cn/api/paas/v4` | `glm-4`, `glm-4-plus` |
| **SiliconFlow** | `https://api.siliconflow.cn/v1` | `Qwen/Qwen2.5-72B-Instruct` |
| **阿里云百炼** | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-max` |
| **零一万物** | `https://api.lingyiwanwu.com/v1` | `yi-large` |

## API Call Method

**Primary: MCP Tool**

```
mcp__llm-chat__chat:
  message: |
    [Review prompt content]
  model: "deepseek-chat"
  system: "You are a senior ML reviewer..."
```

**Fallback: curl**

```bash
curl -s "${LLM_BASE_URL}/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${LLM_API_KEY}" \
  -d '{
    "model": "${LLM_MODEL}",
    "messages": [
      {"role": "system", "content": "You are a senior ML reviewer..."},
      {"role": "user", "content": "[review prompt]"}
    ],
    "max_tokens": 4096
  }'
```

## State Persistence (Compact Recovery)

Persist state to `review-stage/REVIEW_STATE.json` after each round:

```json
{
  "round": 2,
  "status": "in_progress",
  "last_score": 5.0,
  "last_verdict": "not ready",
  "pending_experiments": [],
  "timestamp": "2026-03-15T10:00:00"
}
```

**Write this file at the end of every Phase E** (after documenting the round).

**On completion**, set `"status": "completed"`.

## Workflow

### Initialization

1. **Check `review-stage/REVIEW_STATE.json`** for recovery *(fall back to `./REVIEW_STATE.json` if not found — legacy path)*
2. Read project context and prior reviews
3. Initialize round counter

### Loop (up to MAX_ROUNDS)

#### Phase A: Review

**If MCP available:**
```
mcp__llm-chat__chat:
  system: "You are a senior ML reviewer (NeurIPS/ICML level)."
  message: |
    [Round N/MAX_ROUNDS of autonomous review loop]

    [Full research context: claims, methods, results, known weaknesses]
    [Changes since last round, if any]

    1. Score this work 1-10 for a top venue
    2. List remaining critical weaknesses (ranked by severity)
    3. For each weakness, specify the MINIMUM fix
    4. State clearly: is this READY for submission? Yes/No/Almost

    Be brutally honest. If the work is ready, say so clearly.
```

**If MCP NOT available:**
```bash
curl -s "${LLM_BASE_URL}/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${LLM_API_KEY}" \
  -d '{
    "model": "${LLM_MODEL}",
    "messages": [
      {"role": "system", "content": "You are a senior ML reviewer (NeurIPS/ICML level)."},
      {"role": "user", "content": "[Full review prompt]"}
    ],
    "max_tokens": 4096
  }'
```

#### Phase B: Parse Assessment

**CRITICAL: Save the FULL raw response** verbatim. Then extract:
- **Score** (numeric 1-10)
- **Verdict** ("ready" / "almost" / "not ready")
- **Action items** (ranked list of fixes)

**STOP**: If score >= 6 AND verdict ∈ {"ready", "almost"} (exact — "not ready" does NOT qualify)

#### Phase C: Implement Fixes

Prioritize verified fixes to critical evidence gaps and informative checks within budget; preserve primary outcomes and label exploratory reframing.

#### Phase D: Wait for Results

Monitor remote experiments

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

[Paste the COMPLETE raw response here — verbatim, unedited.]

</details>

### Actions Taken
- [what was implemented/changed]

### Results
- [experiment outcomes, if any]

### Status
- [continuing to round N+1 / stopping]
```

**Write `review-stage/REVIEW_STATE.json`** with current state.

### Termination

1. Set `review-stage/REVIEW_STATE.json` status to "completed"
2. Write final summary

## Key Rules

- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.

- Be honest about weaknesses
- Implement fixes BEFORE re-reviewing
- Document everything
- Include previous context in round 2+ prompts
- Prefer MCP tool over curl when available

## Prompt Template for Round 2+

```
mcp__llm-chat__chat:
  system: "You are a senior ML reviewer (NeurIPS/ICML level)."
  message: |
    [Round N/MAX_ROUNDS of autonomous review loop]

    ## Previous Review Summary (Round N-1)
    - Previous Score: X/10
    - Previous Verdict: [ready/almost/not ready]
    - Previous Key Weaknesses: [list]

    ## Changes Since Last Review
    1. [Action 1]: [result]
    2. [Action 2]: [result]

    ## Updated Results
    [paste updated metrics/tables]

    Please re-score and re-assess:
    1. Score this work 1-10 for a top venue
    2. List remaining critical weaknesses (ranked by severity)
    3. For each weakness, specify the MINIMUM fix
    4. State clearly: is this READY for submission? Yes/No/Almost

    Be brutally honest. If the work is ready, say so clearly.
```


## Output Protocols

> Follow these shared protocols for all output files:
> - **[Output Versioning Protocol](../../shared-references/output-versioning.md)** — write timestamped file first, then copy to fixed name
> - **[Output Manifest Protocol](../../shared-references/output-manifest.md)** — log every output to MANIFEST.md
> - **[Output Language Protocol](../../shared-references/output-language.md)** — respect the project's language setting
