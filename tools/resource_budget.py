"""One user-selected resource table per research session; fresh admission checks.

This stdlib helper reads host telemetry and declared peak requirements. It does
not schedule jobs, meter spending, reserve GPUs or replace execution ownership.
JSON is the single stored table; Markdown is a view, never a second policy file.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

try:
    from .registry_common import (RegistryError, atomic_write, configure_utf8_output,
                                  file_lock, identifier, local_path, now, read_record)
    from .state_paths import resolve_state_root, state_writer
except ImportError:
    from registry_common import (RegistryError, atomic_write, configure_utf8_output,
                                 file_lock, identifier, local_path, now, read_record)
    from state_paths import resolve_state_root, state_writer


DEFAULT_POLICY = {
    'allowed_gpu_ids': 'all_visible', 'allow_gpu_sharing': True,
    'max_cpu_cores': None, 'max_ram_bytes': None, 'max_total_vram_bytes': None,
    'max_dataset_bytes': None, 'max_weight_bytes': None, 'max_disk_bytes': None,
    'auto_approve_job_seconds': 12 * 3600, 'max_new_spend': 0,
}
CHOICES = [
    {'preset': 'maximum', 'description': 'Maximum available local resources; GPU sharing allowed'},
    {'preset': 'exclusive', 'description': 'Maximum available local resources; idle GPUs only'},
    {'preset': 'custom', 'description': 'Choose GPU IDs, sharing, duration, memory, disk or spending limits'},
]
STORAGE_FIELDS = ('dataset_bytes', 'weight_bytes', 'checkpoint_peak_bytes', 'other_bytes', 'reserve_bytes')


class ResourceAdmissionError(RegistryError):
    """A deferred allocation, carrying its check without implying training failure."""

    def __init__(self, result):
        self.result = result
        super().__init__(f"Session resources {result['status']}; inspect {result['table_path']}")


def session_id(value=None):
    """Prefer the stable host thread ID; never invent a new ID on continuation."""
    value = value or os.environ.get('CODEX_THREAD_ID') or os.environ.get('CODEX_SESSION_ID')
    if not value:
        raise RegistryError('Supply --session or the host session ID; do not create per-skill IDs')
    return identifier(value)


def table_path(root, session=None):
    return local_path(resolve_state_root(root, 'read'), f'resource-sessions/{session_id(session)}.json')


def _number(value, name, *, nullable=False, positive=False):
    if value is None and nullable:
        return
    if (type(value) not in (int, float) or not math.isfinite(value)
            or value < 0 or (positive and value == 0)):
        raise RegistryError(f'{name} requires a finite {"positive" if positive else "nonnegative"} number')


def _validate_policy(policy):
    if not isinstance(policy, dict) or set(policy) != set(DEFAULT_POLICY):
        raise RegistryError('Unknown or missing session resource policy fields')
    allowed = policy['allowed_gpu_ids']
    if allowed != 'all_visible' and (not isinstance(allowed, list)
            or any(not isinstance(item, str) or not item for item in allowed)
            or len(set(allowed)) != len(allowed)):
        raise RegistryError('allowed_gpu_ids must be all_visible or unique GPU IDs (empty means CPU only)')
    if type(policy['allow_gpu_sharing']) is not bool:
        raise RegistryError('allow_gpu_sharing must be boolean')
    for key in set(policy) - {'allowed_gpu_ids', 'allow_gpu_sharing'}:
        _number(policy[key], key, nullable=key not in ('auto_approve_job_seconds', 'max_new_spend'),
                positive=key == 'auto_approve_job_seconds')


def read_table(root, session=None):
    """Read without initialization; preserve another session's table and choices."""
    path = table_path(root, session)
    if not path.exists():
        return None
    data = read_record(path)
    if (data.get('schema_version') != 1 or data.get('session_id') != session_id(session)
            or data.get('project_root') != str(Path(root).resolve())
            or data.get('status') not in ('selection_required', 'active')
            or type(data.get('revision')) is not int or data['revision'] < 0):
        raise RegistryError('Invalid session resource table identity or status')
    _validate_policy(data.get('policy'))
    if data['status'] == 'active' and (not data.get('selected_by') or not data.get('selected_at')):
        raise RegistryError('Active resource table is missing its user selection')
    return data


