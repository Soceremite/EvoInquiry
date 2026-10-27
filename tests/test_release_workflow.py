"""Exercise publication arguments without a network call or GitHub token."""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess

import pytest
import yaml


REPO = Path(__file__).resolve().parents[1]


def test_release_covers_portable_windows_validation_before_publication():
    workflows = {
        name: yaml.load((REPO / '.github/workflows' / name).read_text(),
                        Loader=yaml.BaseLoader)
        for name in ('test-suite.yml', 'release-beta.yml')
    }

    def windows_modules(workflow):
        return {
            token
            for step in workflow['jobs']['windows']['steps']
            for token in shlex.split(step.get('run', ''))
            if token.startswith('tests/') and token.endswith('.py')
        }

    development = windows_modules(workflows['test-suite.yml'])
    release = workflows['release-beta.yml']
    assert development, 'The normal Windows validation suite must be nonempty'
    bounded_research = {
        'tests/test_run_state.py',
        'tests/test_research_control.py',
        'tests/test_experiment_block_reflection.py',
        'tests/test_research_handoff.py',
        'tests/test_research_events.py',
        'tests/test_research_memory.py',
        'tests/test_candidate_comparison.py',
        'tests/test_research_pilots.py',
    }
    assert bounded_research <= development, (
        'Native Windows validation omits bounded research modules: '
        + ', '.join(sorted(bounded_research - development))
    )
    assert development <= windows_modules(release), (
        'Publication omits Windows validation modules: '
        + ', '.join(sorted(development - windows_modules(release)))
    )
    assert {'powershell.exe', 'pwsh'} <= set(
        release['jobs']['windows']['strategy']['matrix']['powershell']
    )
    assert {'test', 'windows'} <= set(release['jobs']['publish']['needs'])


@pytest.mark.parametrize('version', ['1.0.0', '1.0.0-beta.5'])
@pytest.mark.parametrize('existing,upload_fails', [(False, False), (True, False), (True, True)])
def test_publish_selects_release_kind_and_only_current_assets(tmp_path, version, existing, upload_fails):
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
        'body = Path(args[args.index("--notes-file") + 1]).read_text() if "--notes-file" in args else None\n'
        'with Path(os.environ["RELEASE_ARGV_CAPTURE"]).open("a") as capture:\n'
        '    capture.write(json.dumps({"args": args, "body": body}) + "\\n")\n'
        'if args[:2] == ["release", "view"]:\n'
        '    raise SystemExit(0 if os.environ["RELEASE_EXISTS"] == "1" else 1)\n'
        'if args[:2] == ["release", "upload"] and os.environ["RELEASE_UPLOAD_FAIL"] == "1":\n'
        '    raise SystemExit(7)\n'
        'for arg in args:\n'
        '    if arg.startswith("dist/") and not Path(arg).is_file():\n'
        '        raise SystemExit("Missing selected asset")\n'
    )
    gh.chmod(0o755)
    capture = tmp_path / 'publication.json'
    environment = os.environ.copy()
    environment.update(
        PATH=str(bin_dir) + os.pathsep + environment.get('PATH', ''),
        RELEASE_TAG='v' + version,
        GITHUB_REPOSITORY='Soceremite/EvoInquiry',
        GITHUB_SHA='a' * 40,
        RELEASE_ARGV_CAPTURE=str(capture),
        RELEASE_EXISTS='1' if existing else '0',
        RELEASE_UPLOAD_FAIL='1' if upload_fails else '0',
    )
    result = subprocess.run([bash, '-e', '-o', 'pipefail', '-c', script],
                            cwd=tmp_path, env=environment, capture_output=True, text=True,
                            timeout=15)
    calls = [json.loads(line) for line in capture.read_text().splitlines()]
    assert calls[0]['args'][:3] == ['release', 'view', 'v' + version]
    if upload_fails:
        assert result.returncode == 7
        assert [call['args'][1] for call in calls] == ['view', 'upload']
        return
    assert result.returncode == 0, result.stderr
    assert [call['args'][1] for call in calls] == (['view', 'upload', 'edit'] if existing else ['view', 'create'])
    published = calls[-1]
    args = published['args']
    assert args[:3] == ['release', 'edit' if existing else 'create', 'v' + version]
    asset_call = calls[1]['args']
    assert [arg for arg in asset_call if arg.startswith('dist/')] == current_assets
    if existing:
        assert '--clobber' in asset_call
        assert args[args.index('--target') + 1] == environment['GITHUB_SHA']
    else:
        assert '--verify-tag' in args
    assert args[args.index('--title') + 1] == 'EvoInquiry ' + version
    assert published['body'] == body
    if '-' in version:
        assert ('--prerelease=true' if existing else '--prerelease') in args
        assert '--latest=false' in args
        assert '--latest' not in args
    else:
        assert '--latest' in args
        assert '--prerelease' not in args
        assert '--latest=false' not in args
        if existing:
            assert '--prerelease=false' in args
