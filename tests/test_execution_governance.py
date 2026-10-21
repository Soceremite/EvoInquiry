"""Actual CPU execution verifies frozen inputs, retries, recovery and code-map drift."""
import json
import multiprocessing
from pathlib import Path
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from tests.governance_helpers import make_environment, make_sources, make_spec
from tools.code_map import build_map, check_freshness, resolve_symbol
from tools.execution_registry import (freeze_snapshot, launch_execution, select_attempts,
                                      start_execution, verify_snapshot, clone_attempt, reconcile_execution,
                                      request_stop_execution, register_spec, spec_digest)
from tools.registry_common import RegistryError, atomic_write, fixed_ref, now, read_record
from tools import research_control, run_state


def _prepare_observable_worker(root, *, seconds=15, interval=None, graceful=False):
    sources, spec, environment = make_sources(root), make_spec(root), make_environment(root)
    (root / 'src/train.py').write_text('''import json, os, pathlib, signal, subprocess, sys, time
output=pathlib.Path(sys.argv[1]); output.mkdir(parents=True,exist_ok=True)
if GRACEFUL:
    def on_stop(signum, frame):
        (output/'saved-before-stop.json').write_text(json.dumps({'signal':signum}))
        raise SystemExit(0)
    signal.signal(signal.SIGTERM,on_stop)
child_code="import pathlib, signal, sys, time; signal.signal(signal.SIGTERM,signal.SIG_IGN); pathlib.Path(sys.argv[1]).write_text('ready'); time.sleep(60)"
child=subprocess.Popen([sys.executable,'-I','-c',child_code,str(output/'child-ready')]) if os.name=='posix' else None
while child is not None and not (output/'child-ready').exists(): time.sleep(0.01)
(output/'ready.json').write_text(json.dumps({'pid':os.getpid(),'child_pid':child.pid if child else None}))
time.sleep(60)
'''.replace('GRACEFUL', repr(graceful)))
    if seconds != 15:
        record = read_record(root / spec['path'])
        record.update(experiment_id='timeout-fixture', budget={'max_seconds_per_attempt':seconds})
        record['spec_sha256'] = spec_digest(record)
        spec = register_spec(root, record)
    run_state.start_run(str(root), 'owned-workflow', ['explore'])
    research_control.configure(root, 'owned-workflow', 'observe owned stop', {
        'max_actions':4,'wall_seconds':120,'max_attempts_per_key':1,
        'resources':{'cpu_seconds':60}}, reflection_interval_seconds=interval)
    output = root / 'runs/owned/outputs'
    args = [str(output)]
    snapshot = freeze_snapshot(root, 'owned', spec, environment, sources,
        {'variant':{'augmentation':0.1},'seed':22}, 'src/train.py','method-b',22,
        arguments=args,output_argument_indices=[0])
    start_execution(root,'owned',snapshot,workflow_run_id='owned-workflow')
    action = research_control.claim_action(root,'owned-workflow','owned','explore',
        'Observe actual cancellation',costs={'cpu_seconds':30},input_refs=[snapshot])['action']
    return args, output, action


def _await_file(path, future, seconds=10):
    deadline=time.monotonic()+seconds
    while not path.exists() and time.monotonic()<deadline:
        if future.done():
            raise AssertionError(f'Worker exited before observation: {future.result()}')
        time.sleep(0.02)
    assert path.exists(), path


def _linux_running(pid):
    path=Path('/proc')/str(pid)/'stat'
    return path.exists() and path.read_text().split(') ',1)[1][0]!='Z'