def initialize(root, session=None):
    """Idempotently create the one pending table. Initialization grants no execution."""
    session = session_id(session)
    with state_writer(root) as state, file_lock(state / 'locks' / f'resources-{session}.lock'):
        existing = read_table(root, session)
        if existing is not None:
            return existing
        data = {'schema_version': 1, 'session_id': session, 'project_root': str(Path(root).resolve()),
                'status': 'selection_required', 'revision': 0, 'created_at': now(),
                'policy': dict(DEFAULT_POLICY), 'selected_by': None, 'selected_at': None,
                'last_check': None}
        atomic_write(table_path(root, session), data)
        return data


def select(root, session=None, *, preset, selected_by, overrides=None):
    """Record the user's one-time choice, or an explicitly requested revision.

    Parameters are a preset and optional scalar limits/GPU list. Null ceilings
    mean available capacity, never an invented large number. This API records a
    choice; the calling skill must obtain it from the user, not self-authorize.
    """
    if preset not in {item['preset'] for item in CHOICES} or not isinstance(selected_by, str) or not selected_by.strip():
        raise RegistryError('Record an actual user selection and a supported preset')
    overrides = overrides or {}
    if not isinstance(overrides, dict) or set(overrides) - set(DEFAULT_POLICY):
        raise RegistryError('Unknown session resource policy overrides')
    if preset != 'custom' and overrides:
        raise RegistryError('Use custom for changed resource limits')
    initialize(root, session)
    session = session_id(session)
    with state_writer(root) as state, file_lock(state / 'locks' / f'resources-{session}.lock'):
        data = read_table(root, session)
        # A request to change one ceiling must preserve the user's other device
        # restrictions. Choosing a named preset explicitly resets to that preset.
        policy = (dict(data['policy']) if preset == 'custom' and data['status'] == 'active'
                  else dict(DEFAULT_POLICY, allow_gpu_sharing=preset != 'exclusive'))
        policy.update(overrides)
        _validate_policy(policy)
        if data['status'] != 'active' or data['policy'] != policy:
            data.update(status='active', preset=preset, policy=policy,
                        selected_by=selected_by, selected_at=now(), revision=data['revision'] + 1,
                        last_check=None)
            atomic_write(table_path(root, session), data)
        return data


def _ram():
    """Return available/total host RAM bytes, or unknown with no fabricated capacity."""
    try:
        if sys.platform.startswith('linux'):
            values = {line.split(':')[0]: int(line.split()[1]) * 1024
                      for line in Path('/proc/meminfo').read_text().splitlines() if line.split()[1].isdigit()}
            total, available = values['MemTotal'], values['MemAvailable']
            # Respect container memory limits when exposed through cgroup v2.
            limit = Path('/sys/fs/cgroup/memory.max')
            current = Path('/sys/fs/cgroup/memory.current')
            if limit.is_file() and current.is_file() and limit.read_text().strip().isdigit():
                ceiling = int(limit.read_text())
                total, available = min(total, ceiling), min(available, max(0, ceiling - int(current.read_text())))
            return {'total_bytes': total, 'available_bytes': available}
        if sys.platform == 'win32':
            import ctypes
            class MemoryStatus(ctypes.Structure):
                _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
                    (name, ctypes.c_ulonglong) for name in
                    ('total', 'available', 'page_total', 'page_available', 'virtual_total', 'virtual_available', 'extended')]
            status = MemoryStatus()
            status.length = ctypes.sizeof(status)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                raise OSError('GlobalMemoryStatusEx failed')
            return {'total_bytes': status.total, 'available_bytes': status.available}
        if sys.platform == 'darwin':
            total = int(subprocess.check_output(['sysctl', '-n', 'hw.memsize'], text=True, timeout=5))
            text = subprocess.check_output(['vm_stat'], text=True, timeout=5)
            page = int(text.split('page size of ')[1].split(' bytes')[0])
            values = {line.split(':')[0]: int(line.split(':')[1].strip().rstrip('.'))
                      for line in text.splitlines()[1:] if ':' in line}
            available = sum(values.get(name, 0) for name in ('Pages free', 'Pages inactive', 'Pages speculative')) * page
            return {'total_bytes': total, 'available_bytes': min(total, available)}
    except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError):
        pass
    return {'total_bytes': None, 'available_bytes': None}


