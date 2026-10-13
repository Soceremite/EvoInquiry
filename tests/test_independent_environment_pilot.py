"""Offline wheels exercise a real solver conflict and incompatible consumer API.

Only two new disposable venvs are installed. Existing control/training
interpreters remain unchanged. This is not a GPU ABI or public-package test.
"""
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from tools.environment_registry import (EnvironmentRegistry, environment_diff, probe_environment,
                                        run_environment_check, verify_environment)
from tools.registry_common import atomic_write, fixed_ref, read_record, verify_ref


def build_wheel(directory, distribution, version, module, content, requires=()):
    name = distribution.replace('-', '_')
    metadata = f'{name}-{version}.dist-info'
    files = {module + '.py': content.encode(),
             metadata + '/METADATA': ('Metadata-Version: 2.1\nName: ' + distribution +
                 '\nVersion: ' + version + '\n' + ''.join('Requires-Dist: ' + r + '\n' for r in requires)).encode(),
             metadata + '/WHEEL': b'Wheel-Version: 1.0\nGenerator: EvoInquiry offline acceptance\nRoot-Is-Purelib: true\nTag: py3-none-any\n'}
    record = ''.join(f'{path},sha256={base64.urlsafe_b64encode(hashlib.sha256(body).digest()).decode().rstrip("=")},{len(body)}\n'
                     for path, body in files.items()) + metadata + '/RECORD,,\n'
    files[metadata + '/RECORD'] = record.encode()
    directory.mkdir(parents=True, exist_ok=True)
    wheel = directory / f'{name}-{version}-py3-none-any.whl'
    with zipfile.ZipFile(wheel, 'w') as archive:
        for path, body in files.items():
            archive.writestr(path, body)
    return wheel


def command_receipt(root, name, command):
    result = subprocess.run(command, capture_output=True, timeout=120)
    log = root / 'installation' / (name + '.log')
    atomic_write(log, result.stdout + result.stderr)
    receipt = {'command': list(map(str, command)), 'exit_code': result.returncode,
               'output_ref': fixed_ref(root, log.relative_to(root)), 'scope': 'Owned isolated venv only; no index access'}
    atomic_write(root / 'installation' / (name + '.json'), receipt)
    return receipt


def register_environment(root, revision, interpreter, installation_ref, compatible, previous=None):
    observed = probe_environment(interpreter, ['evoi_pilot_kernel'])
    imports = observed['imports']['evoi_pilot_kernel']
    directory = root / 'env/recipes/kernel' / revision
    for name in ('recipe.json', 'lock.json', 'build.json'):
        atomic_write(directory / name, {'fingerprint': observed, 'installation_receipt': installation_ref})
    codes = {
        'metadata': 'import importlib.metadata; print(importlib.metadata.version("evoi-pilot-kernel"))',
        'imports': 'import evoi_pilot_kernel as k; print(k.__file__,k.__version__)',
        'numerical': 'import evoi_pilot_kernel as k; '
                     'y=k.normalize([1.,3.]' + (',scale=1.' if not compatible else '') + '); '
                     'assert y==[0.25,0.75]; print(y)',
        'consumers': 'import evoi_pilot_kernel as k; '
                     'assert k.normalize([1.,1.])==[0.5,0.5]; print("Existing method API works")',
    }
    receipts = [run_environment_check(root, interpreter, revision + '-' + stage, stage,
                    ['-I', '-B', '-c', code], observed, ['comparison-task'])
                for stage, code in codes.items()]
    record = {'schema_version':1, 'env_id':'kernel', 'revision':revision,
              'platform':observed['platform'], 'interpreter':str(interpreter),
              'expected_fingerprint':{'python':observed['python']},
              'observed_fingerprint':observed,'test_receipts':receipts,
              'lifecycle':'candidate','consumer_inventory_ref':None}
    for key,name in [('recipe_ref','recipe.json'),('lock_ref','lock.json'),('build_ref','build.json')]:
        record[key] = fixed_ref(root,(directory/name).relative_to(root))
    registry=EnvironmentRegistry(root)
    candidate=registry.record_candidate(record, environment_diff(previous or {},observed), receipts, ['comparison-task'])
    if not compatible:
        return candidate, observed
    approval={'approved':True,'candidate_ref':candidate,'confirmed_by':'authorized-isolated-pilot',
              'confirmed_at':'2026-10-13T00:00:00Z'}
    return registry.promote_candidate(candidate,approval,['comparison-task']),observed