@pytest.mark.skipif(sys.platform!='linux', reason='Owned process-group observation uses Linux procfs')
@pytest.mark.parametrize('source',['workflow','execution','elapsed-review'])
def test_stop_intent_reaches_the_owned_process_group_and_preserves_other_work(tmp_path,source):
    args, output, action = _prepare_observable_worker(tmp_path, interval=0.1 if source=='elapsed-review' else None)
    unrelated=subprocess.Popen([sys.executable,'-I','-c','import time; time.sleep(60)'])
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(launch_execution,tmp_path,'owned',args)
            _await_file(output/'ready.json',future)
            identities=read_record(output/'ready.json')
            if source=='elapsed-review':
                inspection=research_control.inspect(tmp_path,'owned-workflow')
                assert inspection['reflection_gate']['reasons']==['elapsed_review_interval']
                assert _linux_running(identities['pid']) and _linux_running(identities['child_pid'])
            started=time.monotonic()
            if source=='execution':
                request=request_stop_execution(tmp_path,'owned','This attempt no longer answers the question')
                assert request_stop_execution(tmp_path,'owned','This attempt no longer answers the question')==request
            else:
                research_control.stop(tmp_path,'owned-workflow','No further training is justified')
            result=future.result(timeout=12)
            assert time.monotonic()-started<10
        terminal=read_record(tmp_path/'runs/owned/execution.final.json')
        receipt=read_record(tmp_path/'runs/owned/termination.json')
        assert result['exit_code']!=0 and terminal['status']=='stopped'
        assert receipt['cause']==('execution_stop' if source=='execution' else 'workflow_stop')
        assert receipt['parent_exited'] and receipt['pid']==identities['pid']
        assert not _linux_running(identities['pid'])
        deadline=time.monotonic()+3
        while _linux_running(identities['child_pid']) and time.monotonic()<deadline:
            time.sleep(0.02)
        assert not _linux_running(identities['child_pid'])
        assert unrelated.poll() is None
        assert research_control.inspect(tmp_path,'owned-workflow')['status']=='RECONCILE'
        settled=research_control.settle_execution(tmp_path,'owned-workflow',action['id'],'owned',
            actual_costs={'cpu_seconds':1},reason='Actual owned process group stopped')
        assert settled['actions'][0]['status']=='cancelled'
        assert research_control.inspect(tmp_path,'owned-workflow')['status']==('READY' if source=='execution' else 'STOPPED')
    finally:
        unrelated.terminate(); unrelated.wait(timeout=5)


@pytest.mark.skipif(sys.platform!='linux', reason='Cooperative SIGTERM acceptance uses Linux process groups')
def test_cooperative_zero_exit_is_cancelled_and_excluded_from_successful_aggregation(tmp_path):
    args,output,action=_prepare_observable_worker(tmp_path,graceful=True)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(launch_execution,tmp_path,'owned',args)
        _await_file(output/'ready.json',future)
        request_stop_execution(tmp_path,'owned','Stop after saving the latest state')
        result=future.result(timeout=12)
    terminal=read_record(tmp_path/'runs/owned/execution.final.json')
    receipt=read_record(tmp_path/'runs/owned/termination.json')
    assert (output/'saved-before-stop.json').is_file()
    assert result['exit_code']==receipt['exit_code']==0
    assert terminal['status']=='stopped' and receipt['parent_exited']
    settled=research_control.settle_execution(tmp_path,'owned-workflow',action['id'],'owned',
        actual_costs={'cpu_seconds':1},reason='Cooperative cancellation, not successful completion')
    assert settled['actions'][0]['status']=='cancelled'
    selection=select_attempts(tmp_path,terminal['spec_ref'],[result['execution_ref']])
    assert selection['attempts'][0]['included'] is False
    assert selection['attempts'][0]['reason']=='stopped'
    assert ('method-b',22) in selection['missing_slots']


@pytest.mark.parametrize('cancelled',[True,False,None])
def test_observed_zero_exit_recovery_preserves_explicit_cancellation_and_legacy_completion(tmp_path,cancelled):
    sources,spec,environment=make_sources(tmp_path),make_spec(tmp_path),make_environment(tmp_path)
    prepare(tmp_path,'observed',spec,environment,sources)
    # Simulate interrupted terminal metadata after an independent observer has
    # established actual exit. No process is launched by reconciliation.
    path=tmp_path/'runs/observed/execution.json'
    record=read_record(path); record['status']='running'; atomic_write(path,record)
    receipt=dict(execution_run_id='observed',job_ref=None,process_alive=False,queued=False,
                 confirmed_at=now(),source='independent-test-observer',exit_code=0)
    if cancelled is not None: receipt['stopped']=cancelled
    atomic_write(tmp_path/'observed-exit.json',receipt)
    reference=reconcile_execution(tmp_path,'observed',termination_ref=fixed_ref(tmp_path,'observed-exit.json'))
    final=read_record(tmp_path/reference['path'])
    assert final['status']==('stopped' if cancelled else 'completed')
    selection=select_attempts(tmp_path,spec,[reference])
    assert selection['attempts'][0]['included'] is (cancelled is not True)


def test_spec_timeout_is_enforced_when_the_caller_omits_a_timeout(tmp_path):
    args,output,action=_prepare_observable_worker(tmp_path,seconds=0.5)
    result=launch_execution(tmp_path,'owned',args)
    receipt=read_record(tmp_path/'runs/owned/termination.json')
    assert result['exit_code']!=0 and receipt['cause']=='timeout'
    assert read_record(tmp_path/'runs/owned/process.json')['effective_timeout_seconds']==0.5


