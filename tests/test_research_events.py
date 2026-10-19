"""Normalize actual CLI event shapes without copying sensitive raw payloads."""
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from tools import research_events as events
from tools.registry_common import RegistryError, file_lock


def write_trace(root, records, *, suffix=b''):
    path = root / 'trace.jsonl'
    path.write_bytes(b''.join(json.dumps(row).encode() + b'\n' for row in records) + suffix)
    return path


def read_log(root):
    return [json.loads(line) for line in (root / '.ei/meta/events.jsonl').read_text().splitlines()]


def test_import_is_idempotent_and_does_not_copy_commands_or_outputs(tmp_path):
    secret = 'sk_not-a-real-key-but-sensitive-fixture'
    write_trace(tmp_path, [
        {'type': 'thread.started', 'thread_id': 'thread-1'},
        {'type': 'item.started', 'item': {'type': 'command_execution', 'id': 'item-1', 'command': f'curl -H "Authorization: Bearer {secret}" example.invalid'}},
        {'type': 'item.completed', 'item': {'type': 'command_execution', 'id': 'item-1', 'command': f'echo {secret}', 'exit_code': 7, 'aggregated_output': secret}},
        {'type': 'turn.completed', 'usage': {'input_tokens': 120, 'cached_input_tokens': 30, 'output_tokens': 40}},
    ])
    first = events.import_codex(tmp_path, 'trace.jsonl', 'session-1', workflow_run_id='pilot')
    second = events.import_codex(tmp_path, 'trace.jsonl', 'session-1', workflow_run_id='pilot')
    assert first['events_appended'] == 5 and second['events_appended'] == 0
    text = (tmp_path / '.ei/meta/events.jsonl').read_text()
    assert secret not in text and 'Authorization' not in text and 'curl' not in text
    records = read_log(tmp_path)
    assert sum(row['event'] == 'tool_failure' for row in records) == 1
    assert records[-1]['usage']['output_tokens'] == 40


def test_appended_trace_preserves_prefix_identity(tmp_path):
    path = write_trace(tmp_path, [{'type': 'thread.started'}])
    events.import_codex(tmp_path, 'trace.jsonl', 'session-1')
    original = read_log(tmp_path)[0]
    with path.open('ab') as stream:
        stream.write(json.dumps({'type': 'turn.completed'}).encode() + b'\n')
    assert events.import_codex(tmp_path, 'trace.jsonl', 'session-1')['events_appended'] == 1
    assert read_log(tmp_path)[0] == original


def test_changed_source_does_not_rewrite_imported_history(tmp_path):
    write_trace(tmp_path, [{'type': 'thread.started'}])
    events.import_codex(tmp_path, 'trace.jsonl', 'session-1')
    before = (tmp_path / '.ei/meta/events.jsonl').read_bytes()
    write_trace(tmp_path, [{'type': 'turn.failed', 'error': 'Changed prefix'}])
    with pytest.raises(RegistryError, match='source changed'):
        events.import_codex(tmp_path, 'trace.jsonl', 'session-1')
    assert (tmp_path / '.ei/meta/events.jsonl').read_bytes() == before


def test_partial_trace_does_not_invent_completion(tmp_path):
    write_trace(tmp_path, [{'type': 'thread.started'}], suffix=b'{"type":"turn.com')
    report = events.import_codex(tmp_path, 'trace.jsonl', 'session-1')
    assert report['partial_final_line'] and report['completion'] == 'unknown'
    assert not any(row['event'] == 'session_end' for row in read_log(tmp_path))


@pytest.mark.parametrize('last', [{'type': 'turn.started'},
    {'type': 'item.started', 'item': {'type': 'command_execution', 'command': 'python train.py'}}])
def test_previous_completed_turn_does_not_complete_new_work(tmp_path, last):
    write_trace(tmp_path, [{'type': 'turn.completed'}, last])
    assert events.import_codex(tmp_path, 'trace.jsonl', 'session-1')['completion'] == 'unknown'


def test_truncated_imported_prefix_is_rejected(tmp_path):
    write_trace(tmp_path, [{'type': 'thread.started'}, {'type': 'turn.completed'}])
    events.import_codex(tmp_path, 'trace.jsonl', 'session-1')
    write_trace(tmp_path, [{'type': 'thread.started'}])
    with pytest.raises(RegistryError, match='source changed'):
        events.import_codex(tmp_path, 'trace.jsonl', 'session-1')


def test_skill_path_mentions_do_not_certify_invocation_or_compliance(tmp_path):
    write_trace(tmp_path, [{'type': 'item.completed', 'item': {'type': 'command_execution',
        'exit_code': 0, 'command': 'python -c "print(\'skills/skills-codex/research-guide/SKILL.md\')"'}}])
    events.import_codex(tmp_path, 'trace.jsonl', 'session-1')
    records = read_log(tmp_path)
    assert not any(row['event'] == 'skill_invoke' for row in records)
    assert records[-1]['event'] == 'skill_reference'


def test_native_shell_wrappers_are_observable_without_claiming_compliance(tmp_path):
    write_trace(tmp_path, [{'type': 'item.completed', 'item': {'type': 'command_execution',
        'exit_code': 0, 'command': "/bin/bash -lc 'cat /cache/evo-inquiry/1.5.0/skills/skills-codex/research-guide/SKILL.md'"}},
        {'type': 'item.completed', 'item': {'type': 'command_execution', 'exit_code': 0,
         'command': "cat /other/skills/imagegen/SKILL.md"}}])
    events.import_codex(tmp_path, 'trace.jsonl', 'session-1')
    references = [row for row in read_log(tmp_path) if row['event'] == 'skill_reference']
    assert references[0]['skill'] == 'evo-inquiry:research-guide'
    assert references[1]['skill'] == 'imagegen' and references[1]['surface'] == 'unclassified'