def _gpus():
    """Read NVIDIA device state without loading CUDA or allocating device memory."""
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu',
                                 '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=8)
        if result.returncode:
            return [], result.stderr.strip() or 'nvidia-smi failed'
        rows = []
        visible = os.environ.get('CUDA_VISIBLE_DEVICES')
        allowed = None if visible is None else [item.strip() for item in visible.split(',')]
        for row in csv.reader(result.stdout.splitlines()):
            index, uuid, total, used, free, utilization = (value.strip() for value in row)
            if allowed is not None and not any(item == index or item == uuid for item in allowed):
                continue
            rows.append({'id': index, 'uuid': uuid, 'total_bytes': int(total) * 1024**2,
                         'used_bytes': int(used) * 1024**2, 'free_bytes': int(free) * 1024**2,
                         'utilization_percent': float(utilization)})
        return rows, None
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        return [], str(error)


def _disk(path):
    path = Path(path).resolve()
    ancestor = path
    while not ancestor.exists() and ancestor.parent != ancestor:
        ancestor = ancestor.parent
    try:
        usage = shutil.disk_usage(ancestor)
        return {'path': str(path), 'filesystem': str(ancestor.stat().st_dev),
                'total_bytes': usage.total, 'used_bytes': usage.used, 'free_bytes': usage.free}
    except OSError as error:
        return {'path': str(path), 'filesystem': None, 'total_bytes': None,
                'used_bytes': None, 'free_bytes': None, 'error': str(error)}


def probe(root, storage=()):
    """Sample current execution-host state. Storage rows are paths, not whole-tree scans."""
    gpus, error = _gpus()
    cores = len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else os.cpu_count()
    quota = Path('/sys/fs/cgroup/cpu.max')
    try:
        amount, period = quota.read_text().split()
        if amount != 'max':
            cores = min(cores, int(amount) / int(period)) if cores else int(amount) / int(period)
    except (OSError, ValueError):
        pass
    paths = [str(Path(root).resolve())] + [str(Path(row['path']).resolve()) for row in storage]
    disks = {path: _disk(path) for path in dict.fromkeys(paths)}
    return {'observed_at': now(), 'host': platform.node(), 'cpu_cores': cores,
            'ram': _ram(), 'gpus': gpus, 'gpu_probe_error': error, 'disks': disks}


def _request(request):
    fields = {'host', 'job_seconds', 'cpu_cores', 'ram_bytes', 'gpus', 'storage', 'new_spend'}
    if not isinstance(request, dict) or set(request) != fields:
        raise RegistryError('Declare host, job_seconds, cpu_cores, ram_bytes, gpus, storage and new_spend')
    if not isinstance(request['host'], str) or not request['host']:
        raise RegistryError('Declare the actual execution host')
    for key in ('job_seconds', 'cpu_cores', 'ram_bytes', 'new_spend'):
        _number(request[key], key, positive=key == 'job_seconds')
    if not isinstance(request['gpus'], list) or not isinstance(request['storage'], list) or not request['storage']:
        raise RegistryError('GPU list and explicit storage peaks are required (GPU list may be empty)')
    ids = []
    for row in request['gpus']:
        if not isinstance(row, dict) or set(row) != {'id', 'peak_bytes'} or not isinstance(row['id'], str):
            raise RegistryError('Each GPU requires its host ID/UUID and additional peak_bytes')
        _number(row['peak_bytes'], 'GPU peak_bytes', positive=True)
        ids.append(row['id'])
    if len(set(ids)) != len(ids):
        raise RegistryError('Declare each GPU once')
    for row in request['storage']:
        if not isinstance(row, dict) or set(row) != {'path', *STORAGE_FIELDS} or not isinstance(row['path'], str) or not Path(row['path']).is_absolute():
            raise RegistryError('Storage requires an absolute destination and all incremental peak byte fields')
        for key in STORAGE_FIELDS:
            _number(row[key], key)