def test_real_conflict_and_failed_consumer_preserve_frozen_environment(tmp_path):
    root=tmp_path
    wheels=root/'wheels'
    first=build_wheel(wheels,'evoi-pilot-kernel','1.0.0','evoi_pilot_kernel',
        '__version__="1.0.0"\ndef normalize(values):\n    return [v/sum(values) for v in values]\n')
    second=build_wheel(wheels,'evoi-pilot-kernel','2.0.0','evoi_pilot_kernel',
        '__version__="2.0.0"\ndef normalize(values,*,scale):\n    return [scale*v/sum(values) for v in values]\n')
    user=build_wheel(wheels,'evoi-pilot-consumer','1.0.0','evoi_pilot_consumer',
        'from evoi_pilot_kernel import normalize\n',requires=['evoi-pilot-kernel<2'])
    interpreters=[]
    for revision in ('r001','r002'):
        directory=root/'candidate-venvs'/revision
        receipt=command_receipt(root,'create-'+revision,[sys.executable,'-I','-B','-m','venv',str(directory)])
        assert receipt['exit_code']==0,receipt
        interpreters.append(directory/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python'))
    first_python,second_python=map(str,interpreters)
    installed=command_receipt(root,'install-r001',[first_python,'-I','-m','pip','--disable-pip-version-check',
                              'install','--no-index',str(first),str(user)])
    assert installed['exit_code']==0,installed
    frozen,observed=register_environment(root,'r001',first_python,
                                        fixed_ref(root,'installation/install-r001.json'),True)
    binding={'schema_version':1,'consumer_id':'comparison-task','project_id':'environment-pilot',
             'experiment_id':'comparison','entrypoint':'evoi_pilot_consumer','job_ref':'queued-task',
             'workflow_run_id':None,'execution_run_id':'queued-task','env_revision':frozen,
             'lease':None,'pin':[],'importance':'standard','lifecycle':'queued',
             'confirmed_by':'authorized-isolated-pilot','confirmed_at':'2026-10-13T00:00:00Z',
             'source':'independent-environment-acceptance'}
    registry=EnvironmentRegistry(root)
    bound=registry.bind_consumer(binding)
    old_record=verify_ref(root,frozen).read_bytes()
    old_module=Path(observed['imports']['evoi_pilot_kernel']['path'])
    old_bytes=old_module.read_bytes()
    conflict=command_receipt(root,'resolver-conflict',[second_python,'-I','-m','pip','--disable-pip-version-check',
                             'install','--no-index',str(second),str(user)])
    assert conflict['exit_code']!=0,conflict
    assert b'ResolutionImpossible' in verify_ref(root,conflict['output_ref']).read_bytes()
    installed_second=command_receipt(root,'install-r002',[second_python,'-I','-m','pip','--disable-pip-version-check',
                                  'install','--no-index',str(second)])
    assert installed_second['exit_code']==0,installed_second
    rejected,changed=register_environment(root,'r002',second_python,
        fixed_ref(root,'installation/install-r002.json'),False,observed)
    candidate=read_record(verify_ref(root,rejected))
    assert candidate['lifecycle']=='rejected'
    consumer_receipt=next(read_record(verify_ref(root,r)) for r in candidate['test_receipts']
                         if read_record(verify_ref(root,r))['stage']=='consumers')
    assert consumer_receipt['exit_code']!=0
    assert b'TypeError' in verify_ref(root,consumer_receipt['output_ref']).read_bytes()
    assert verify_ref(root,frozen).read_bytes()==old_record and old_module.read_bytes()==old_bytes
    assert verify_environment(root,frozen)==observed
    assert read_record(verify_ref(root,bound))['env_revision']==frozen
    assert read_record(root/'.ei/consumers/comparison-task.json')['env_revision']==frozen
    assert registry.find_compatible({'imports':{'evoi_pilot_kernel':observed['imports']['evoi_pilot_kernel']}})==[frozen]
    atomic_write(root/'acceptance-summary.json',{'status':'PASS','solver_conflict':conflict,
        'failed_candidate':rejected,'failed_consumer_receipt':consumer_receipt,
        'frozen_environment':frozen,'unchanged_binding':bound,'old_package_bytes_unchanged':True,
        'scope':'Actual offline pip solver and consumer API checks; GPU ABI not assessed here'})
