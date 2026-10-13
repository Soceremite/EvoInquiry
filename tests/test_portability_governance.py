"""Real interpreter, source and path regressions from the beta.1 portability audit."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import venv

import pytest

from tests.governance_helpers import consumer, make_environment, make_spec
from tools.code_map import build_map
from tools.environment_registry import (EnvironmentRegistry, probe_environment,
                                        run_environment_check, verify_environment)
from tools.execution_registry import freeze_snapshot, launch_execution, start_execution
from tools.filesystem_doctor import inspect_directory, probe_directory
from tools.project_registry import init_project, inventory
from tools.registry_common import (RegistryError, atomic_write, fixed_ref, identifier,
                                   is_junction, local_path, read_record, verify_ref)
from tools.state_paths import resolve_state_root, tree_inventory


@pytest.fixture
def isolated_python(tmp_path):
    directory = tmp_path / 'research 环境 with spaces' / '.venv'
    venv.EnvBuilder(with_pip=False).create(directory)
    interpreter = directory / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    sites = subprocess.check_output([str(interpreter), '-I', '-c',
        'import json,sysconfig; print(json.dumps(sysconfig.get_path("purelib")))'])
    return interpreter, Path(json.loads(sites.decode('ascii')))


def candidate(root, interpreter, *, env_id='portability', profile=2, imports=('math',),
              declarations=None, failed_consumer=False):
    """Four real checks; consumer IDs only label the methods exercised here."""
    observed = probe_environment(interpreter, imports, fingerprint_version=profile)
    inputs = root / 'env/recipes' / env_id
    for name in ('recipe.json', 'lock.json', 'build.json'):
        atomic_write(inputs / name, {'python': observed['python'], 'name': name})
    declarations = declarations if declarations is not None else {'consumers': ['method-a', 'method-b']}
    checks = {
        'metadata': 'import os,sys; assert sys.version_info >= (3,10); print(sys.version)\n'
                    + f'assert os.path.normcase(sys.executable) == os.path.normcase({observed["interpreter"]!r})\n'
                    + 'import json; print(json.dumps(sys.prefix))',
        'imports': 'import math; assert math.isfinite(math.pi); print(math.__spec__.origin)',
        'numerical': 'import math; assert math.fsum([.1]*10) == 1.; print("numeric-ok")',
        'consumers': 'methods = {"method-a": lambda: sum([1,2,3]), "method-b": lambda: len({1,2,3})}\n'
                     + 'expected = {"method-a": 6, "method-b": 3}\n'
                     + f'for name in {declarations.get("consumers", [])!r}:\n'
                     + '    assert methods[name]() == expected[name]\n'
                     + 'print("consumer-check-complete")',
    }
    if failed_consumer:
        checks['consumers'] += '\nraise SystemExit(9)'
    receipts = [run_environment_check(root, interpreter, env_id + '-' + stage, stage,
        ['-I', '-c', code], observed, declarations.get(stage, [])) for stage, code in checks.items()]
    record = {'schema_version': 1, 'env_id': env_id, 'revision': 'r001',
        'platform': observed['platform'], 'interpreter': str(interpreter),
        'expected_fingerprint': {'python': observed['python']}, 'observed_fingerprint': observed,
        'test_receipts': receipts, 'lifecycle': 'candidate'}
    for key, name in [('recipe_ref', 'recipe.json'), ('lock_ref', 'lock.json'), ('build_ref', 'build.json')]:
        record[key] = fixed_ref(root, (inputs / name).relative_to(root))
    registry = EnvironmentRegistry(root)
    reference = registry.record_candidate(record, [], receipts, ['method-a', 'method-b'])
    return registry, reference


def promote(registry, reference):
    return registry.promote_candidate(reference, {'approved': True, 'candidate_ref': reference,
        'confirmed_by': 'portability-test', 'confirmed_at': '2026-10-13T00:00:00Z'}, ['method-a', 'method-b'])


@pytest.mark.parametrize('declarations,failed', [
    ({'metadata': ['method-a', 'method-b']}, False),
    ({'imports': ['method-a', 'method-b']}, False),
    ({'numerical': ['method-a', 'method-b']}, False),
    ({'metadata': ['method-b'], 'consumers': ['method-a']}, False),
    ({'consumers': ['method-a', 'method-b']}, True),
])
def test_only_passing_consumer_layer_can_cover_required_methods(tmp_path, declarations, failed):
    original = make_environment(tmp_path)
    EnvironmentRegistry(tmp_path).bind_consumer(consumer(original))
    before = verify_ref(tmp_path, original).read_bytes()
    registry, reference = candidate(tmp_path, sys.executable, declarations=declarations, failed_consumer=failed)
    assert read_record(verify_ref(tmp_path, reference))['lifecycle'] == 'rejected'
    with pytest.raises(RegistryError, match='validation failed'):
        promote(registry, reference)
    assert verify_ref(tmp_path, original).read_bytes() == before
    assert read_record(tmp_path / '.ei/consumers/job-1.json')['env_revision'] == original


def test_consumer_layer_covers_both_methods_and_can_promote(tmp_path):
    registry, reference = candidate(tmp_path, sys.executable)
    frozen = promote(registry, reference)
    assert read_record(verify_ref(tmp_path, frozen))['lifecycle'] == 'frozen'
    assert verify_environment(tmp_path, frozen)['fingerprint_version'] == 2


@pytest.mark.parametrize('legacy', [False, True])
def test_relative_venv_entry_survives_registration_verification_and_snapshot_cwd(tmp_path, isolated_python, monkeypatch, legacy):
    interpreter, site = isolated_python
    (site / 'portability_dependency.py').write_text('VALUE = 37\n', encoding='utf-8')
    root = interpreter.parent.parent.parent
    relative = interpreter.relative_to(root)
    monkeypatch.chdir(root)
    registry, reference = candidate(root, relative, profile=1 if legacy else 2, imports=('portability_dependency',))
    frozen = promote(registry, reference)
    frozen_record = read_record(verify_ref(root, frozen))
    assert Path(frozen_record['interpreter']).is_absolute()
    if legacy:
        # Create an independent historical-format fixture; never rewrite a fixed record.
        historical = dict(frozen_record, env_id='historical', interpreter=str(relative))
        atomic_write(root / '.ei/environments/historical/r001/record.json', historical)
        frozen = fixed_ref(root, '.ei/environments/historical/r001/record.json')
    before = verify_ref(root, frozen).read_bytes()
    init_project(root, 'relative-entry', 'governed-v1')
    (root / 'src').mkdir()
    (root / 'src/train.py').write_text('''import json, pathlib, sys
import portability_dependency
configuration = json.loads(pathlib.Path('configuration.json').read_text(encoding='utf-8'))
assert pathlib.Path(sys.prefix).samefile(configuration['expected_prefix'])
assert sys.prefix != sys.base_prefix
assert portability_dependency.VALUE == 37
print('venv-entry-and-dependency-preserved: 中文日志')
''', encoding='utf-8')
    snapshot = freeze_snapshot(root, 'relative-run', make_spec(root), frozen, ['src/train.py'],
        {'variant': {'augmentation': 0}, 'seed': 11, 'expected_prefix': str(interpreter.parent.parent)},
        'src/train.py', 'baseline', 11, arguments=[])
    start_execution(root, 'relative-run', snapshot)
    monkeypatch.chdir(tmp_path)
    observed = verify_environment(root, frozen)
    if not legacy:
        assert Path(observed['prefix']).samefile(interpreter.parent.parent)
    result = launch_execution(root, 'relative-run', timeout=15)
    assert result['exit_code'] == 0, (root / 'runs/relative-run/process.log').read_text(errors='replace')
    assert 'venv-entry-and-dependency-preserved' in (root / 'runs/relative-run/process.log').read_text()
    assert '中文日志' in (root / 'runs/relative-run/process.log').read_text(encoding='utf-8')
    assert verify_ref(root, frozen).read_bytes() == before


@pytest.mark.parametrize('omit_suffix', [False,
    pytest.param(True, marks=pytest.mark.skipif(os.name != 'nt', reason='Windows PATH omits the executable suffix'))])
def test_path_alias_is_pinned_before_path_changes(tmp_path, isolated_python, monkeypatch, omit_suffix):
    interpreter, _ = isolated_python
    monkeypatch.setenv('PATH', str(interpreter.parent))
    registry, reference = candidate(tmp_path, interpreter.stem if omit_suffix else interpreter.name)
    frozen = promote(registry, reference)
    for check in read_record(verify_ref(tmp_path, frozen))['test_receipts']:
        command_entry = read_record(verify_ref(tmp_path, check))['command'][0]
        assert Path(command_entry).is_absolute()
        assert os.path.normcase(command_entry) == os.path.normcase(str(interpreter.absolute()))
    monkeypatch.setenv('PATH', '')
    assert Path(verify_environment(tmp_path, frozen)['interpreter']).samefile(interpreter)
    assert os.path.normcase(read_record(verify_ref(tmp_path, frozen))['interpreter']) == os.path.normcase(str(interpreter.absolute()))


def test_noisy_imports_have_a_separate_fingerprint_frame_and_diagnostics(tmp_path, isolated_python):
    interpreter, site = isolated_python
    (site / 'noisy_dependency.py').write_text('''import sys
print('package initialization notice: 中文日志')
print('{"interpreter":"unrelated log JSON"}')
print('EVOINQUIRY_FINGERPRINT_log_only:{}')
sys.stderr.write('package stderr notice: 中文错误日志\\n')
__version__ = '1.0'
''', encoding='utf-8')
    diagnostics = {}
    observed = probe_environment(interpreter, ['noisy_dependency', 'sys', 'math'], diagnostics=diagnostics)
    assert observed['imports']['noisy_dependency']['kind'] == 'file'
    assert observed['imports']['sys']['kind'] == 'builtin'
    assert observed['imports']['math']['kind'] in ('builtin', 'extension')
    assert diagnostics['exit_code'] == 0
    assert 'package initialization notice' in diagnostics['stdout']
    assert '中文日志' in diagnostics['stdout']
    assert 'unrelated log JSON' in diagnostics['stdout']
    assert diagnostics['stderr'].splitlines() == ['package stderr notice: 中文错误日志']
    assert not (tmp_path / '.ei').exists()


def test_inspect_cli_returns_noisy_diagnostics_without_initializing_project(tmp_path, isolated_python):
    interpreter, site = isolated_python
    (site / 'cli_dependency.py').write_text('print("CLI import notice: 中文")\n', encoding='utf-8')
    tool = Path(__file__).resolve().parents[1] / 'tools/environment_registry.py'
    process = subprocess.run([sys.executable, '-B', str(tool), '--root', str(tmp_path),
        'inspect', '--interpreter', str(interpreter), '--imports', 'cli_dependency', '--diagnostics'],
        capture_output=True, env=dict(os.environ, PYTHONIOENCODING='ascii'))
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout.decode('utf-8'))
    assert result['fingerprint']['fingerprint_version'] == 2
    assert 'CLI import notice' in result['probe_diagnostics']['stdout']
    assert '中文' in result['probe_diagnostics']['stdout']
    assert result['probe_diagnostics']['exit_code'] == 0
    assert not (tmp_path / '.ei').exists()


@pytest.mark.parametrize('tool', ['project_registry', 'filesystem_doctor', 'state_paths'])
def test_readonly_governance_cli_emits_unicode_under_ascii_output(tmp_path, tool):
    root = tmp_path / '项目 with spaces'
    root.mkdir()
    script = Path(__file__).resolve().parents[1] / 'tools' / (tool + '.py')
    arguments = (['--directory', str(root)] if tool == 'filesystem_doctor'
                 else ['--root', str(root), '--mode', 'read'] if tool == 'state_paths'
                 else ['--root', str(root), 'audit'])
    process = subprocess.run([sys.executable, '-B', str(script), *arguments], capture_output=True,
        env=dict(os.environ, PYTHONIOENCODING='ascii'))
    assert process.returncode == 0, process.stderr
    decoded = process.stdout.decode('utf-8')
    if tool == 'state_paths':
        assert '项目' in decoded
    else:
        result = json.loads(decoded)
        assert Path(result['directory' if tool == 'filesystem_doctor' else 'root']).samefile(root)
    assert not (root / '.ei').exists()


@pytest.mark.parametrize('tool,command', [('artifact_registry', 'resolve'), ('execution_registry', 'verify-snapshot')])
def test_governance_cli_keeps_unicode_errors_readable_under_ascii_output(tmp_path, tool, command):
    script = Path(__file__).resolve().parents[1] / 'tools' / (tool + '.py')
    process = subprocess.run([sys.executable, '-B', str(script), '--root', str(tmp_path),
        command, '--ref', str(tmp_path / '缺失.json')], capture_output=True,
        env=dict(os.environ, PYTHONIOENCODING='ascii'))
    assert process.returncode == 2
    assert '缺失.json' in process.stderr.decode('utf-8')
    assert not process.stdout
    assert not (tmp_path / '.ei').exists()


def test_code_map_cli_preserves_unicode_purpose_and_path_under_ascii_output(tmp_path):
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src/模型.py').write_text('def greeting():\n    """中文用途。"""\n    return 1\n', encoding='utf-8')
    script = Path(__file__).resolve().parents[1] / 'tools/code_map.py'
    process = subprocess.run([sys.executable, '-B', str(script), '--root', str(tmp_path),
        'build', '--paths', 'src/模型.py', '--output', 'docs/code-map.json'], capture_output=True,
        env=dict(os.environ, PYTHONIOENCODING='ascii'))
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout.decode('utf-8'))
    assert result['symbols'][0]['purpose'] == '中文用途。'
    assert result['symbols'][0]['path'] == 'src/模型.py'
    assert read_record(tmp_path / 'docs/code-map.json') == result
    assert not (tmp_path / '.ei').exists()


@pytest.mark.parametrize('code,message', [
    ('import sys; print(sys.argv[4] + "{}"); print("duplicate")', 'one framed fingerprint'),
    ('import os,sys; print(sys.argv[4] + "[]", flush=True); os._exit(0)', 'invalid fingerprint'),
    ('import os,sys; print(sys.argv[4] + "bad-json", flush=True); os._exit(0)', 'not a fingerprint'),
    ('print("import diagnostic", flush=True); raise SystemExit(11)', 'exit 11'),
])
def test_probe_rejects_duplicate_invalid_or_failed_frames(tmp_path, isolated_python, code, message):
    interpreter, site = isolated_python
    (site / 'broken_dependency.py').write_text(code, encoding='utf-8')
    diagnostics = {}
    with pytest.raises(RegistryError, match=message):
        probe_environment(interpreter, ['broken_dependency'], diagnostics=diagnostics)
    assert diagnostics['exit_code'] == (11 if 'exit 11' in message else 0)
    assert not (tmp_path / '.ei').exists()


def test_probe_timeout_and_missing_executable_are_structured_errors(tmp_path, isolated_python):
    interpreter, site = isolated_python
    (site / 'slow_dependency.py').write_text('import time; print("starting", flush=True); time.sleep(30)', encoding='utf-8')
    diagnostics = {}
    with pytest.raises(RegistryError, match='could not complete'):
        probe_environment(interpreter, ['slow_dependency'], timeout=.3, diagnostics=diagnostics)
    assert diagnostics['exit_code'] is None
    with pytest.raises(RegistryError, match='could not complete'):
        probe_environment(tmp_path / 'nonexistent-python')
    assert not (tmp_path / '.ei').exists()


def test_namespace_source_drift_is_detected_and_legacy_profile_is_not_rewritten(tmp_path, isolated_python):
    interpreter, site = isolated_python
    for origin in ('source-a', 'source-b'):
        (site / origin / 'portability_namespace').mkdir(parents=True)
    locator = site / 'portability.pth'
    locator.write_text('source-a\n', encoding='ascii')
    legacy_before = probe_environment(interpreter, ['portability_namespace'], fingerprint_version=1)
    registry, reference = candidate(tmp_path, interpreter, imports=('portability_namespace',))
    frozen = promote(registry, reference)
    before = verify_ref(tmp_path, frozen).read_bytes()
    first = verify_environment(tmp_path, frozen)
    module = first['imports']['portability_namespace']
    assert module['kind'] == 'namespace' and module['path'] is None and module['origin'] is None
    assert module['search_locations'] == [str(site / 'source-a/portability_namespace')]
    locator.write_text('source-b\n', encoding='ascii')
    assert probe_environment(interpreter, ['portability_namespace'], fingerprint_version=1) == legacy_before
    assert probe_environment(interpreter, ['portability_namespace']) != first
    with pytest.raises(RegistryError, match='fingerprint changed'):
        verify_environment(tmp_path, frozen)
    assert verify_ref(tmp_path, frozen).read_bytes() == before


@pytest.mark.parametrize('body', [
    'def greeting():\n    """中文文档。"""\n    return "你好"\n'.encode('utf-8'),
    b'\xef\xbb\xbf' + 'def greeting():\n    """中文文档。"""\n    return "你好"\n'.encode('utf-8'),
    '# coding: latin-1\ndef greeting():\n    """café documentation."""\n    return "café"\n'.encode('latin-1'),
])
def test_code_map_reads_python_source_encoding_and_hashes_original_bytes(tmp_path, body):
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src/source.py').write_bytes(body)
    compile(body, 'source.py', 'exec')
    mapping = build_map(tmp_path, ['src/source.py'])
    assert mapping['symbols'][0]['source_hash'] == hashlib.sha256(body).hexdigest()
    assert mapping['symbols'][0]['purpose'] in ('中文文档。', 'café documentation.')


@pytest.mark.parametrize('body', [b'def broken(:\n', b'# coding: nonexistent-codec\n', b'\xef\xbb\xbf# coding: latin-1\n'])
def test_code_map_still_rejects_invalid_python_source(tmp_path, body):
    (tmp_path / 'source.py').write_bytes(body)
    with pytest.raises((SyntaxError, UnicodeDecodeError)):
        build_map(tmp_path, ['source.py'])


@pytest.mark.parametrize('name', ['CON', 'nul', 'COM1', 'LPT1', 'con.txt', 'NUL.data', 'run.', 'run '])
def test_reserved_ids_and_evidence_components_fail_before_writes(tmp_path, name):
    with pytest.raises(RegistryError):
        identifier(name)
    with pytest.raises(RegistryError, match='path component'):
        local_path(tmp_path, 'reports/' + name)
    with pytest.raises(RegistryError, match='path component'):
        atomic_write(tmp_path / 'reports' / name, {'must_not_be_written': True})
    assert not (tmp_path / 'reports').exists()
    assert not (tmp_path / '.ei').exists()


@pytest.mark.parametrize('path', ['C:report.json', 'C:/report.json', r'\report.json', r'reports\report.json', 'reports/file:stream', 'reports/../outside'])
def test_nonportable_or_drive_relative_references_are_rejected(tmp_path, path):
    with pytest.raises(RegistryError):
        local_path(tmp_path, path)
    assert list(tmp_path.iterdir()) == []


def test_portable_paths_and_metadata_only_project_label_are_supported(tmp_path):
    root = tmp_path / '项目 with spaces'
    root.mkdir()
    init_project(root, 'CON')  # A metadata label does not become a filename.
    target = local_path(root, 'reports/中文 results.json')
    atomic_write(target, {'中文': True})
    assert read_record(target) == {'中文': True}
    assert inspect_directory(root)['probe_performed'] is False


@pytest.mark.skipif(sys.platform != 'win32', reason='NTFS Junction requires a native Windows runner')
@pytest.mark.parametrize('relative', ['.ei', '.aris', '.ei-migration', 'reports', 'src'])
@pytest.mark.parametrize('fallback', [False, True])
def test_native_windows_junction_cannot_redirect_state_evidence_or_doctor(tmp_path, relative, fallback, monkeypatch):
    root, outside = tmp_path / 'project', tmp_path / 'outside'
    root.mkdir()
    outside.mkdir()
    marker = outside / 'sentinel.txt'
    marker.write_bytes(b'unchanged outside project')
    link = root / relative
    created = subprocess.run(['cmd.exe', '/c', 'mklink', '/J', str(link), str(outside)], capture_output=True)
    assert created.returncode == 0, created.stdout + created.stderr
    if fallback:
        monkeypatch.setattr(Path, 'is_junction', None)  # Exercise the Python 3.10/3.11 stat fallback on NTFS.
    assert is_junction(link) and not link.is_symlink()
    with pytest.raises(RegistryError, match='Junction'):
        local_path(root, relative + '/record.json')
    with pytest.raises(RegistryError, match='Junction'):
        atomic_write(link / 'record.json', {'redirected': True})
    with pytest.raises(RegistryError, match='Junction'):
        inspect_directory(link)
    with pytest.raises(RegistryError, match='Junction'):
        probe_directory(link)
    if relative in ('.ei', '.aris', '.ei-migration'):
        with pytest.raises(RegistryError):
            init_project(root, 'junction-negative')
        with pytest.raises(RegistryError):
            resolve_state_root(root, 'read')
        with pytest.raises(RegistryError):
            inventory(root)
    else:
        with pytest.raises(RegistryError, match='Junction'):
            tree_inventory(root)
    assert list(outside.iterdir()) == [marker]
    assert marker.read_bytes() == b'unchanged outside project'


@pytest.mark.skipif(sys.platform != 'win32', reason='Case insensitive identity requires a Windows runner')
def test_native_windows_consumer_case_collision_preserves_original_binding(tmp_path):
    environment = make_environment(tmp_path)
    registry = EnvironmentRegistry(tmp_path)
    original = consumer(environment, 'method-a', lifecycle='completed')
    reference = registry.bind_consumer(original)
    before = (tmp_path / '.ei/consumers/method-a.json').read_bytes()
    with pytest.raises(RegistryError, match='collides'):
        registry.bind_consumer(dict(original, consumer_id='METHOD-A'))
    assert (tmp_path / '.ei/consumers/method-a.json').read_bytes() == before
    assert read_record(verify_ref(tmp_path, reference)) == original
