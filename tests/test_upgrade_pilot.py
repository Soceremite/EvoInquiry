"""Real CPU engineering pilot; these checks make no scientific comparison claim."""
import json

import pytest

from tests.governance_helpers import consumer, make_environment, make_sources, make_spec
from tests.test_project_governance import artifact
from tools.artifact_registry import ArtifactRegistry
from tools.environment_registry import EnvironmentRegistry
from tools.execution_registry import freeze_snapshot, launch_execution, select_attempts, start_execution
from tools.project_registry import init_project
from tools.registry_common import RegistryError, fixed_ref, read_record, verify_ref


def test_two_methods_three_seeds_failure_environment_and_fixed_report(tmp_path):
    init_project(tmp_path,'pilot','governed-v1')
    sources, spec, environment = make_sources(tmp_path), make_spec(tmp_path), make_environment(tmp_path)
    attempts, outputs = [], []
    for variant, augmentation in [('baseline',0),('method-b',0.1)]:
        for seed in (11,22,33):
            failure = variant == 'method-b' and seed == 22
            parent = None
            for number in range(2 if failure else 1):
                run_id = f'{variant}-{seed}-{number}'
                arguments = [str(tmp_path / 'runs' / run_id / 'outputs/metrics.json')]
                snapshot = freeze_snapshot(tmp_path,run_id,spec,environment,sources,
                    {'variant':{'augmentation':augmentation},'seed':seed,'inject_failure':failure and number==0},
                    'src/train.py',variant,seed,arguments=arguments,output_argument_indices=[0])
                start_execution(tmp_path,run_id,snapshot,retry_of=parent,job_ref=run_id)
                with pytest.raises(RegistryError,match='arguments differ'):
                    launch_execution(tmp_path,run_id,arguments+['undeclared-override'])
                result = launch_execution(tmp_path,run_id,arguments,timeout=15)
                assert result['exit_code'] == (7 if failure and number==0 else 0)
                attempts.append(result['execution_ref'])
                if result['exit_code']:
                    parent = run_id
                else:
                    output = fixed_ref(tmp_path,f'runs/{run_id}/outputs/metrics.json')
                    metrics = read_record(verify_ref(tmp_path,output))
                    assert metrics['ids']==list(range(6)) and metrics['labels']==[0,1,0,1,0,1]
                    assert metrics['variant']=={'augmentation':augmentation}
                    outputs.append(output)
    analysis = select_attempts(tmp_path,spec,attempts)
    assert len(attempts)==7 and not analysis['missing_slots']
    assert sum(row['included'] for row in analysis['attempts'])==6
    assert sum(row['record']['status']=='failed' for row in analysis['attempts'])==1
    assert analysis['scientific_verdict']=='not-assessed'
    registry = EnvironmentRegistry(tmp_path)
    bound = registry.bind_consumer(consumer(environment,'held-job'))
    registry.acquire_lease('held-job','held-lease','held-job',expires_at='2020-01-01T00:00:00Z')
    frozen_before = (tmp_path / environment['path']).read_bytes()
    rejected = make_environment(tmp_path,revision='r002',fail_stage='numerical')
    assert read_record(tmp_path / rejected['path'])['lifecycle']=='rejected'
    assert (tmp_path / environment['path']).read_bytes()==frozen_before
    assert verify_ref(tmp_path,bound).is_file()
    assert registry.reconcile_leases({})[0]['status']=='protected-needs-reconciliation'
    report = {'scope':'CPU engineering validation; scientific quality not assessed',
              'spec_ref':spec,'env_revision':environment,'analysis':analysis,'outputs':outputs}
    body = json.dumps(report,sort_keys=True).encode()
    artifacts = ArtifactRegistry(tmp_path)
    r1 = artifacts.publish_artifact(artifact(content=body),body)
    r2 = artifacts.publish_artifact(artifact('r002','pilot-report-2',body) | {
        'inputs':[spec,environment,*attempts,*outputs]},body,r1)
    (tmp_path / 'reports/current/report.json').write_text(json.dumps(r1))
    assert verify_ref(tmp_path,r2).read_bytes()==body
    assert artifacts.audit()['problems']==['Alias drift: report']
    artifacts.reconcile()
    assert artifacts.current('report')==r2 and artifacts.audit()['status']=='PASS'
    assert 'lease:held-lease' in registry.plan_retirement(environment)['blockers']
