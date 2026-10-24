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
      "status": "running",  # pending|running|completed|failed_oom|failed_other|stuck
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
import os
import platform
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


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
    return datetime.utcnow().isoformat() + "Z"


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
    """Return list of GPU indices with memory.used < threshold."""
    used = gpu_memory_used()
    return [i for i in allowed if i < len(used) and used[i] < threshold_mib]


def screen_exists(name):
    out, _ = run("screen -ls")
    return re.search(rf"^\s*\d+\.{re.escape(name)}\s", out, re.MULTILINE) is not None


def kill_screen(name):
    run(f"screen -S {name} -X quit", check=False)


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
    tmp = state_file + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.rename(tmp, state_file)


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
    return all(j["status"] in ("completed", "stuck") for j in phase_jobs)


def assign_jobs_to_phases(manifest, state):
    """Ensure state.jobs contains all manifest jobs; idempotent."""
    for phase in manifest.get("phases", []):
        phase_name = phase.get("name")
        for job in phase.get("jobs", []):
            existing = next((j for j in state["jobs"] if j["id"] == job["id"]), None)
            if not existing:
                state["jobs"].append({
                    "id": job["id"],
                    "phase": phase_name,
                    "cmd": job["cmd"],
                    "expected_output": job.get("expected_output"),
                    "status": "pending",
                    "gpu": None,
                    "screen_name": None,
                    "pid": None,
                    "attempts": 0,
                    "started": None,
                    "completed": None,
                    "error": None,
                    **({'execution': json.loads(json.dumps(job['execution'])), 'execution_attempts': []} if 'execution' in job else {}),
                })


def launch_job(job, gpu, conda_env, cwd, log_dir, conda_hook):
    """Launch job in a detached screen, return (screen_name, pid)."""
    screen_name = f"EQ_{job['id']}"
    if screen_exists(screen_name):
        if job.get('execution'):
            raise ValueError('Existing governed screen must be reconciled before another launch')
        # Shouldn't happen; clean up
        kill_screen(screen_name)
        time.sleep(2)
    log_file = os.path.join(log_dir, f"{job['id']}.log")
    if job.get('execution'):
        cmd = governed_launch_command(job)
    else:
        cmd = job["cmd"]
    # Substitute GPU placeholder if present
    cmd_with_gpu = cmd.replace("${GPU}", str(gpu))
    activation = '' if job.get('execution') else f'{conda_hook} && conda activate {shlex.quote(conda_env)} && '
    full = (
        f'cd {shlex.quote(cwd)} && '
        f'{activation}'
        f'CUDA_VISIBLE_DEVICES={gpu} {cmd_with_gpu} 2>&1 | tee {shlex.quote(log_file)}'
    )
    screen_cmd = f'screen -dmS {screen_name} bash -c {shlex.quote(full)}'
    run(screen_cmd)
    time.sleep(2)
    # Get pid (find python process for this CUDA_VISIBLE_DEVICES)
    pid_out, _ = run(
        f"ps -ef | grep 'CUDA_VISIBLE_DEVICES={gpu} ' | grep -v grep | "
        f"grep python | awk '{{print $2}}' | head -1")
    pid = pid_out.strip()
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
            if record['status'] == 'completed' and record['exit_code'] == 0:
                if job.get('expected_output') and not output_exists(job['expected_output'], cwd):
                    return 'failed_other', 'Terminal execution has no expected output'
                return 'completed', None
            own_log = final.parent / 'process.log'
            return ('failed_oom', 'CUDA OOM in terminal execution') if detect_oom_in_log(str(own_log)) else (
                'failed_other', f"Recorded execution exit {record['exit_code']}")
        if screen_name and screen_exists(screen_name):
            return 'running', None
        prepared = final.parent / 'execution.json'
        admission = final.parent / 'resource-admission.json'
        if prepared.is_file() and admission.is_file() and not (final.parent / 'process.json').exists():
            current, receipt = read_record(prepared), read_record(admission)
            if (current['status'] == 'prepared' and receipt.get('execution_run_id') == binding['execution_run_id']
                    and receipt.get('snapshot_ref') == binding['snapshot_ref']
                    and receipt.get('check', {}).get('status') in
                    ('WAIT_RESOURCE', 'NEEDS_APPROVAL', 'NEEDS_ESTIMATE', 'SELECTION_REQUIRED')):
                return 'pending', 'Session resources ' + receipt['check']['status']
        return 'failed_other', 'No verified terminal execution; inspect before retry or lease release'

    # 1. Output exists → completed
    if job.get("expected_output") and output_exists(job["expected_output"], cwd):
        return "completed", None

    # 2. OOM detected → failed_oom
    if detect_oom_in_log(log_file):
        return "failed_oom", "CUDA OOM detected"

    # 3. Screen alive + python alive → still running
    if screen_name and screen_exists(screen_name):
        if job.get("pid"):
            _, rc = run(f"kill -0 {job['pid']} 2>/dev/null")
            if rc == 0:
                return "running", None
            # Python died but the screen lingers → stale; step() kills the screen.
            return "failed_other", "Process exited without expected output (stale screen)"
        else:
            # No pid known; trust screen for now
            return "running", None

    # 4. Screen gone (or never recorded), no output → failed_other
    return "failed_other", "Screen exited without expected output"


