#!/usr/bin/env python3
"""queue_manager.py — ARIS experiment-queue scheduler.

Runs on the SSH remote host (or locally for Modal/Vast.ai future support).
Reads a manifest, launches jobs across free GPUs via `screen`, retries on OOM,
cleans stale screens, and writes state continuously to disk.

Usage (on remote):
    nohup python3 queue_manager.py \\
        --manifest manifest.json \\
        --state queue_state.json \\
        --log-dir ./logs \\
        > queue_mgr.log 2>&1 &

(Pass --log-dir, NOT --log: --log is declared but unused; per-job log
files in --log-dir drive OOM detection and stale-screen cleanup.)

The manifest.json is either produced manually or by `build_manifest.py`.

State file format (queue_state.json):
{
  "meta": {"project": "...", "started": "ISO8601", "host": "..."},
  "phases": [{"name": "...", "depends_on": [...], "status": "..."}],
  "jobs": [
    {
      "id": "s200_N64_n50K",
      "phase": "distill",
      "status": "running",  # pending|running|completed|failed_oom|failed_other|stuck|deferred
      "gpu": 3,
      "screen_name": "EQ_s200_N64_n50K",
      "pid": 12345,
      "attempts": 1,
      "started": "...",
      "completed": null,
      "expected_output": "figures/distill_sw_N64_n50K_...json",
      "error": null
    }, ...
  ]
}
"""

import argparse
import glob
import json
import math
import os
import platform
import re
import shlex
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path


DEFERRED_ADMISSIONS = frozenset(('WAIT_RESOURCE', 'REPLAN_REQUIRED', 'NEEDS_APPROVAL',
    'NEEDS_ESTIMATE', 'SELECTION_REQUIRED', 'WAIT_REVIEW', 'WORKFLOW_STOPPED',
    'DISPATCH_BUDGET_EXHAUSTED', 'CONTROL_UNAVAILABLE', 'WAIT_PRIMARY'))
TERMINAL = frozenset(('completed', 'stuck', 'deferred'))
SCHEDULE_FIELDS = ('priority', 'ready_at', 'backfill', 'during', 'isolate_host')


def job_shell(job, command, cwd, log_file, activation='', gpu_prefix=''):
    """Wrap one attempt with pipefail and identity-bound atomic exit evidence."""
    token = uuid.uuid4().hex
    receipt = Path(log_file).with_name(f"{job['id']}.{token}.exit.json").resolve()
    pid_receipt = receipt.with_suffix('.pid')
    job.update(launch_token=token, exit_receipt=str(receipt), pid_receipt=str(pid_receipt))
    # Git Bash accepts drive-prefixed forward-slash paths; backslash-native
    # Windows strings must not become shell escape sequences or literal names.
    shell_receipt, shell_pid = receipt.as_posix(), pid_receipt.as_posix()
    shell_cwd, shell_log = Path(cwd).as_posix(), Path(log_file).as_posix()
    # Capture PIPESTATUS immediately: tee success must not hide trainer failure.
    return (f'set -o pipefail; printf "%s" "$$" > {shlex.quote(shell_pid)}; '
            f'{{ cd {shlex.quote(shell_cwd)} && {activation}{gpu_prefix}{command}; }} '
            f'2>&1 | tee {shlex.quote(shell_log)}; '
            'statuses=("${PIPESTATUS[@]}"); trainer_rc=${statuses[0]}; log_rc=${statuses[1]}; '
            'rc=$trainer_rc; if [ "$rc" -eq 0 ]; then rc=$log_rc; fi; '
            f'printf \'{{"launch_token":"{token}","exit_code":%d,"trainer_exit_code":%d,"log_exit_code":%d}}\\n\' '
            f'"$rc" "$trainer_rc" "$log_rc" > {shlex.quote(shell_receipt + ".tmp")}; '
            f'mv {shlex.quote(shell_receipt + ".tmp")} {shlex.quote(shell_receipt)}; exit "$rc"')


OOM_RE = re.compile(r"(CUDA out of memory|torch\.OutOfMemoryError)")
DEFAULT_GPU_FREE_THRESHOLD_MIB = 500
POLL_INTERVAL_SEC = 60


def resolve_conda_hook(manifest_hook=None):
    """Resolve conda hook command via (1) manifest, (2) env var, (3) auto-detect, (4) PATH.

    manifest_hook: value of `conda_hook` field in manifest (full hook command, e.g.
        `eval "$(/custom/path/conda shell.bash hook)"`), or a bare conda binary path
        which will be wrapped automatically.
    """
    def wrap(path_or_cmd):
        if path_or_cmd.startswith("eval"):
            return path_or_cmd
        return f'eval "$({path_or_cmd} shell.bash hook)"'

    # 1. Manifest override
    if manifest_hook:
        return wrap(manifest_hook)
    # 2. Env var override
    env_hook = os.environ.get("ARIS_CONDA_HOOK")
    if env_hook:
        return wrap(env_hook)
    # 3. Auto-detect common install paths
    for p in (
        os.path.expanduser("~/anaconda3/bin/conda"),
        os.path.expanduser("~/miniconda3/bin/conda"),
        os.path.expanduser("~/miniforge3/bin/conda"),
        "/opt/anaconda3/bin/conda",
        "/opt/miniconda3/bin/conda",
        "/opt/miniforge3/bin/conda",
        "/usr/local/anaconda3/bin/conda",
        "/opt/homebrew/anaconda3/bin/conda",
    ):
        if os.path.exists(p):
            return wrap(p)
    # 4. Fall back to PATH
    out, rc = run("command -v conda 2>/dev/null")
    if rc == 0 and out.strip():
        return wrap(out.strip())
    # 5. Last resort
    return 'eval "$(conda shell.bash hook)"'


