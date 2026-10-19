"""Decisions are reusable only with their original scope and current evidence."""
import json

import pytest

from tools.registry_common import RegistryError
from tools.research_memory import retrieve
from tools.research_wiki import init_wiki, record_decision


def test_original_decisions_keep_uncertainty_provenance_and_successors(tmp_path):
    init_wiki(str(tmp_path / 'notes'))
    (tmp_path / 'pilot.csv').write_text('seed,delta\n1,-1\n2,0\n', encoding='utf-8')
    decision = {'id': 'd1', 'question': 'Does augmentation improve accuracy?',
        'alternatives': ['Retain baseline', 'Train augmentation'], 'choice': 'Retain baseline',
        'reason': 'Augmentation did not improve the primary outcome in this pilot.',
        'provenance': 'verified_observation', 'evidence': ['pilot.csv'],
        'uncertainties': ['Limited seed coverage'], 'revisit_when': 'After a different dataset is available'}
    record_decision(tmp_path / 'notes', decision, project_root=tmp_path)
    record_decision(tmp_path / 'notes', dict(decision, id='d2', supersedes='d1',
                    choice='Revisit augmentation on the new dataset'), project_root=tmp_path)
    ledger = tmp_path / 'notes/decisions.jsonl'
    before = ledger.read_bytes()
    report = retrieve(tmp_path, 'augmentation accuracy', ['notes/decisions.jsonl'])
    first = next(row for row in report['matches'] if row['id'] == 'd1')
    assert first['superseded_by'] == ['d2']
    assert first['evidence_status'] == 'current'
    assert first['provenance'] == 'verified_observation'
    assert first['uncertainties'] == ['Limited seed coverage']
    (tmp_path / 'pilot.csv').write_text('changed\n')
    changed = retrieve(tmp_path, 'augmentation', ['notes/decisions.jsonl'])
    assert all(row['evidence_status'] == 'changed-or-unavailable' for row in changed['matches'])
    assert ledger.read_bytes() == before and not (tmp_path / '.ei').exists()


def test_markdown_and_chinese_work_without_wiki_or_state_initialization(tmp_path):
    (tmp_path / 'DECISIONS.md').write_text('# 数据增强\n负面结果：数据增强未提升准确率，应复核数据分布。\n', encoding='utf-8')
    before = (tmp_path / 'DECISIONS.md').read_bytes()
    report = retrieve(tmp_path, '数据增强 准确率', ['DECISIONS.md'])
    assert len(report['matches']) == 1
    assert report['matches'][0]['evidence_status'] == 'unbound'
    assert (tmp_path / 'DECISIONS.md').read_bytes() == before
    assert not (tmp_path / '.ei').exists() and not (tmp_path / 'notes').exists()


def test_missing_source_does_not_hide_other_records(tmp_path):
    (tmp_path / 'decisions.md').write_text('# Pilot\nThe regression pilot failed.\n')
    report = retrieve(tmp_path, 'pilot', ['missing.md', 'decisions.md'])
    assert report['matches'] and report['source_issues'][0]['source'] == 'missing.md'


def test_incomplete_tail_remains_unread_and_unchanged(tmp_path):
    path = tmp_path / 'decisions.jsonl'
    path.write_bytes(json.dumps({'id': 'd1', 'question': 'pilot failed'}).encode() + b'\n{"id":"d2"')
    before = path.read_bytes()
    report = retrieve(tmp_path, 'pilot', ['decisions.jsonl'])
    assert len(report['matches']) == 1 and report['source_issues']
    assert path.read_bytes() == before


def test_lexical_match_does_not_certify_or_promote_an_agent_proposal(tmp_path):
    (tmp_path / 'decisions.jsonl').write_text(json.dumps({'id': 'd1', 'question': 'pilot improved',
        'provenance': 'agent_proposal', 'uncertainties': ['Unverified'], 'revisit_when': 'Check raw results'}) + '\n')
    row = retrieve(tmp_path, 'pilot improved', ['decisions.jsonl'])['matches'][0]
    assert row['provenance'] == 'agent_proposal' and row['evidence_status'] == 'unbound'


def test_external_source_and_invalid_limits_are_rejected(tmp_path):
    for sources, kwargs in [(['../private.md'], {}), (['test.md'], {'limit': True}),
                             (['test.md'], {'excerpt_chars': 99999})]:
        with pytest.raises(RegistryError):
            retrieve(tmp_path, 'pilot', sources, **kwargs)
    assert not (tmp_path / '.ei').exists()