def pending_jobs_in_active_phases(state, manifest):
    active_phases = []
    for phase in manifest.get("phases", []):
        phase_name = phase.get("name")
        if phase_ready(phase_name, state) and not phase_complete(phase_name, state):
            active_phases.append(phase_name)
    return [
        j for j in state["jobs"]
        if j["status"] == "pending" and j["phase"] in active_phases
    ]


def governed_launch_command(job):
    """Keep the queue as coordinator while each actual launch gets frozen evidence."""
    binding = job['execution']
    tools_dir = Path(binding['registry_tools_dir']).resolve()
    if not (tools_dir / 'execution_registry.py').is_file():
        raise ValueError('Governed queue needs the complete registry tools and schemas on this host')
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    from execution_registry import clone_attempt, verify_queue_binding, verify_snapshot, check_execution_resources
    from environment_registry import EnvironmentRegistry
    from registry_common import read_record
    from state_paths import resolve_state_root
    root = Path(binding['project_root']).resolve()
    current = read_record(root / 'runs' / binding['execution_run_id'] / 'execution.json')
    if current['status'] in ('failed', 'stopped'):
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
            job['expected_output'] = job['expected_output'].replace('runs/' + previous + '/', 'runs/' + new_id + '/')
    verify_queue_binding(root, binding)
    check_execution_resources(root, current)
    if current['execution_run_id'] not in job.setdefault('execution_attempts', []):
        job['execution_attempts'].append(current['execution_run_id'])
    return shlex.join([binding.get('registry_python', sys.executable), str(tools_dir / 'execution_registry.py'),
                       '--root', str(root), 'launch', '--execution-id', current['execution_run_id'],
                       *binding.get('arguments', [])])


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
    process = read_record(process_path)
    if (process.get('host') != platform.node() or process.get('execution_run_id') != record['execution_run_id']
            or not isinstance(process.get('pid'), int)):
        job['lease_release'] = 'protected-needs-process-reconciliation'
        return
    try:
        os.kill(process['pid'], 0)
    except ProcessLookupError:
        pass
    except (OSError, PermissionError):
        job['lease_release'] = 'protected-needs-process-reconciliation'
        return
    else:
        job['lease_release'] = 'protected-process-present'
        return
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


