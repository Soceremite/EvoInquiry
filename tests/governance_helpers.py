"""Small real CPU fixtures shared by governance integration tests."""
from pathlib import Path
import json
import sys

from tools.environment_registry import (EnvironmentRegistry, probe_environment,
                                        run_environment_check)
from tools.execution_registry import register_spec, spec_digest
from tools.registry_common import atomic_write, fixed_ref


def make_environment(root, env_id='cpu', revision='r001', *, fail_stage=None,
                     interpreter=None, imports=('math',)):
    interpreter = str(interpreter or sys.executable)
    observed = probe_environment(interpreter, imports)
    recipes = Path(root) / 'env/recipes' / env_id / revision
    for name in ('recipe.json', 'lock.json', 'build.json'):
        atomic_write(recipes / name, {'python': observed['python'], 'manager': 'existing-python', 'name': name})
    receipts = []
    for stage in ('metadata', 'imports', 'numerical', 'consumers'):
        code = {'metadata': 'import sys; assert sys.version_info >= (3, 10); print(sys.version)',
                'imports': 'import math; assert math.isfinite(math.pi); print(math.__file__)',
                'numerical': 'import math; assert math.fsum([0.1]*10)==1.; print("numeric-ok")',
                'consumers': 'assert len(set([11,22,33]))==3; print("consumer-contract-ok")'}[stage]
        if stage == fail_stage:
            code += '; raise SystemExit(9)'
        receipts.append(run_environment_check(root, interpreter, f'{env_id}-{revision}-{stage}', stage,
                                             ['-I', '-c', code], observed, ['method-a', 'method-b']))
    record = {'schema_version': 1, 'env_id': env_id, 'revision': revision,
              'recipe_ref': fixed_ref(root, (recipes / 'recipe.json').relative_to(root)),
              'lock_ref': fixed_ref(root, (recipes / 'lock.json').relative_to(root)),
              'build_ref': fixed_ref(root, (recipes / 'build.json').relative_to(root)),
              'platform': observed['platform'], 'interpreter': interpreter,
              'expected_fingerprint': {'python': observed['python'], 'platform': observed['platform']},
              'observed_fingerprint': observed, 'test_receipts': receipts,
              'lifecycle': 'candidate', 'consumer_inventory_ref': None}
    registry = EnvironmentRegistry(root)
    candidate = registry.record_candidate(record, [], receipts, ['method-a', 'method-b'])
    if fail_stage:
        return candidate
    approval = {'approved': True, 'candidate_ref': candidate,
                'confirmed_by': 'test-maintainer', 'confirmed_at': '2026-10-12T00:00:00Z'}
    return registry.promote_candidate(candidate, approval, ['method-a', 'method-b'])


def consumer(environment, consumer_id='job-1', lifecycle='queued'):
    return {'schema_version': 1, 'consumer_id': consumer_id, 'project_id': 'project-1',
            'experiment_id': 'exp-001', 'entrypoint': 'src/train.py', 'job_ref': consumer_id,
            'workflow_run_id': 'workflow-001', 'execution_run_id': consumer_id,
            'env_revision': environment, 'lease': None, 'pin': [], 'importance': 'standard',
            'lifecycle': lifecycle, 'confirmed_by': 'test-maintainer',
            'confirmed_at': '2026-10-12T00:00:00Z', 'source': 'integration-test'}


def make_spec(root):
    for filename, content in [('protocol.json', {'main_metric': 'mean', 'aggregation': 'first-success'}),
                              ('data.json', {'samples': list(range(12)), 'label_map': {'negative': 0, 'positive': 1}}),
                              ('split.json', {'train': [0,1,2,3,4,5], 'validation': [6,7,8], 'test': [9,10,11]}),
                              ('evaluator.json', {'revision': 'r001', 'metric': 'mean'})]:
        atomic_write(Path(root) / 'data' / filename, content)
    record = {'schema_version': 1, 'experiment_id': 'exp-001', 'spec_revision': 'r001',
              'hypothesis': 'Engineering pilot of method-specific extensions to a shared data protocol',
              'variants': [{'variant_id': 'baseline', 'configuration': {'augmentation': 0}},
                           {'variant_id': 'method-b', 'configuration': {'augmentation': 0.1}}],
              'seeds': [11,22,33], 'budget': {'kind': 'tiny-cpu-pilot', 'max_seconds_per_attempt': 15},
              'decision_rule': {'scientific_verdict': 'not-assessed'},
              'failure_policy': {'aggregation': 'first-success', 'description': 'Keep failed attempts; retry once'}}
    for key, filename in [('protocol_ref','protocol.json'),('data_ref','data.json'),
                          ('split_ref','split.json'),('evaluator_ref','evaluator.json')]:
        record[key] = fixed_ref(root, 'data/' + filename)
    record['spec_sha256'] = spec_digest(record)
    return register_spec(root, record)


def make_sources(root):
    source = Path(root) / 'src/research_shared'
    source.mkdir(parents=True, exist_ok=True)
    (source / '__init__.py').write_text('')
    (source / 'data.py').write_text('''"""Stable batch protocol for the CPU engineering pilot."""
import random
def make_batches(seed, augmentation=0):
    """Return x: list[float][B,1], y: list[int][B] and sample IDs.

    Labels are 0/1. This pilot uses fixed train IDs [0..5]; it fits no
    statistics, reads/writes no files and uses an isolated RNG. Augmentation
    is an explicit method extension, never a hidden split change.
    Example: x, y, ids = make_batches(11, augmentation=0)
    Callers preserve sample and label meaning; tests check both methods.
    """
    rng = random.Random(seed)
    ids = list(range(6))
    x = [[float(i) + augmentation*rng.random()] for i in ids]
    y = [i%2 for i in ids]
    return x,y,ids
''')
    (Path(root) / 'src/train.py').write_text('''"""Run one tiny deterministic CPU pilot attempt."""
import json, pathlib, sys
from research_shared.data import make_batches
config = json.loads(pathlib.Path('configuration.json').read_text())
if config.get('inject_failure'):
    print('deliberate failure before results')
    raise SystemExit(7)
x,y,ids = make_batches(config['seed'], **config['variant'])
assert len(x)==len(y)==len(ids)==6 and all(len(row)==1 for row in x)
assert set(y)=={0,1} and set(ids).isdisjoint({6,7,8,9,10,11})
target=pathlib.Path(sys.argv[1]); target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps({'metric':sum(row[0] for row in x)/len(x),'ids':ids,'labels':y,
                            'variant':config['variant'],'seed':config['seed']}))
print('pilot-complete')
''')
    return ['src/train.py', 'src/research_shared/__init__.py', 'src/research_shared/data.py']
