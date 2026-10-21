---
name: auto-review-loop-llm
description: Autonomous research review loop using any OpenAI-compatible LLM API. Configure via llm-chat MCP server or environment variables. Trigger with "auto review loop llm" or "llm review".
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


# Research review loop — OpenAI-compatible API

Use the [shared research review cycle](../shared-references/research-review-cycle.md)
for the complete loop, issue closure, state recovery and stopping. This entrypoint
supplies its API backend; keep the default four-round limit and existing output
paths. Use it when this backend is requested or already owns the resumed loop.
Do not start a second loop through another reviewer entrypoint.

## Reviewer adapter

Reuse the project's configured `llm-chat` MCP service when available:

```text
mcp__llm-chat__chat:
  model: <configured LLM_MODEL>
  system: You are a research reviewer. Assess claims against the supplied evidence.
  prompt: <review brief with original question, artifact evidence, prior concerns and changes>
```

Otherwise use the existing OpenAI-compatible API client with `LLM_BASE_URL`,
`LLM_MODEL` and `LLM_API_KEY`. Credentials stay outside prompts, logs and source
snapshots. Review does not authorize changing global configuration. If required
configuration or the reviewer is unavailable, preserve pending state and record
the specific BLOCKED condition; do not silently switch providers.

Ask for score out of ten, verdict `ready | almost | not ready`, evidence-backed
strengths, unresolved material issues and minimum useful fixes. Supply actual
relevant artifacts or contents and include prior unresolved concerns in later
rounds. Preserve the full raw response, API/model provenance and failure receipt.
The API being external does not establish reviewer independence or acceptance.

## Outputs

Keep `review-stage/AUTO_REVIEW.md` and `review-stage/REVIEW_STATE.json`, or their
existing legacy locations when resuming. Preserve `run_id`, completed rounds,
pending experiments and original limits under the shared cycle. Document each
round before continuation; a completed loop does not accept a research claim.

## Output Protocols

> Follow these shared protocols for all output files:
> - **[Output Versioning Protocol](../shared-references/output-versioning.md)** — write timestamped file first, then copy to fixed name
> - **[Output Manifest Protocol](../shared-references/output-manifest.md)** — log every output to MANIFEST.md
> - **[Output Language Protocol](../shared-references/output-language.md)** — respect the project's language setting
