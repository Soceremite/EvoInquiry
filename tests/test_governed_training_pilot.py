"""Real training connects fixed execution identities with checkpoint restoration.

Optional EI_PILOT_TRAINING_PYTHON selects an existing, unchanged PyTorch
interpreter; EI_PILOT_DEVICE selects cpu or an authorized CUDA device. Missing
PyTorch skips, while an explicitly requested unavailable GPU fails acceptance.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from tools.artifact_registry import ArtifactRegistry
from tools.checkpoint_retention import CheckpointStore
from tools.environment_registry import EnvironmentRegistry, probe_environment, run_environment_check
from tools.execution_registry import (clone_attempt, freeze_snapshot, launch_execution,
                                      register_spec, select_attempts, spec_digest, start_execution)
from tools.project_registry import init_project
from tools.registry_common import atomic_write, digest, fixed_ref, read_record, verify_ref

REPO = Path(__file__).resolve().parents[1]


def training_environment(root, interpreter, device):
    observed = probe_environment(interpreter, ['torch'], device_probe=device.startswith('cuda'))
    directory = root / 'env/recipes/torch/r001'
    for filename in ('recipe.json', 'lock.json', 'build.json'):
        atomic_write(directory / filename, {'interpreter': interpreter, 'fingerprint': observed,
                     'installation': 'Existing interpreter inspected without changing dependencies'})
    programs = {
        'metadata': 'import sys; assert sys.version_info >= (3,10); print(sys.version)',
        'imports': 'import torch; print(torch.__version__); print(torch.__file__)',
        'numerical': 'import torch; d=torch.device(' + repr(device) + '); '
                     'x=torch.arange(8,dtype=torch.float64,device=d); '
                     'assert float(x @ x)==140.; print(d, float(x @ x))',
        'consumers': 'import torch; d=torch.device(' + repr(device) + '); '
                     'model=torch.nn.Linear(8,1).double().to(d); '
                     'opt=torch.optim.AdamW(model.parameters()); '
                     'x=torch.ones(16,8,dtype=torch.float64,device=d); '
                     'loss=model(x).square().mean(); loss.backward(); opt.step(); '
                     'assert torch.isfinite(loss); print("trainer-shape/optimizer-ok",d)',
    }
    receipts = [run_environment_check(root, interpreter, 'torch-r001-' + stage, stage,
                                     ['-I', '-B', '-c', code], observed, ['baseline', 'method-b'])
                for stage, code in programs.items()]
    record = {'schema_version': 1, 'env_id': 'torch', 'revision': 'r001',
              'platform': observed['platform'], 'interpreter': interpreter,
              'expected_fingerprint': {'python': observed['python']},
              'observed_fingerprint': observed, 'test_receipts': receipts,
              'lifecycle': 'candidate', 'consumer_inventory_ref': None}
    for key, filename in [('recipe_ref', 'recipe.json'), ('lock_ref', 'lock.json'), ('build_ref', 'build.json')]:
        record[key] = fixed_ref(root, (directory / filename).relative_to(root))
    registry = EnvironmentRegistry(root)
    candidate = registry.record_candidate(record, [], receipts, ['baseline', 'method-b'])
    return registry.promote_candidate(candidate, {'approved': True, 'candidate_ref': candidate,
        'confirmed_by': 'authorized-disposable-pilot', 'confirmed_at': '2026-10-13T00:00:00Z'},
        ['baseline', 'method-b'])


def training_spec(root):
    files = {
        'protocol': {'dtype': 'float64', 'shape': [128,8], 'train_ids': list(range(96)),
                     'validation_ids': list(range(96,128)), 'test_used': False},
        'data': {'generator': 'torch.randn', 'seed': 2026, 'samples': 128,
                 'target': '0.8*x0 - 0.2*x1'},
        'split': {'train': list(range(96)), 'validation': list(range(96,128))},
        'evaluator': {'metric': 'validation MSE', 'dtype': 'float64'},
    }
    record = {'schema_version': 1, 'experiment_id': 'training-pilot', 'spec_revision': 'r001',
              'hypothesis': 'Engineering acceptance of governed training and full-state restoration',
              'variants': [{'variant_id': 'baseline', 'configuration': {'augmentation': 0}},
                           {'variant_id': 'method-b', 'configuration': {'augmentation': 0.1}}],
              'seeds': [11,22,33],
              'budget': {'steps': 24, 'checkpoint_bytes_per_run': 512_000,
                         'max_seconds_per_attempt': 60},
              'decision_rule': {'scientific_verdict': 'not-assessed'},
              'failure_policy': {'aggregation': 'first-success',
                                 'description': 'Retain interruption; resume once; separate restoration control spec'}}
    for key, content in files.items():
        atomic_write(root / 'data' / (key + '.json'), content)
        record[key + '_ref'] = fixed_ref(root, 'data/' + key + '.json')
    record['spec_sha256'] = spec_digest(record)
    return register_spec(root, record)


def test_real_training_restoration_and_bounded_storage(tmp_path):
    interpreter = os.environ.get('EI_PILOT_TRAINING_PYTHON', sys.executable)
    available = subprocess.run([interpreter, '-I', '-B', '-c',
        'import importlib.util; raise SystemExit(0 if importlib.util.find_spec("torch") else 1)'],
        capture_output=True, timeout=10)
    if available.returncode:
        pytest.skip('Real PyTorch interpreter is not available')
    device = os.environ.get('EI_PILOT_DEVICE', 'cpu')
    root = tmp_path
    init_project(root, 'training-acceptance', 'governed-v1')
    environment = training_environment(root, interpreter, device)
    spec = training_spec(root)
    (root / 'src').mkdir()
    shutil.copy2(REPO / 'tests/pilots/governed_train.py', root / 'src/train.py')
    shutil.copy2(REPO / 'tools/checkpoint_retention.py', root / 'src/checkpoint_retention.py')
    sources = ['src/train.py', 'src/checkpoint_retention.py']
    attempts, metrics, recovery_reference = [], {}, None

    def execute(run_id, variant, seed, augmentation, stop_step=None, spec_ref=spec):
        args = [str(root / 'runs' / run_id / 'outputs/metrics.json')]
        config = {'variant': {'augmentation': augmentation}, 'seed': seed,
                  'device': device, 'steps': 24, 'stop_step': stop_step}
        snapshot = freeze_snapshot(root, run_id, spec_ref, environment, sources, config,
                                  'src/train.py', variant, seed, arguments=args,
                                  output_argument_indices=[0])
        start_execution(root, run_id, snapshot, job_ref=run_id)
        return launch_execution(root, run_id, args, timeout=60)

    for variant, augmentation in [('baseline', 0), ('method-b', 0.1)]:
        for seed in (11,22,33):
            interrupted = variant == 'method-b' and seed == 22
            run_id = f'{variant}-{seed}'
            result = execute(run_id, variant, seed, augmentation, 12 if interrupted else None)
            assert result['exit_code'] == (17 if interrupted else 0), result
            attempts.append(result['execution_ref'])
            if interrupted:
                parent_store = CheckpointStore(root / 'runs' / run_id / 'outputs/checkpoints')
                recovery_path = parent_store.latest() / 'state.pt'
                recovery_reference = fixed_ref(root, recovery_path.relative_to(root))
                parent_store.pin(recovery_path.parent.name, 'Fixed input to the resumed execution')
                resumed_id = run_id + '-resumed'
                args = [str(root / 'runs' / resumed_id / 'outputs/metrics.json')]
                clone_attempt(root, run_id, resumed_id, checkpoint_ref=recovery_reference)
                result = launch_execution(root, resumed_id, args, timeout=60)
                assert result['exit_code'] == 0, result
                attempts.append(result['execution_ref'])
                terminal = read_record(verify_ref(root, result['execution_ref']))
                assert terminal['resumed_from'] == run_id and terminal['retry_of'] is None
                assert terminal['checkpoint_ref'] == recovery_reference
                run_id = resumed_id
            reference = fixed_ref(root, f'runs/{run_id}/outputs/metrics.json')
            metrics[(variant, seed)] = (reference, read_record(verify_ref(root, reference)))

    # Continuous restoration control is declared separately and never counted
    # as an extra primary seed result or used to choose the best attempt.
    control = read_record(verify_ref(root, spec))
    control.update(experiment_id='restoration-control', variants=[control['variants'][1]], seeds=[22])
    control['spec_sha256'] = spec_digest(control)
    control_spec = register_spec(root, control)
    control_result = execute('continuous-control', 'method-b', 22, 0.1, spec_ref=control_spec)
    assert control_result['exit_code'] == 0, control_result
    control_ref = fixed_ref(root, 'runs/continuous-control/outputs/metrics.json')
    continuous = read_record(verify_ref(root, control_ref))
    resumed = metrics[('method-b',22)][1]
    assert resumed['start_step'] == 12 and continuous['start_step'] == 0
    for key in ('model_state', 'optimizer_state', 'scheduler_state', 'python_rng',
                'cpu_rng', 'device_rng', 'validation_loss', 'best_validation_loss'):
        assert resumed[key] == continuous[key], key
    for reference, metric in metrics.values():
        assert metric['step'] == 24 and metric['save_peak_bytes'] <= metric['save_budget_bytes']
        assert set(metric['train_ids']).isdisjoint(metric['validation_ids'])
        run_id = metric['execution_run_id']
        store = CheckpointStore(root / 'runs' / run_id / 'outputs/checkpoints')
        assert store.status()['lifecycle']['state'] == 'completed'
        assert not any(e['kind'] == 'resume' for e in store._read()['entries'])
    assert verify_ref(root, recovery_reference).is_file()
    analysis = select_attempts(root, spec, attempts)
    assert len(attempts) == 7 and not analysis['missing_slots']
    assert sum(row['included'] for row in analysis['attempts']) == 6
    report = {'scope': 'Real training engineering acceptance; research claims not assessed',
              'device': device, 'environment': environment, 'spec_ref': spec,
              'analysis': analysis, 'metrics': [v[0] for v in metrics.values()],
              'restoration_control': control_result['execution_ref'],
              'control_metrics': control_ref, 'resumed_checkpoint': recovery_reference,
              'full_state_restoration_identical': True,
              'peak_save_bytes': max(v[1]['save_peak_bytes'] for v in metrics.values()),
              'peak_device_allocated_bytes': max(v[1]['device_peak_allocated_bytes'] for v in metrics.values())}
    body = json.dumps(report, sort_keys=True).encode()
    artifact = {'schema_version':1, 'artifact_id':'training-acceptance', 'revision':'r001',
                'sha256':digest(body), 'authority_path':'reports/history/training-acceptance/r001/report.json',
                'inputs':[spec, environment, *attempts, *[v[0] for v in metrics.values()], control_ref],
                'producer':{'kind':'tool','id':'real-training-acceptance'},
                'transaction_id':'training-acceptance-r001','lifecycle_status':'published',
                'review_status':'unreviewed','verdict_ref':None}
    published = ArtifactRegistry(root).publish_artifact(artifact, body)
    assert verify_ref(root, published).read_bytes() == body
    assert ArtifactRegistry(root).audit()['status'] == 'PASS'
    atomic_write(root / 'acceptance-summary.json', report | {'report_ref':published})
