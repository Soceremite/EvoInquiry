#!/usr/bin/env python3
"""Normalize offline literature records without asserting completeness or truth."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit

try:
    from .registry_common import configure_utf8_output
except ImportError:
    from registry_common import configure_utf8_output

STATUSES = {'ok', 'empty', 'unavailable', 'rate_limited', 'timeout', 'error'}
LEVELS = {'metadata', 'abstract', 'full_text', 'sections'}


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be a nonempty string')
    return value.strip()


def normalize_doi(value):
    value = _text(value, 'doi').strip()
    if value.lower().startswith(('https://doi.org/', 'http://doi.org/', 'https://dx.doi.org/', 'http://dx.doi.org/')):
        value = unquote(urlsplit(value).path.lstrip('/'))
    value = re.sub(r'^doi:\s*', '', value, flags=re.I).lower()
    if not re.fullmatch(r'10\.\d{4,9}/\S+', value):
        raise ValueError(f'Invalid DOI: {value!r}')
    return value


def normalize_arxiv(value):
    value = _text(value, 'arxiv_id')
    if value.startswith(('https://arxiv.org/', 'http://arxiv.org/')):
        value = re.sub(r'^/(?:abs|pdf)/', '', urlsplit(value).path).removesuffix('.pdf')
    value = re.sub(r'^arxiv:\s*', '', value, flags=re.I)
    match = re.fullmatch(r'((?:\d{4}\.\d{4,5}|[a-zA-Z-]+(?:\.[A-Z]{2})?/\d{7}))(v[1-9]\d*)?', value)
    if not match:
        raise ValueError(f'Invalid arXiv ID: {value!r}')
    return match[1], match[2] or ''


def normalize_register(register):
    if not isinstance(register, dict) or register.get('schema_version') != 1:
        raise ValueError('Expected literature register schema_version 1')
    searches, papers = register.get('searches'), register.get('papers')
    if not isinstance(searches, list) or not isinstance(papers, list):
        raise ValueError('searches and papers must be lists')
    result = {'schema_version': 1, 'searches': copy.deepcopy(searches), 'papers': [], 'possible_title_matches': []}
    search_ids = set()
    for search in result['searches']:
        if not isinstance(search, dict): raise ValueError('Search must be an object')
        for name in ('id', 'source', 'query', 'searched_at'):
            search[name] = _text(search.get(name), 'search.' + name)
        if search['id'] in search_ids: raise ValueError('Duplicate search ID')
        search_ids.add(search['id'])
        if search.get('status') not in STATUSES: raise ValueError('Unknown search status')
    # A normalized paper is a derived view over its original observations.
    # Expand those observations when reading our own output, so re-exporting
    # never discards other providers, versions, titles or reading receipts.
    observations = []
    for paper in papers:
        if not isinstance(paper, dict):
            raise ValueError('Paper must be an object')
        if 'observations' in paper:
            if not isinstance(paper['observations'], list) or not paper['observations']:
                raise ValueError('observations must be a nonempty list')
            if any(not isinstance(item, dict) or 'observations' in item for item in paper['observations']):
                raise ValueError('Observations must be original paper records')
            observations.extend(paper['observations'])
        else:
            observations.append(paper)
    seen_ids, identities, title_map = set(), {}, {}
    for raw in observations:
        if not isinstance(raw, dict): raise ValueError('Paper must be an object')
        paper = copy.deepcopy(raw)
        for name in ('id', 'title', 'source', 'search_id', 'url'):
            paper[name] = _text(paper.get(name), 'paper.' + name)
        if paper['id'] in seen_ids: raise ValueError('Duplicate paper ID')
        seen_ids.add(paper['id'])
        if paper['search_id'] not in search_ids: raise ValueError('Unknown search_id')
        if paper.get('reading_level') not in LEVELS: raise ValueError('Unknown reading level')
        locators = paper.get('locators', [])
        if not isinstance(locators, list) or any(not isinstance(v, str) or not v.strip() for v in locators):
            raise ValueError('locators must be nonempty strings')
        if paper['reading_level'] == 'sections' and not locators: raise ValueError('Section reading needs a locator')
        keys=[]
        if paper.get('doi'):
            paper['doi']=normalize_doi(paper['doi']); keys.append('doi:' + paper['doi'])
        if paper.get('arxiv_id'):
            base, version=normalize_arxiv(paper['arxiv_id'])
            paper['arxiv_id']=base+version
            keys.append('arxiv:' + base)
        candidates={identities[k] for k in keys if k in identities}
        if len(candidates)>1:
            raise ValueError('Conflicting DOI/arXiv identity bridge; review the source records')
        index=next(iter(candidates), None)
        provenance = copy.deepcopy(paper)
        if index is not None:
            existing=result['papers'][index]
            # A shared arXiv ID cannot silently collapse inconsistent formal identities.
            if existing.get('doi') and paper.get('doi') and existing['doi'] != paper['doi']:
                raise ValueError('Conflicting DOIs for the same arXiv identity')
            existing['observations'].append(provenance)
            for k in ('doi', 'arxiv_id'):
                if not existing.get(k) and paper.get(k): existing[k]=paper[k]
        else:
            index=len(result['papers'])
            paper['observations']=[provenance]
            result['papers'].append(paper)
        for key in keys: identities[key]=index
        title=unicodedata.normalize('NFKC', paper['title']).casefold()
        title=re.sub(r'\W+', '', title)
        for other in title_map.get(title, []):
            if other != index:
                pair=sorted([result['papers'][other]['id'], result['papers'][index]['id']])
                if pair not in result['possible_title_matches']: result['possible_title_matches'].append(pair)
        title_map.setdefault(title, []).append(index)
    result['possible_title_matches'].sort()
    return result


def main():
    configure_utf8_output()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    try:
        result=normalize_register(json.loads(args.input.read_text(encoding='utf-8')))
        rendered=json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
        if args.output:
            with args.output.open('x',encoding='utf-8') as handle: handle.write(rendered)
        else: print(rendered,end='')
    except (OSError, ValueError, TypeError) as error:
        parser.exit(2, f'Literature record error: {error}\n')
    return 0


if __name__ == '__main__': sys.exit(main())