def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def run(cmd, check=False, capture=True):
    """Run shell command, return (stdout, returncode)."""
    r = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{r.stderr}")
    return r.stdout, r.returncode


def gpu_memory_used():
    """Return list of used MiB per GPU index."""
    out, rc = run("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits")
    if rc != 0:
        return []
    return [int(x.strip()) for x in out.strip().split("\n") if x.strip()]


def free_gpus(allowed, threshold_mib=DEFAULT_GPU_FREE_THRESHOLD_MIB):
    """Legacy exclusive admission uses observed occupants, not a VRAM threshold.

    threshold_mib remains a compatibility argument. Resource-bound jobs use the
    selected session policy and measured peak instead of this idle-device path.
    """
    tools_dir = next((parent / 'tools' for parent in Path(__file__).resolve().parents
                      if (parent / 'tools/resource_budget.py').is_file()), None)
    if tools_dir is not None and str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    try:
        from resource_budget import _gpus
    except ImportError:
        # The legacy manager can still be copied alone to an SSH host.
        import xml.etree.ElementTree as ET
        raw, code = run('nvidia-smi -q -x')
        if code:
            return []
        try:
            devices = []
            for gpu in ET.fromstring(raw).findall('gpu'):
                processes = gpu.find('processes')
                devices.append({'id': str(int(gpu.findtext('minor_number'))), 'uuid': gpu.findtext('uuid'),
                    'process_ids': [] if processes is not None and not processes.findall('process_info') else None,
                    'utilization_percent': float(gpu.findtext('utilization/gpu_util').split()[0]),
                    'free_bytes': int(gpu.findtext('fb_memory_usage/free').split()[0]) * 1024**2})
        except (ET.ParseError, TypeError, ValueError, AttributeError):
            return []
    else:
        devices, _ = _gpus()
    selected = {str(item) for item in allowed}
    visibility = os.environ.get('CUDA_VISIBLE_DEVICES')
    visible = None if visibility is None else {item.strip() for item in visibility.split(',')}
    return [int(row['id']) for row in devices if (row['id'] in selected or row['uuid'] in selected)
            and (visible is None or row['id'] in visible or row['uuid'] in visible)
            and row.get('process_ids') == [] and row['utilization_percent'] == 0 and row['free_bytes'] > 0]


def screen_exists(name):
    out, _ = run("screen -ls")
    return re.search(rf"^\s*\d+\.{re.escape(name)}\s", out, re.MULTILINE) is not None


def kill_screen(name, *, confirmed_by=None):
    if not isinstance(confirmed_by, str) or not confirmed_by.strip():
        raise ValueError('Stopping a screen session requires explicit user confirmation')
    run(f"screen -S {shlex.quote(name)} -X quit", check=False)


def detect_oom_in_log(log_path):
    if not log_path or not Path(log_path).exists():
        return False
    try:
        # Check tail of log for OOM marker
        out, _ = run(f"tail -c 10000 {shlex.quote(log_path)}")
        return bool(OOM_RE.search(out))
    except Exception:
        return False


def output_exists(path_pattern, cwd):
    """Check if output file exists (pattern supports shell glob)."""
    if not path_pattern:
        return False
    full = os.path.join(cwd, path_pattern) if not os.path.isabs(path_pattern) else path_pattern
    return bool(glob.glob(full))


def _normalize_depends_on(value):
    """A bare string was the shape our own docs showed until 2026-08; without this
    it would be iterated character by character and the phase never becomes ready."""
    return [value] if isinstance(value, str) else (value or [])


def load_state(state_file, manifest):
    """Load state from disk or initialize from manifest."""
    if Path(state_file).exists():
        with open(state_file) as f:
            state = json.load(f)
        # a state file written before the fix carries the un-normalized shape
        for phase in state.get("phases", []):
            phase["depends_on"] = _normalize_depends_on(phase.get("depends_on"))
        return state
    # Initialize from manifest
    state = {
        "meta": {
            "project": manifest.get("project", "unknown"),
            "started": now(),
            "manifest_path": str(manifest.get("_path", "")),
        },
        "phases": [
            {"name": p.get("name", f"phase_{i}"),
             "depends_on": _normalize_depends_on(p.get("depends_on")),
             "status": "pending"}
            for i, p in enumerate(manifest.get("phases", []))
        ],
        "jobs": [],
    }
    return state


def save_state(state, state_file):
    """Atomically replace existing queue state on POSIX and native Windows."""
    destination = Path(state_file)
    descriptor, temporary = tempfile.mkstemp(dir=destination.parent, prefix='.' + destination.name + '.')
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as output:
            json.dump(state, output, indent=2, ensure_ascii=False, allow_nan=False)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        # os.rename cannot replace an existing destination on Windows.
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def phase_ready(phase_name, state):
    """Check if all depends_on phases are completed."""
    for p in state["phases"]:
        if p["name"] == phase_name:
            if not p["depends_on"]:
                return True
            for dep in p["depends_on"]:
                dep_phase = next((x for x in state["phases"] if x["name"] == dep), None)
                if not dep_phase or dep_phase["status"] != "completed":
                    return False
            return True
    return False


