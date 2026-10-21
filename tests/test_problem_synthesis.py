"""Problem-level reflection gates and existing-ledger integration."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.problem_synthesis import SynthesisError, record, reflection_due, validate_request
from tools import research_control, run_state
from tools.registry_common import RegistryError


def _candidate():
    return {
        "id": "C1",
        "affected_problem_ids": ["P1", "P2"],
        "shared_cause": "the representation removes a rare-condition cue",
        "joint_prediction": "both failures should improve when that cue is restored",
        "discriminating_test": "evaluate the same held-out cases with and without the cue",
        "supporting_evidence_refs": ["results/main.json#cases"],
        "contradicting_evidence_refs": [],
        "complexity_assessment": "one controlled test is cheaper than two unrelated repairs",
    }


def _request(decision="MERGE"):
    request = {
        "schema_version": 1,
        "problems": [
            {"id": "P1", "observation": "class A regresses", "status": "open",
             "evidence_refs": ["results/main.json#A"]},
            {"id": "P2", "observation": "class B regresses", "status": "open",
             "evidence_refs": ["results/main.json#B"]},
        ],
        "candidates": [_candidate()],
        "decision": decision,
        "reason": "The joint test is the smallest way to distinguish the explanations.",
        "selected_candidate": "C1",
        "next_action": {"skill": "research-refine", "description": "state the unified question"},
    }
    if decision == "KEEP_SEPARATE":
        request.pop("selected_candidate")
        request["next_actions"] = [
            {"problem_id": "P1", "action": "inspect class-A sampling"},
            {"problem_id": "P2", "action": "inspect class-B labels"},
        ]
    return request


def test_merge_requires_joint_prediction_and_discriminating_check():
    normalized = validate_request(_request())
    assert normalized["decision"] == "MERGE"
    assert normalized["candidates"][0]["joint_prediction"]

    bad = _request()
    bad["candidates"][0].pop("discriminating_test")
    with pytest.raises(SynthesisError, match="discriminating_test"):
        validate_request(bad)


def test_keep_separate_requires_action_for_each_problem():
    normalized = validate_request(_request("KEEP_SEPARATE"))
    assert normalized["decision"] == "KEEP_SEPARATE"
    bad = _request("KEEP_SEPARATE")
    bad["next_actions"] = [{"problem_id": "P1", "action": "one action"}]
    with pytest.raises(SynthesisError, match="every problem"):
        validate_request(bad)


def test_merge_rejects_missing_supporting_evidence():
    bad = _request()
    bad["candidates"][0]["supporting_evidence_refs"] = []
    bad["candidates"][0]["contradicting_evidence_refs"] = []
    with pytest.raises(SynthesisError, match="evidence"):
        # A candidate without any supporting or contradicting evidence is not
        # allowed to masquerade as a merge decision.
        validate_request(bad)


def test_acceptance_fields_stay_with_claim_and_review_gates():
    bad = _request()
    bad["verdict"] = "supported"
    with pytest.raises(SynthesisError, match="outside problem-synthesis"):
        validate_request(bad)


def test_due_reports_cadence_signals_without_claiming_quality():
    result = reflection_due({
        "open_problem_count": 3,
        "completed_blocks": 2,
        "local_repairs": 2,
        "stale_count": 0,
        "branch_count": 1,
        "overlapping_failures": 0,
        "milestone_complete": False,
    })
    assert result["due"] is True
    assert "multiple_open_problems" in result["reasons"]
    assert "verdict" not in result


def test_record_uses_existing_iteration_ledger_and_not_run_state(tmp_path: Path):
    run_state.start_run(str(tmp_path), "reflection-run", ["decision"])
    before = (tmp_path / ".ei/runs/reflection-run.json").read_bytes()
    output = record(str(tmp_path), "reflection-run", "decision", _request())
    ledger = Path(output["ledger"])
    assert ledger.name == "reflection-run.iterations.jsonl"
    lines = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    assert lines[0]["event"] == "reflection"
    assert lines[0]["reflection"]["decision"] == "MERGE"
    assert (tmp_path / ".ei/runs/reflection-run.json").read_bytes() == before


def test_defer_and_blocked_require_explicit_blocker():
    for decision in ("DEFER", "BLOCKED"):
        request = _request(decision)
        request.pop("selected_candidate", None)
        request["blocker"] = "held-out labels are unavailable"
        assert validate_request(request)["decision"] == decision
        request.pop("blocker")
        with pytest.raises(SynthesisError, match="blocker"):
            validate_request(request)


def test_existing_continuation_contract_brakes_new_actions_until_recorded(tmp_path: Path):
    run_state.start_run(str(tmp_path), "long-run", ["explore", "review"])
    research_control.configure(tmp_path, "long-run", "save an evidence-backed handoff", {
        "max_actions": 4, "wall_seconds": 600, "max_attempts_per_key": 1,
        "resources": {"gpu_seconds": 0},
    })
    research_control.require_reflection(tmp_path, "long-run", ["milestone_complete"], level="milestone")
    assert research_control.inspect(tmp_path, "long-run")["status"] == "SYNTHESIS_REQUIRED"
    with pytest.raises(RegistryError, match="SYNTHESIS_REQUIRED"):
        research_control.claim_action(tmp_path, "long-run", "next", "explore", "What changes next?",
                                      costs={"gpu_seconds": 0})

    request = _request("KEEP_SEPARATE")
    request["gate_id"] = research_control.inspect(tmp_path, "long-run")["reflection_gate"]["id"]
    outcome = record(str(tmp_path), "long-run", "explore", request)
    assert outcome["reflection_gate"] == "cleared"
    assert research_control.inspect(tmp_path, "long-run")["status"] == "READY"
    metadata = run_state.load_run(str(tmp_path), "long-run")["coordination"]
    assert "reflection_gate" not in metadata
    assert metadata["last_reflection"]["decision"] == "KEEP_SEPARATE"


def test_active_gate_cannot_be_cleared_by_a_stale_ledger(tmp_path: Path):
    run_state.start_run(str(tmp_path), "stale-gate", ["explore"])
    research_control.configure(tmp_path, "stale-gate", "inspect evidence", {
        "max_actions": 2, "wall_seconds": 600, "max_attempts_per_key": 1,
        "resources": {"gpu_seconds": 0},
    })
    research_control.require_reflection(tmp_path, "stale-gate", ["branch_growth"])
    with pytest.raises(RegistryError, match="no valid record"):
        research_control.clear_reflection(tmp_path, "stale-gate")


def test_invalid_direct_ledger_payload_cannot_release_brake(tmp_path: Path):
    from tools.iteration_log import record_reflection

    run_state.start_run(str(tmp_path), "invalid-reflection", ["explore"])
    research_control.configure(tmp_path, "invalid-reflection", "inspect evidence", {
        "max_actions": 2, "wall_seconds": 600, "max_attempts_per_key": 1,
        "resources": {"gpu_seconds": 0},
    })
    research_control.require_reflection(tmp_path, "invalid-reflection", ["stale_progress"])
    record_reflection(tmp_path, "invalid-reflection", "explore", {
        "decision": "MERGE", "reason": "unvalidated direct write"
    })
    with pytest.raises(RegistryError, match="no valid record"):
        research_control.clear_reflection(tmp_path, "invalid-reflection")


def _configured(root, run_id='pilot', **limits):
    run_state.start_run(str(root), run_id, ['explore', 'review'])
    research_control.configure(root, run_id, 'save a reproducible research handoff', {
        'max_actions': 8, 'wall_seconds': 600, 'max_attempts_per_key': 1,
        'resources': {'fits': 20}, **limits,
    })
    return run_id


def _gated(root, run_id, decision='KEEP_SEPARATE'):
    request = _request(decision)
    request['gate_id'] = research_control.inspect(root, run_id)['reflection_gate']['id']
    return request


def _cadenced(root, every=2):
    run_state.start_run(str(root), 'cadence', ['explore', 'review'])
    return research_control.configure(root, 'cadence', 'inspect actual waves', {
        'max_actions': 12, 'wall_seconds': 600, 'max_attempts_per_key': 1,
        'resources': {'fits': 20}}, reflection_every_actions=every)


def _wave(root, key):
    return research_control.claim_action(root, 'cadence', key, 'explore',
        'Does this wave distinguish the explanations?', costs={'fits': 1})['action']


def _settle_wave(root, action, outcome='succeeded'):
    from tools.registry_common import fixed_ref
    path = root / (action['id'] + '.json')
    path.write_text(json.dumps({'wave': action['key'], 'observed': True}))
    return research_control.finish_action(root, 'cadence', action['id'], outcome,
        actual_costs={'fits': 1}, result_refs=[fixed_ref(root, path.name)],
        reason='' if outcome == 'succeeded' else 'Actual attempt failed')


def _continue_checkpoint(root, gate):
    return research_control.record_reflection(root, 'cadence', 'explore', {
        'schema_version': 1, 'kind': 'checkpoint', 'gate_id': gate['id'],
        'decision': 'CONTINUE', 'reason': 'The supplied evidence warrants the next distinguishing check',
        'evidence_refs': ['a000001.json'],
        'next_action': {'skill': 'experiment-plan', 'description': 'Run the remaining control'}})


def test_settlement_automatically_brakes_at_fixed_cadence_without_selecting_a_verdict(tmp_path):
    original = _cadenced(tmp_path)
    _settle_wave(tmp_path, _wave(tmp_path, 'wave-one'))
    assert research_control.inspect(tmp_path, 'cadence')['status'] == 'READY'
    second = _wave(tmp_path, 'wave-two')
    metadata = _settle_wave(tmp_path, second, 'failed')
    gate = metadata['reflection_gate']
    assert gate['action_ids'] == ['a000001', 'a000002']
    assert gate['reasons'] == ['completed_action_cadence']
    assert 'decision' not in gate
    with pytest.raises(RegistryError, match='REFLECTION_REQUIRED'):
        _wave(tmp_path, 'unreviewed-third-wave')
    _continue_checkpoint(tmp_path, gate)
    state = run_state.load_run(str(tmp_path), 'cadence')['coordination']
    assert state['reflection_reviewed_actions'] == gate['action_ids']
    assert state['limits'] == original['limits'] and state['started_at'] == original['started_at']
    assert research_control.inspect(tmp_path, 'cadence')['status'] == 'READY'
    # Identical settlement recovery cannot reopen the addressed boundary.
    assert 'reflection_gate' not in _settle_wave(tmp_path, second, 'failed')


def test_cadence_does_not_credit_results_that_arrived_during_the_review(tmp_path):
    _cadenced(tmp_path, every=1)
    first = _wave(tmp_path, 'first')
    metadata = research_control.require_reflection(tmp_path, 'cadence',
        ['direction_boundary'], kind='checkpoint')
    gate = metadata['reflection_gate']
    assert gate['action_ids'] == []
    _settle_wave(tmp_path, first)
    result = _continue_checkpoint(tmp_path, gate)
    metadata = run_state.load_run(str(tmp_path), 'cadence')['coordination']
    assert metadata['reflection_reviewed_actions'] == []
    assert metadata['reflection_gate']['action_ids'] == [first['id']]
    assert metadata['reflection_gate']['id'] != gate['id']
    assert result['reflection_gate'] == 'required'


def test_cancelled_unstarted_work_does_not_count_as_a_completed_scientific_wave(tmp_path):
    _cadenced(tmp_path)
    action = _wave(tmp_path, 'cancelled-before-launch')
    research_control.finish_action(tmp_path, 'cadence', action['id'], 'cancelled',
        actual_costs={'fits': 0}, reason='Confirmed never launched')
    metadata = _settle_wave(tmp_path, _wave(tmp_path, 'first-actual-wave'))
    assert 'reflection_gate' not in metadata


@pytest.mark.parametrize('every', [0, -1, True, 1.5])
def test_invalid_cadence_cannot_create_a_contract(tmp_path, every):
    with pytest.raises(RegistryError, match='cadence'):
        _cadenced(tmp_path, every)
    assert 'coordination' not in run_state.load_run(str(tmp_path), 'cadence')


def test_recovery_keeps_the_original_cadence_and_old_contracts_remain_opt_in(tmp_path):
    initial = _cadenced(tmp_path)
    again = research_control.configure(tmp_path, 'cadence', initial['objective'], initial['limits'])
    assert again['reflection_every_actions'] == 2
    with pytest.raises(RegistryError, match='fixed'):
        research_control.configure(tmp_path, 'cadence', initial['objective'], initial['limits'],
                                   reflection_every_actions=9)
    _configured(tmp_path, 'legacy')
    assert 'reflection_every_actions' not in run_state.load_run(str(tmp_path), 'legacy')['coordination']


def test_elapsed_review_is_persisted_before_a_new_dispatch_even_without_monitoring(tmp_path):
    from datetime import datetime, timedelta, timezone
    run_state.start_run(str(tmp_path), 'cadence', ['explore'])
    research_control.configure(tmp_path, 'cadence', 'inspect elapsed trajectory', {
        'max_actions': 4, 'wall_seconds': 600, 'max_attempts_per_key': 1,
        'resources': {'fits': 5}},
        started_at=(datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat(),
        reflection_interval_seconds=5)
    with pytest.raises(RegistryError, match='REFLECTION_REQUIRED'):
        _wave(tmp_path, 'must-review-first')
    gate = research_control.inspect(tmp_path, 'cadence')['reflection_gate']
    assert gate['reasons'] == ['elapsed_review_interval'] and gate['action_ids'] == []
    assert research_control.inspect(tmp_path, 'cadence')['reflection_gate']['id'] == gate['id']
    assert run_state.load_run(str(tmp_path), 'cadence')['coordination']['actions'] == []


def test_short_advice_cannot_initialize_a_runtime(tmp_path):
    with pytest.raises(FileNotFoundError):
        record(str(tmp_path), 'advice', 'explore', _request())
    assert not (tmp_path / '.ei').exists()


def test_separate_problems_do_not_require_an_invented_shared_cause():
    request = _request('KEEP_SEPARATE')
    request['candidates'] = []
    assert validate_request(request)['candidates'] == []
    request['next_actions'].append(request['next_actions'][0])
    with pytest.raises(SynthesisError, match='every problem'):
        validate_request(request)


@pytest.mark.parametrize('decision', ['DEFER', 'BLOCKED'])
def test_blocked_and_deferred_reflections_retain_brake(tmp_path, decision):
    run_id = _configured(tmp_path)
    research_control.require_reflection(tmp_path, run_id, ['local_repairs'])
    request = _gated(tmp_path, run_id, decision)
    request['blocker'] = 'Need the missing data provenance before another comparison'
    assert record(str(tmp_path), run_id, 'explore', request)['reflection_gate'] == 'required'
    assert research_control.clear_reflection(tmp_path, run_id)['reflection_gate']['blocker'] == request['blocker']
    with pytest.raises(RegistryError, match='SYNTHESIS_REQUIRED'):
        research_control.claim_action(tmp_path, run_id, 'retry', 'explore', 'Try again?', costs={'fits': 1})
    resolved = _gated(tmp_path, run_id)
    assert record(str(tmp_path), run_id, 'explore', resolved)['reflection_gate'] == 'cleared'


def test_pivot_waits_for_fixed_handoff_and_preserves_review_and_budget(tmp_path):
    from tools.registry_common import fixed_ref
    run_id = _configured(tmp_path)
    before = run_state.load_run(str(tmp_path), run_id)
    research_control.require_reflection(tmp_path, run_id, ['direction_boundary'], level='direction')
    output = record(str(tmp_path), run_id, 'explore', _gated(tmp_path, run_id, 'MERGE'))
    assert output['reflection_gate'] == 'required'
    assert research_control.inspect(tmp_path, run_id)['reflection_gate']['handoff_required']
    research_control.clear_reflection(tmp_path, run_id)
    assert research_control.inspect(tmp_path, run_id)['status'] == 'SYNTHESIS_REQUIRED'
    plan = tmp_path / 'REVISED_PLAN.md'
    plan.write_text('Probe the common cause with a controlled intervention. Budget: one fit.', encoding='utf-8')
    research_control.clear_reflection(tmp_path, run_id, handoff_ref=fixed_ref(tmp_path, 'REVISED_PLAN.md'))
    after = run_state.load_run(str(tmp_path), run_id)
    assert before['phases'] == after['phases']
    for field in ('limits', 'started_at', 'actions'):
        assert before['coordination'][field] == after['coordination'][field]
    assert research_control.inspect(tmp_path, run_id)['status'] == 'READY'
    plan.write_text('Changed plan', encoding='utf-8')
    assert research_control.inspect(tmp_path, run_id)['status'] == 'EVIDENCE_CHANGED'


def test_stale_reflection_cannot_release_next_gate_even_with_identical_clock(tmp_path, monkeypatch):
    run_id = _configured(tmp_path)
    monkeypatch.setattr(research_control, 'now', lambda: '2026-01-01T00:00:00Z')
    research_control.require_reflection(tmp_path, run_id, ['first'])
    request = _gated(tmp_path, run_id)
    first = record(str(tmp_path), run_id, 'explore', request)
    assert record(str(tmp_path), run_id, 'explore', request)['reflection_id'] == first['reflection_id']
    research_control.require_reflection(tmp_path, run_id, ['second'])
    with pytest.raises(RegistryError, match='active gate'):
        record(str(tmp_path), run_id, 'explore', request)
    with pytest.raises(RegistryError, match='no valid record'):
        research_control.clear_reflection(tmp_path, run_id)


def test_append_before_interrupted_state_save_recovers_without_duplicate(tmp_path, monkeypatch):
    run_id = _configured(tmp_path)
    research_control.require_reflection(tmp_path, run_id, ['milestone_complete'])
    request = _gated(tmp_path, run_id)
    save = run_state._save
    def interrupted(*args):
        raise OSError('simulated interruption after ledger append')
    monkeypatch.setattr(run_state, '_save', interrupted)
    with pytest.raises(OSError, match='interruption'):
        record(str(tmp_path), run_id, 'explore', request)
    monkeypatch.setattr(run_state, '_save', save)
    output = record(str(tmp_path), run_id, 'explore', request)
    assert output['record'] == 'existing'
    assert output['reflection_gate'] == 'cleared'
    assert len(Path(output['ledger']).read_text().splitlines()) == 1


def test_reflection_envelope_cannot_change_the_original_stale_ladder(tmp_path):
    from tools.iteration_log import note, record_reflection as append
    run_id = _configured(tmp_path)
    note(str(tmp_path), run_id, 'explore', 0)
    append(str(tmp_path), run_id, 'explore', {'stale_count': -99, 'event': 'note'})
    assert note(str(tmp_path), run_id, 'explore', 0) == {'stale_count': 2, 'pivot': 'structural'}


@pytest.mark.parametrize('problems', [0, 1])
def test_ordinary_milestone_does_not_force_multiple_problem_synthesis(problems):
    result = reflection_due({'milestone_complete': True, 'open_problem_count': problems})
    assert result['due']
    assert result['kind'] == 'checkpoint'
    assert result['skill'] is None


def test_fairness_drift_routes_to_audit():
    assert reflection_due({'fairness_drift': True, 'open_problem_count': 3})['skill'] == 'experiment-audit'


def test_generic_checkpoint_can_continue_replan_or_stop_without_fake_problems(tmp_path):
    run_id = _configured(tmp_path)
    research_control.require_reflection(tmp_path, run_id, ['milestone_complete'], kind='checkpoint')
    assert research_control.inspect(tmp_path, run_id)['status'] == 'REFLECTION_REQUIRED'
    payload = {'kind': 'checkpoint', 'schema_version': 1,
               'gate_id': research_control.inspect(tmp_path, run_id)['reflection_gate']['id'],
               'decision': 'CONTINUE', 'reason': 'The new observation discriminates between hypotheses.',
               'evidence_refs': ['results/block-1.json'],
               'next_action': {'skill': 'experiment-plan', 'description': 'Use remaining budget on the next test'}}
    research_control.record_reflection(tmp_path, run_id, 'explore', payload)
    assert research_control.inspect(tmp_path, run_id)['status'] == 'READY'
    research_control.require_reflection(tmp_path, run_id, ['direction_boundary'], kind='checkpoint')
    payload.update(gate_id=research_control.inspect(tmp_path, run_id)['reflection_gate']['id'],
                   decision='STOP', reason='The direction no longer answers the research question.')
    research_control.record_reflection(tmp_path, run_id, 'explore', payload)
    assert research_control.inspect(tmp_path, run_id)['status'] == 'STOPPED'
    assert run_state.load_run(str(tmp_path), run_id)['phases'][0]['status'] == 'pending'


def test_other_required_gates_keep_priority_and_allow_terminal_reconciliation(tmp_path):
    run_id = _configured(tmp_path, max_actions=1)
    action = research_control.claim_action(tmp_path, run_id, 'first', 'explore', 'Does the baseline run?', costs={'fits': 1})
    research_control.require_reflection(tmp_path, run_id, ['local_repairs'])
    assert research_control.inspect(tmp_path, run_id)['status'] == 'RECONCILE'
    research_control.finish_action(tmp_path, run_id, action['action']['id'], 'failed',
                                   actual_costs={'fits': 1}, reason='Known terminal failure')
    assert research_control.inspect(tmp_path, run_id)['status'] == 'BUDGET_EXHAUSTED'
    record(str(tmp_path), run_id, 'explore', _gated(tmp_path, run_id))
    assert research_control.inspect(tmp_path, run_id)['status'] == 'BUDGET_EXHAUSTED'


@pytest.mark.parametrize('bad', [True, '1', 2])
def test_schema_version_is_an_integer(bad):
    request = _request()
    request['schema_version'] = bad
    with pytest.raises(SynthesisError, match='schema_version'):
        validate_request(request)


def test_public_cli_round_trip_outside_the_toolkit_directory(tmp_path):
    import subprocess
    import sys
    run_id = _configured(tmp_path)
    root = Path(__file__).resolve().parents[1]
    tool = root / 'tools/problem_synthesis.py'
    control = root / 'tools/research_control.py'
    def invoke(script, *args, expected=0):
        output = subprocess.run([sys.executable, str(script), *map(str, args)], cwd=tmp_path,
                                capture_output=True, encoding='utf-8', timeout=30)
        assert output.returncode == expected, output.stderr
        return json.loads(output.stdout) if expected == 0 else output
    metadata = invoke(control, '--root', tmp_path, '--run-id', run_id,
                      'require-reflection', '--reason', 'direction_boundary', '--level', 'direction')
    request = _request('MERGE')
    request['reason'] = '两组异常需要共同预测，不能仅凭曲线相似合并。'
    request['gate_id'] = metadata['reflection_gate']['id']
    request_path = tmp_path / 'reflection.json'
    request_path.write_text(json.dumps(request, ensure_ascii=False), encoding='utf-8')
    invoke(tool, 'validate', request_path)
    result = invoke(tool, 'record', tmp_path, run_id, 'explore', request_path)
    assert result['reflection_gate'] == 'required'
    (tmp_path / 'plan.md').write_text('Compare the joint intervention on the same held-out cases.', encoding='utf-8')
    invoke(control, '--root', tmp_path, '--run-id', run_id, 'clear-reflection', '--handoff', 'plan.md')
    assert invoke(control, '--root', tmp_path, '--run-id', run_id, 'inspect')['status'] == 'READY'
    request_path.write_text('{"schema_version":true}', encoding='utf-8')
    failed = invoke(tool, 'validate', request_path, expected=2)
    assert 'schema_version' in failed.stderr


def test_latest_valid_reflection_survives_a_truncated_or_nonobject_ledger_line(tmp_path):
    from tools.iteration_log import record_reflection as append
    run_id = _configured(tmp_path)
    research_control.require_reflection(tmp_path, run_id, ['local_repairs'])
    request = validate_request(_gated(tmp_path, run_id))
    ledger = tmp_path / '.ei/runs/pilot.iterations.jsonl'
    ledger.write_text('[]\n{"interrupted":', encoding='utf-8')
    output = append(str(tmp_path), run_id, 'explore', request)
    research_control.clear_reflection(tmp_path, run_id)
    assert research_control.inspect(tmp_path, run_id)['status'] == 'READY'
    assert json.loads(Path(output['ledger']).read_text().splitlines()[-1])['reflection'] == request


def test_later_continue_cannot_forget_the_active_plan_identity(tmp_path):
    from tools.registry_common import fixed_ref
    run_id = _configured(tmp_path)
    research_control.require_reflection(tmp_path, run_id, ['direction_boundary'])
    record(str(tmp_path), run_id, 'explore', _gated(tmp_path, run_id, 'MERGE'))
    plan = tmp_path / 'plan.md'
    plan.write_text('Original discriminating comparison', encoding='utf-8')
    reference = fixed_ref(tmp_path, 'plan.md')
    research_control.clear_reflection(tmp_path, run_id, handoff_ref=reference)
    research_control.require_reflection(tmp_path, run_id, ['milestone_complete'], kind='checkpoint')
    payload = {'kind': 'checkpoint', 'schema_version': 1,
               'gate_id': research_control.inspect(tmp_path, run_id)['reflection_gate']['id'],
               'decision': 'CONTINUE', 'reason': 'The next planned comparison remains informative',
               'evidence_refs': ['results/first.json'],
               'next_action': {'skill': 'experiment-bridge', 'description': 'Use the reviewed plan'}}
    research_control.record_reflection(tmp_path, run_id, 'explore', payload)
    assert research_control.inspect(tmp_path, run_id)['status'] == 'READY'
    assert run_state.load_run(str(tmp_path), run_id)['coordination']['reflection_plan_ref'] == reference
    plan.write_text('Unreviewed change', encoding='utf-8')
    assert research_control.inspect(tmp_path, run_id)['status'] == 'EVIDENCE_CHANGED'


def test_three_actual_cpu_waves_with_brakes_recovery_and_original_accounting(tmp_path):
    """Programmed control-flow exercise, not an autonomous scientific judgment."""
    import subprocess
    import sys
    from tools.registry_common import fixed_ref
    pilot = Path(__file__).parent / 'research_pilots/run_study.py'
    run_id = _configured(tmp_path, max_actions=3, resources={'fits': 12})
    original = run_state.load_run(str(tmp_path), run_id)
    receipts = []
    for wave, scenario in enumerate(('negative', 'pivot', 'positive'), 1):
        request = dict(action_key=f'wave-{wave}', phase='explore',
                       question=f'Collect held-out evidence for programmed {scenario} fixture',
                       costs={'fits': 6 if scenario == 'pivot' else 3})
        action = research_control.claim_action(tmp_path, run_id, **request)['action']
        # Recovery before terminal settlement must find this same reservation.
        assert research_control.claim_action(tmp_path, run_id, **request)['claim'] == 'existing'
        study = tmp_path / f'wave-{wave}'
        outcome = subprocess.run([sys.executable, str(pilot), '--output', str(study),
                                  '--scenario', scenario], capture_output=True, text=True, timeout=15)
        assert outcome.returncode == 0, outcome.stderr
        report = json.loads((study / 'results.json').read_text(encoding='utf-8'))
        assert report['review_status'] == 'not-reviewed'
        reference = fixed_ref(tmp_path, f'wave-{wave}/results.json')
        receipts.append(reference)
        research_control.finish_action(tmp_path, run_id, action['id'], 'succeeded',
                                       actual_costs=request['costs'], result_refs=[reference])
        research_control.require_reflection(tmp_path, run_id, ['milestone_complete'], kind='checkpoint')
        with pytest.raises(RegistryError, match='REFLECTION_REQUIRED|BUDGET_EXHAUSTED'):
            research_control.claim_action(tmp_path, run_id, f'early-{wave}', 'explore',
                                          'Must not dispatch past the checkpoint', costs={'fits': 0})
        payload = {'schema_version': 1, 'kind': 'checkpoint',
                   'gate_id': research_control.inspect(tmp_path, run_id)['reflection_gate']['id'],
                   'decision': 'REPLAN' if wave == 1 else 'CONTINUE' if wave == 2 else 'STOP',
                   'reason': f'Programmed {scenario} fixture; see raw result and paired cases',
                   'evidence_refs': [reference['path']],
                   'next_action': {'skill': 'experiment-plan', 'description': 'Prepare the next bounded comparison'}}
        research_control.record_reflection(tmp_path, run_id, 'explore', payload)
        if wave == 1:
            assert research_control.inspect(tmp_path, run_id)['status'] == 'REFLECTION_REQUIRED'
            (tmp_path / 'revised-plan.md').write_text('Test the signal feature; preserve the negative original result.', encoding='utf-8')
            research_control.clear_reflection(tmp_path, run_id,
                handoff_ref=fixed_ref(tmp_path, 'revised-plan.md'))
    state = run_state.load_run(str(tmp_path), run_id)
    assert state['phases'] == original['phases']
    assert state['coordination']['started_at'] == original['coordination']['started_at']
    assert research_control.inspect(tmp_path, run_id)['status'] == 'STOPPED'
    assert research_control.inspect(tmp_path, run_id)['spent_or_reserved'] == {'fits': 12}
    assert research_control.inspect(tmp_path, run_id)['actions_used'] == 3
    assert all((tmp_path / ref['path']).is_file() for ref in receipts)


def test_public_forward_use_tables_are_reproducible(tmp_path):
    import csv
    import subprocess
    import sys
    fixtures = Path(__file__).parent / 'behavior/v160-fixtures'
    generated = subprocess.run([sys.executable, str(fixtures / 'generate.py'), '--output', str(tmp_path)],
                               capture_output=True, text=True, timeout=15)
    assert generated.returncode == 0, generated.stderr
    for case in ('T01', 'T02'):
        with (fixtures / case / 'results.csv').open(newline='', encoding='utf-8') as source:
            expected = list(csv.DictReader(source))
        with (tmp_path / case / 'results.csv').open(newline='', encoding='utf-8') as source:
            assert list(csv.DictReader(source)) == expected
        assert len(expected) == 40
