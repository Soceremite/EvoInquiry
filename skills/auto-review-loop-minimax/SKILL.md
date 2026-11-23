---
name: auto-review-loop-minimax
description: Autonomous multi-round research review loop using MiniMax API. Use when you want to use MiniMax instead of Codex MCP for external review. Trigger with "auto review loop minimax" or "minimax review".
argument-hint: "[topic-or-scope]"
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit, Skill
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.

When changing research code, use [code-reuse-and-docs](../shared-references/code-reuse-and-docs.md) for readable interfaces and code-side documentation.
<!-- EVO-INQUIRY:END -->


# Research review loop

Use the configured `minimax-chat` MCP or the existing MiniMax API client.
Call `mcp__minimax-chat__minimax_chat` with `MiniMax-M3` or the explicitly
configured model override and the evidence brief. Direct configuration uses
`MINIMAX_API_KEY`.

```text
mcp__minimax-chat__minimax_chat:
  model: MiniMax-M3
  system: You are a research reviewer. Assess claims against the supplied evidence.
  prompt: <review brief with original question, artifact evidence, prior concerns and changes>
```

Follow the [external review loop](../shared-references/external-review-loop.md).