def phase_complete(phase_name, state):
    phase_jobs = [j for j in state["jobs"] if j.get("phase") == phase_name]
    if not phase_jobs:
        return False
    return all(j['status'] in TERMINAL for j in phase_jobs)


def _schedule(job):
    """Validate optional scheduling metadata independently of frozen launch inputs."""
    fields = {key: job[key] for key in SCHEDULE_FIELDS if key in job}
    if 'priority' in fields and type(fields['priority']) is not int:
        raise ValueError(f"Job {job['id']} priority must be an integer")
    if 'ready_at' in fields:
        value = fields['ready_at']
        if not isinstance(value, str):
            raise ValueError('ready_at requires an ISO 8601 timestamp with timezone')
        ready = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if ready.tzinfo is None:
            raise ValueError('ready_at requires a timezone')
        fields['ready_at'] = ready.timestamp()
    if 'during' in fields and (not isinstance(fields['during'], str) or not fields['during']):
        raise ValueError('during must identify a primary job')
    if 'isolate_host' in fields and type(fields['isolate_host']) is not bool:
        raise ValueError('isolate_host must be boolean')
    if set(fields) - {'priority', 'ready_at'} and not job.get('execution'):
        raise ValueError('Companion work, isolation and evidenced backfill require a governed job')
    if 'backfill' in fields:
        evidence = fields['backfill']
        if (not isinstance(evidence, dict) or set(evidence) != {'seconds', 'evidence'}
                or type(evidence['seconds']) not in (int, float)
                or not math.isfinite(evidence['seconds']) or evidence['seconds'] <= 0
                or not isinstance(evidence['evidence'], dict)):
            raise ValueError('backfill requires a positive runtime bound and a fixed evidence reference')
    return fields


def assign_jobs_to_phases(manifest, state):
    """Append eligible manifest entries without changing an existing execution binding."""
    phases = {phase['name']: phase for phase in state['phases']}
    existing = {job['id']: job for job in state['jobs']}
    declared, additions, updates = {}, [], []
    new_bindings = set()
    known_phases = set()
    new_phases = []
    for phase in manifest.get("phases", []):
        phase_name = phase['name']
        if phase_name in known_phases:
            raise ValueError(f'Duplicate queue phase: {phase_name}')
        known_phases.add(phase_name)
        depends = _normalize_depends_on(phase.get('depends_on'))
        if phase_name not in phases:
            new_phases.append({'name': phase_name, 'depends_on': depends, 'status': 'pending'})
        elif phases[phase_name]['depends_on'] != depends:
            raise ValueError(f'Cannot change dependencies of an existing phase: {phase_name}')
        for job in phase.get("jobs", []):
            name = job['id']
            if name in declared:
                raise ValueError(f'Duplicate queue job ID: {name}')
            schedule = _schedule(job)
            declared[name] = (job, schedule)
            if binding := job.get('execution'):
                identity = (Path(binding['project_root']).resolve(), binding['execution_run_id'])
                if identity in new_bindings:
                    raise ValueError(f'An execution attempt can belong to only one queue job: {name}')
                new_bindings.add(identity)
            current = existing.get(name)
            if current is None:
                additions.append({
                    "id": job["id"],
                    "phase": phase_name,
                    "cmd": job.get("cmd"),
                    "expected_output": job.get("expected_output"),
                    "status": "pending",
                    "gpu": None,
                    "screen_name": None,
                    "pid": None,
                    "attempts": 0,
                    "started": None,
                    "completed": None,
                    "error": None,
                    **schedule,
                    **({'execution': json.loads(json.dumps(job['execution'])), 'execution_attempts': []} if 'execution' in job else {}),
                })
            else:
                primary = current.get('execution_attempts', [])[:1]
                original = current.get('execution', {})
                incoming = job.get('execution', {})
                if (current['phase'] != phase_name or current.get('cmd') != job.get('cmd')
                        or original.get('project_root') != incoming.get('project_root')
                        or (primary or [original.get('execution_run_id')]) != [incoming.get('execution_run_id')]):
                    raise ValueError(f'Cannot replace an existing queue job: {name}')
                if current['status'] == 'pending':
                    updates.append((current, schedule))
    for name, (entry, schedule) in declared.items():
        if parent := schedule.get('during'):
            parent_job, parent_schedule = declared.get(parent, (None, {}))
            if (parent == name or parent_job is None or not parent_job.get('execution')
                    or parent_schedule.get('during') or parent_job['execution']['project_root'] != entry['execution']['project_root']):
                raise ValueError(f'Companion {name} requires a same-project primary job in the queue')
    state['phases'].extend(new_phases)
    state['jobs'].extend(additions)
    for current, schedule in updates:
        for key in SCHEDULE_FIELDS:
            current.pop(key, None)
        current.update(schedule)
    refresh_phase_status(state)


