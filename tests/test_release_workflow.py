"""Exercise publication arguments without a network call or GitHub token."""
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml


REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('version', ['1.0.0', '1.0.0-beta.5'])
def test_publish_selects_release_kind_and_only_current_assets(tmp_path, version):
    bash = shutil.which('bash')
    if bash is None:
        pytest.skip('Release publication uses bash on GitHub Ubuntu runners')
    workflow = yaml.load(
        (REPO / '.github/workflows/release-beta.yml').read_text(),
        Loader=yaml.BaseLoader,
    )
    script = next(step['run'] for step in workflow['jobs']['publish']['steps']
                  if 'gh release create' in step.get('run', ''))
    dist = tmp_path / 'dist'
    dist.mkdir()
    current_assets = [
        f'dist/evo-inquiry-{version}.tar.gz',
        f'dist/evo-inquiry-{version}.zip',
        'dist/SHA256SUMS',
        'dist/release-manifest.json',
    ]
    for name in current_assets + ['dist/evo-inquiry-0.9.0.tar.gz', 'dist/old.zip']:
        (tmp_path / name).write_text('fixture')
    body = '# Release\n\nA complete paragraph without forced line breaks.\n'
    (tmp_path / 'RELEASE_NOTES.md').write_text(body)
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    gh = bin_dir / 'gh'
    gh.write_text(
        '#!/usr/bin/env python3\n'
        'import json, os, sys\n'
        'from pathlib import Path\n'
        'args = sys.argv[1:]\n'
        'for arg in args:\n'
        '    if arg.startswith("dist/") and not Path(arg).is_file():\n'
        '        raise SystemExit("Missing selected asset")\n'
        'body = Path(args[args.index("--notes-file") + 1]).read_text()\n'
        'Path(os.environ["RELEASE_ARGV_CAPTURE"]).write_text(json.dumps({"args": args, "body": body}))\n'
    )
    gh.chmod(0o755)
    capture = tmp_path / 'publication.json'
    environment = os.environ.copy()
    environment.update(
        PATH=str(bin_dir) + os.pathsep + environment.get('PATH', ''),
        RELEASE_TAG='v' + version,
        GITHUB_REPOSITORY='Soceremite/EvoInquiry',
        RELEASE_ARGV_CAPTURE=str(capture),
    )
    subprocess.run([bash, '-e', '-o', 'pipefail', '-c', script],
                   cwd=tmp_path, env=environment, capture_output=True, text=True,
                   check=True, timeout=15)
    published = json.loads(capture.read_text())
    args = published['args']
    assert args[:3] == ['release', 'create', 'v' + version]
    assert [arg for arg in args if arg.startswith('dist/')] == current_assets
    assert args[args.index('--title') + 1] == 'EvoInquiry ' + version
    assert '--verify-tag' in args
    assert published['body'] == body
    if '-' in version:
        assert '--prerelease' in args
        assert '--latest=false' in args
        assert '--latest' not in args
    else:
        assert '--latest' in args
        assert '--prerelease' not in args
        assert '--latest=false' not in args
