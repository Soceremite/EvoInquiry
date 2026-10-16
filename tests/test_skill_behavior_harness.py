"""The evaluation harness must retain evidence without leaking or self-grading."""
from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import time

import pytest

from tools.evaluate_skill_behavior import discover_variant, run_case, selection_config
from tools import evaluate_skill_behavior as harness


@pytest.fixture
def setup_case(tmp_path):
    fixtures = tmp_path / 'fixtures'
    (fixtures / '01').mkdir(parents=True)
    (fixtures / '01/input.txt').write_text('Raw fixture, not a grading rubric.\n')
    toolkit = tmp_path / 'toolkit'
    (toolkit / '.codex-plugin').mkdir(parents=True)
    (toolkit / '.codex-plugin/plugin.json').write_text('{"version":"1.0.0-beta.4"}')
    case = {'id': '01', 'fixture': '01', 'prompt': 'Read input.txt and report its contents.',
            'acceptable_skills': ['private-expected-route'],
            'required_outcome': 'PRIVATE_JUDGING_ONLY', 'timeout_seconds': 5, 'max_tool_actions': 3}
    return case, fixtures, tmp_path / 'evidence', toolkit


def fake_cli(tmp_path: Path, program: str) -> str:
    path = tmp_path / 'fake-codex'
    path.write_text('#!' + sys.executable + '\n' + program)
    path.chmod(0o755)
    return str(path)


@pytest.mark.skipif(os.name != 'posix', reason='CLI process-group harness uses POSIX signals')
def test_session_sees_only_request_and_cannot_grade_itself(setup_case, tmp_path):
    case, fixtures, output, toolkit = setup_case
    cli = fake_cli(tmp_path, '''import json,sys
from pathlib import Path
request = sys.stdin.read()
Path('received.txt').write_text(request)
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'I declare this case PASS'}}))
print(json.dumps({'type':'turn.completed'}))
''')
    result = run_case(case, fixtures, output, toolkit, cli, 'evo-inquiry@evo-inquiry-eval-beta4')
    assert (output / '01/project/received.txt').read_text() == case['prompt'] + '\n'
    assert 'PRIVATE_JUDGING_ONLY' not in (output / '01/prompt.txt').read_text()
    assert result['session_completed']
    assert result['assessment'] == 'UNASSESSED'
    assert result['changed_or_created_files'] == ['received.txt']
    with pytest.raises(ValueError, match='Refusing to overwrite'):
        run_case(case, fixtures, output, toolkit, cli, 'evo-inquiry@evo-inquiry-eval-beta4')


@pytest.mark.skipif(os.name != 'posix', reason='CLI process-group harness uses POSIX signals')
def test_wrong_cache_variant_is_recorded_even_if_cli_exits_successfully(setup_case, tmp_path):
    case, fixtures, output, toolkit = setup_case
    cli = fake_cli(tmp_path, '''import json,sys
sys.stdin.read()
print(json.dumps({'type':'item.completed','item':{'type':'command_execution','command':'cat /x/plugins/cache/evo-inquiry-eval-beta3/evo-inquiry/1.0.0-beta.3/skills/skills-codex/analyze-results/SKILL.md','exit_code':0,'status':'completed'}}))
print(json.dumps({'type':'turn.completed'}))
''')
    result = run_case(case, fixtures, output, toolkit, cli, 'evo-inquiry@evo-inquiry-eval-beta4')
    assert result['exit_code'] == 0
    assert result['variant_mismatch']
    assert result['assessment'] == 'UNASSESSED'