def launch_job(job, gpu, conda_env, cwd, log_dir, conda_hook, state_file=None):
    """Launch a detached screen and return its name and observed wrapper PID.

    Resource-bound jobs use the assignment persisted in state_file. Explicit
    legacy jobs run on their single selected GPU.
    """
    screen_name = f"EQ_{job['id']}"
    if screen_exists(screen_name):
        raise ValueError('Existing screen must be reconciled before another launch; do not terminate it automatically')
    log_file = os.path.join(log_dir, f"{job['id']}.log")
    placement = job.get('resource_assignment')
    if job.get('execution'):
        cmd = governed_launch_command(job, queue_state=state_file if placement else None)
    else:
        cmd = job["cmd"]
    # Substitute GPU placeholder if present
    cmd_with_gpu = cmd if job.get('execution') else cmd.replace("${GPU}", str(gpu))
    activation = '' if job.get('execution') else f'{conda_hook} && conda activate {shlex.quote(conda_env)} && '
    full = job_shell(job, cmd_with_gpu, cwd, log_file, activation,
                     f'CUDA_VISIBLE_DEVICES={gpu} ' if not placement and gpu is not None else '')
    screen_cmd = f'screen -dmS {shlex.quote(screen_name)} bash -c {shlex.quote(full)}'
    _, rc = run(screen_cmd)
    if rc:
        raise ValueError('Screen launcher failed; inspect the recorded attempt before retry')
    time.sleep(2)
    # Observe this wrapper's PID, never an unrelated Python job on the same GPU.
    try:
        pid = Path(job['pid_receipt']).read_text().strip()
    except OSError:
        pid = ''
    return screen_name, (int(pid) if pid.isdigit() else None)


def job_status_check(job, log_dir, cwd):
    """Return new status for a running job."""
    screen_name = job["screen_name"]
    log_file = os.path.join(log_dir, f"{job['id']}.log")

    if job.get('execution'):
        binding = job['execution']
        tools_dir = Path(binding['registry_tools_dir']).resolve()
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from registry_common import read_record
        final = Path(binding['project_root']) / 'runs' / binding['execution_run_id'] / 'execution.final.json'
        if final.is_file():
            from execution_registry import inspect_terminal
            from state_paths import resolve_state_root
            resolve_state_root(binding['project_root'], 'read')
            record, _ = inspect_terminal(binding['project_root'], binding['execution_run_id'])
            if any(record[key] != binding[key] for key in ('snapshot_ref', 'env_revision')):
                raise ValueError('Terminal execution differs from its queue binding')
            if job.get('resource_assignment'):
                unresolved = termination_pending(job, record, final.parent, read_record)
                if unresolved:
                    return 'running', unresolved
            if record['status'] == 'completed' and record['exit_code'] == 0:
                if job.get('expected_output') and not output_exists(job['expected_output'], cwd):
                    return 'failed_other', 'Terminal execution has no expected output'
                return 'completed', None
            own_log = final.parent / 'process.log'
            if record['status'] == 'stopped':
                return 'failed_other', 'Execution was stopped; do not automatically retry a user cancellation'
            return ('failed_oom', 'CUDA OOM in terminal execution') if detect_oom_in_log(str(own_log)) else (
                'failed_other', f"Recorded execution exit {record['exit_code']}")
        if screen_name and screen_exists(screen_name):
            return 'running', None
        prepared = final.parent / 'execution.json'
        if prepared.is_file() and not (final.parent / 'process.json').exists():
            current = read_record(prepared)
            for name, label in (('dispatch-admission.json', 'Workflow dispatch '),
                                ('resource-admission.json', 'Session resources ')):
                admission = final.parent / name
                if not admission.is_file():
                    continue
                receipt = read_record(admission)
                if (current['status'] == 'prepared' and receipt.get('execution_run_id') == binding['execution_run_id']
                        and receipt.get('snapshot_ref') == binding['snapshot_ref']
                        and receipt.get('check', {}).get('status') in DEFERRED_ADMISSIONS):
                    return 'pending', label + receipt['check']['status']
        if (job.get('resource_assignment') and prepared.is_file()
                and read_record(prepared)['status'] != 'prepared'):
            return 'running', 'Execution is awaiting termination reconciliation; keep its placement protected'
        return 'failed_other', 'No verified terminal execution; inspect before retry or lease release'

    # A partial output or OOM-looking log does not prove the process has exited.
    if job.get('pid') and _process_alive(job['pid']) is not False:
        return 'running', None
    if screen_name and screen_exists(screen_name):
        return 'running', None
    receipt_path = job.get('exit_receipt')
    if not receipt_path or not Path(receipt_path).is_file():
        return 'failed_other', 'No verified exit receipt; partial outputs cannot establish completion'
    try:
        receipt = json.loads(Path(receipt_path).read_text(encoding='utf-8'))
        if (not job.get('launch_token') or receipt['launch_token'] != job['launch_token']
                or type(receipt['exit_code']) is not int):
            raise ValueError('Exit receipt identity/status differs from this attempt')
    except (OSError, ValueError, KeyError, TypeError) as error:
        return 'failed_other', 'Invalid exit receipt: ' + str(error)
    if receipt['exit_code'] != 0:
        return ('failed_oom', 'CUDA OOM detected after actual exit') if detect_oom_in_log(log_file) else (
            'failed_other', f"Recorded command exit {receipt['exit_code']}")
    if job.get('expected_output') and not output_exists(job['expected_output'], cwd):
        return 'failed_other', 'Successful command has no expected output'
    return 'completed', None


def pending_jobs_in_active_phases(state, manifest):
    active_phases = []
    for phase in manifest.get("phases", []):
        phase_name = phase.get("name")
        if phase_ready(phase_name, state) and not phase_complete(phase_name, state):
            active_phases.append(phase_name)
    return sorted((
        j for j in state["jobs"]
        if j["status"] == "pending" and j["phase"] in active_phases
    ), key=lambda job: -job.get('priority', 0))