def test_stopped_workflow_and_invalid_timeouts_never_launch_a_prepared_execution(tmp_path):
    args,_,_=_prepare_observable_worker(tmp_path)
    for timeout in (0,-1,True,float('nan'),float('inf')):
        with pytest.raises(RegistryError,match='finite and positive'):
            launch_execution(tmp_path,'owned',args,timeout=timeout)
    research_control.stop(tmp_path,'owned-workflow','Stop before actual launch')
    with pytest.raises(RegistryError,match='already stopped'):
        launch_execution(tmp_path,'owned',args)
    assert not (tmp_path/'runs/owned/process.json').exists()
    assert read_record(tmp_path/'runs/owned/execution.json')['status']=='prepared'


def prepare(root, run_id, spec, environment, sources, *, failure=False, parent=None):
    configuration = {'variant':{'augmentation':0.1},'seed':22,'inject_failure':failure}
    snapshot = freeze_snapshot(root, run_id, spec, environment, sources, configuration,
                               'src/train.py', 'method-b',22)
    start_execution(root,run_id,snapshot,retry_of=parent)
    return snapshot


def test_checkout_and_development_recipe_changes_do_not_change_queued_snapshot(tmp_path):
    sources, spec, environment = make_sources(tmp_path), make_spec(tmp_path), make_environment(tmp_path)
    snapshot = prepare(tmp_path,'run-1',spec,environment,sources)
    (tmp_path / 'src/research_shared/data.py').write_text('raise RuntimeError("mutable checkout")')
    (tmp_path / 'env/recipes/cpu/r001/lock.json').write_text('{}')
    result = launch_execution(tmp_path,'run-1',[str(tmp_path / 'runs/run-1/outputs/metrics.json')],timeout=15)
    assert result['exit_code'] == 0
    imports = read_record(tmp_path / 'runs/run-1/import-paths.json')
    assert Path(imports['research_shared.data']).is_relative_to(tmp_path / 'runs/run-1/snapshot')
    assert verify_snapshot(tmp_path,snapshot)['seed']==22
    with pytest.raises(RegistryError,match='only once'):
        launch_execution(tmp_path,'run-1')


def test_failure_and_retry_keep_separate_terminal_attempts_and_use_declared_aggregation(tmp_path):
    sources, spec, environment = make_sources(tmp_path), make_spec(tmp_path), make_environment(tmp_path)
    prepare(tmp_path,'run-a',spec,environment,sources,failure=True)
    failed=launch_execution(tmp_path,'run-a',timeout=15)
    assert failed['exit_code']==7
    prepare(tmp_path,'run-b',spec,environment,sources,parent='run-a')
    good=launch_execution(tmp_path,'run-b',[str(tmp_path / 'runs/run-b/outputs/metrics.json')],timeout=15)
    assert good['exit_code']==0
    analysis=select_attempts(tmp_path,spec,[failed['execution_ref'],good['execution_ref']])
    assert [row['included'] for row in analysis['attempts']]==[False,True]
    assert analysis['attempts'][1]['record']['retry_of']=='run-a'
    assert len(analysis['missing_slots'])==5
    assert analysis['scientific_verdict']=='not-assessed'
    with pytest.raises(RegistryError,match='Duplicate'):
        select_attempts(tmp_path,spec,[good['execution_ref'],good['execution_ref']])


def test_snapshot_corruption_extra_sources_and_credentials_are_rejected(tmp_path):
    sources, spec, environment = make_sources(tmp_path), make_spec(tmp_path), make_environment(tmp_path)
    snapshot=prepare(tmp_path,'run-1',spec,environment,sources)
    (tmp_path / 'runs/run-1/snapshot/rogue.py').write_text('print("unexpected")')
    with pytest.raises(RegistryError,match='unapproved'):
        verify_snapshot(tmp_path,snapshot)
    with pytest.raises(RegistryError,match='Credentials'):
        freeze_snapshot(tmp_path,'run-secret',spec,environment,sources,
                        {'variant':{'augmentation':0.1},'seed':22,'api_key':'do-not-copy'},
                        'src/train.py','method-b',22)


def test_checkpoint_recovery_requires_new_identity_and_a_fixed_checkpoint(tmp_path):
    sources, spec, environment = make_sources(tmp_path), make_spec(tmp_path), make_environment(tmp_path)
    prepare(tmp_path,'run-failed',spec,environment,sources,failure=True)
    launch_execution(tmp_path,'run-failed',timeout=15)
    (tmp_path / 'runs/run-failed/checkpoint.bin').write_bytes(b'validated-fixture-checkpoint')
    configuration={'variant':{'augmentation':0.1},'seed':22}
    snapshot=freeze_snapshot(tmp_path,'run-resumed',spec,environment,sources,configuration,
                              'src/train.py','method-b',22)
    with pytest.raises(RegistryError,match='both'):
        start_execution(tmp_path,'run-resumed',snapshot,resumed_from='run-failed')
    record=start_execution(tmp_path,'run-resumed',snapshot,resumed_from='run-failed',
                           checkpoint_ref=fixed_ref(tmp_path,'runs/run-failed/checkpoint.bin'))
    assert record['resumed_from']=='run-failed' and record['checkpoint_ref']['sha256']