@pytest.mark.skipif(os.name != 'posix', reason='CLI process-group harness uses POSIX signals')
def test_mainline_read_is_not_mistaken_for_the_discovered_codex_entrypoint(setup_case, tmp_path):
    case, fixtures, output, toolkit = setup_case
    entrypoint = '/x/plugins/cache/evo-inquiry-eval-beta4/evo-inquiry/1.0.0-beta.4/skills/research-review/SKILL.md'
    cli = fake_cli(tmp_path, '''import json,sys
sys.stdin.read()
print(json.dumps({'type':'item.completed','item':{'type':'command_execution','command':''' + repr('cat ' + entrypoint) + ''','exit_code':0,'status':'completed'}}))
print(json.dumps({'type':'turn.completed'}))
''')
    result = run_case(case, fixtures, output, toolkit, cli, 'evo-inquiry@evo-inquiry-eval-beta4')
    assert not result['variant_mismatch']
    assert result['observed_skill_entrypoints'] == [entrypoint]
    assert result['noncanonical_skill_entrypoints'] == [entrypoint]
    assert result['assessment'] == 'UNASSESSED'


@pytest.mark.skipif(os.name != 'posix', reason='CLI process-group harness uses POSIX signals')
def test_startup_failure_is_separate_from_behavior_and_keeps_evidence(setup_case, tmp_path):
    case, fixtures, output, toolkit = setup_case
    cli = fake_cli(tmp_path, '''import sys
sys.stdin.read()
sys.stderr.write('Error: failed to initialize in-process app-server client: Resource temporarily unavailable\\n')
raise SystemExit(1)
''')
    result = run_case(case, fixtures, output, toolkit, cli, 'evo-inquiry@evo-inquiry-eval-beta4')
    assert result['failure_kind'] == 'runtime_startup'
    assert result['tool_actions'] == 0 and not result['session_completed']
    assert result['assessment'] == 'UNASSESSED'
    assert 'Resource temporarily unavailable' in (output / '01/stderr.txt').read_text()


@pytest.mark.skipif(os.name != 'posix', reason='CLI process-group harness uses POSIX signals')
def test_time_limit_stops_a_session_and_preserves_raw_trace(setup_case, tmp_path):
    case, fixtures, output, toolkit = setup_case
    case['timeout_seconds'] = 0.2
    cli = fake_cli(tmp_path, '''import json,sys,time
sys.stdin.read()
print(json.dumps({'type':'turn.started'}),flush=True)
time.sleep(20)
''')
    result = run_case(case, fixtures, output, toolkit, cli, 'evo-inquiry@evo-inquiry-eval-beta4')
    assert result['limit'] == 'time_limit'
    assert not result['session_completed']
    assert result['seconds'] < 3
    assert (output / '01/events.jsonl').is_file()


@pytest.mark.parametrize('selection,has_case', [('all', False), ('smoke', True)])
def test_empty_case_selection_fails_before_discovery_or_output(tmp_path, monkeypatch, selection, has_case):
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'cases': [{'id': '01'}] if has_case else [], 'smoke_cases': []}))
    output = tmp_path / 'evidence'
    monkeypatch.setattr(sys, 'argv', ['evaluate_skill_behavior', '--toolkit', str(tmp_path / 'source'),
                                    '--output', str(output), '--manifest', str(manifest), '--cases', selection])
    monkeypatch.setattr(harness, 'discover_variant', lambda *a, **kw: pytest.fail('Empty invocation must not start discovery'))
    with pytest.raises(SystemExit) as error:
        harness.main()
    assert error.value.code == 2
    assert not output.exists()


@pytest.mark.skipif(os.name != 'posix', reason='CLI process-group harness uses POSIX signals')
def test_cleanup_stops_a_group_member_that_outlives_the_cli(tmp_path):
    cli = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'], process_group=0)
    survivor = None
    try:
        ready = tmp_path / 'ready'
        survivor = subprocess.Popen([sys.executable, '-c', '''import signal,sys,time
from pathlib import Path
signal.signal(signal.SIGTERM, signal.SIG_IGN)
Path(sys.argv[1]).touch()
time.sleep(30)
''', str(ready)], process_group=cli.pid)
        deadline = time.monotonic() + 10
        while not ready.exists() and survivor.poll() is None and time.monotonic() < deadline:
            time.sleep(0.025)
        assert ready.is_file(), 'Group member did not install its signal handler'
        harness._terminate_session(cli)
        assert cli.returncode == -signal.SIGTERM
        assert survivor.wait(timeout=3) == -signal.SIGKILL
    finally:
        for proc in (survivor, cli):
            if proc is not None:
                if proc.poll() is None:
                    proc.kill()
                proc.wait()


