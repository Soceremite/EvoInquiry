"""Native Windows acceptance of one complete local governance execution."""
import json
import sys

import pytest

from tests.governance_helpers import make_environment, make_sources, make_spec
from tools.artifact_registry import ArtifactRegistry
from tools.execution_registry import freeze_snapshot, launch_execution, start_execution
from tools.filesystem_doctor import probe_directory
from tools.project_registry import init_project
from tools.registry_common import digest, fixed_ref, read_record, verify_ref


@pytest.mark.skipif(sys.platform != 'win32', reason='Native Windows acceptance requires a Windows runner')
def test_native_windows_profile_environment_execution_and_publication(tmp_path):
    probe=probe_directory(tmp_path)
    assert probe['status']=='PASS',probe
    init_project(tmp_path,'windows-acceptance','governed-v1')
    environment=make_environment(tmp_path)
    spec=make_spec(tmp_path)
    sources=make_sources(tmp_path)
    arguments=[str(tmp_path/'runs/windows-run/outputs/metrics.json')]
    snapshot=freeze_snapshot(tmp_path,'windows-run',spec,environment,sources,
        {'variant':{'augmentation':0},'seed':11},'src/train.py','baseline',11,
        arguments=arguments,output_argument_indices=[0])
    start_execution(tmp_path,'windows-run',snapshot)
    executed=launch_execution(tmp_path,'windows-run',arguments,timeout=30)
    assert executed['exit_code']==0,executed
    output=fixed_ref(tmp_path,'runs/windows-run/outputs/metrics.json')
    assert read_record(verify_ref(tmp_path,output))['ids']==list(range(6))
    body=json.dumps({'execution':executed['execution_ref'],'output':output}).encode()
    record={'schema_version':1,'artifact_id':'windows-report','revision':'r001',
            'sha256':digest(body),'authority_path':'reports/history/windows-report/r001/report.json',
            'inputs':[spec,environment,executed['execution_ref'],output],
            'producer':{'kind':'tool','id':'windows-acceptance'},'transaction_id':'windows-publish',
            'lifecycle_status':'published','review_status':'unreviewed','verdict_ref':None}
    registry=ArtifactRegistry(tmp_path)
    published=registry.publish_artifact(record,body)
    assert verify_ref(tmp_path,published).read_bytes()==body
    assert registry.audit()['status']=='PASS'
