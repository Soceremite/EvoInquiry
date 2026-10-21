"""Exercise documented reviewer calls against the shipped MCP request handlers.

Only the network function is replaced. Loading the handler AST avoids the
servers' module-level stdio setup and needs no credentials or external service.
"""
import ast
from pathlib import Path
import re

import jsonschema
import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('surface', ['skills', 'skills/skills-codex'])
@pytest.mark.parametrize('skill,server,outbound', [
    ('auto-review-loop-llm', 'llm-chat', 'call_llm'),
    ('auto-review-loop-minimax', 'minimax-chat', 'call_minimax'),
])
def test_documented_review_call_delivers_brief_to_real_handler(surface, skill, server, outbound):
    source = REPO / 'mcp-servers' / server / 'server.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    handler_node = next(node for node in tree.body
                        if isinstance(node, ast.FunctionDef) and node.name == 'handle_request')
    captured = []

    def capture(messages, *args):
        captured.append(messages)
        return 'local transport receipt', None

    namespace = {'DEFAULT_MODEL': 'MiniMax-M3', 'SERVER_NAME': server,
                 'REVIEW_FALLBACK_ENABLED': False, 'debug_log': lambda *args: None,
                 outbound: capture}
    exec(compile(ast.Module(body=[handler_node], type_ignores=[]), str(source), 'exec'), namespace)
    handle = namespace['handle_request']
    definitions = handle({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'})['result']['tools']
    text = (REPO / surface / skill / 'SKILL.md').read_text(encoding='utf-8')
    calls = [yaml.safe_load(block) for block in re.findall(r'```text\n(.*?)```', text, re.S)]
    calls = [call for call in calls if isinstance(call, dict)]
    assert calls, 'The adapter needs a usable tool invocation'
    for call in calls:
        for name, arguments in call.items():
            tool = next(item for item in definitions if item['name'] == name.split('__')[-1])
            jsonschema.validate(arguments, tool['inputSchema'])
            response = handle({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
                               'params': {'name': tool['name'], 'arguments': arguments}})
            assert response['result']['content'][0]['text'] == 'local transport receipt'
            assert captured[-1][-1]['role'] == 'user'
            assert captured[-1][-1]['content'] == arguments['prompt']
            assert captured[-1][-1]['content'].strip()
