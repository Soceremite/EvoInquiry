# Codex backend compatibility

These corrections apply to the retained ARIS examples in the named skills.
Use them for Codex setup; retain each skill's research workflow and artifacts.
No provider credentials, paid requests, or MCP installations are included in
the package. Choose a backend that is actually available in the user's session.

## auto-review-loop-llm and auto-review-loop-minimax

Codex MCP configuration uses `~/.codex/config.toml` with
`[mcp_servers.<name>]` tables. The inherited `~/.codex/settings.json` and
`mcpServers` user-configuration examples do not configure Codex.
See [the official Codex MCP documentation](https://developers.openai.com/codex/mcp).

For the generic backend, this is a template, not a command to run unchanged:

```toml
[mcp_servers.llm-chat]
command = "/absolute/path/to/python"
args = ["/absolute/path/to/evo-inquiry/mcp-servers/llm-chat/server.py"]
env_vars = ["LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"]
```

Resolve the interpreter and server path on the user's machine. Install the
server's declared requirements only when setting up that backend is within the
user's requested scope. Forward variables from the launch environment; do not
invent keys or persist credentials in this distributable. The MiniMax server
is at `mcp-servers/minimax-chat/server.py`; its environment key is
`MINIMAX_API_KEY`. An environment key is also usable by the documented direct
API fallback; a key configured for one MCP process is not automatically
available to the shell fallback.

The bundled `llm-chat` tool `chat` and MiniMax tool `minimax_chat` both require
the argument **`prompt`**, not the inherited examples' `message`. Read the
actual session tool schema; use `prompt`, `model`, and `system` for these
bundled versions. The separate generic `review` / `review_reply` tools have
additional provenance and thread requirements; do not substitute them for
`chat` without following their schema and review contract.

For the generic curl fallback, **do not execute the inherited single-quoted
JSON sample as written**: its `${LLM_MODEL}` placeholder is sent literally.
Require a configured endpoint and model, read the actual review prompt from a
file, and construct the request with a JSON serializer such as Python's
`json.dumps`. Preserve the skill's system prompt, messages and token settings.
Provider/model tables are examples, not verified current availability or
recommended defaults. Check the chosen provider's official documentation
before first use. If setup is missing, report the dependency and continue only
with an explicitly selected available backend.

## paper-illustration-image2

This entry is an experimental alternative. Its inherited description and
planner diagram still refer to Claude Code; their presence is not evidence
that the Codex runtime has a renderer. Require the actual image2 MCP bridge
or working bundled helper before invoking its rendering flow. Without it,
report the missing renderer and select an available illustration tool with
the user. Keep the figure brief and output validation requirements. Do not
claim that image generation or visual validation succeeded without an image.