@pytest.mark.skipif(os.name != 'posix', reason='CLI process-group harness uses POSIX signals')
def test_inspection_exception_stops_the_running_cli(setup_case, tmp_path, monkeypatch):
    case, fixtures, output, toolkit = setup_case
    cli = fake_cli(tmp_path, 'import sys,time\nsys.stdin.read()\ntime.sleep(30)\n')
    processes = []
    original_popen = subprocess.Popen

    def capture_process(*args, **kwargs):
        proc = original_popen(*args, **kwargs)
        processes.append(proc)
        return proc

    def fail_inspection(*args):
        raise OSError('Simulated trace-read failure')

    monkeypatch.setattr(harness.subprocess, 'Popen', capture_process)
    monkeypatch.setattr(harness, 'read_events', fail_inspection)
    with pytest.raises(OSError, match='Simulated trace-read failure'):
        run_case(case, fixtures, output, toolkit, cli, 'evo-inquiry@evo-inquiry-eval-beta4')
    assert len(processes) == 1
    assert processes[0].poll() is not None
    assert (output / '01/events.jsonl').is_file()


@pytest.mark.skipif(os.name != 'posix', reason='CLI process-group harness uses POSIX signals')
@pytest.mark.parametrize('stop_signal', [signal.SIGINT, signal.SIGTERM])
def test_cli_cancellation_stops_children_preserves_trace_and_skips_queued_cases(setup_case, tmp_path, stop_signal):
    case, fixtures, output, toolkit = setup_case
    case = dict(case, fixture=str(fixtures / '01'), timeout_seconds=30)
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'cases': [case, dict(case, id='02')], 'smoke_cases': ['01', '02']}))
    cli = fake_cli(tmp_path, '''import json,os,signal,subprocess,sys,time
from pathlib import Path
if '--version' in sys.argv:
    print('codex-cli test fixture')
    raise SystemExit(0)
sys.stdin.read()
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
def stop(signum, frame):
    child.wait(timeout=3)
    raise SystemExit(128 + signum)
signal.signal(signal.SIGTERM, stop)
Path('processes.tmp').write_text(json.dumps([os.getpid(), child.pid]))
Path('processes.tmp').replace('processes.json')
print(json.dumps({'type':'turn.started'}), flush=True)
time.sleep(30)
''')
    command = '''import sys
from tools import evaluate_skill_behavior as harness
harness.discover_variant = lambda *args, **kwargs: {'entrypoints': 1}
harness.main()
'''
    env = dict(os.environ, CODEX_HOME=str(tmp_path / 'codex-home'))
    proc = subprocess.Popen([sys.executable, '-c', command, '--toolkit', str(toolkit),
                             '--output', str(output), '--manifest', str(manifest),
                             '--cases', 'all', '--codex', cli, '--jobs', '1'],
                            cwd=Path(__file__).resolve().parents[1], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            start_new_session=True)
    pids = []
    try:
        path = output / '01/project/processes.json'
        deadline = time.monotonic() + 10
        while not path.exists() and proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.025)
        assert path.is_file(), 'Fixture CLI did not start'
        pids = json.loads(path.read_text())
        proc.send_signal(stop_signal)
        stdout, stderr = proc.communicate(timeout=10)
        assert proc.returncode == 128 + stop_signal, (stdout, stderr)
        run = json.loads((output / '01/run.json').read_text())
        assert run['limit'] == run['failure_kind'] == 'cancelled'
        assert not run['session_completed']
        assert run['assessment'] == 'UNASSESSED'
        assert (output / '01/events.jsonl').is_file()
        assert not (output / '02').exists()
        assert [row['case'] for row in json.loads((output / 'runs.json').read_text())] == ['01']
        metadata = json.loads((output / 'environment.json').read_text())
        assert metadata['interrupted_signal'] == stop_signal
        assert metadata['unrecorded_cases'] == ['02']
        for pid in pids:
            with pytest.raises(ProcessLookupError):
                os.kill(pid, 0)
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.communicate()
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


