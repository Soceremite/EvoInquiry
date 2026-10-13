#!/usr/bin/env python3
"""Inspect a deployment directory, or probe owned temporary files before use.

A successful probe establishes observed local locking/replace/fsync behavior.
It cannot establish storage persistence, power-loss durability, or multi-host
lock exclusion. Default inspection makes no files and does not initialize .ei.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

try:
    from .registry_common import RegistryError, configure_utf8_output, atomic_write, file_lock, file_digest, _regular_ancestors
except ImportError:
    from registry_common import RegistryError, configure_utf8_output, atomic_write, file_lock, file_digest, _regular_ancestors


def inspect_directory(directory):
    requested = _regular_ancestors(directory)
    if not requested.is_dir():
        raise RegistryError('Choose an existing deployment directory')
    result = {'directory': str(requested), 'platform': sys.platform,
              'device': requested.stat().st_dev,
              'free_bytes': shutil.disk_usage(requested).free,
              'probe_performed': False, 'status': 'NOT_TESTED',
              'persistence': 'operator-confirmation-required',
              'scope': 'Single host only; no power-loss or multi-host certification'}
    if shutil.which('findmnt'):
        mount = subprocess.run(['findmnt', '-T', str(requested), '-J',
                                '-o', 'TARGET,SOURCE,FSTYPE'], capture_output=True,
                               text=True, timeout=5)
        if mount.returncode == 0:
            result['mount'] = json.loads(mount.stdout)['filesystems'][0]
    return result


_CONTENDER = r'''
import errno, json, os, sys
with open(sys.argv[1], 'r+b') as handle:
    try:
        if os.name == 'posix':
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        elif os.name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            raise RuntimeError('Unsupported lock backend')
    except OSError as error:
        if error.errno not in (errno.EAGAIN, errno.EACCES):
            raise
        print(json.dumps({'excluded': True, 'errno': error.errno}))
    else:
        print(json.dumps({'excluded': False}))
'''


def probe_directory(directory):
    result = inspect_directory(directory)
    result['probe_performed'] = True
    result['checks'] = {}
    scratch = None
    try:
        with tempfile.TemporaryDirectory(prefix='.ei-filesystem-probe-', dir=directory) as name:
            scratch = Path(name)
            lock = scratch / 'writer.lock'
            with file_lock(lock):
                contender = subprocess.run([sys.executable, '-I', '-B', '-c', _CONTENDER,
                                            str(lock)], capture_output=True, text=True, timeout=10)
                if contender.returncode or not json.loads(contender.stdout)['excluded']:
                    raise RegistryError('Another process acquired the held writer lock')
                result['checks']['cross_process_lock_exclusion'] = 'PASS'
            with file_lock(lock, blocking=False):
                result['checks']['lock_release_and_reacquire'] = 'PASS'
            body = scratch / 'atomic.json'
            atomic_write(body, {'generation': 1})
            first = file_digest(body)
            atomic_write(body, {'generation': 2})
            if json.loads(body.read_text()) != {'generation': 2} or file_digest(body) == first:
                raise RegistryError('Atomic replacement readback failed')
            result['checks']['file_fsync_replace_readback'] = 'PASS'
            result['checks']['directory_fsync'] = 'PASS' if os.name == 'posix' else 'NOT_TESTED'
        result['status'] = 'PASS'
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result.update(status='FAIL', error=str(error))
    result['temporary_probe_removed'] = scratch is None or not scratch.exists()
    return result


def main():
    configure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True)
    parser.add_argument('--probe', action='store_true',
                        help='Create and remove owned temporary files; never writes project state')
    args = parser.parse_args()
    try:
        result = probe_directory(args.directory) if args.probe else inspect_directory(args.directory)
    except (RegistryError, OSError) as error:
        result = {'status': 'FAIL', 'error': str(error), 'probe_performed': False}
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if result['status'] == 'FAIL' else 0)


if __name__ == '__main__':
    main()
