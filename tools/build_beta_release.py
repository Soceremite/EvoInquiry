#!/usr/bin/env python3
"""Build source release assets from a clean, committed EvoInquiry Git checkout."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

from publication_policy import publication_errors

ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> bytes:
    return subprocess.run(['git', '-C', str(ROOT), *args], check=True, capture_output=True).stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    version = (ROOT / 'VERSION').read_text().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', version):
        raise SystemExit('VERSION must be a package version, not a path')
    manifest = json.loads((ROOT / '.codex-plugin/plugin.json').read_text())
    if manifest.get('name') != 'evo-inquiry' or manifest.get('version') != version:
        raise SystemExit('Release identity/version differs from the Codex manifest')
    if git('status', '--porcelain', '--untracked-files=normal').strip():
        raise SystemExit('Commit all intended release files before building; checkout is not clean')
    tracked = [Path(p) for p in git('ls-files', '-z').decode().split('\0') if p]
    policy_errors = publication_errors(ROOT, (str(p) for p in tracked))
    if policy_errors:
        raise SystemExit('\n'.join(policy_errors))
    forbidden = [str(p) for p in tracked if
                 p.parts[0] in {'validation', 'dist', '.aris', '.claude', '.git'} or
                 p.name in {'auth.json', 'config.before.toml', '.env', 'id_rsa', 'id_ed25519'} or
                 (p.name.startswith('.env.') and p.name != '.env.example')]
    if forbidden:
        raise SystemExit('Local evidence or credentials are tracked: ' + ', '.join(forbidden))
    for required in ['VERSION', 'LICENSE', 'NOTICE', 'README.md', 'README_CN.md',
                     '.codex-plugin/plugin.json', '.agents/plugins/marketplace.json',
                     'skills/skills-codex/shared-references/evo-inquiry.md']:
        if Path(required) not in tracked:
            raise SystemExit('Required release file is not tracked: ' + required)
    prefix = f'evo-inquiry-{version}/'
    tar_bytes = git('archive', '--format=tar', f'--prefix={prefix}', 'HEAD')
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode='r:') as archive:
        entries = [m.name for m in archive if m.isfile() and
                   m.name.startswith(prefix + 'skills/skills-codex/') and
                   m.name.endswith('/SKILL.md') and len(Path(m.name).parts) == 5]
    expected = {p.parent.name for p in (ROOT / 'skills/skills-codex').glob('*/SKILL.md')}
    archived = {Path(p).parent.name for p in entries}
    if not expected or archived != expected:
        raise SystemExit('Release skill inventory differs from the committed package')
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    stem = f'evo-inquiry-{version}'
    tar_path = output / (stem + '.tar.gz')
    zip_path = output / (stem + '.zip')
    tar_path.write_bytes(gzip.compress(tar_bytes, mtime=0))
    zip_path.write_bytes(git('archive', '--format=zip', f'--prefix={prefix}', 'HEAD'))
    sums = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [tar_path, zip_path]}
    (output / 'SHA256SUMS').write_text(''.join(f'{digest}  {name}\n' for name, digest in sums.items()))
    report = {'version': version, 'commit': git('rev-parse', 'HEAD').decode().strip(),
              'skill_entrypoints': len(entries), 'sha256': sums,
              'source': 'Committed Git files only; local validation/session records excluded'}
    (output / 'release-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