@pytest.mark.skipif(os.name != 'posix', reason='CLI process-group harness uses POSIX signals')
def test_repeated_service_errors_stop_early_and_remain_unassessed(setup_case, tmp_path):
    case, fixtures, output, toolkit = setup_case
    case['timeout_seconds'] = 5
    cli = fake_cli(tmp_path, '''import json,sys,time
sys.stdin.read()
sys.stderr.write('The server is currently overloaded; reconnecting soon\\n')
sys.stderr.flush()
print(json.dumps({'type':'item.completed','item':{'type':'error','message':'stream disconnected; retrying'}}), flush=True)
time.sleep(20)
''')
    result = run_case(case, fixtures, output, toolkit, cli, 'evo-inquiry@evo-inquiry-eval-beta4')
    assert result['limit'] == 'service_error'
    assert result['failure_kind'] == 'service_error'
    assert result['service_error_count'] == 2
    assert not result['session_completed']
    assert result['seconds'] < 3
    assert result['assessment'] == 'UNASSESSED'
    assert 'overloaded' in '\n'.join(result['service_error_messages']).lower()
    assert (output / '01/events.jsonl').is_file()


@pytest.mark.skipif(os.name != 'posix', reason='CLI process-group harness uses POSIX signals')
def test_frozen_model_override_survives_changed_user_default(setup_case, tmp_path, monkeypatch):
    case, fixtures, output, toolkit = setup_case
    defaults = tmp_path / 'mutable-defaults.json'
    defaults.write_text(json.dumps({'model': 'gpt-6.1-sol', 'model_reasoning_effort': 'max'}))
    monkeypatch.setenv('EI_TEST_MODEL_DEFAULTS', str(defaults))
    pinned = json.loads(defaults.read_text())
    cli = fake_cli(tmp_path, '''import json,os,sys
from pathlib import Path
settings=json.loads(Path(os.environ['EI_TEST_MODEL_DEFAULTS']).read_text())
for i,arg in enumerate(sys.argv[:-1]):
    if arg=='-c':
        key,_,value=sys.argv[i+1].partition('=')
        if key in ('model','model_reasoning_effort'):
            settings[key]=json.loads(value)
sys.stdin.read()
Path('observed-model.json').write_text(json.dumps(settings))
print(json.dumps({'type':'turn.completed'}))
''')
    for identifier, ambient in [('01', 'gpt-6.1-sol'), ('02', 'gpt-6-astra')]:
        defaults.write_text(json.dumps({'model': ambient, 'model_reasoning_effort': 'xhigh'}))
        result = run_case(dict(case, id=identifier), fixtures, output, toolkit, cli,
                          'evo-inquiry@evo-inquiry-eval-beta4', pinned)
        assert result['session_completed']
        assert result['model_settings'] == pinned
        assert json.loads((output / identifier / 'project/observed-model.json').read_text()) == pinned