def evaluate(table, request, observation, *, stage):
    """Pure projected-peak check; an approval ceiling never claims physical capacity."""
    if stage not in ('plan', 'launch'):
        raise RegistryError('Resource check stage must be plan or launch')
    if table is None or table['status'] != 'active':
        return {'status': 'SELECTION_REQUIRED', 'choices': CHOICES, 'checks': []}
    policy = table['policy']
    _validate_policy(policy)
    if request is None:
        if stage == 'launch':
            raise RegistryError('Launch needs measured or conservatively estimated peak requirements')
        return {'status': 'READY_TO_PLAN', 'checks': []}
    _request(request)
    checks = []
    def add(name, status, required, available):
        checks.append({'resource': name, 'status': status, 'required': required, 'available': available})
    def fit(name, required, available):
        add(name, 'NEEDS_ESTIMATE' if available is None else 'WAIT_RESOURCE' if required > available else 'OK', required, available)
    def ceiling(name, required, limit):
        if limit is not None:
            add(name, 'NEEDS_ESTIMATE' if required is None else 'NEEDS_APPROVAL' if required > limit else 'OK', required, limit)
    add('execution_host', 'OK' if request['host'] == observation['host'] else 'NEEDS_ESTIMATE', request['host'], observation['host'])
    ceiling('job_seconds', request['job_seconds'], policy['auto_approve_job_seconds'])
    ceiling('new_spend', request['new_spend'], policy['max_new_spend'])
    fit('cpu_cores', request['cpu_cores'], observation['cpu_cores'])
    fit('ram_bytes', request['ram_bytes'], observation['ram']['available_bytes'])
    ceiling('cpu_cores_limit', request['cpu_cores'], policy['max_cpu_cores'])
    ceiling('ram_bytes_limit', request['ram_bytes'], policy['max_ram_bytes'])
    allocated, seen = 0, set()
    for required in request['gpus']:
        device = next((row for row in observation['gpus'] if required['id'] in (row['id'], row['uuid'])), None)
        allowed = policy['allowed_gpu_ids']
        permitted = device is not None and (allowed == 'all_visible' or device['id'] in allowed or device['uuid'] in allowed)
        add('gpu:' + required['id'], 'OK' if permitted else 'NEEDS_APPROVAL' if device else 'NEEDS_ESTIMATE', required['id'], allowed)
        if device is None:
            continue
        if device['uuid'] in seen:
            raise RegistryError('GPU index and UUID refer to the same device twice')
        seen.add(device['uuid'])
        fit('vram:' + device['uuid'], required['peak_bytes'], device['free_bytes'])
        if not policy['allow_gpu_sharing'] and (device['used_bytes'] > 0 or device['utilization_percent'] > 0):
            add('exclusive:' + device['uuid'], 'WAIT_RESOURCE', 'idle GPU', device['used_bytes'])
        allocated += required['peak_bytes']
    current_vram = None if observation.get('gpu_probe_error') else sum(row['used_bytes'] for row in observation['gpus'])
    projected_vram = current_vram + allocated if current_vram is not None else None
    ceiling('total_vram_bytes', projected_vram, policy['max_total_vram_bytes'])
    filesystems, totals = {}, dict.fromkeys(STORAGE_FIELDS, 0)
    for row in request['storage']:
        path = str(Path(row['path']).resolve())
        disk = observation['disks'].get(path)
        for key in STORAGE_FIELDS:
            totals[key] += row[key]
        if disk is None or disk['filesystem'] is None or disk['free_bytes'] is None:
            add('disk:' + path, 'NEEDS_ESTIMATE', sum(row[key] for key in STORAGE_FIELDS), None)
            continue
        group = filesystems.setdefault(disk['filesystem'], {'required': 0, 'free': disk['free_bytes']})
        group['required'] += sum(row[key] for key in STORAGE_FIELDS)
        group['free'] = min(group['free'], disk['free_bytes'])
    for name, row in filesystems.items():
        fit('disk_filesystem:' + name, row['required'], row['free'])
    ceiling('dataset_bytes', totals['dataset_bytes'], policy['max_dataset_bytes'])
    ceiling('weight_bytes', totals['weight_bytes'] + totals['checkpoint_peak_bytes'], policy['max_weight_bytes'])
    ceiling('disk_bytes', sum(totals.values()), policy['max_disk_bytes'])
    statuses = {row['status'] for row in checks}
    status = next((value for value in ('NEEDS_APPROVAL', 'NEEDS_ESTIMATE', 'WAIT_RESOURCE') if value in statuses), 'AUTO_APPROVED')
    return {'status': status, 'checks': checks, 'current_total_vram_bytes': current_vram,
            'projected_total_vram_bytes': projected_vram, 'storage_peaks': totals}