def step(manifest, state, state_file, log_dir):
    """Run one scheduler step: poll, launch, update state."""
    cwd = manifest.get("cwd", ".")
    conda_env = manifest.get("conda", "base")
    conda_hook = resolve_conda_hook(manifest.get("conda_hook"))
    allowed_gpus = manifest.get("gpus", list(range(8)))
    max_parallel = manifest.get("max_parallel", len(allowed_gpus))
    gpu_free_threshold = manifest.get("gpu_free_threshold_mib",
                                       DEFAULT_GPU_FREE_THRESHOLD_MIB)
    oom_delay = manifest.get("oom_retry", {}).get("delay", 120)
    max_oom_attempts = manifest.get("oom_retry", {}).get("max_attempts", 3)

    # 1. Check running jobs
    for job in state["jobs"]:
        if job["status"] != "running":
            continue
        new_status, err = job_status_check(job, log_dir, cwd)
        if new_status == "completed":
            job["status"] = "completed"
            job["completed"] = now()
            # Clean up screen
            if job["screen_name"]:
                kill_screen(job["screen_name"])
        elif new_status == "failed_oom":
            job["status"] = "failed_oom"
            job["error"] = err
            job["completed"] = now()
            if job["screen_name"]:
                kill_screen(job["screen_name"])
        elif new_status == "failed_other":
            job["status"] = "failed_other"
            job["error"] = err
            job["completed"] = now()
            if job["screen_name"]:
                kill_screen(job["screen_name"])
        elif new_status == 'pending':
            # The admitted launcher never started a training process. Waiting
            # for resources is not a failed experiment or a consumed retry.
            job.update(status='pending', gpu=None, screen_name=None, pid=None, started=None, error=err,
                       attempts=max(0, job['attempts'] - 1))

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
            elapsed = (datetime.utcnow() - last).total_seconds()
            if elapsed >= oom_delay:
                job["status"] = "pending"  # Requeue

    # 3. Launch new jobs up to max_parallel
    running = [j for j in state["jobs"] if j["status"] == "running"]
    pending = pending_jobs_in_active_phases(state, manifest)
    free = free_gpus(allowed_gpus, gpu_free_threshold)
    # Exclude GPUs already assigned to running jobs
    taken = {j["gpu"] for j in running if j.get("gpu") is not None}
    free = [g for g in free if g not in taken]

    slots = min(max_parallel - len(running), len(free), len(pending))
    for i in range(slots):
        job = pending[i]
        gpu = free[i]
        governed = bool(job.get('execution'))
        if governed:
            try:
                governed_launch_command(job)
            except ValueError as error:
                if getattr(error, 'result', {}).get('status') not in (
                        'WAIT_RESOURCE', 'NEEDS_APPROVAL', 'NEEDS_ESTIMATE', 'SELECTION_REQUIRED'):
                    raise
                job['error'] = str(error)
                continue
            # Persist the selected attempt before screen can start. Recovery
            # sees this same binding and never relaunches a running identity.
            job.update(status='running', gpu=gpu, screen_name=f"EQ_{job['id']}",
                       pid=None, started=now(), error=None)
            job['attempts'] += 1
            save_state(state, state_file)
        try:
            screen_name, pid = launch_job(job, gpu, conda_env, cwd, log_dir, conda_hook)
        except ValueError as error:
            if not governed or getattr(error, 'result', {}).get('status') not in (
                    'WAIT_RESOURCE', 'NEEDS_APPROVAL', 'NEEDS_ESTIMATE', 'SELECTION_REQUIRED'):
                raise
            job.update(status='pending', gpu=None, screen_name=None, pid=None, started=None,
                       error=str(error), attempts=max(0, job['attempts'] - 1))
            continue
        job["status"] = "running"
        job["gpu"] = gpu
        job["screen_name"] = screen_name
        job["pid"] = pid
        if not governed:
            job["attempts"] += 1
        job["started"] = now()
        job["error"] = None

    # 4. Update phase status
    for job in state['jobs']:
        release_governed_lease(job)
    for phase in state["phases"]:
        if phase_complete(phase["name"], state):
            phase["status"] = "completed"
        elif any(j["status"] == "running"
                 for j in state["jobs"] if j.get("phase") == phase["name"]):
            phase["status"] = "running"

    save_state(state, state_file)


def all_done(state):
    return all(j["status"] in ("completed", "stuck") for j in state["jobs"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--log", default=None, help="Human-readable log file")
    ap.add_argument("--log-dir", default=None,
                    help="Per-job log directory (default: cwd)")
    ap.add_argument("--poll", type=int, default=POLL_INTERVAL_SEC)
    args = ap.parse_args()

    with open(args.manifest) as f:
        manifest = json.load(f)
    manifest["_path"] = args.manifest

    log_dir = args.log_dir or manifest.get("cwd", ".")
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    state = load_state(args.state, manifest)
    assign_jobs_to_phases(manifest, state)
    save_state(state, args.state)

    print(f"[{now()}] Queue manager started with {len(state['jobs'])} jobs")
    sys.stdout.flush()

    while not all_done(state):
        try:
            step(manifest, state, args.state, log_dir)
        except Exception as e:
            print(f"[{now()}] Step error: {e}")
            sys.stdout.flush()
        time.sleep(args.poll)

    print(f"[{now()}] All jobs done")


if __name__ == "__main__":
    main()
