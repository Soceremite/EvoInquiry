"""Training budgets start at an observed first step, preserving resumed segments."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from tools import resource_budget as budget
from tools.registry_common import RegistryError


def clock(*segments):
    return {'schema_version': 1, 'experiment_id': 'method-a-seed-11', 'segments': list(segments)}


def segment(attempt='attempt-1', start='2026-10-26T02:00:00+00:00', end=None):
    return {'attempt_id': attempt, 'first_step_at': start, 'ended_at': end}


def test_engineering_time_does_not_consume_training_allowance(tmp_path):
    budget.select(tmp_path, 'session', preset='custom', selected_by='fixture-user-choice',
                  overrides={'job_notice_after_seconds': 7200})
    # Engineering started at midnight; the actual first step began at 02:00.
    report = budget.check_duration(tmp_path, 'session', training_clock=clock(segment()),
        experiment_id='method-a-seed-11', observed_at='2026-10-26T02:10:00+00:00')
    assert report['seconds'] == 600 and report['status'] == 'OK'
    assert report['time_basis'] == 'training_from_first_step'


def test_preparation_without_a_first_step_is_not_training(tmp_path):
    budget.select(tmp_path, 'session', preset='maximum', selected_by='fixture-user-choice')
    path = budget.table_path(tmp_path, 'session')
    before = path.read_bytes()
    report = budget.check_duration(tmp_path, 'session', training_clock=clock(),
        experiment_id='method-a-seed-11', observed_at='2026-10-26T22:00:00+00:00')
    assert report['status'] == 'TRAINING_NOT_STARTED'
    assert report['seconds'] == 0 and report['first_step_at'] is None
    assert report['action'] == 'continue' and report['notice_required'] is False
    assert path.read_bytes() == before


def test_resume_preserves_training_cost_and_excludes_reinitialization_gap():
    record = clock(segment(end='2026-10-26T03:00:00+00:00'),
                   segment('attempt-2', '2026-10-26T08:00:00+00:00'))
    report = budget.training_elapsed(record, 'method-a-seed-11',
                                     observed_at='2026-10-26T09:00:00+00:00')
    assert report['training_elapsed_seconds'] == 7200
    assert report['first_step_at'] == '2026-10-26T02:00:00+00:00'
    assert report['training_state'] == 'running'
    record['segments'][-1]['ended_at'] = '2026-10-26T09:00:00+00:00'
    ended = budget.training_elapsed(record, 'method-a-seed-11',
                                    observed_at='2026-10-26T19:00:00+00:00')
    assert ended['training_elapsed_seconds'] == 7200 and ended['training_state'] == 'ended'


@pytest.mark.parametrize('record,expected', [
    ({'schema_version': True, 'experiment_id': 'method-a-seed-11', 'segments': []}, 'identity'),
    (clock(segment(start='2026-10-26T02:00:00')), 'timezone-aware'),
    (clock(segment(start='2026-10-27T02:00:00+00:00')), 'future'),
    (clock(segment(end='2026-10-26T01:00:00+00:00')), 'backwards'),
    (clock(segment(), segment('attempt-2', '2026-10-26T03:00:00+00:00')), 'overlap'),
    (clock(segment(end='2026-10-26T04:00:00+00:00'),
           segment('attempt-2', '2026-10-26T03:00:00+00:00')), 'overlap'),
    (clock(segment(end='2026-10-26T03:00:00+00:00'),
           segment('attempt-1', '2026-10-26T04:00:00+00:00')), 'distinct'),
    ({'schema_version': 1, 'experiment_id': 'other', 'segments': []}, 'identity'),
    ({'schema_version': 1, 'experiment_id': 'method-a-seed-11',
      'process_started_at': '2026-10-26T02:00:00+00:00'}, 'segments'),
    (clock({'attempt_id': 'a', 'step': 200, 'timestamp': '2026-10-26T02:00:00+00:00'}), 'complete'),
])
def test_unverified_or_inconsistent_clock_cannot_invent_training_time(record, expected):
    with pytest.raises(RegistryError, match=expected):
        budget.training_elapsed(record, 'method-a-seed-11', observed_at='2026-10-26T10:00:00+00:00')


def test_clock_cli_reads_the_existing_owner_record_without_writing(tmp_path):
    budget.select(tmp_path, 'session', preset='custom', selected_by='fixture-user-choice',
                  overrides={'job_notice_after_seconds': 7200})
    anchor = datetime.now(timezone.utc) - timedelta(seconds=9000)
    record = clock(segment(start=anchor.isoformat()))
    source = tmp_path / 'owner-training-time.json'
    source.write_text(json.dumps(record))
    table = budget.table_path(tmp_path, 'session')
    before = (source.read_bytes(), table.read_bytes())
    process = subprocess.run([sys.executable, str(Path(budget.__file__)), '--root', str(tmp_path),
        '--session', 'session', 'duration', '--training-clock', str(source),
        '--experiment-id', 'method-a-seed-11'], capture_output=True, text=True, timeout=15)
    assert process.returncode == 0, process.stderr
    report = json.loads(process.stdout)
    assert report['status'] == 'NOTICE_CONTINUE' and report['seconds'] >= 9000
    assert (source.read_bytes(), table.read_bytes()) == before


def test_real_preparation_then_gradient_updates_use_a_separate_training_clock(tmp_path):
    """A paced CPU worker emits its first-step receipt after actual setup."""
    budget.select(tmp_path, 'session', preset='custom', selected_by='fixture-user-choice',
                  overrides={'job_notice_after_seconds': 0.2, 'auto_approve_job_seconds': 10})
    program = '''from datetime import datetime, timezone
import json, time
time.sleep(0.35)  # Deliberately paced preparation; not a training update.
weight = 2.0
first_step = datetime.now(timezone.utc).isoformat()
print(json.dumps({'first_step_at': first_step}), flush=True)
for step in range(1, 61):
    weight -= 0.05 * 2 * (weight - 1)
    time.sleep(0.005)
print(json.dumps({'steps': step, 'weight': weight, 'ended_at': datetime.now(timezone.utc).isoformat()}), flush=True)
'''
    wall_started = time.monotonic()
    child = subprocess.Popen([sys.executable, '-u', '-c', program],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    first = json.loads(child.stdout.readline())
    record = clock(segment(start=first['first_step_at']))
    initial = budget.check_duration(tmp_path, 'session', training_clock=record,
        experiment_id='method-a-seed-11', observed_at=first['first_step_at'])
    assert initial['seconds'] == 0 and initial['status'] == 'OK'
    stdout, stderr = child.communicate(timeout=10)
    assert child.returncode == 0, stderr
    end = json.loads(stdout)
    assert end['steps'] == 60 and abs(end['weight'] - 1) < 0.01
    record['segments'][0]['ended_at'] = end['ended_at']
    report = budget.check_duration(tmp_path, 'session', training_clock=record,
                                   experiment_id='method-a-seed-11')
    assert report['status'] == 'NOTICE_CONTINUE' and report['training_state'] == 'ended'
    assert time.monotonic() - wall_started - report['seconds'] >= 0.3