def test_code_map_detects_signature_semantic_and_documentation_drift(tmp_path):
    make_sources(tmp_path)
    (tmp_path / 'tests').mkdir()
    (tmp_path / 'tests/test_shared.py').write_text('def test_contract(): pass\n')
    annotations={'research_shared.data.make_batches':{'reuse_example':'make_batches(11)',
                    'tests':['tests/test_shared.py::test_contract'],'callers':['train']}}
    mapping=build_map(tmp_path,['src/research_shared/data.py'],annotations)
    assert check_freshness(tmp_path,mapping)['status']=='PASS'
    assert resolve_symbol(mapping,'research_shared.data.make_batches')['path']=='src/research_shared/data.py'
    path=tmp_path / 'src/research_shared/data.py'
    path.write_text(path.read_text().replace('ids = list(range(6))','ids = list(range(9))'))
    issues=check_freshness(tmp_path,mapping)['issues']
    assert {row['reason'] for row in issues}>={'source-stale','documentation-review-needed'}
    path.write_text(path.read_text().replace('seed, augmentation=0','seed, augmentation=0, hidden=True'))
    assert 'public-interface-changed' in {row['reason'] for row in check_freshness(tmp_path,mapping)['issues']}


def test_retry_allocation_recovers_and_only_declared_output_arguments_move(tmp_path):
    sources, spec, environment = make_sources(tmp_path), make_spec(tmp_path), make_environment(tmp_path)
    arguments = [str(tmp_path / 'runs/failed/outputs/metrics.json'),str(tmp_path / 'runs/failed/input.json')]
    snapshot = freeze_snapshot(tmp_path,'failed',spec,environment,sources,
        {'variant':{'augmentation':0.1},'seed':22,'inject_failure':True},
        'src/train.py','method-b',22,arguments=arguments,output_argument_indices=[0])
    start_execution(tmp_path,'failed',snapshot)
    launch_execution(tmp_path,'failed',arguments,timeout=15)
    retry = clone_attempt(tmp_path,'failed','retry')
    assert clone_attempt(tmp_path,'failed','retry')==retry
    manifest = verify_snapshot(tmp_path,retry['snapshot_ref'])
    assert manifest['arguments'][0]==arguments[0].replace('runs/failed/','runs/retry/')
    assert manifest['arguments'][1]==arguments[1]


def test_interrupted_final_projection_recovers_from_fixed_terminal_record(tmp_path,monkeypatch):
    import tools.execution_registry as module
    sources, spec, environment = make_sources(tmp_path), make_spec(tmp_path), make_environment(tmp_path)
    prepare(tmp_path,'run-1',spec,environment,sources)
    original=module.atomic_write
    def interrupted(path,data):
        if Path(path).name=='execution.json' and data.get('status')=='completed':
            raise OSError('interrupted terminal projection')
        return original(path,data)
    monkeypatch.setattr(module,'atomic_write',interrupted)
    with pytest.raises(OSError,match='interrupted'):
        launch_execution(tmp_path,'run-1',[str(tmp_path / 'runs/run-1/output.json')],timeout=15)
    monkeypatch.setattr(module,'atomic_write',original)
    final=fixed_ref(tmp_path,'runs/run-1/execution.final.json')
    assert read_record(tmp_path / 'runs/run-1/execution.json')['status']=='running'
    assert reconcile_execution(tmp_path,'run-1',final_ref=final)==final
    assert read_record(tmp_path / 'runs/run-1/execution.json')['status']=='completed'


def isolated_execution_worker(root, run_id, arguments, output):
    result = launch_execution(root,run_id,arguments,timeout=15)
    output.put(result['exit_code'])


