#!/usr/bin/env python3
"""Unwrap prose in release notes while retaining Markdown block structure."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

BLOCK = re.compile(r'^(?:\s|#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\||<|\[[^]]+\]:|[-*_]{3,}\s*$)')
FENCE = re.compile(r'^\s*(`{3,}|~{3,})')


def unwrap_prose(text: str) -> str:
    output: list[str] = []
    paragraph: list[str] = []
    fence: str | None = None

    def flush() -> None:
        if paragraph:
            output.append(' '.join(paragraph))
            paragraph.clear()

    for line in text.splitlines():
        marker = FENCE.match(line)
        if fence is not None:
            output.append(line)
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
        elif marker:
            flush()
            output.append(line)
            fence = marker[1]
        elif not line.strip():
            flush()
            output.append(line)
        elif BLOCK.match(line) or line.endswith(('  ', '\\')):
            flush()
            output.append(line)
        else:
            paragraph.append(line.strip())
    flush()
    return '\n'.join(output).rstrip() + '\n'


def release_state(release: dict) -> dict:
    return {key: release[key] for key in ('id', 'tag_name', 'target_commitish', 'draft', 'prerelease')} | {
        'assets': [(a['id'], a['name'], a['size'], a.get('digest')) for a in release['assets']]
    }


def synchronize(repository: str) -> None:
    if not re.fullmatch(r'[\w.-]+/[\w.-]+', repository):
        raise SystemExit('Expected owner/repository')
    token = os.environ.get('GH_TOKEN')
    if not token:
        raise SystemExit('GH_TOKEN is required to update release descriptions')
    base = f'https://api.github.com/repos/{repository}'

    def api(path: str, body: dict | None = None):
        headers = {'Accept': 'application/vnd.github+json',
                   'Authorization': f'Bearer {token}',
                   'User-Agent': 'EvoInquiry-release-notes',
                   'X-GitHub-Api-Version': '2022-11-28'}
        data = None if body is None else json.dumps(body).encode()
        if data is not None:
            headers['Content-Type'] = 'application/json'
        request = Request(base + path, data=data, headers=headers,
                          method='GET' if body is None else 'PATCH')
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    report = []
    page = 1
    while True:
        releases = api(f'/releases?per_page=100&page={page}')
        for release in releases:
            if release['draft'] or not re.fullmatch(r'v\d+\.\d+\.\d+-beta\.\d+', release['tag_name']):
                continue
            original = release.get('body') or ''
            normalized = unwrap_prose(original)
            if original == normalized:
                report.append({'tag': release['tag_name'], 'status': 'already formatted'})
                continue
            if original.split() != normalized.split():
                raise RuntimeError('Formatting would change release-note content')
            before = release_state(release)
            api(f"/releases/{release['id']}", {'body': normalized})
            verified = api(f"/releases/{release['id']}")
            if verified['body'] != normalized or release_state(verified) != before:
                raise RuntimeError(f"Release verification failed: {release['tag_name']}")
            report.append({'tag': release['tag_name'], 'status': 'paragraph wrapping corrected',
                           'content_preserved': True, 'release_and_assets_preserved': True})
        if len(releases) < 100:
            break
        page += 1
    print(json.dumps(report, indent=2))
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with Path(summary).open('a') as out:
            out.write('## Release note formatting\n\n')
            for item in report:
                out.write(f"- {item['tag']}: {item['status']}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check-file', type=Path)
    group.add_argument('--repository')
    args = parser.parse_args()
    if args.check_file is not None:
        original = args.check_file.read_text(encoding='utf-8')
        if original != unwrap_prose(original):
            raise SystemExit('Release-note prose contains fixed-width line breaks')
        print('Release-note paragraphs use natural wrapping.')
    else:
        synchronize(args.repository)


if __name__ == '__main__':
    main()
