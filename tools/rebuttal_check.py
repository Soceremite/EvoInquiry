"""Check the recorded venue, evidence, coverage and commitments for exact rebuttal files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

if __package__:
    from .registry_common import RegistryError, atomic_write, fixed_ref, local_path, read_record, verify_ref
    from .review_gate import derive_model_family
    from .state_paths import resolve_state_root, state_writer
else:
    from registry_common import RegistryError, atomic_write, fixed_ref, local_path, read_record, verify_ref
    from review_gate import derive_model_family
    from state_paths import resolve_state_root, state_writer


MODES = {'openreview_per_reviewer', 'unified_limited', 'pdf_one_page', 'global_comment',
         'hybrid', 'openreview_markdown_latex'}
COMMITMENTS = {'already_done', 'approved_for_rebuttal', 'future_work_only'}
CHECKBOX = re.compile(r'^- \[[xX ]\] \(([A-Za-z0-9_.-]+)\) ')
PRIVATE = re.compile(r'leaflink|overleaf\.com|(?:/home/|/Users/|[A-Z]:\\Users\\)|\bTODO\b', re.I)


def _intake(root, workspace):
    rules_file = workspace / 'memory/venue_rules.json'
    legacy = (root / 'rebuttal/REBUTTAL_STATE.md').is_file()
    if not rules_file.is_file():
        return None, {'status': 'BLOCKED', 'issues': ['Provide confirmed venue rules'], 'legacy_available': legacy}
    rules = read_record(rules_file)
    confirmation = rules.get('confirmation', {})
    issues = []
    if (rules.get('status') != 'user_confirmed' or confirmation.get('confirmed_by_user') is not True
            or confirmation.get('pending_confirmation_items') or confirmation.get('rule_conflicts')):
        issues.append('Venue rules require confirmation before drafting')
    if rules.get('response', {}).get('mode') not in MODES:
        issues.append('Select a permitted response mode')
    return rules, {'status': 'BLOCKED' if issues else 'READY_TO_DRAFT', 'issues': issues, 'legacy_available': legacy}


def _ids(rows, key):
    result = {}
    for row in rows:
        value = row[key]
        if not isinstance(value, str) or not value or value in result:
            raise RegistryError(f'Use a distinct nonempty {key} for every record')
        result[value] = row
    return result


def _evidence(root, sources):
    """Require a verified reference and an excerpt in its source text."""
    for item in sources:
        source = verify_ref(root, item['ref'])
        excerpt = item['excerpt']
        if not isinstance(excerpt, str) or not excerpt.strip() or excerpt not in source.read_text(encoding='utf-8'):
            raise RegistryError(f'Evidence excerpt missing in {item["ref"]["path"]}')


def _rehearsal(root, record):
    issues = []
    backend = record.get('backend')
    rounds = record.get('external_rounds', [])
    if backend not in (None, 'codex', 'manual', 'oracle-pro'):
        issues.append('Unknown optional reviewer backend')
    if not isinstance(rounds, list):
        rounds = []
    if len(rounds) > 5:
        issues.append('At most five external review rounds are permitted')
    executor_model = record.get('executor_model')
    executor = derive_model_family(executor_model) if isinstance(executor_model, str) else 'unknown'
    verified = []
    if backend and executor != 'unknown' and not issues:
        for row in rounds:
            try:
                model = row['reviewer_model']
                family = derive_model_family(model) if isinstance(model, str) else 'unknown'
                if row.get('identity_verified') is not True or family in ('unknown', executor):
                    continue
                ref = row['response_ref']
                with verify_ref(root, ref).open(encoding='utf-8') as response:
                    if response.readline().strip() == f'Reviewer-Model: {model}':
                        verified.append(ref)
            except (OSError, ValueError, TypeError, KeyError):
                # A missing or unverifiable optional response leaves the
                # in-context rehearsal as the available evidence.
                continue
    scope = 'cross_family_external' if verified else 'in_context'
    note = ('Cross-family review recorded for the referenced scope.' if scope == 'cross_family_external' else
            'In-context persona rehearsal. Cross-family external validation was not performed.')
    return {'scope': scope, 'note': note, 'verified_response_refs': verified,
            'external_status': 'REVIEW_UNAVAILABLE' if backend and not verified else scope}, issues


def _draft_checks(root, rules, ledger, concerns, revisions):
    issues, counts, covered, promised = [], [], set(), set()
    seen = set()
    response = rules['response']
    mode, limits = response['mode'], response.get('limits', {})
    permissions = rules['content_permissions']
    for output in ledger['drafts']:
        name, reviewer = output['path'], output.get('reviewer')
        path = local_path(root, name)
        if name in seen:
            issues.append(f'Duplicate output {name}')
        seen.add(name)
        text = path.read_bytes().decode('utf-8')
        if not text.strip() or PRIVATE.search(text):
            issues.append(f'Empty, unfinished or private content in {name}')
        if permissions.get('external_links_allowed') == 'no' and re.search(r'https?://', text, re.I):
            issues.append(f'Links exceed venue permissions in {name}')
        if mode == 'openreview_per_reviewer' and not reviewer:
            issues.append(f'Missing reviewer thread for {name}')
        if reviewer and response.get('per_reviewer_replies_allowed') == 'no':
            issues.append(f'Per-reviewer replies exceed venue permissions in {name}')
        if not reviewer and mode in ('global_comment', 'hybrid', 'openreview_markdown_latex'):
            if response.get('global_response_allowed') == 'no':
                issues.append(f'Global reply exceeds venue permissions in {name}')
        if ''.join(unit['text'] for unit in output['units']) != text:
            issues.append(f'Ledger text differs from exact output {name}')
        for field, actual in (('character_limit', len(text)), ('word_limit', len(text.split()))):
            maximum = limits.get(field)
            if maximum is not None and actual > maximum:
                issues.append(f'{name} exceeds {field} ({actual}/{maximum})')
        counts.append({'ref': fixed_ref(root, name), 'characters': len(text), 'words': len(text.split())})
        for unit in output['units']:
            if unit['kind'] not in ('fact', 'framing', 'commitment'):
                issues.append(f'Unknown response unit type in {name}')
            if unit['kind'] == 'fact' and not unit.get('sources'):
                issues.append(f'Missing evidence for factual text in {name}: {unit["text"].strip()}')
            _evidence(root, unit.get('sources', []))
            linked = set(unit.get('concerns', []))
            for concern_id in linked:
                if concern_id not in concerns:
                    issues.append(f'Unknown concern {concern_id}')
                elif reviewer and concerns[concern_id]['reviewer'] != reviewer:
                    issues.append(f'{concern_id} is outside reviewer thread {reviewer}')
                elif unit['text'].strip():
                    covered.add(concern_id)
            if unit['kind'] == 'commitment':
                commitment = unit['commitment']
                promised.add(commitment)
                if permissions.get('revision_commitments_allowed') == 'no':
                    issues.append(f'Revision commitment exceeds venue permissions: {commitment}')
                if commitment not in revisions or revisions[commitment]['concern_id'] not in linked:
                    issues.append(f'Missing corresponding revision for {commitment}')
                elif revisions[commitment]['status'] == 'future_work_only':
                    issues.append(f'Future work cannot be stated as a commitment: {commitment}')
    if not seen:
        issues.append('No submission draft to check')
    if mode == 'pdf_one_page':
        pdf = ledger.get('pdf')
        if not pdf:
            issues.append('Compile the submission PDF and record its page count')
        else:
            pdf_path = verify_ref(root, pdf['ref'])
            if not pdf_path.read_bytes().startswith(b'%PDF-') or type(pdf['pages']) is not int or pdf['pages'] != 1:
                issues.append('Require a compiled one-page PDF')
            cap = limits.get('page_limit')
            if cap is not None and pdf['pages'] > cap:
                issues.append('Submission PDF exceeds the venue page limit')
    return issues, counts, covered, promised


def check(root, *, finalize=False):
    """Check one project. Return status, issues and evidence without writing files."""
    root = Path(root).resolve()
    workspace = local_path(resolve_state_root(root, 'read'), 'rebuttal')
    rules, result = _intake(root, workspace)
    if not finalize or result['status'] == 'BLOCKED':
        return result
    ledger = read_record(workspace / 'memory/submission-check.json')
    concerns = _ids(ledger['concerns'], 'id')
    revisions = _ids(ledger['revisions'], 'id')
    issues, counts, covered, promised = _draft_checks(root, rules, ledger, concerns, revisions)
    for concern_id, row in concerns.items():
        if row['status'] == 'answered' and concern_id in covered:
            continue
        if row['status'] == 'deferred_intentionally' and row.get('reason'):
            continue
        issues.append(f'Concern requires a response or an explicit deferral: {concern_id}')
    for revision_id, row in revisions.items():
        if row['concern_id'] not in concerns or row['status'] not in COMMITMENTS:
            issues.append(f'Invalid revision item {revision_id}')
        if row['status'] in ('approved_for_rebuttal', 'already_done'):
            if revision_id not in promised:
                issues.append(f'Orphan revision item {revision_id}')
            if not row.get('evidence'):
                issues.append(f'Missing approval or completion evidence for {revision_id}')
            _evidence(root, row.get('evidence', []))
    plan = (workspace / 'drafts/REVISION_PLAN.md').read_text(encoding='utf-8')
    checklist = [match[1] for line in plan.splitlines() if (match := CHECKBOX.match(line))]
    if len(checklist) != len(set(checklist)) or set(checklist) != set(revisions):
        issues.append('REVISION_PLAN.md checklist differs from the recorded revision items')
    rehearsal, review_issues = _rehearsal(root, ledger.get('rehearsal', {}))
    issues.extend(review_issues)
    result.update(status='BLOCKED' if issues else 'MECHANICAL_CHECKS_PASSED', issues=issues,
                  outputs=counts, rehearsal=rehearsal)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.', help='Project containing the rebuttal workspace')
    parser.add_argument('--check', choices=('intake', 'finalize'), required=True)
    parser.add_argument('--record', action='store_true', help='Write the check report to the project log')
    args = parser.parse_args()
    try:
        result = check(args.root, finalize=args.check == 'finalize')
        if args.record:
            with state_writer(args.root) as state:
                atomic_write(local_path(state, 'rebuttal/logs/evoinquiry_check.json'), result)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        result = {'status': 'BLOCKED', 'issues': [str(error)]}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 3 if result['status'] == 'BLOCKED' else 0


if __name__ == '__main__':
    sys.exit(main())