def test_failed_process_identity_write_stops_owned_child_without_claiming_completion(tmp_path,monkeypatch):
    import tools.execution_registry as module
    sources, spec, environment = make_sources(tmp_path), make_spec(tmp_path), make_environment(tmp_path)
    (tmp_path / 'src/train.py').write_text('import time\ntime.sleep(60)\n')
    prepare(tmp_path,'identity-failure',spec,environment,sources)
    original_write, original_popen = module.atomic_write, module.subprocess.Popen
    launched=[]
    def launch(*args,**kwargs):
        process=original_popen(*args,**kwargs)
        if 'start_new_session' in kwargs:
            launched.append(process)
        return process
    def interrupted(path,data):
        if Path(path).name=='process.json':
            raise OSError('process identity storage failed')
        return original_write(path,data)
    monkeypatch.setattr(module.subprocess,'Popen',launch)
    monkeypatch.setattr(module,'atomic_write',interrupted)
    with pytest.raises(OSError,match='process identity storage failed'):
        launch_execution(tmp_path,'identity-failure',timeout=15)
    assert len(launched)==1 and launched[0].poll() is not None
    assert read_record(tmp_path / 'runs/identity-failure/execution.json')['status']=='running'
    assert not (tmp_path / 'runs/identity-failure/execution.final.json').exists()


def test_project_virtualenv_dependencies_are_allowed_but_mutable_checkout_imports_are_rejected(tmp_path):
    subprocess.run([sys.executable,'-I','-B','-m','venv','--without-pip',str(tmp_path / '.venv')],
                   check=True,capture_output=True,timeout=30)
    interpreter=tmp_path / '.venv' / ('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
    purelib=Path(subprocess.check_output([str(interpreter),'-I','-B','-c',
        'import sysconfig; print(sysconfig.get_paths()["purelib"])'],text=True).strip())
    dependency=purelib/'frozen_dependency'
    dependency.mkdir()
    (dependency/'__init__.py').write_text('__version__="1"\nVALUE=42\n')
    sources=make_sources(tmp_path)
    source=tmp_path / 'src/train.py'
    source.write_text(source.read_text()+
        '\nimport frozen_dependency\nassert frozen_dependency.VALUE==42\n'+
        f'if config.get("import_mutable"):\n    import sys\n    sys.path.insert(0,{str(tmp_path / "mutable")!r})\n    import mutable_dependency\n')
    (tmp_path/'mutable').mkdir()
    (tmp_path/'mutable/mutable_dependency.py').write_text('VALUE=42\n')
    spec=make_spec(tmp_path)
    environment=make_environment(tmp_path,interpreter=interpreter,imports=('math','frozen_dependency'))
    for run_id,mutable in [('venv-ok',False),('mutable-rejected',True)]:
        arguments=[str(tmp_path/'runs'/run_id/'outputs/metrics.json')]
        snapshot=freeze_snapshot(tmp_path,run_id,spec,environment,sources,
            {'variant':{'augmentation':0.1},'seed':22,'import_mutable':mutable},
            'src/train.py','method-b',22,arguments=arguments,output_argument_indices=[0])
        start_execution(tmp_path,run_id,snapshot)
        result=launch_execution(tmp_path,run_id,arguments,timeout=15)
        assert (result['exit_code']!=0)==mutable
    imports=read_record(tmp_path/'runs/venv-ok/import-paths.json')
    assert Path(imports['frozen_dependency']).is_relative_to(purelib)
    assert 'Mutable project import rejected' in (tmp_path/'runs/mutable-rejected/process.log').read_text()


def test_concurrent_consumers_share_frozen_environment_and_isolate_mutable_cache(tmp_path):
    sources, spec, environment = make_sources(tmp_path), make_spec(tmp_path), make_environment(tmp_path)
    script = tmp_path / 'src/train.py'
    script.write_text(script.read_text()+"\n(target.parent / 'mutable-cache.json').write_text(json.dumps({'seed':config['seed']}))\n")
    jobs=[]
    for seed in (11,33):
        run_id=f'isolated-{seed}'
        arguments=[str(tmp_path / 'runs' / run_id / 'outputs/metrics.json')]
        snapshot=freeze_snapshot(tmp_path,run_id,spec,environment,sources,
            {'variant':{'augmentation':0.1},'seed':seed},'src/train.py','method-b',seed,
            arguments=arguments,output_argument_indices=[0])
        start_execution(tmp_path,run_id,snapshot)
        jobs.append((run_id,arguments))
    before=(tmp_path / environment['path']).read_bytes()
    context=multiprocessing.get_context('spawn')
    output=context.Queue()
    workers=[context.Process(target=isolated_execution_worker,args=(str(tmp_path),run_id,args,output)) for run_id,args in jobs]
    for worker in workers:
        worker.start()
    assert [output.get(timeout=30) for _ in workers]==[0,0]
    for worker in workers:
        worker.join(10)
        assert worker.exitcode==0
    for seed in (11,33):
        assert read_record(tmp_path / f'runs/isolated-{seed}/outputs/mutable-cache.json')=={'seed':seed}
    assert (tmp_path / environment['path']).read_bytes()==before