def test_selection_discovers_future_marketplaces_and_preserves_unrelated_preferences(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_HOME', str(tmp_path))
    (tmp_path / 'config.toml').write_text('''[plugins."evo-inquiry@future-v999"]
enabled=true
[plugins."unrelated@other"]
enabled=true
[skills]
config=[{path="/personal/unrelated/SKILL.md",enabled=false}]
''', encoding='utf-8')
    cached = tmp_path / 'plugins/cache/stale-unconfigured/evo-inquiry/9/skills/skills-codex/example'
    cached.mkdir(parents=True); (cached / 'SKILL.md').write_text('stale', encoding='utf-8')
    settings = selection_config('evo-inquiry@candidate-v140')
    assert 'plugins."evo-inquiry@future-v999".enabled=false' in settings
    assert 'plugins."evo-inquiry@stale-unconfigured".enabled=false' in settings
    assert not any('unrelated@other' in setting for setting in settings)
    assert any('/personal/unrelated/SKILL.md' in setting and 'enabled=false' in setting for setting in settings)
    assert settings[-1] == 'plugins."evo-inquiry@candidate-v140".enabled=true'


@pytest.mark.parametrize('drift', ['skill', 'guidance', 'storage', 'helper', 'governance', 'schema', 'mainline', 'overlay',
                                 'deferred_codex', 'deferred_mainline', 'deferred_claude', 'deferred_gemini'])
def test_discovery_rejects_stale_cache_with_the_correct_name_and_version(tmp_path, drift):
    toolkit = tmp_path / 'source'
    cache = tmp_path / 'cache/market/evo-inquiry/1.0.0-beta.4'
    skill_rel = Path('skills/skills-codex/example/SKILL.md')
    common_rel = Path('skills/skills-codex/shared-references/evo-inquiry.md')
    storage_rel = Path('skills/skills-codex/shared-references/experiment-storage.md')
    helper_rel = Path('tools/checkpoint_retention.py')
    governance_rel = Path('tools/execution_registry.py')
    schema_rel = Path('tools/schemas/execution.schema.json')
    mainline_rel = Path('skills/example/SKILL.md')
    overlay_rel = Path('skills/skills-codex-claude-review/example/SKILL.md')
    deferred = {name: Path('skills') / runtime / 'example/references/full-workflow.md'
                for name, runtime in (('deferred_codex', 'skills-codex'), ('deferred_mainline', ''),
                                      ('deferred_claude', 'skills-codex-claude-review'),
                                      ('deferred_gemini', 'skills-codex-gemini-review'))}
    for root in (toolkit, cache):
        for rel, text in ((skill_rel, 'Current skill bytes'), (common_rel, 'Current guidance'),
                          (storage_rel, 'Current storage guidance'), (helper_rel, 'Current helper'),
                          (governance_rel, 'Current governed launcher'), (schema_rel, '{}'),
                          (mainline_rel, 'Current mainline'), (overlay_rel, 'Current overlay')):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text)
        for rel in deferred.values():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text('Current deferred reviewer instructions')
    (toolkit / '.codex-plugin').mkdir()
    (toolkit / '.codex-plugin/plugin.json').write_text('{"version":"1.0.0-beta.4"}')
    (cache / {'skill': skill_rel, 'guidance': common_rel, 'storage': storage_rel,
              'helper': helper_rel, 'governance': governance_rel,
              'schema': schema_rel, 'mainline': mainline_rel,
              'overlay': overlay_rel, **deferred}[drift]).write_text('Stale installed bytes')
    selector = 'evo-inquiry@evo-inquiry-eval-beta4'
    response = {'data': [{'skills': [{'name': 'evo-inquiry:example', 'enabled': True,
                                      'pluginId': selector, 'path': str(cache / skill_rel)}]}]}
    cli = fake_cli(tmp_path, '''import json,sys
response = ''' + repr(response) + '''
for line in sys.stdin:
    request = json.loads(line)
    if 'id' in request:
        print(json.dumps({'method':'notification'})+'\\n'+json.dumps({'id':request['id'],'result':response if request['method']=='skills/list' else {}}),flush=True)
''')
    message = {'skill': 'skill bytes', 'guidance': 'shared guidance',
               'storage': 'support resource', 'helper': 'support resource',
               'governance': 'support resource', 'schema': 'support resource',
               'mainline': 'support resource', 'overlay': 'support resource',
               **{name: 'support resource' for name in deferred}}[drift]
    with pytest.raises(RuntimeError, match=message):
        discover_variant(toolkit, selector, cli)
