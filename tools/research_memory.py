"""Read relevant decisions from explicitly selected project records, without a DB.

Lexical matches are retrieval candidates, not recommendations or verified facts.
The caller must inspect original context, uncertainty and evidence before reuse.
No global history, new state directory or automatic wiki initialization is used.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

try:
    from .registry_common import RegistryError, configure_utf8_output, digest, local_path, verify_ref
except ImportError:
    from registry_common import RegistryError, configure_utf8_output, digest, local_path, verify_ref


def _tokens(text):
    words = set(re.findall(r'[a-z0-9]+', text.lower()))
    for part in re.findall(r'[\u3400-\u9fff]+', text):
        words.update(part[i:i + 2] for i in range(max(1, len(part) - 1)))
    return words


def _evidence(root, references):
    if not references:
        return 'unbound', []
    issues = []
    for reference in references:
        try:
            verify_ref(root, reference)
        except (RegistryError, OSError, ValueError) as error:
            issues.append({'reference': reference, 'reason': str(error)})
    return ('changed-or-unavailable' if issues else 'current'), issues


def retrieve(root, query, sources, *, limit=5, excerpt_chars=1800):
    """Return bounded matches and fixed source refs from explicit Markdown/JSONL.

    JSONL uses existing research-wiki decision fields. Markdown remains unbound
    unless a human checks its cited evidence; merely seeing a link is not proof.
    Superseded decisions remain visible with their successor IDs. No file changes
    are made, even when a source is missing, malformed or has an incomplete tail.
    """
    if not isinstance(query, str) or not _tokens(query):
        raise RegistryError('A nonempty research query is required')
    if (isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20
            or isinstance(excerpt_chars, bool) or not isinstance(excerpt_chars, int)
            or not 80 <= excerpt_chars <= 8000):
        raise RegistryError('Use 1–20 matches and excerpts of 80–8000 characters')
    if not isinstance(sources, list) or not sources or any(not isinstance(p, str) for p in sources):
        raise RegistryError('Select existing project record paths explicitly')
    terms = _tokens(query)
    matches, issues = [], []
    for source in dict.fromkeys(sources):
        path = local_path(root, source)
        if path.suffix.lower() not in ('.md', '.jsonl'):
            raise RegistryError('Decision sources must be Markdown or JSONL')
        try:
            if path.stat().st_size > 2 * 1024 * 1024:
                issues.append({'source': source, 'reason': 'Select a smaller record (maximum 2 MiB)'})
                continue
            raw = path.read_bytes()
            text = raw.decode('utf-8')
        except (OSError, UnicodeError) as error:
            issues.append({'source': source, 'reason': str(error)})
            continue
        source_ref = {'path': source, 'sha256': digest(raw)}
        if path.suffix.lower() == '.md':
            chunks = re.split(r'(?=^#{1,6}\s)', text, flags=re.M)
            records = [{'id': f'section-{index + 1}', 'text': chunk}
                       for index, chunk in enumerate(chunks) if chunk.strip()]
            successors = {}
        else:
            lines = text.splitlines()
            if text and not text.endswith('\n'):
                lines = lines[:-1]
                issues.append({'source': source, 'reason': 'Incomplete final JSONL record was not read'})
            try:
                records = [json.loads(line) for line in lines if line.strip()]
                if any(not isinstance(row, dict) or not isinstance(row.get('id'), str) for row in records):
                    raise ValueError('Expected decision objects with IDs')
                if len({row['id'] for row in records}) != len(records):
                    raise ValueError('Duplicate decision IDs')
            except (ValueError, TypeError) as error:
                issues.append({'source': source, 'reason': f'Invalid decision ledger: {error}'})
                continue
            successors = {}
            for row in records:
                if row.get('supersedes'):
                    successors.setdefault(row['supersedes'], []).append(row['id'])
        for record in records:
            content = record.get('text') or '\n'.join(str(record.get(key, '')) for key in (
                'question', 'alternatives', 'choice', 'reason', 'uncertainties', 'revisit_when'))
            overlap = terms & _tokens(content)
            if not overlap:
                continue
            status, evidence_issues = _evidence(root, record.get('evidence_refs', []))
            matches.append({'id': record['id'], 'source_ref': source_ref,
                'matched_terms': sorted(overlap), 'score': len(overlap) / len(terms),
                'excerpt': content[:excerpt_chars], 'excerpt_truncated': len(content) > excerpt_chars,
                'provenance': record.get('provenance', 'unclassified-record'),
                'evidence_status': status, 'evidence_refs': record.get('evidence_refs', []),
                'evidence_issues': evidence_issues, 'uncertainties': record.get('uncertainties', []),
                'revisit_when': record.get('revisit_when'), 'superseded_by': successors.get(record['id'], [])})
    matches.sort(key=lambda row: (-row['score'], row['source_ref']['path'], row['id']))
    return {'query': query, 'matches': matches[:limit], 'total_matches': len(matches),
            'source_issues': issues, 'interpretation': 'retrieval-candidates-only',
            'scientific_verdict': 'not-assessed'}


def main():
    configure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--query', required=True)
    parser.add_argument('--source', action='append', required=True)
    parser.add_argument('--limit', type=int, default=5)
    args = parser.parse_args()
    try:
        print(json.dumps(retrieve(args.root, args.query, args.source, limit=args.limit), ensure_ascii=False, indent=2))
        return 0
    except (RegistryError, OSError, ValueError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