def check(root, session=None, *, stage, request=None, persist=True):
    """Reload the selected table and sample live state on every planning/launch check.

    Plan-only hosts can set persist=False, which reads without initializing or
    changing the table. Estimates must cover a whole concurrently dispatched
    group, including cached inputs' additional copies and atomic save peaks.
    """
    table = read_table(root, session)
    if table is None and persist:
        table = initialize(root, session)
    if request is not None:
        _request(request)
    observation = probe(root, request['storage'] if request else ())
    result = evaluate(table, request, observation, stage=stage)
    result.update(stage=stage, table_path=str(table_path(root, session)),
                  policy_revision=table['revision'] if table else None,
                  observed=observation, request=request)
    if persist and table is not None:
        session = session_id(session)
        with state_writer(root) as state, file_lock(state / 'locks' / f'resources-{session}.lock'):
            current = read_table(root, session)
            if current['revision'] != table['revision']:
                raise RegistryError('Resource table changed during check; recheck the current selection')
            current['last_check'] = result
            atomic_write(table_path(root, session), current)
    return result


def check_launch(root, binding):
    """Admission hook for the existing launcher; no launch on an unresolved check."""
    if (not isinstance(binding, dict) or not {'session_id', 'request'} <= set(binding)
            or set(binding) - {'session_id', 'request', 'table_root'}):
        raise RegistryError('Bind resource_budget to session_id and its complete peak request')
    table_root = binding.get('table_root', root)
    if not isinstance(table_root, (str, Path)) or not Path(table_root).is_absolute():
        raise RegistryError('Resource table_root must identify the original absolute project root')
    result = check(table_root, binding['session_id'], stage='launch', request=binding['request'])
    if result['status'] != 'AUTO_APPROVED':
        raise ResourceAdmissionError(result)
    return result


