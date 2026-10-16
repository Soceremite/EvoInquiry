"""Actual wiki decisions survive retries, revisions and cooperating writers."""
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from tools.research_wiki import init_wiki, record_decision
from tools.registry_common import verify_ref

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path):
    init_wiki(str(tmp_path / 'notes'))
    (tmp_path / 'results.csv').write_text('seed,value\n1,2\n2,2\n', encoding='utf-8')
    return tmp_path


def decision(identifier='d1', **values):
    return dict({'id': identifier, 'question': 'Which explanation should we investigate?',
                 'alternatives': ['Keep the current method', 'Test a simpler explanation'],
                 'choice': 'Test the simpler explanation', 'reason': 'The pilot did not distinguish the mechanisms.',
                 'provenance': 'agent_proposal', 'evidence': ['results.csv'],
                 'uncertainties': ['Whether the measurement is sensitive enough'],
                 'revisit_when': 'After checking measurement sensitivity'}, **values)


def record(root, entry):
    return record_decision(root / 'notes', entry, project_root=root)


def test_retry_is_identical_and_revision_keeps_original_bytes(project):
    first = record(project, decision())
    ledger = project / 'notes/decisions.jsonl'; before = ledger.read_bytes()
    assert record(project, decision()) == first
    assert ledger.read_bytes() == before
    second = record(project, decision('d2', supersedes='d1', choice='Pause the hypothesis'))
    assert ledger.read_bytes().startswith(before)
    assert second['supersedes'] == 'd1'
    assert verify_ref(project, first['evidence_refs'][0]) == project / 'results.csv'
    assert not (project / '.ei').exists()


def test_conflicting_retry_or_changed_evidence_does_not_rewrite_history(project):
    record(project, decision()); ledger = project / 'notes/decisions.jsonl'; before = ledger.read_bytes()
    with pytest.raises(ValueError, match='different content'):
        record(project, decision(provenance='user_decision'))
    (project / 'results.csv').write_text('Changed data\n', encoding='utf-8')
    with pytest.raises(ValueError, match='changed evidence'):
        record(project, decision())
    assert ledger.read_bytes() == before


@pytest.mark.parametrize('changes', [
    {'provenance': 'user_probably_wanted'}, {'provenance': 'verified_observation', 'evidence': []},
    {'status': 'accepted'}, {'supersedes': 'nonexistent'}, {'evidence': ['../outside']},
    {'choice': ''},
])
def test_bad_provenance_runtime_state_or_evidence_is_not_recorded(project, changes):
    with pytest.raises(ValueError):
        record(project, decision(**changes))
    assert not (project / 'notes/decisions.jsonl').exists()


def test_interrupted_ledger_preserved_for_recovery(project):
    ledger = project / 'notes/decisions.jsonl'; ledger.write_bytes(b'{"id":"partial')
    with pytest.raises(ValueError, match='Interrupted'):
        record(project, decision())
    assert ledger.read_bytes() == b'{"id":"partial'


def test_failed_commit_preserves_prior_decisions(project):
    record(project, decision()); ledger = project / 'notes/decisions.jsonl'; before = ledger.read_bytes()
    with patch('tools.registry_common.atomic_write', side_effect=OSError('simulated publication failure')):
        with pytest.raises(OSError, match='publication failure'):
            record(project, decision('d2'))
    assert ledger.read_bytes() == before
    record(project, decision('d2'))
    assert len(ledger.read_text(encoding='utf-8').splitlines()) == 2


def test_process_writers_preserve_both_decisions_and_deduplicate_retries(project):
    script = '''from tools.research_wiki import record_decision
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); entry=json.loads(sys.argv[2])
record_decision(root/'notes',entry,project_root=root)
entry['id']=sys.argv[3]
record_decision(root/'notes',entry,project_root=root)
'''
    children = [subprocess.Popen([sys.executable, '-c', script, str(project), json.dumps(decision()), key],
                                 cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                for key in ('writer-a', 'writer-b')]
    try:
        for child in children:
            stdout, stderr = child.communicate(timeout=30)
            assert child.returncode == 0, (stdout, stderr)
    finally:
        for child in children:
            if child.poll() is None:
                child.kill(); child.wait()
    entries = [json.loads(v) for v in (project / 'notes/decisions.jsonl').read_text(encoding='utf-8').splitlines()]
    assert {entry['id'] for entry in entries} == {'d1', 'writer-a', 'writer-b'}


def test_simple_negative_research_statement_is_valid(project):
    result = record(project, decision(choice='Stop training and reject this hypothesis',
                                      reason='The primary outcome deteriorated on both seeds.'))
    assert result['choice'].startswith('Stop training')


def test_missing_wiki_is_not_automatically_initialized(tmp_path):
    with pytest.raises(ValueError, match='existing initialized wiki'):
        record(tmp_path, decision())
    assert not (tmp_path / 'notes').exists()


def test_decision_cli_keeps_unicode_under_ascii_pipe(project):
    data = decision(question='这个结果能否支持原假设？', choice='先检查测量灵敏度')
    source = project / 'decision.json'
    source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    run = subprocess.run([sys.executable, str(ROOT / 'tools/research_wiki.py'),
                          'record_decision', str(project / 'notes'), '--input', str(source),
                          '--project-root', str(project)], cwd=ROOT,
                         env=dict(os.environ, PYTHONIOENCODING='ascii'), capture_output=True)
    assert run.returncode == 0, run.stderr.decode('utf-8')
    assert json.loads(run.stdout.decode('utf-8'))['question'] == data['question']