def test_invalid_complete_line_does_not_initialize_event_log(tmp_path):
    write_trace(tmp_path, [{'type': 'thread.started'}], suffix=b'broken-json\n')
    with pytest.raises(RegistryError, match='line 2'):
        events.import_codex(tmp_path, 'trace.jsonl', 'session-1')
    assert not (tmp_path / '.ei').exists()


def test_legacy_event_records_are_preserved(tmp_path):
    path = tmp_path / '.ei/meta/events.jsonl'
    path.parent.mkdir(parents=True)
    original = b'{"event":"skill_invoke","skill":"research-lit","session":"legacy"}\n'
    path.write_bytes(original)
    events.append_event(tmp_path, {'event': 'session_start', 'session': 'new-session'})
    assert path.read_bytes().startswith(original)


def test_unknown_tool_exit_is_not_success(tmp_path):
    write_trace(tmp_path, [{'type': 'item.completed', 'item': {'type': 'command_execution', 'status': 'completed', 'command': 'cat missing/SKILL.md'}}])
    events.import_codex(tmp_path, 'trace.jsonl', 'session-1')
    assert read_log(tmp_path)[0]['status'] == 'unknown'
    assert not any(row['event'] == 'skill_invoke' for row in read_log(tmp_path))


def test_unknown_payload_and_credentials_are_rejected(tmp_path):
    for payload in ({'event': 'session_start', 'session': 's', 'command': 'secret'},
                    {'event': 'session_start', 'session': 'sk_this-is-not-a-real-key'}):
        with pytest.raises(RegistryError):
            events.append_event(tmp_path, payload)
    assert not (tmp_path / '.ei').exists()


def test_external_trace_path_is_not_scanned(tmp_path):
    with pytest.raises(RegistryError):
        events.import_codex(tmp_path, '../private.jsonl', 'session-1')
    assert not (tmp_path / '.ei').exists()


def test_summary_does_not_treat_turns_as_complete_workflows(tmp_path):
    write_trace(tmp_path, [{'type': 'turn.completed'}, {'type': 'turn.failed'}])
    events.import_codex(tmp_path, 'trace.jsonl', 'session-1')
    report = events.summarize(tmp_path)
    assert report['completed_turn_observations'] == 1 and report['failed_turn_observations'] == 1
    assert report['session_completion'] == 'not-inferred'
    assert report['workflow_completeness'] == 'not-established'


def test_empty_summary_is_read_only(tmp_path):
    assert events.summarize(tmp_path)['events'] == 0
    assert not (tmp_path / '.ei').exists()


def test_cooperating_importers_publish_complete_batches_without_duplicates(tmp_path):
    count = 1000
    write_trace(tmp_path, [{'type': 'item.completed', 'item': {
        'type': 'command_execution', 'command': 'python inspect.py', 'exit_code': 0}}
        for _ in range(count)])
    program = '''import json,sys
from tools.research_events import import_codex
print(json.dumps(import_codex(sys.argv[1], 'trace.jsonl', 'shared-import')))
'''
    children = [subprocess.Popen([sys.executable, '-c', program, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[1], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE) for _ in range(2)]
    log = tmp_path / '.ei/meta/events.jsonl'
    observed = []
    try:
        deadline = time.monotonic() + 30
        while any(child.poll() is None for child in children) and time.monotonic() < deadline:
            with file_lock(log.with_suffix('.lock'), shared=True):
                if log.exists():
                    observed.append(len(log.read_bytes().splitlines()))
            time.sleep(0.002)
        results = []
        for child in children:
            stdout, stderr = child.communicate(timeout=5)
            assert child.returncode == 0, stderr.decode()
            results.append(json.loads(stdout))
        assert sorted(row['events_appended'] for row in results) == [0, count]
        records = read_log(tmp_path)
        assert len(records) == len({row['event_id'] for row in records}) == count
        assert all(length == count for length in observed)
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.wait()


def test_failed_import_replacement_preserves_all_previous_observations(tmp_path, monkeypatch):
    path = write_trace(tmp_path, [{'type': 'thread.started'}])
    events.import_codex(tmp_path, 'trace.jsonl', 'session-1')
    before = (tmp_path / '.ei/meta/events.jsonl').read_bytes()
    with path.open('ab') as stream:
        stream.write(b'{"type":"turn.completed"}\n')
    def fail(*args, **kwargs):
        raise OSError('simulated failed atomic replacement')
    monkeypatch.setattr(events, 'atomic_write', fail)
    with pytest.raises(OSError, match='failed atomic replacement'):
        events.import_codex(tmp_path, 'trace.jsonl', 'session-1')
    assert (tmp_path / '.ei/meta/events.jsonl').read_bytes() == before


def test_source_changed_after_parsing_cannot_publish_an_import(tmp_path, monkeypatch):
    path = write_trace(tmp_path, [{'type': 'thread.started'}])
    original = events._normalize
    def changed(event, base):
        path.write_bytes(b'{"type":"turn.failed"}\n')
        yield from original(event, base)
    monkeypatch.setattr(events, '_normalize', changed)
    with pytest.raises(RegistryError, match='source changed during import'):
        events.import_codex(tmp_path, 'trace.jsonl', 'session-1')
    assert not (tmp_path / '.ei/meta/events.jsonl').exists()