def governed_launch_command(job, *, return_admission=False, state=None, queue_state=None, preview=False):
    """Return the frozen launcher command and optionally this queue's admission.

    ``state`` supplies other active job peaks during selection. ``queue_state``
    is its durable path, used only for the final launcher after that selection
    was saved. A new OOM attempt keeps the original scientific configuration.
    """
    binding = job['execution']
    tools_dir = Path(binding['registry_tools_dir']).resolve()
    if not (tools_dir / 'execution_registry.py').is_file():
        raise ValueError('Governed queue needs the complete registry tools and schemas on this host')
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    from execution_registry import (clone_attempt, verify_queue_binding, verify_snapshot,
                                    check_execution_resources, check_execution_dispatch, rebase_execution_output)
    from environment_registry import EnvironmentRegistry
    from registry_common import read_record, verify_ref
    from state_paths import resolve_state_root
    root = Path(binding['project_root']).resolve()
    current = read_record(root / 'runs' / binding['execution_run_id'] / 'execution.json')
    if not preview and current['status'] in ('failed', 'stopped'):
        previous = binding['execution_run_id']
        attempts = job.setdefault('execution_attempts', [])
        if previous not in attempts:
            attempts.append(previous)
        new_id = attempts[0] + '-retry-' + str(max(1, job['attempts']))
        current = clone_attempt(root, previous, new_id)
        binding.update(execution_run_id=new_id, snapshot_ref=current['snapshot_ref'])
        consumer_path = resolve_state_root(root, 'read') / 'consumers' / (binding['consumer_id'] + '.json')
        consumer = read_record(consumer_path)
        consumer['execution_run_id'] = new_id
        EnvironmentRegistry(root).bind_consumer(consumer)
        # Execution-specific output arguments are explicit, never a global
        # replacement in code or historical evidence.
        binding['arguments'] = verify_snapshot(root, current['snapshot_ref'])['arguments']
        if job.get('expected_output'):
            job['expected_output'] = rebase_execution_output(job['expected_output'], previous, new_id)
    if state is not None and state['meta'].get('require_resource_binding'):
        configuration = verify_ref(root, current['snapshot_ref']).parent / 'configuration.json'
        if not read_record(configuration).get('resource_budget'):
            raise ResourceBindingRequired('Bind the frozen job to a session or specify gpus and max_parallel')
    verify_queue_binding(root, binding)
    admission = None
    if queue_state is None:
        if state is None:
            check_execution_dispatch(root, current)
            admission = check_execution_resources(root, current)
        else:
            from resource_planner import queue_context
            context = queue_context(state, job)
            if preview:
                from resource_planner import plan
                check_execution_dispatch(root, current, persist=False)
                snapshot = verify_ref(root, current['snapshot_ref']).parent
                resources = read_record(snapshot / 'configuration.json').get('resource_budget')
                return plan(root, resources, queue_context=context) if resources else None
            check_execution_dispatch(root, current)
            if parent := job.get('during'):
                from execution_registry import check_companion_window
                row = next(item for item in state['jobs'] if item['id'] == parent)
                check_companion_window(root, row['execution']['execution_run_id'])
            admission = check_execution_resources(root, current, queue_context=context)
            if admission is None and (job.get('during') or job.get('isolate_host')):
                raise ResourceBindingRequired('Bind the job to a session before dispatch')
    else:
        check_execution_dispatch(root, current)
    if current['execution_run_id'] not in job.setdefault('execution_attempts', []):
        job['execution_attempts'].append(current['execution_run_id'])
    command = [binding.get('registry_python', sys.executable), str(tools_dir / 'execution_registry.py'),
               '--root', str(root), 'launch', '--execution-id', current['execution_run_id']]
    if queue_state is not None:
        command.extend(['--queue-state', str(Path(queue_state).resolve())])
    command = shlex.join(command + binding.get('arguments', []))
    return (command, admission) if return_admission else command


def _windows_process_alive(pid):
    """Observe a PID without sending a signal; None means access is inconclusive."""
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE only.
    if not handle:
        return False if ctypes.get_last_error() == 87 else None  # Invalid PID.
    try:
        result = kernel.WaitForSingleObject(handle, 0)
        if result == 0:  # Process handle signaled: exited, even if still open elsewhere.
            return False
        return True if result == 258 else None  # WAIT_TIMEOUT or unknown failure.
    finally:
        kernel.CloseHandle(handle)


