"""Exercise the migrated rebuttal gate on synthetic author-response workspaces."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from tools.rebuttal_check import check
from tools.registry_common import fixed_ref

ROOT = Path(__file__).resolve().parents[1]


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding='utf-8')


def prepared(root, mode):
    work = root / '.ei/rebuttal'
    memory = work / 'memory'
    evidence = root / 'submitted-paper.txt'
    evidence.write_text('All three runs use the validation split.', encoding='utf-8')
    approval = root / 'author-approval.txt'
    approval.write_text('Approved clarification of the protocol in Section 3.', encoding='utf-8')
    rules = {'status': 'user_confirmed', 'response': {'mode': mode, 'limits': {'character_limit': 500}},
             'confirmation': {'confirmed_by_user': True}, 'content_permissions': {'external_links_allowed': 'no'}}
    save(memory / 'venue_rules.json', rules)
    claim = {'text': evidence.read_text(encoding='utf-8')+'\n','kind':'fact','concerns':['R1-C1'],
             'sources':[{'ref':fixed_ref(root,'submitted-paper.txt'),'excerpt':evidence.read_text(encoding='utf-8')}]}
    promise = {'text':'We will clarify the protocol in Section 3.\n', 'kind':'commitment',
               'commitment':'REV-01','concerns':['R1-C1']}
    ledger = {'concerns':[{'id':'R1-C1','reviewer':'R1','status':'answered'}],
              'revisions':[{'id':'REV-01','concern_id':'R1-C1','status':'approved_for_rebuttal',
                            'evidence':[{'ref':fixed_ref(root,'author-approval.txt'),'excerpt':'Approved clarification'}]}],
              'rehearsal':{'backend':'manual','executor_model':'gpt-6.1-sol','external_rounds':[]}, 'drafts':[]}
    if mode == 'hybrid':
        ledger['drafts'].append({'path':'.ei/rebuttal/drafts/global.md',
            'units':[{'text':'Thank you for the careful review.\n','kind':'framing'}]})
    output = 'PASTE_READY.txt' if mode != 'openreview_per_reviewer' else 'R1.md'
    ledger['drafts'].append({'path':f'.ei/rebuttal/drafts/{output}','reviewer':'R1','units':[claim,promise]})
    for draft in ledger['drafts']:
        path = root / draft['path']
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(''.join(row['text'] for row in draft['units']).encode())
    (work/'drafts/REVISION_PLAN.md').write_text('## Overall checklist\n\n- [ ] (REV-01) R1-C1 · Section 3 · Clarify the protocol\n',encoding='utf-8')
    save(memory/'submission-check.json',ledger)
    return memory, rules, ledger


@pytest.mark.parametrize('mode', ['openreview_per_reviewer','hybrid','unified_limited','global_comment','openreview_markdown_latex'])
def test_ready_text_preserves_scope_without_external_backend(tmp_path, mode):
    _, _, _ = prepared(tmp_path, mode)
    result = subprocess.run([sys.executable,str(ROOT/'tools/rebuttal_check.py'),'--root',str(tmp_path),
        '--check','finalize','--record'],text=True,capture_output=True,timeout=20)
    assert result.returncode==0,result.stdout+result.stderr
    receipt=json.loads(result.stdout)
    assert receipt['status']=='MECHANICAL_CHECKS_PASSED'
    assert receipt['rehearsal']['external_status']=='REVIEW_UNAVAILABLE'
    assert receipt['rehearsal']['scope']=='in_context'
    assert 'Cross-family external validation was not performed' in receipt['rehearsal']['note']
    assert len(receipt['outputs']) == (2 if mode=='hybrid' else 1)
    assert (tmp_path/'.ei/rebuttal/logs/evoinquiry_check.json').is_file()


@pytest.mark.parametrize('reviewer_model,trace_present,expected', [
    ('gpt-5.4', True, 'REVIEW_UNAVAILABLE'),
    ('claude-sonnet-4', False, 'REVIEW_UNAVAILABLE'),
    ('claude-sonnet-4', True, 'cross_family_external'),
])
def test_optional_reviewer_requires_a_verifiable_cross_family_trace(
        tmp_path, reviewer_model, trace_present, expected):
    memory, _, ledger = prepared(tmp_path, 'openreview_per_reviewer')
    raw = tmp_path / '.ei/traces/rebuttal/round-01.txt'
    raw.parent.mkdir(parents=True)
    raw.write_text(f'Reviewer-Model: {reviewer_model}\nSynthetic reviewer test.\n', encoding='utf-8')
    ref = fixed_ref(tmp_path, raw.relative_to(tmp_path))
    if not trace_present:
        raw.unlink()
    ledger['rehearsal']['external_rounds'] = [
        {'reviewer_model': reviewer_model, 'identity_verified': True, 'response_ref': ref},
    ]
    save(memory / 'submission-check.json', ledger)

    result = check(tmp_path, finalize=True)
    assert result['status'] == 'MECHANICAL_CHECKS_PASSED'
    assert result['rehearsal']['external_status'] == expected
    assert result['rehearsal']['verified_response_refs'] == ([ref] if expected == 'cross_family_external' else [])


@pytest.mark.parametrize('change,diagnostic',[
    ('venue','confirmation before drafting'),('source','Missing evidence'),('coverage','requires a response'),
    ('length','exceeds character_limit'),('orphan','Orphan revision item'),
    ('unapproved','Invalid revision item'),('thread','outside reviewer thread'),
    ('no-thread','Missing reviewer thread'),('venue-promise','commitment exceeds venue permissions'),
    ('link','Links exceed venue permissions'),('fake-excerpt','Evidence excerpt missing'),
])
def test_rebuttal_blocks_unverified_ready_artifacts(tmp_path,change,diagnostic):
    memory,rules,ledger=prepared(tmp_path,'openreview_per_reviewer')
    units=ledger['drafts'][0]['units']
    if change=='venue':
        rules['status']='ai_found_pending_confirmation'
    elif change=='source':
        units[0]['sources']=[]
    elif change=='coverage':
        ledger['concerns'].append({'id':'R2-C1','reviewer':'R2','status':'answered'})
    elif change=='length':
        rules['response']['limits']['character_limit']=5
    elif change=='orphan':
        ledger['revisions'].append(ledger['revisions'][0]|{'id':'REV-02'})
    elif change=='unapproved':
        ledger['revisions'][0]['status']='needs_user_input'
    elif change=='thread':
        ledger['drafts'][0]['reviewer']='R2'
    elif change=='no-thread':
        ledger['drafts'][0].pop('reviewer')
    elif change=='venue-promise':
        rules['content_permissions']['revision_commitments_allowed']='no'
    elif change=='link':
        units[0]['text']+='https://example.invalid/rebuttal\n'
        (tmp_path / ledger['drafts'][0]['path']).write_bytes(''.join(row['text'] for row in units).encode())
    else:
        units[0]['sources'][0]['excerpt']='All test splits improved by 10%.'
    save(memory/'venue_rules.json',rules)
    save(memory/'submission-check.json',ledger)
    result = subprocess.run([sys.executable, str(ROOT / 'tools/rebuttal_check.py'), '--root', str(tmp_path),
                             '--check', 'finalize'], text=True, capture_output=True, timeout=20)
    assert result.returncode == 3, result.stdout + result.stderr
    result = json.loads(result.stdout)
    assert result['status']=='BLOCKED'
    assert any(diagnostic in text for text in result['issues']),result


def test_intake_looks_for_legacy_without_moving_it(tmp_path):
    previous=tmp_path/'rebuttal/REBUTTAL_STATE.md'
    previous.parent.mkdir()
    previous.write_text('Legacy round 2',encoding='utf-8')
    result=check(tmp_path)
    assert result['legacy_available'] is True and result['status']=='BLOCKED'
    assert previous.read_text()=='Legacy round 2'
    assert not (tmp_path/'.ei').exists()


def test_pdf_requires_measured_compilation_evidence(tmp_path):
    prepared(tmp_path,'pdf_one_page')
    result=check(tmp_path,finalize=True)
    assert result['status']=='BLOCKED'
    assert 'Compile the submission PDF' in result['issues'][0]
