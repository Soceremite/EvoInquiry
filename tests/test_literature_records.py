"""Literature exports retain identities, source observations and uncertainty."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tools.literature_records import normalize_arxiv, normalize_doi, normalize_register


def register():
    return {'schema_version': 1, 'searches': [
        {'id': 's1', 'source': 'local', 'query': '中文 reasoning', 'searched_at': '2026-10-15', 'status': 'ok'},
        {'id': 's2', 'source': 'openalex', 'query': 'counter evidence', 'searched_at': '2026-10-15', 'status': 'rate_limited'},
    ], 'papers': []}


def paper(identifier='p1', **values):
    return dict({'id': identifier, 'title': 'A study / 中文研究', 'source': 'local',
                 'search_id': 's1', 'url': 'https://example.org/paper',
                 'reading_level': 'abstract'}, **values)


@pytest.mark.parametrize('value', ['DOI:10.1234/ABC.X', 'https://doi.org/10.1234/ABC.X',
                                 'https://dx.doi.org/10.1234/ABC%2EX'])
def test_doi_variants(value):
    assert normalize_doi(value) == '10.1234/abc.x'


@pytest.mark.parametrize('value,expected', [
    ('https://arxiv.org/pdf/2401.12345v2.pdf', ('2401.12345', 'v2')),
    ('arXiv:math.GT/0309136v1', ('math.GT/0309136', 'v1')),
    ('2401.12345', ('2401.12345', '')),
])
def test_arxiv_versions(value, expected):
    assert normalize_arxiv(value) == expected


def test_merging_versions_retains_every_source_and_is_idempotent():
    data = register()
    data['papers'] = [paper(arxiv_id='2401.12345v1'),
                      paper('p2', title='Revised study', arxiv_id='2401.12345v3',
                            doi='https://doi.org/10.1234/ABC.X', reading_level='sections',
                            locators=['Table 2; section 4'], notes='Contrary results in subgroup B')]
    original = copy.deepcopy(data)
    result = normalize_register(data)
    assert data == original
    assert len(result['papers']) == 1
    assert [p['arxiv_id'] for p in result['papers'][0]['observations']] == ['2401.12345v1', '2401.12345v3']
    assert result['papers'][0]['observations'][1]['title'] == 'Revised study'
    assert result['searches'][1]['status'] == 'rate_limited'
    assert normalize_register(result) == result


def test_equal_titles_without_shared_identity_only_flag_possible_matches():
    data = register()
    data['papers'] = [paper(doi='10.1234/a'), paper('p2', doi='10.1234/b')]
    result = normalize_register(data)
    assert len(result['papers']) == 2
    assert result['possible_title_matches'] == [['p1', 'p2']]


def test_title_candidates_are_stable_after_interleaved_identity_merge():
    data = register()
    data['papers'] = [paper('p' + str(i), title=title, doi='10.1234/' + doi)
                      for i, (title, doi) in enumerate([('a', '0'), ('b', '1'), ('b', '0'), ('b', '2')])]
    result = normalize_register(data)
    assert normalize_register(result) == result


@pytest.mark.parametrize('papers', [
    [paper(arxiv_id='2401.12345', doi='10.1234/a'), paper('p2', arxiv_id='2401.12345v2', doi='10.1234/b')],
    [paper(doi='10.1234/a'), paper('p2', arxiv_id='2401.12345'),
     paper('p3', doi='10.1234/a', arxiv_id='2401.12345')],
])
def test_conflicting_strong_identities_require_review(papers):
    data = register(); data['papers'] = papers
    with pytest.raises(ValueError, match='Conflicting'):
        normalize_register(data)


@pytest.mark.parametrize('change', [
    {'search_id': 'absent'}, {'reading_level': 'I read everything'},
    {'reading_level': 'sections'}, {'title': ''}, {'doi': 'not-a-doi'},
    {'observations': []},
])
def test_incomplete_or_unverifiable_records_rejected(change):
    data = register(); data['papers'] = [paper(**change)]
    with pytest.raises(ValueError):
        normalize_register(data)


def test_cli_does_not_overwrite_existing_export(tmp_path):
    source = tmp_path / 'input.json'; source.write_text(json.dumps(register()), encoding='utf-8')
    output = tmp_path / 'output.json'; output.write_text('Keep the previous record', encoding='utf-8')
    run = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / 'tools/literature_records.py'),
                          str(source), '--output', str(output)], capture_output=True, text=True)
    assert run.returncode == 2
    assert output.read_text() == 'Keep the previous record'


def test_unicode_stdout_export_works_in_non_utf8_pipe(tmp_path):
    source = tmp_path / 'input.json'; source.write_text(json.dumps(register()), encoding='utf-8')
    run = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / 'tools/literature_records.py'),
                          str(source)], capture_output=True, env=dict(os.environ, PYTHONIOENCODING='ascii'))
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout.decode('utf-8'))['searches'][0]['query'] == '中文 reasoning'