def markdown(table, result=None):
    """Render the only policy table with current readings and projected requirements."""
    policy = table['policy'] if table else DEFAULT_POLICY
    result = result or (table or {}).get('last_check') or {}
    observed = result.get('observed', {})
    request = result.get('request') or {}
    peaks = result.get('storage_peaks', {})
    def size(value):
        return 'unknown' if value is None else f'{value / 1024**3:.2f} GiB'
    def limit(value, *, bytes=False):
        return 'maximum available' if value is None else size(value) if bytes else str(value)
    gpus = '; '.join(f"GPU {row['id']}: {size(row['used_bytes'])} used / {size(row['free_bytes'])} free / {size(row['total_bytes'])} total, {row['utilization_percent']:g}% busy"
                     for row in observed.get('gpus', [])) or 'not observed'
    gpu_need = '; '.join(f"{row['id']}: +{size(row['peak_bytes'])}" for row in request.get('gpus', [])) or 'none declared'
    ram = observed.get('ram', {})
    disks = {row['filesystem']: row for row in observed.get('disks', {}).values()}
    disk_state = '; '.join(f"{name}: {size(row['used_bytes'])} used / {size(row['free_bytes'])} free"
                           for name, row in disks.items()) or 'not observed'
    total_peak = sum(peaks.values()) if peaks else None
    current_vram = result.get('current_total_vram_bytes')
    if 'current_total_vram_bytes' not in result and observed.get('gpus') and not observed.get('gpu_probe_error'):
        current_vram = sum(row['used_bytes'] for row in observed['gpus'])
    rows = [
        ('GPU IDs', str(policy['allowed_gpu_ids']), gpus, gpu_need),
        ('GPU sharing', 'allowed' if policy['allow_gpu_sharing'] else 'exclusive', 'existing scheduler/leases apply', 'check each device'),
        ('CPU cores', limit(policy['max_cpu_cores']), str(observed.get('cpu_cores', 'unknown')), str(request.get('cpu_cores', 'unknown'))),
        ('Host RAM', limit(policy['max_ram_bytes'], bytes=True), f"{size(ram.get('available_bytes'))} available / {size(ram.get('total_bytes'))} total", size(request.get('ram_bytes'))),
        ('Total GPU VRAM', limit(policy['max_total_vram_bytes'], bytes=True), size(current_vram), size(result.get('projected_total_vram_bytes'))),
        ('Single job duration', f"{policy['auto_approve_job_seconds'] / 3600:g} hours", 'no invented Goal total window', f"{request['job_seconds'] / 60:g} minutes" if request else 'not estimated'),
        ('Dataset growth', limit(policy['max_dataset_bytes'], bytes=True), 'existing bytes included in disk usage', size(peaks.get('dataset_bytes'))),
        ('Weights + save peaks', limit(policy['max_weight_bytes'], bytes=True), 'existing bytes included in disk usage', f"weights {size(peaks.get('weight_bytes'))}; checkpoint peak {size(peaks.get('checkpoint_peak_bytes'))}"),
        ('Disk growth', limit(policy['max_disk_bytes'], bytes=True), disk_state, size(total_peak)),
        ('New spending per job', str(policy['max_new_spend']), 'reuse existing authorized allocations', str(request.get('new_spend', 'unknown'))),
    ]
    lines = [f"Session: {(table or {}).get('session_id', 'uninitialized')}; status: {result.get('status', (table or {}).get('status', 'selection_required'))}",
             f"Observed at: {observed.get('observed_at', 'not sampled')}", '',
             '| Resource | Session authorization ceiling | Current state | Proposed peak / use |', '| --- | --- | --- | --- |']
    for row in rows:
        lines.append('| ' + ' | '.join(str(value).replace('|', '\\|').replace('\n', ' ') for value in row) + ' |')
    return '\n'.join(lines) + '\n'


def main():
    configure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--session', help='Stable host thread/session ID; defaults to CODEX_THREAD_ID')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    choose = sub.add_parser('select')
    choose.add_argument('--preset', choices=[row['preset'] for row in CHOICES], required=True)
    choose.add_argument('--selected-by', required=True)
    choose.add_argument('--overrides', help='JSON object file, used with custom')
    inspect = sub.add_parser('check')
    inspect.add_argument('--stage', choices=['plan', 'launch'], required=True)
    inspect.add_argument('--request', help='JSON peak-requirements file; required for launch')
    inspect.add_argument('--read-only', action='store_true')
    inspect.add_argument('--markdown', action='store_true')
    sub.add_parser('show')
    args = parser.parse_args()
    try:
        if args.command == 'init':
            result = {'table': initialize(args.root, args.session), 'choices': CHOICES}
        elif args.command == 'select':
            result = select(args.root, args.session, preset=args.preset, selected_by=args.selected_by,
                            overrides=read_record(args.overrides) if args.overrides else None)
        elif args.command == 'show':
            print(markdown(read_table(args.root, args.session)), end='')
            return 0
        else:
            result = check(args.root, args.session, stage=args.stage,
                           request=read_record(args.request) if args.request else None,
                           persist=not args.read_only)
            if args.markdown:
                print(markdown(read_table(args.root, args.session), result), end='')
                return 0 if result['status'] in ('AUTO_APPROVED', 'READY_TO_PLAN') else 3
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0 if result.get('status') not in ('SELECTION_REQUIRED', 'NEEDS_APPROVAL', 'WAIT_RESOURCE', 'NEEDS_ESTIMATE') else 3
    except (RegistryError, OSError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
