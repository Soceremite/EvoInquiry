---
name: "auto-review-loop-llm"
description: "Run iterative research review and revision with an OpenAI-compatible LLM API. Use when that reviewer backend is requested; requires llm-chat or API setup. Trigger with llm review."
---
<!-- GENERATED from skills/auto-review-loop-llm/SKILL.md — do not edit directly -->

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

Use the configured `llm-chat` MCP or the existing OpenAI-compatible client.
The MCP call is `mcp__llm-chat__chat` with the configured `LLM_MODEL` and
the evidence brief. Direct configuration uses `LLM_BASE_URL`, `LLM_MODEL`,
and `LLM_API_KEY`.

```text
mcp__llm-chat__chat:
  model: <configured LLM_MODEL>
  system: You are a research reviewer. Assess claims against the supplied evidence.
  prompt: <review brief with original question, artifact evidence, prior concerns and changes>
```

Follow the [external review loop](../shared-references/external-review-loop.md).
