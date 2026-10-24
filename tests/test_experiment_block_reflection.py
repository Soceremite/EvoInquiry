"""Progress-based reviews over whole comparisons, with continuous and finite runs."""
from datetime import datetime, timedelta, timezone
import json
import time

import pytest

from tools import research_control as control, run_state
from tools.registry_common import RegistryError, fixed_ref
from tools import iteration_log


def evidence(root, name, payload):
    (root / name).write_text(json.dumps(payload), encoding='utf-8')
    return fixed_ref(root, name)


def continuous(root, every=2, *, resources=None, **options):
    run_state.start_run(str(root), 'ongoing', ['explore'])
    return control.configure(root, 'ongoing', 'Resolve the planned experimental question', {
        'max_actions': None, 'wall_seconds': None, 'max_attempts_per_key': 2,
        'resources': {'fits': 100} if resources is None else resources},
        started_at=(datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
        reflection_every_blocks=every, **options)


def define(root, block_id, members):
    plan = evidence(root, f'{block_id}-plan.json', {'members': members,
                    'completion': 'All planned members accounted for and analysis saved'})
    control.define_block(root, 'ongoing', block_id, members, plan)
    return plan


def member(root, key, outcome='succeeded'):
    action = control.claim_action(root, 'ongoing', key, 'explore',
                                 'Does this planned comparison distinguish the explanations?',
                                 costs={'fits': 1})['action']
    result = evidence(root, action['id'] + '.json', {'member': key, 'outcome': outcome})
    control.finish_action(root, 'ongoing', action['id'], outcome, actual_costs={'fits': 1},
                          result_refs=[result], reason='' if outcome == 'succeeded' else 'Observed failure')
    return action


def complete(root, block_id):
    report = evidence(root, f'{block_id}-analysis.json',
                      {'block': block_id, 'claim': 'not-assessed', 'coverage': 'planned members checked'})
    return control.complete_block(root, 'ongoing', block_id, [report])


def reflect(root, gate):
    return control.record_reflection(root, 'ongoing', 'explore', {
        'schema_version': 1, 'kind': 'checkpoint', 'gate_id': gate['id'], 'decision': 'CONTINUE',
        'reason': 'Evidence and alternatives checked; the next planned control remains informative',
        'evidence_refs': [f'{block}-analysis.json' for block in gate['block_ids']],
        'next_action': {'skill': 'experiment-plan', 'description': 'Continue the next authorized comparison'}})


def test_plan_inspection_reports_due_review_without_mutating_state_or_stall_ledger(tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    continuous(tmp_path, reflection_interval_seconds=3600)
    iteration_log.note(str(tmp_path), 'ongoing', 'explore', 0)
    state_path = tmp_path / '.ei/runs/ongoing.json'
    before = state_path.read_bytes()
    ledger_before = iteration_log.show(str(tmp_path), 'ongoing')
    for _ in range(5):
        observation = control.inspect(tmp_path, 'ongoing', read_only=True)
        assert observation['status'] == 'REFLECTION_REQUIRED'
        assert observation['reflection_gate'] is None
        assert observation['reflection_due'] == ['elapsed_review_interval']
        assert observation['host_goal_modified'] is False
    assert state_path.read_bytes() == before
    assert iteration_log.show(str(tmp_path), 'ongoing') == ledger_before
    result = subprocess.run([sys.executable, '-B', 'tools/research_control.py', '--root', str(tmp_path),
        '--run-id', 'ongoing', 'inspect', '--read-only'], cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['reflection_due'] == ['elapsed_review_interval']
    assert state_path.read_bytes() == before
    assert iteration_log.show(str(tmp_path), 'ongoing') == ledger_before
    # The execution owner can subsequently persist and address the same due
    # signal; a Plan observer has not silently performed that write for it.
    owned = control.inspect(tmp_path, 'ongoing')
    assert owned['reflection_gate']['reasons'] == ['elapsed_review_interval']
    assert control.inspect(tmp_path, 'ongoing', read_only=True)['reflection_gate'] == owned['reflection_gate']


def test_two_whole_comparisons_trigger_one_review_then_continue_past_two_hours(tmp_path):
    original = continuous(tmp_path)
    for block_id in ('control-one', 'control-two'):
        keys = [f'{block_id}-{method}-{seed}' for method in ('base', 'candidate') for seed in (11, 22, 33)]
        define(tmp_path, block_id, keys)
        for key in keys:
            member(tmp_path, key)
            # Six terminal actions alone are not a completed scientific comparison.
            assert control.inspect(tmp_path, 'ongoing')['status'] == 'READY'
        metadata = complete(tmp_path, block_id)
        assert len(metadata['experiment_blocks']) == (1 if block_id == 'control-one' else 2)
    decision = control.inspect(tmp_path, 'ongoing')
    assert decision['elapsed_seconds'] > 7200
    assert decision['timing']['deadline_at'] is None
    assert decision['timing']['dispatch_seconds_remaining'] is None
    assert decision['blocks_completed'] == 2 and decision['actions_used'] == 12
    assert decision['status'] == 'REFLECTION_REQUIRED'
    assert decision['host_goal_modified'] is False
    gate = decision['reflection_gate']
    assert gate['block_ids'] == ['control-one', 'control-two']
    assert gate['reasons'] == ['completed_block_cadence']
    with pytest.raises(RegistryError, match='REFLECTION_REQUIRED'):
        member(tmp_path, 'too-early')
    reflect(tmp_path, gate)
    # Recovery does not renew a clock or erase cost; it just addresses this review.
    observed = control.configure(tmp_path, 'ongoing', original['objective'], original['limits'])
    assert observed['started_at'] == original['started_at']
    assert observed['reflection_reviewed_blocks'] == gate['block_ids']
    assert control.inspect(tmp_path, 'ongoing')['spent_or_reserved'] == {'fits': 12}
    assert control.inspect(tmp_path, 'ongoing')['status'] == 'READY'
    member(tmp_path, 'next-independent-check')
    assert control.inspect(tmp_path, 'ongoing')['actions_used'] == 13


@pytest.mark.parametrize('state', ['missing', 'live', 'cancelled'])
def test_partial_comparison_does_not_count_even_with_an_analysis_file(tmp_path, state):
    continuous(tmp_path, every=1)
    define(tmp_path, 'whole', ['baseline', 'candidate'])
    member(tmp_path, 'baseline')
    if state != 'missing':
        action = control.claim_action(tmp_path, 'ongoing', 'candidate', 'explore',
                                      'Compare the candidate', costs={'fits': 1})['action']
        if state == 'cancelled':
            control.finish_action(tmp_path, 'ongoing', action['id'], 'cancelled',
                                  actual_costs={'fits': 0}, reason='Confirmed never launched')
    with pytest.raises(RegistryError, match='incomplete'):
        complete(tmp_path, 'whole')
    assert control.inspect(tmp_path, 'ongoing')['blocks_completed'] == 0
    assert control.inspect(tmp_path, 'ongoing')['reflection_gate'] is None


def test_retry_is_one_member_and_completed_block_cannot_be_split_or_retried(tmp_path):
    continuous(tmp_path, every=1)
    define(tmp_path, 'diagnosis', ['attempt'])
    failed = member(tmp_path, 'attempt', 'failed')
    assert control.inspect(tmp_path, 'ongoing')['blocks_completed'] == 0
    succeeded = member(tmp_path, 'attempt')
    assert succeeded['attempt'] == 2
    metadata = complete(tmp_path, 'diagnosis')
    assert metadata['experiment_blocks'][0]['action_ids'] == [succeeded['id']]
    assert succeeded['id'] != failed['id']
    assert complete(tmp_path, 'diagnosis') == metadata
    reflect(tmp_path, metadata['reflection_gate'])
    assert control.inspect(tmp_path, 'ongoing')['unreviewed_blocks'] == []
    with pytest.raises(RegistryError, match='Completed block'):
        member(tmp_path, 'attempt')
    with pytest.raises(RegistryError, match='disjoint'):
        define(tmp_path, 'double-count', ['attempt'])


def test_closed_failed_comparison_counts_once_without_claiming_scientific_success(tmp_path):
    continuous(tmp_path, every=1)
    define(tmp_path, 'closed-failure', ['failed-member'])
    member(tmp_path, 'failed-member', 'failed')
    metadata = complete(tmp_path, 'closed-failure')
    assert metadata['experiment_blocks'][0]['status'] == 'completed'
    assert control.inspect(tmp_path, 'ongoing')['scientific_verdict'] == 'not-assessed'
    reflect(tmp_path, metadata['reflection_gate'])
    with pytest.raises(RegistryError, match='Completed block'):
        member(tmp_path, 'failed-member')


def test_late_block_completion_is_not_credited_to_an_earlier_review(tmp_path):
    continuous(tmp_path, every=1)
    for name in ('early', 'late'):
        define(tmp_path, name, [name])
        member(tmp_path, name)
    first_gate = complete(tmp_path, 'early')['reflection_gate']
    assert first_gate['block_ids'] == ['early']
    complete(tmp_path, 'late')
    reflect(tmp_path, first_gate)
    decision = control.inspect(tmp_path, 'ongoing')
    assert decision['status'] == 'REFLECTION_REQUIRED'
    second_gate = decision['reflection_gate']
    assert second_gate['id'] != first_gate['id'] and second_gate['block_ids'] == ['late']
    reflect(tmp_path, second_gate)
    assert control.inspect(tmp_path, 'ongoing')['status'] == 'READY'


def test_block_membership_is_fixed_before_dispatch_and_analysis_is_hash_bound(tmp_path):
    continuous(tmp_path)
    plan = define(tmp_path, 'fixed', ['planned'])
    before = run_state.load_run(str(tmp_path), 'ongoing')
    control.define_block(tmp_path, 'ongoing', 'fixed', ['planned'], plan)
    assert run_state.load_run(str(tmp_path), 'ongoing') == before
    with pytest.raises(RegistryError, match='fixed'):
        control.define_block(tmp_path, 'ongoing', 'fixed', ['different'], plan)
    member(tmp_path, 'unassigned')
    with pytest.raises(RegistryError, match='before claiming'):
        define(tmp_path, 'retroactive', ['unassigned'])
    member(tmp_path, 'planned')
    complete(tmp_path, 'fixed')
    evidence(tmp_path, 'fixed-analysis.json', {'claim': 'rewritten'})
    decision = control.inspect(tmp_path, 'ongoing')
    assert decision['status'] == 'EVIDENCE_CHANGED'
    assert decision['evidence_issues'][0]['block_id'] == 'fixed'
    with pytest.raises(RegistryError, match='EVIDENCE_CHANGED'):
        member(tmp_path, 'new-work')


def test_unset_total_caps_do_not_remove_resource_retry_or_stop_boundaries(tmp_path):
    continuous(tmp_path, resources={'fits': 1})
    member(tmp_path, 'one-fit')
    with pytest.raises(RegistryError, match='Insufficient remaining fits'):
        member(tmp_path, 'unauthorized-extra-fit')
    control.stop(tmp_path, 'ongoing', 'User requested an end to this investigation')
    decision = control.inspect(tmp_path, 'ongoing')
    assert decision['status'] == 'STOPPED' and decision['host_goal_modified'] is False
    with pytest.raises(RegistryError, match='STOPPED'):
        control.claim_action(tmp_path, 'ongoing', 'even-free', 'explore', 'Stopped', costs={'fits': 0})


@pytest.mark.parametrize('wall, actions, expected', [(7200, None, 'BUDGET_EXHAUSTED'),
                                                  (None, 1, 'READY')])
def test_explicit_total_caps_are_independent_and_cannot_be_silently_removed(tmp_path, wall, actions, expected):
    run_state.start_run(str(tmp_path), 'finite', ['explore'])
    limits = {'max_actions': actions, 'wall_seconds': wall, 'max_attempts_per_key': 1, 'resources': {}}
    original = control.configure(tmp_path, 'finite', 'Respect the actual authorization', limits,
        started_at=(datetime.now(timezone.utc) - timedelta(hours=3)).isoformat())
    assert control.inspect(tmp_path, 'finite')['status'] == expected
    with pytest.raises(RegistryError, match='fixed'):
        control.configure(tmp_path, 'finite', original['objective'], dict(limits, max_actions=None, wall_seconds=None))
    if wall is None:
        action = control.claim_action(tmp_path, 'finite', 'only', 'explore', 'One action', costs={})['action']
        control.finish_action(tmp_path, 'finite', action['id'], 'succeeded', actual_costs={},
                              result_refs=[evidence(tmp_path, 'finite.json', {'result': 1})])
        assert control.inspect(tmp_path, 'finite')['status'] == 'BUDGET_EXHAUSTED'


@pytest.mark.parametrize('options', [{'reflection_every_actions': 1}, {'closeout_seconds': 1},
                                     {'reflection_every_blocks': 0}])
def test_conflicting_or_invalid_continuous_policy_cannot_be_attached(tmp_path, options):
    run_state.start_run(str(tmp_path), 'invalid', ['explore'])
    arguments = dict(reflection_every_blocks=2)
    arguments.update(options)
    with pytest.raises(RegistryError):
        control.configure(tmp_path, 'invalid', 'Validate policy', {
            'max_actions': None, 'wall_seconds': None, 'max_attempts_per_key': 1, 'resources': {}}, **arguments)
    assert 'coordination' not in run_state.load_run(str(tmp_path), 'invalid')


def test_public_cli_can_configure_and_record_whole_experiments(tmp_path):
    import subprocess
    import sys
    from pathlib import Path

    run_state.start_run(str(tmp_path), 'ongoing', ['explore'])
    evidence(tmp_path, 'limits.json', {'max_actions': None, 'wall_seconds': None,
                                      'max_attempts_per_key': 1, 'resources': {'fits': 2}})
    def cli(*arguments):
        process = subprocess.run([sys.executable, '-B', '-m', 'tools.research_control',
            '--root', str(tmp_path), '--run-id', 'ongoing', *arguments],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
        assert process.returncode == 0, process.stderr
        return json.loads(process.stdout)
    policy = cli('configure', '--objective', 'Check public progress review commands',
                 '--limits', str(tmp_path / 'limits.json'), '--reflection-every-blocks', '1')
    assert policy['limits']['wall_seconds'] is None
    plan = evidence(tmp_path, 'plan.json', {'members': ['one-run']})
    evidence(tmp_path, 'definition.json', {'block_id': 'cli-block', 'action_keys': ['one-run'], 'plan_ref': plan})
    cli('define-block', '--request', str(tmp_path / 'definition.json'))
    member(tmp_path, 'one-run')
    report = evidence(tmp_path, 'analysis.json', {'finding': 'fixture checked'})
    evidence(tmp_path, 'completion.json', {'block_id': 'cli-block', 'result_refs': [report]})
    first = cli('complete-block', '--request', str(tmp_path / 'completion.json'))
    again = cli('complete-block', '--request', str(tmp_path / 'completion.json'))
    assert first == again
    decision = cli('inspect')
    assert decision['status'] == 'REFLECTION_REQUIRED'
    assert decision['reflection_gate']['block_ids'] == ['cli-block']


def test_real_cpu_comparisons_resume_after_progress_review_without_a_wall_deadline(tmp_path):
    """Real subprocesses test orchestration; simulated age is not a long-run claim."""
    from tests.governance_helpers import make_environment, make_sources, make_spec
    from tools.execution_registry import (freeze_snapshot, launch_execution,
                                           select_attempts, start_execution)
    from tools.registry_common import read_record

    observed_start = time.monotonic()
    sources, spec, environment = make_sources(tmp_path), make_spec(tmp_path), make_environment(tmp_path)
    continuous(tmp_path, resources={'cpu_jobs': 18})
    completed, reviews = [], []
    variants = {'baseline': {'augmentation': 0}, 'method-b': {'augmentation': 0.1}}
    for block_id in ('comparison-1', 'comparison-2', 'comparison-3'):
        keys = [f'{block_id}-{variant}-{seed}' for variant in variants for seed in (11, 22, 33)]
        define(tmp_path, block_id, keys)
        executions, metrics = [], {variant: [] for variant in variants}
        for variant, configuration in variants.items():
            for seed in (11, 22, 33):
                key = f'{block_id}-{variant}-{seed}'
                output = tmp_path / 'runs' / key / 'outputs' / 'metrics.json'
                args = [str(output)]
                snapshot = freeze_snapshot(tmp_path, key, spec, environment, sources,
                    {'variant': configuration, 'seed': seed}, 'src/train.py', variant, seed,
                    arguments=args, output_argument_indices=[0])
                start_execution(tmp_path, key, snapshot, workflow_run_id='ongoing')
                action = control.claim_action(tmp_path, 'ongoing', key, 'explore',
                    'Verify complete comparison accounting and continuation', costs={'cpu_jobs': 1},
                    input_refs=[snapshot])['action']
                terminal = launch_execution(tmp_path, key, args)
                assert terminal['exit_code'] == 0
                assert read_record(tmp_path / 'runs' / key / 'process.json')['effective_timeout_seconds'] == 15
                control.settle_execution(tmp_path, 'ongoing', action['id'], key,
                    actual_costs={'cpu_jobs': 1}, result_refs=[fixed_ref(tmp_path, output.relative_to(tmp_path))])
                executions.append(terminal['execution_ref'])
                metrics[variant].append(read_record(output)['metric'])
                assert control.inspect(tmp_path, 'ongoing')['status'] == 'READY'
        selection = select_attempts(tmp_path, spec, executions)
        assert selection['missing_slots'] == [] and all(row['included'] for row in selection['attempts'])
        report = evidence(tmp_path, f'{block_id}-analysis.json', {
            'block': block_id, 'execution_refs': executions,
            'per_seed': metrics, 'mean': {key: sum(values)/len(values) for key, values in metrics.items()},
            'scientific_verdict': 'not-assessed', 'scope': 'CPU orchestration regression fixture'})
        metadata = control.complete_block(tmp_path, 'ongoing', block_id, [report])
        completed.append(block_id)
        if block_id == 'comparison-2':
            assert control.inspect(tmp_path, 'ongoing')['status'] == 'REFLECTION_REQUIRED'
            gate = metadata['reflection_gate']
            assert gate['block_ids'] == completed
            with pytest.raises(RegistryError, match='REFLECTION_REQUIRED'):
                control.claim_action(tmp_path, 'ongoing', 'premature', 'explore', 'Must review',
                                     costs={'cpu_jobs': 1})
            reflect(tmp_path, gate)
            reviews.append(gate['id'])
            assert control.inspect(tmp_path, 'ongoing')['status'] == 'READY'
    final = control.inspect(tmp_path, 'ongoing')
    assert final['status'] == 'READY' and final['blocks_completed'] == 3
    assert final['actions_used'] == 18 and final['spent_or_reserved'] == {'cpu_jobs': 18}
    assert final['unreviewed_blocks'] == ['comparison-3']
    assert final['host_goal_modified'] is False and final['phase']['status'] == 'pending'
    evidence(tmp_path, 'practice-receipt.json', {
        'execution': '18 actual local CPU subprocesses, 3 comparisons, 2 methods x 3 seeds each',
        'review_cadence_blocks': 2, 'completed_blocks': completed, 'review_ids': reviews,
        'actual_elapsed_seconds': time.monotonic() - observed_start,
        'simulated_original_start_hours_ago': 3, 'native_goal_behavior': 'not-tested',
        'model_autonomy': 'not-tested', 'scientific_verdict': 'not-assessed', 'final': final})