def _process_alive(pid):
    """Return True/False only for observed liveness/absence; protect unknown PIDs."""
    if type(pid) is not int or pid <= 0:
        return None
    if os.name == 'nt':
        return _windows_process_alive(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return None
    return True


def termination_pending(job, record, directory, read_record):
    """Return a protection reason until the recorded local attempt has drained."""
    process_path = directory / 'process.json'
    if (not process_path.is_file() or
            (job.get('screen_name') and screen_exists(job['screen_name']))):
        return 'protected-needs-process-reconciliation'
    process = read_record(process_path)
    termination = directory / 'termination.json'
    if termination.is_file() and read_record(termination).get('termination_scope') == 'windows-parent-only':
        return 'protected-needs-process-tree-reconciliation'
    if (process.get('host') != platform.node() or process.get('execution_run_id') != record['execution_run_id']
            or type(process.get('pid')) is not int):
        return 'protected-needs-process-reconciliation'
    alive = _process_alive(process['pid'])
    if alive is None:
        return 'protected-needs-process-reconciliation'
    return 'protected-process-present' if alive else None


def release_governed_lease(job):
    """Release a final queue binding only after its recorded process and screen ended.

    Pending OOM retries retain the same lease. Missing process metadata or an
    inaccessible/reused PID is protected until an external observer reconciles
    it; a screen timeout never constitutes termination evidence.
    """
    if not job.get('execution') or job['status'] not in ('completed', 'stuck'):
        return
    binding = job['execution']
    tools_dir = Path(binding['registry_tools_dir']).resolve()
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    from execution_registry import inspect_terminal
    from environment_registry import EnvironmentRegistry
    from registry_common import atomic_write, fixed_ref, identifier, read_record
    from state_paths import resolve_state_root, state_writer
    root = Path(binding['project_root']).resolve()
    state = resolve_state_root(root, 'read')
    lease = read_record(state / 'leases' / (identifier(binding['lease_id']) + '.json'))
    if lease['status'] == 'released':
        return
    final = root / 'runs' / binding['execution_run_id'] / 'execution.final.json'
    process_path = final.parent / 'process.json'
    if not final.is_file() or not process_path.is_file() or (job.get('screen_name') and screen_exists(job['screen_name'])):
        job['lease_release'] = 'protected-needs-process-reconciliation'
        return
    record, reference = inspect_terminal(root, binding['execution_run_id'])
    unresolved = termination_pending(job, record, final.parent, read_record)
    if unresolved:
        job['lease_release'] = unresolved
        return
    process = read_record(process_path)
    receipt = {'job_ref': record['job_ref'], 'execution_run_id': record['execution_run_id'],
               'lease_id': binding['lease_id'], 'consumer_id': binding['consumer_id'],
               'execution_ref': reference, 'pid': process['pid'], 'host': process['host'],
               'status': 'completed' if job['status'] == 'completed' else 'failed',
               'queued': False, 'process_alive': False, 'source': 'queue-manager-and-local-process-observer',
               'confirmed_at': now()}
    with state_writer(root) as state:
        path = state / 'queue/termination-receipts' / (identifier(record['execution_run_id']) + '.json')
        if not path.exists():
            atomic_write(path, receipt)
        receipt_ref = fixed_ref(root, path.relative_to(root))
    registry = EnvironmentRegistry(root)
    result = registry.reconcile_leases({record['job_ref']: receipt_ref})
    consumer = read_record(state / 'consumers' / (identifier(binding['consumer_id']) + '.json'))
    consumer.update(lifecycle='completed', confirmed_at=now(), confirmed_by='queue-manager',
                    source='queue-manager-and-local-process-observer')
    registry.bind_consumer(consumer)
    job['lease_release'] = next((item['status'] for item in result if item['lease_id'] == binding['lease_id']), 'released')


def resource_limits(manifest):
    """Read optional queue ceilings without assigning devices or inventing slots."""
    devices, parallel = manifest.get('gpus'), manifest.get('max_parallel')
    if devices is not None and (not isinstance(devices, list)
            or any(type(item) not in (int, str) or not str(item) for item in devices)):
        raise ValueError('gpus must list GPU indices or UUIDs')
    if parallel is not None and (type(parallel) is not int or parallel < 0):
        raise ValueError('max_parallel must be a nonnegative integer')
    return {'allowed_gpu_ids': [str(item) for item in devices] if devices is not None else None,
            'max_parallel_jobs': parallel}


class ResourceBindingRequired(ValueError):
    """A new manifest needs an explicit policy for this unbound job."""


def refresh_phase_status(state):
    for phase in state['phases']:
        if phase_complete(phase['name'], state):
            phase['status'] = 'completed'
        elif any(job['status'] == 'running' and job['phase'] == phase['name'] for job in state['jobs']):
            phase['status'] = 'running'
        else:
            phase['status'] = 'pending'


def reserve_job(state, job, admission, ready_at=None):
    """Keep the first resource-feasible waiting job's selected footprint."""
    if not admission or state['meta'].get('reservation') or admission['status'] not in ('AUTO_APPROVED', 'WAIT_RESOURCE'):
        return
    request = admission.get('request')
    if not request:
        return
    assignment = admission.get('assignment') or {}
    releasing = []
    if ready_at is None:
        cards = {row['id']: row['total_bytes'] for row in admission['observed']['gpus']}
        cards.update({row['uuid']: row['total_bytes'] for row in admission['observed']['gpus']})
        needed = {row['id']: row['peak_bytes'] for row in request['gpus']}
        for active in state['jobs']:
            placement = active.get('resource_assignment')
            if active['status'] != 'running' or not placement:
                continue
            conflict = any(row['id'] in needed and (placement['exclusive']
                           or admission.get('exclusive', False)
                           or row['peak_bytes'] + needed[row['id']] > cards.get(row['id'], math.inf))
                           for row in placement['request']['gpus'])
            if conflict:
                releasing.append(active['id'])
    state['meta']['reservation'] = {
        'job_id': job['id'], 'request': request, 'ready_at': ready_at, 'releasing_jobs': releasing,
        'isolate_host': job.get('isolate_host', False),
        'max_parallel_jobs': assignment.get('max_parallel_jobs', admission.get('parallel_limit')),
    }


def step(manifest, state, state_file, log_dir):
    """Observe the active attempts, dispatch admitted jobs and save queue state.

    Mutates ``state`` in place and writes it to ``state_file``. Per-attempt
    logs go under ``log_dir``. A deferred launch leaves the job pending.
    """
    cwd = manifest.get("cwd", ".")
    conda_env = manifest.get("conda", "base")
    limits = resource_limits(manifest)
    state['meta']['resource_limits'] = limits
    allowed_gpus = limits['allowed_gpu_ids']
    max_parallel = limits['max_parallel_jobs']
    state['meta']['require_resource_binding'] = (manifest.get('schema_version') == 2
                                                 and (not allowed_gpus or max_parallel is None))
    gpu_free_threshold = manifest.get("gpu_free_threshold_mib",
                                       DEFAULT_GPU_FREE_THRESHOLD_MIB)
    oom_delay = manifest.get("oom_retry", {}).get("delay", 120)
    max_oom_attempts = manifest.get("oom_retry", {}).get("max_attempts", 3)

    # 1. Check running jobs
    for job in state["jobs"]:
        if job["status"] != "running":
            continue
        new_status, err = job_status_check(job, log_dir, cwd)
        if new_status == 'running':
            job['error'] = err
        if new_status == "completed":
            job["status"] = "completed"
            job["completed"] = now()
        elif new_status == "failed_oom":
            job["status"] = "failed_oom"
            job["error"] = err
            job["completed"] = now()
        elif new_status == "failed_other":
            job["status"] = "failed_other"
            job["error"] = err
            job["completed"] = now()
        elif new_status == 'pending':
            # The admitted launcher never started a training process. Waiting
            # for resources is not a failed experiment or a consumed retry.
            job.update(status='pending', gpu=None, screen_name=None, pid=None, started=None, error=err,
                       attempts=max(0, job['attempts'] - 1), assigned_gpus=[])
            job.pop('resource_assignment', None)
    # 2. Park non-OOM failures as terminal, retry OOM jobs that have waited long enough
    current_time = time.time()
    for job in state["jobs"]:
        if job["status"] == "failed_other":
            job["status"] = "stuck"   # no retry path exists for non-OOM failures
            continue
        if job["status"] != "failed_oom":
            continue
        if job["attempts"] >= max_oom_attempts:
            job["status"] = "stuck"
            continue
        # Wait oom_delay after failure before retry
        if job["completed"]:
            last = datetime.fromisoformat(job["completed"].rstrip("Z"))
            elapsed = (datetime.now(timezone.utc).replace(tzinfo=None) - last).total_seconds()
            if elapsed >= oom_delay:
                job["status"] = "pending"  # Requeue

    # 3. Find a fit against live peaks and the first waiting priority reservation.
    jobs = {job['id']: job for job in state['jobs']}
    for job in state['jobs']:
        if job['status'] == 'pending' and job.get('during') and jobs[job['during']]['status'] in TERMINAL:
            job.update(status='deferred', error='Primary execution finished before this companion could start',
                       completed=now())
    refresh_phase_status(state)
    state['meta'].pop('reservation', None)
    running = [job for job in state['jobs'] if job['status'] == 'running']
    pending = pending_jobs_in_active_phases(state, manifest)
    use_priorities = any('priority' in job or 'ready_at' in job for job in pending)
    free = None
    taken = {gpu for job in running for gpu in job.get('assigned_gpus',
             [job['gpu']] if job.get('gpu') is not None else [])}
    for job in pending:
        if max_parallel is not None and len(running) >= max_parallel:
            break
        governed = bool(job.get('execution'))
        admission = None
        if job.get('during') and jobs[job['during']]['status'] != 'running':
            job['error'] = 'Waiting for the primary execution'
            continue
        ready_at = job.get('ready_at')
        if ready_at is not None and ready_at > current_time:
            job['error'] = 'Waiting for the declared ready time'
            if governed and not state['meta'].get('reservation'):
                try:
                    preview = governed_launch_command(job, state=state, preview=True)
                except (OSError, ValueError) as error:
                    job['error'] = str(error)
                else:
                    reserve_job(state, job, preview, ready_at)
            continue
        if governed:
            try:
                _, admission = governed_launch_command(job, return_admission=True, state=state)
            except ResourceBindingRequired as error:
                job['error'] = str(error)
                continue
            except (OSError, ValueError) as error:
                deferred = getattr(error, 'result', {})
                job['error'] = str(error)
                if use_priorities and deferred.get('status') in DEFERRED_ADMISSIONS:
                    reserve_job(state, job, deferred)
                continue
        if admission is not None:
            by_uuid = {row['uuid']: int(row['id']) for row in admission['observed']['gpus']}
            assigned = [by_uuid[row['id']] for row in admission['request']['gpus']]
            gpu = assigned[0] if assigned else None
            job['resource_assignment'] = admission['assignment']
        else:
            job.pop('resource_assignment', None)
            if not allowed_gpus or state['meta']['require_resource_binding']:
                job['error'] = 'Bind a session resource table or explicitly specify gpus and max_parallel'
                continue
            if any(item.get('resource_assignment') for item in running):
                job['error'] = 'Wait for the resource-bound batch to finish before launching unbound jobs'
                continue
            if state['meta'].get('reservation'):
                job['error'] = 'Explicit resource peaks required to share capacity reserved for an earlier job'
                continue
            if free is None:
                free = free_gpus(allowed_gpus, gpu_free_threshold)
            gpu = next((device for device in free if device not in taken), None)
            if gpu is None:
                continue
            assigned = [gpu]
        if governed:
            # Persist the selected attempt before screen can start. Recovery
            # sees this same binding and never relaunches a running identity.
            previous_job = dict(job)
            job.update(status='running', gpu=gpu, screen_name=f"EQ_{job['id']}",
                       pid=None, started=now(), error=None, assigned_gpus=assigned)
            job['attempts'] += 1
            try:
                save_state(state, state_file)
            except OSError:
                job.clear()
                job.update(previous_job)
                job.pop('resource_assignment', None)
                raise
        try:
            conda_hook = '' if governed else resolve_conda_hook(manifest.get('conda_hook'))
            screen_name, pid = launch_job(job, gpu, conda_env, cwd, log_dir, conda_hook, state_file)
        except ValueError as error:
            if not governed or getattr(error, 'result', {}).get('status') not in DEFERRED_ADMISSIONS:
                raise
            job.update(status='pending', gpu=None, screen_name=None, pid=None, started=None,
                       error=str(error), attempts=max(0, job['attempts'] - 1), assigned_gpus=[])
            job.pop('resource_assignment', None)
            continue
        job["status"] = "running"
        job["gpu"] = gpu
        job["screen_name"] = screen_name
        job["pid"] = pid
        if not governed:
            job["attempts"] += 1
        job["started"] = now()
        job["error"] = None
        job['assigned_gpus'] = assigned
        taken.update(assigned)
        running.append(job)

    # 4. Update phase status and release leases for newly parked failures
    for job in state['jobs']:
        release_governed_lease(job)
    refresh_phase_status(state)

    save_state(state, state_file)


def all_done(state):
    return all(job['status'] in TERMINAL for job in state['jobs'])


def manager_lock(manifest, state_file):
    """Serialize managers sharing a state file, including on resume."""
    binding = next((job['execution'] for phase in manifest.get('phases', [])
                    for job in phase['jobs'] if job.get('execution')), None)
    tools_dir = (Path(binding['registry_tools_dir']).resolve() if binding else
                 (Path(__file__).resolve().parent / '../../../tools').resolve())
    if not (tools_dir / 'registry_common.py').is_file():
        if binding is None:
            return nullcontext()
        raise ValueError('Use the complete registry tools on the execution host')
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    from registry_common import file_lock
    path = Path(state_file).resolve()
    return file_lock(path.with_name(path.name + '.lock'), blocking=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--log", default=None, help="Human-readable log file")
    ap.add_argument("--log-dir", default=None,
                    help="Per-job log directory (default: cwd)")
    ap.add_argument("--poll", type=int, default=POLL_INTERVAL_SEC)
    ap.add_argument('--inspect', action='store_true', help='Read the queue without launching or updating jobs')
    args = ap.parse_args()

    try:
        manifest = read_manifest(args.manifest)
        if args.inspect:
            state = load_state(args.state, manifest)
            assign_jobs_to_phases(manifest, state)
            pending = pending_jobs_in_active_phases(state, manifest)
            fields = ('id', 'status', 'phase', 'priority', 'ready_at', 'during', 'assigned_gpus')
            print(json.dumps({'pending_order': [job['id'] for job in pending],
                              'reservation': state['meta'].get('reservation'),
                              'jobs': [{key: job[key] for key in fields if key in job} for job in state['jobs']]},
                             indent=2))
            return
        with manager_lock(manifest, args.state):
            run_queue(manifest, args.state, args.log_dir or manifest.get('cwd', '.'), args.poll)
    except (OSError, ValueError) as error:
        ap.error(str(error))


def read_manifest(path):
    with open(path, encoding='utf-8') as stream:
        manifest = json.load(stream)
    manifest['_path'] = path
    limits = resource_limits(manifest)
    if not limits['allowed_gpu_ids'] or (manifest.get('schema_version') == 2 and limits['max_parallel_jobs'] is None):
        if any(not job.get('execution') for phase in manifest.get('phases', []) for job in phase['jobs']):
            raise ValueError('Bind jobs to a governed session or specify both gpus and max_parallel')
    return manifest


def run_queue(manifest, state_file, log_dir, poll):
    """Resume the queue at state_file, write logs and poll every poll seconds."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    state = load_state(state_file, manifest)
    assign_jobs_to_phases(manifest, state)
    save_state(state, state_file)

    print(f"[{now()}] Queue manager started with {len(state['jobs'])} jobs")
    sys.stdout.flush()

    while True:
        if manifest_path := manifest.get('_path'):
            try:
                incoming = read_manifest(manifest_path)
                if incoming != manifest:
                    for key in ('cwd', 'conda', 'conda_hook'):
                        if manifest.get(key) != incoming.get(key):
                            raise ValueError(f'Cannot change the live queue {key}')
                    assign_jobs_to_phases(incoming, state)
                    manifest = incoming
            except (KeyError, OSError, TypeError, ValueError) as error:
                print(f"[{now()}] Manifest update deferred: {error}", flush=True)
        if all_done(state):
            break
        try:
            step(manifest, state, state_file, log_dir)
        except Exception as e:
            print(f"[{now()}] Step error: {e}")
            sys.stdout.flush()
        time.sleep(poll)

    print(f"[{now()}] All jobs done")


if __name__ == "__main__":
    main()
