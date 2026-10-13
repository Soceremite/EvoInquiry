"""The evaluation harness must retain evidence without leaking or self-grading."""
from pathlib import Path
import json
import os
import sys

import pytest

from tools.evaluate_skill_behavior import discover_variant, run_case


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


@pytest.mark.parametrize('drift', ['skill', 'guidance', 'storage', 'helper', 'governance', 'schema'])
def test_discovery_rejects_stale_cache_with_the_correct_name_and_version(tmp_path, drift):
    toolkit = tmp_path / 'source'
    cache = tmp_path / 'cache/market/evo-inquiry/1.0.0-beta.4'
    skill_rel = Path('skills/skills-codex/example/SKILL.md')
    common_rel = Path('skills/skills-codex/shared-references/evo-inquiry.md')
    storage_rel = Path('skills/skills-codex/shared-references/experiment-storage.md')
    helper_rel = Path('tools/checkpoint_retention.py')
    governance_rel = Path('tools/execution_registry.py')
    schema_rel = Path('tools/schemas/execution.schema.json')
    for root in (toolkit, cache):
        for rel, text in ((skill_rel, 'Current skill bytes'), (common_rel, 'Current guidance'),
                          (storage_rel, 'Current storage guidance'), (helper_rel, 'Current helper'),
                          (governance_rel, 'Current governed launcher'), (schema_rel, '{}')):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text)
    (toolkit / '.codex-plugin').mkdir()
    (toolkit / '.codex-plugin/plugin.json').write_text('{"version":"1.0.0-beta.4"}')
    (cache / {'skill': skill_rel, 'guidance': common_rel, 'storage': storage_rel,
              'helper': helper_rel, 'governance': governance_rel,
              'schema': schema_rel}[drift]).write_text('Stale installed bytes')
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
               'governance': 'support resource', 'schema': 'support resource'}[drift]
    with pytest.raises(RuntimeError, match=message):
        discover_variant(toolkit, selector, cli)
