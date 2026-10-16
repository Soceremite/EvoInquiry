#!/usr/bin/env python3
"""Run frozen offline cases in fresh Codex CLI sessions; never auto-grade prose.

Raw traces stay in validation/. Sessions see only the request and project
fixture, not the routing rubric. A completed CLI process is not a passed case.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import tomllib
import re
import selectors
import threading

ROOT = Path(__file__).resolve().parents[1]

# A transient transport error should remain visible in the trace, but a
# repeated overload/reconnect failure cannot be useful evidence of skill
# behaviour.  Stop after two observed occurrences so the harness does not
# spend the whole case budget waiting for a service that is already failing.
SERVICE_ERROR_RE = re.compile(
    r"(?:servers?\s+(?:(?:is|are)\s+)?(?:currently\s+)?overloaded|"
    r"service\s+overloaded|overloaded\s+server|"
    r"reconnect(?:ing|ed)?|stream\s+(?:disconnected|disconnect|closed|reset)|"
    r"connection\s+(?:reset|closed|lost)|upstream\s+(?:disconnect|unavailable|error)|"
    r"temporarily\s+unavailable)",
    re.IGNORECASE,
)
SERVICE_ERROR_THRESHOLD = 2
REQUEST_ONLY_PROTOCOL = "request-only-v1"
PUBLIC_BUDGET_PROTOCOL = "public-execution-budget-v1"


def _error_texts(events: list[dict]) -> list[tuple[str, str]]:
    """Return error-bearing event fields without treating normal output as errors."""
    texts = []
    for index, event in enumerate(events):
        if event.get("type") == "error" and isinstance(event.get("message"), str):
            texts.append((f"event:{index}", event["message"]))
        item = event.get("item")
        if isinstance(item, dict) and item.get("type") == "error":
            for field in ("message", "text"):
                if isinstance(item.get(field), str):
                    texts.append((f"event:{index}:{field}", item[field]))
    return texts


def _new_service_errors(events: list[dict], stderr_text: str,
                        seen: set[tuple[str, int, str]]) -> list[str]:
    """Find new service failures in the JSON error events and stderr stream.

    The position-based keys make polling an append-only stderr file idempotent,
    while still counting two identical messages emitted at different positions.
    """
    sources = _error_texts(events)
    if stderr_text:
        sources.append(("stderr", stderr_text))
    found = []
    for source, text in sources:
        offset = 0
        for line in text.splitlines(keepends=True):
            content = line.strip()
            if content and SERVICE_ERROR_RE.search(content):
                # Count one incident per error-bearing line.  A single client
                # message often contains both "overloaded" and "reconnecting";
                # those two words must not be mistaken for two failures.
                key = (source, offset, "service-error")
                if key not in seen:
                    seen.add(key)
                    found.append(content[:300])
            offset += len(line)
    return found


def cli_command(codex: str) -> list[str]:
    # CPU affinity bounds runtime thread pools on Linux without touching other
    # users' training processes. Use the same two cores for paired variants.
    if hasattr(os, "sched_getaffinity") and shutil.which("taskset"):
        cores = sorted(os.sched_getaffinity(0))[:2]
        return ["taskset", "-c", ",".join(map(str, cores)), codex]
    return [codex]


def selection_config(selector: str) -> list[str]:
    settings = []
    if not selector.startswith('evo-inquiry@') or not selector.partition('@')[2]:
        raise ValueError('Expected an EvoInquiry plugin@marketplace selector')
    codex_root = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
    config_file = codex_root / 'config.toml'
    config = tomllib.loads(config_file.read_text(encoding='utf-8')) if config_file.is_file() else {}
    # skills/list includes skills from installed but disabled plugins in this
    # CLI version. Disable other variants by their exact skill paths as well,
    # so their descriptions cannot enter selection context or shadow an alias.
    cache = codex_root / 'plugins/cache'
    marketplace = selector.split("@", 1)[1]
    variants = {'evo-inquiry@evo-inquiry', selector}
    variants.update(name for name in config.get('plugins', {}) if name.startswith('evo-inquiry@'))
    variants.update('evo-inquiry@' + path.parent.name for path in cache.glob('*/evo-inquiry') if path.is_dir())
    for name in sorted(variants - {selector}):
        settings += ['-c', 'plugins.' + json.dumps(name) + '.enabled=false']
    excluded = sorted(p for p in cache.glob("*/evo-inquiry/*/skills/skills-codex/*/SKILL.md")
                      if p.parents[5].name != marketplace)
    original = config.get('skills', {}).get('config', [])
    preserved = [entry for entry in original if isinstance(entry, dict)
                 and isinstance(entry.get('path'), str)
                 and not str(entry['path']).startswith(str(cache) + os.sep)]
    entries_list = preserved + [{'path': str(p), 'enabled': False} for p in excluded]
    if entries_list:
        entries = ','.join('{path=' + json.dumps(v['path']) + ',enabled=' +
                           ('true' if v.get('enabled', True) else 'false') + '}' for v in entries_list)
        settings += ["-c", "skills.config=[" + entries + "]"]
    return settings + ["-c", 'plugins.' + json.dumps(selector) + '.enabled=true']


def model_config(settings: dict | None) -> list[str]:
    """Pin the recorded model choices instead of re-reading mutable defaults."""
    return [part for key in ("model", "model_reasoning_effort", "model_provider")
            if isinstance((settings or {}).get(key), str) and settings[key]
            for part in ("-c", key + "=" + json.dumps(settings[key]))]


def discover_variant(toolkit: Path, selector: str, codex: str, model_settings: dict | None = None,
                     diagnostic_path: Path | None = None) -> dict:
    """Reject an empty or mixed discovery context before running paid sessions."""
    command = cli_command(codex) + ["app-server", "--listen", "stdio://"] + selection_config(selector) + model_config(model_settings)
    diagnostics = tempfile.TemporaryFile()
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=diagnostics,
                            env=dict(os.environ, TOKIO_WORKER_THREADS="2"))
    pending = bytearray()
    def send(data: dict) -> None:
        assert proc.stdin is not None
        proc.stdin.write((json.dumps(data) + "\n").encode())
        proc.stdin.flush()
    def receive(identifier: int) -> dict:
        assert proc.stdout is not None
        deadline = time.monotonic() + 45
        with selectors.DefaultSelector() as ready:
            ready.register(proc.stdout, selectors.EVENT_READ)
            while time.monotonic() < deadline:
                while b'\n' in pending:
                    line, _, remainder = pending.partition(b'\n')
                    pending[:] = remainder
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    if data.get("id") == identifier:
                        if "error" in data:
                            raise RuntimeError(data["error"])
                        return data["result"]
                if ready.select(1):
                    chunk = os.read(proc.stdout.fileno(), 65536)
                    if not chunk:
                        raise RuntimeError("Discovery app-server exited")
                    pending.extend(chunk)
        raise TimeoutError("Skill discovery response timed out")
    try:
        send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "evo-inquiry-eval", "version": "1"}}})
        receive(1)
        send({"method": "initialized"})
        send({"id": 2, "method": "skills/list", "params": {"cwds": ["/tmp"], "forceReload": True}})
        response = receive(2)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        diagnostics.seek(0)
        if diagnostic_path is not None:
            diagnostic_path.write_bytes(diagnostics.read())
        diagnostics.close()
    skills = [s for row in response.get("data", []) for s in row.get("skills", [])
              if s["name"].startswith("evo-inquiry:") and s["enabled"]]
    expected = {"evo-inquiry:" + p.parent.name for p in (toolkit / "skills/skills-codex").glob("*/SKILL.md")}
    version = json.loads((toolkit / ".codex-plugin/plugin.json").read_text())["version"]
    if ({s["name"] for s in skills} != expected or len(skills) != len(expected)
            or any(s.get("pluginId") != selector or Path(s["path"]).parents[3].name != version for s in skills)):
        raise RuntimeError("Skill discovery is empty or mixes variants; install and persistently enable the selected plugin before evaluation")
    hashes = {s["name"]: hashlib.sha256(Path(s["path"]).read_bytes()).hexdigest() for s in skills}
    source_hashes = {"evo-inquiry:" + p.parent.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (toolkit / "skills/skills-codex").glob("*/SKILL.md")}
    if hashes != source_hashes:
        raise RuntimeError("Installed skill bytes differ from the evaluation source; refresh the selected plugin cache")
    common = Path("skills/skills-codex/shared-references/evo-inquiry.md")
    common_hash = hashlib.sha256((toolkit / common).read_bytes()).hexdigest()
    cached_common_hashes = {hashlib.sha256((Path(s["path"]).parents[3] / common).read_bytes()).hexdigest()
                            for s in skills}
    if cached_common_hashes != {common_hash}:
        raise RuntimeError("Installed shared guidance differs from the evaluation source; refresh the selected plugin cache")
    resources = sorted((toolkit / 'skills/skills-codex/shared-references').glob('*.md'))
    # All entrypoint trees are physically reachable inside a native package.
    # A model can read a mainline/overlay path instead of the discovered Codex
    # path, so pin those bytes too and report path deviations separately.
    resources.extend(sorted((toolkit / 'skills/shared-references').glob('*.md')))
    resources.extend(sorted((toolkit / 'skills').glob('*/SKILL.md')))
    for overlay in ('skills-codex-claude-review', 'skills-codex-gemini-review'):
        resources.extend(sorted((toolkit / 'skills' / overlay).glob('*/SKILL.md')))
    # Instructions deferred from an entrypoint remain behavior-affecting bytes.
    # Pin each reachable runtime's local references as well as its entrypoints.
    for runtime in ('', 'skills-codex', 'skills-codex-claude-review', 'skills-codex-gemini-review'):
        resources.extend(p for p in (toolkit / 'skills' / runtime).glob('*/references/**/*')
                         if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    resources.extend(sorted((toolkit / 'tools').glob('*.py')))
    resources.extend(p for p in (toolkit / 'skills/figure-spec/scripts').glob('*') if p.is_file())
    resources.extend(p for relative in ('VERSION', '.codex-plugin/plugin.json', 'tools/skill-contracts.json',
                                        'tools/skill-groups.tsv', 'templates/EVOINQUIRY_AGENTS_SNIPPET.md')
                     if (p := toolkit / relative).is_file())
    resources.extend(sorted((toolkit / 'tools/schemas').glob('*.schema.json')))
    resource_hashes = {}
    installed_roots = {Path(skill['path']).parents[3] for skill in skills}
    for resource in sorted(set(resources)):
        relative = resource.relative_to(toolkit)
        expected_hash = hashlib.sha256(resource.read_bytes()).hexdigest()
        for installed_root in installed_roots:
            installed = installed_root / relative
            if not installed.is_file() or hashlib.sha256(installed.read_bytes()).hexdigest() != expected_hash:
                raise RuntimeError(f'Installed support resource differs from the evaluation source: {relative}')
        resource_hashes[str(relative)] = expected_hash
    return {"entrypoints": len(skills), "selector": selector, "version": version,
            "skill_paths": [s["path"] for s in skills],
            "skill_sha256": hashes, "common_reference_sha256": common_hash,
            "support_resource_sha256": resource_hashes}


def _terminate_session(proc: subprocess.Popen) -> None:
    """Stop the isolated CLI process group and reap its direct child."""
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    finally:
        # The CLI may exit before a descendant that ignores SIGTERM.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()


def run_case(case: dict, fixture_root: Path, output: Path, toolkit: Path, codex: str, selector: str, model_settings: dict | None = None,
             cancel_event: threading.Event | None = None, public_budget_context: bool = False) -> dict:
    if cancel_event is not None and cancel_event.is_set():
        raise CancelledError('Evaluation stopped before this case started')
    destination = output / case["id"]
    if destination.exists():
        raise ValueError(f"Refusing to overwrite evaluation evidence: {destination}")
    workspace = destination / "project"
    shutil.copytree(fixture_root / case["fixture"], workspace)
    before = {str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in workspace.rglob("*") if p.is_file()}
    command = cli_command(codex) + ["-a", "never", "exec", "--ephemeral", "--json",
               "--skip-git-repo-check", "-s", "workspace-write", "-C", str(workspace),
               "-o", str(destination / "answer.md")] + selection_config(selector) + model_config(model_settings) + ["-"]
    started = time.monotonic()
    started_utc = datetime.now(timezone.utc)
    started_at = started_utc.isoformat()
    request = case["prompt"] + "\n"
    effective_prompt = request
    protocol = PUBLIC_BUDGET_PROTOCOL if public_budget_context else REQUEST_ONLY_PROTOCOL
    execution_context = None
    if public_budget_context:
        # Public facts only: never expose the private rubric, expected route or
        # answer hints. Both variants use the same format and timer semantics.
        # The monotonic ceiling includes prompt preparation and CLI startup.
        budget = {"wall_time_seconds": case["timeout_seconds"],
                  "max_tool_actions": case["max_tool_actions"],
                  "started_at_utc": started_at,
                  "deadline_at_utc": (started_utc + timedelta(seconds=case["timeout_seconds"])).isoformat()}
        notice = "\n<execution_budget>\n" + json.dumps(budget, indent=2) + "\n</execution_budget>\n"
        effective_prompt += notice
        execution_context = {"protocol": protocol, "public_budget": budget,
                             "timer_origin": "Before prompt preparation and CLI startup; enforced with monotonic time",
                             "request_sha256": hashlib.sha256(request.encode("utf-8")).hexdigest(),
                             "notice_sha256": hashlib.sha256(notice.encode("utf-8")).hexdigest(),
                             "effective_prompt_sha256": hashlib.sha256(effective_prompt.encode("utf-8")).hexdigest()}
        (destination / "request.txt").write_text(request, encoding="utf-8")
        (destination / "execution-context.json").write_text(json.dumps(execution_context, indent=2) + "\n", encoding="utf-8")
    (destination / "prompt.txt").write_text(effective_prompt, encoding="utf-8")
    progress = []
    previous_count = -1
    service_errors = []
    seen_service_errors: set[tuple[str, int, str]] = set()
    stderr_path = destination / "stderr.txt"
    with (destination / "events.jsonl").open("w") as stdout, (destination / "stderr.txt").open("w") as stderr:
        # Keep parallel CLI instances within thread limits on shared runners.
        environment = dict(os.environ, TOKIO_WORKER_THREADS="2")
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                text=True, start_new_session=True, env=environment, cwd=workspace)
        limit = None
        try:
            assert proc.stdin is not None
            proc.stdin.write(effective_prompt)
            proc.stdin.close()
            while proc.poll() is None:
                if cancel_event is not None and cancel_event.is_set():
                    limit = "cancelled"
                    break
                events = read_events(destination / "events.jsonl")
                service_errors.extend(_new_service_errors(
                    events, stderr_path.read_text(encoding="utf-8", errors="replace"), seen_service_errors))
                if len(events) != previous_count:
                    progress.append({'seconds': round(time.monotonic() - started, 2),
                                     'events': len(events),
                                     'last_event': events[-1].get('type') if events else None})
                    previous_count = len(events)
                if len(service_errors) >= SERVICE_ERROR_THRESHOLD:
                    limit = "service_error"
                    break
                if time.monotonic() - started > case["timeout_seconds"]:
                    limit = "time_limit"
                    break
                actions = [e for e in events if e.get("type") == "item.started"
                           and e.get("item", {}).get("type") not in ("agent_message", "reasoning", "error")]
                if len(actions) > case["max_tool_actions"]:
                    limit = "tool_limit"
                    break
                time.sleep(0.5)
        finally:
            if proc.poll() is None:
                _terminate_session(proc)
            if proc.stdin is not None and not proc.stdin.closed:
                proc.stdin.close()
            proc.wait()
    events = read_events(destination / "events.jsonl")
    service_errors.extend(_new_service_errors(
        events, stderr_path.read_text(encoding="utf-8", errors="replace"), seen_service_errors))
    (destination / 'progress.json').write_text(json.dumps(progress, indent=2) + '\n', encoding='utf-8')
    startup_failure = (proc.returncode != 0 and not events and
                       'failed to initialize in-process app-server client' in
                       (destination / 'stderr.txt').read_text(errors='replace'))
    action_count = sum(e.get("type") == "item.started" and
                       e.get("item", {}).get("type") not in ("agent_message", "reasoning", "error") for e in events)
    if limit is None and action_count > case["max_tool_actions"]:
        limit = "tool_limit"
    if limit is None and len(service_errors) >= SERVICE_ERROR_THRESHOLD:
        limit = "service_error"
    commands = [e["item"] for e in events if e.get("type") == "item.completed"
                and e.get("item", {}).get("type") == "command_execution"]
    cache_variants = sorted({match for c in commands for match in
                             re.findall(r'/plugins/cache/([^/]+)/evo-inquiry/([^/\s\"\']+)', c.get("command", ""))})
    expected_version = json.loads((toolkit / ".codex-plugin/plugin.json").read_text())["version"]
    expected_variant = (selector.split("@", 1)[1], expected_version)
    entrypoints = sorted({path for c in commands for path in re.findall(
        r'/[^\s\"\'\\]+/plugins/cache/[^\s\"\'\\]+/SKILL\.md', c.get('command', ''))})
    noncanonical = [path for path in entrypoints
                    if not re.search(r'/skills/skills-codex/[^/]+/SKILL\.md$', path)]
    after = {str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in workspace.rglob("*") if p.is_file()}
    result = {"case": case["id"], "exit_code": proc.returncode, "limit": limit,
              "seconds": round(time.monotonic() - started, 2),
              "started_at": started_at, "finished_at": datetime.now(timezone.utc).isoformat(),
              "tool_actions": action_count,
              "commands": [{k: c.get(k) for k in ("command", "exit_code", "status")} for c in commands],
              "changed_or_created_files": sorted(k for k, v in after.items() if before.get(k) != v),
              "deleted_files": sorted(before.keys() - after.keys()),
              "session_completed": any(e.get("type") == "turn.completed" for e in events),
              "failure_kind": "runtime_startup" if startup_failure else limit,
              "service_error_count": len(service_errors),
              "service_error_messages": service_errors,
              "observed_cache_variants": cache_variants,
              "variant_mismatch": any(tuple(v) != expected_variant for v in cache_variants),
              "observed_skill_entrypoints": entrypoints,
              "noncanonical_skill_entrypoints": noncanonical,
              "model_settings": dict(model_settings or {}),
              "evaluation_protocol": protocol,
              "public_budget_context": public_budget_context,
              "execution_context": execution_context,
              "assessment": "UNASSESSED", "evidence": str(destination)}
    (destination / "run.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def read_events(path: Path) -> list[dict]:
    result = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            result.append(event)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolkit", type=Path, required=True, help="Installed marketplace source for this variant")
    parser.add_argument("--output", type=Path, required=True, help="New private evidence directory")
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--selector", default="evo-inquiry@evo-inquiry", help="Installed plugin ID; use separate marketplace IDs for paired runs")
    parser.add_argument("--cases", default="smoke", help="smoke, all, or comma-separated IDs")
    parser.add_argument("--manifest", type=Path, default=ROOT / 'tests/behavior/evo-inquiry-cases.json',
                        help="Separate frozen case manifest; the original 24-case rubric stays unchanged")
    parser.add_argument("--jobs", type=int, default=1, choices=range(1, 5),
                        help="Default serial runs avoid runtime startup resource contention")
    parser.add_argument("--timeout-seconds", type=int, help="Explicit equal runtime ceiling for both variants; retain earlier attempts")
    parser.add_argument("--model", help="Pin this model for every session; otherwise snapshot the current configured model")
    parser.add_argument("--reasoning-effort", help="Pin the reasoning setting; otherwise snapshot the current configured effort")
    parser.add_argument("--public-budget-context", action="store_true",
                        help="Opt in to a distinct protocol exposing only the time/action budget and UTC start/deadline; apply equally to paired variants")
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text())
    selected = set(manifest["smoke_cases"] if args.cases == "smoke" else
                   [c["id"] for c in manifest["cases"]] if args.cases == "all" else args.cases.split(","))
    cases = [c for c in manifest["cases"] if c["id"] in selected]
    if args.timeout_seconds is not None:
        if not 30 <= args.timeout_seconds <= 900:
            parser.error("Runtime ceiling must be between 30 and 900 seconds")
        cases = [dict(c, timeout_seconds=args.timeout_seconds) for c in cases]
    if selected != {c["id"] for c in cases}:
        parser.error("Unknown case ID")
    if not cases:
        parser.error("No cases selected; check the manifest and case filter")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    config_path = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml"
    config = tomllib.loads(config_path.read_text()) if config_path.exists() else {}
    model_settings = {key: config.get(key) for key in ("model", "model_reasoning_effort", "model_provider")}
    if args.model is not None:
        model_settings["model"] = args.model
    if args.reasoning_effort is not None:
        model_settings["model_reasoning_effort"] = args.reasoning_effort
    discovery = discover_variant(args.toolkit.resolve(), args.selector, args.codex, model_settings,
                                 output / 'discovery-stderr.txt')
    metadata = {"toolkit": str(args.toolkit.resolve()), "codex": subprocess.check_output([args.codex, "--version"], text=True).strip(),
                "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "case_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                "settings": "Recorded model/provider/effort pinned as CLI overrides for every session; unspecified fields use Codex defaults; TOKIO_WORKER_THREADS=2",
                "runtime_command_prefix": cli_command(args.codex),
                "model_settings": model_settings,
                "model_override_arguments": model_config(model_settings),
                "plugin_selector": args.selector,
                "timeout_seconds_override": args.timeout_seconds,
                "jobs": args.jobs,
                "evaluation_protocol": PUBLIC_BUDGET_PROTOCOL if args.public_budget_context else REQUEST_ONLY_PROTOCOL,
                "public_budget_context": args.public_budget_context,
                "discovery": discovery,
                "cases": sorted(selected), "grading": "Manual trace and artifact assessment against frozen rubric"}
    (output / "environment.json").write_text(json.dumps(metadata, indent=2) + "\n")
    results = []
    cancel_event = threading.Event()
    received_signals = []
    previous_handlers = {}

    def cancel(signum, _frame):
        received_signals.append(signum)
        cancel_event.set()

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.signal(signum, cancel)
        with ThreadPoolExecutor(max_workers=args.jobs) as executor:
            futures = [executor.submit(run_case, c, manifest_path.parent, output, args.toolkit.resolve(), args.codex, args.selector, model_settings, cancel_event, args.public_budget_context) for c in cases]
            try:
                for future in as_completed(futures):
                    try:
                        result = future.result()
                    except CancelledError:
                        continue
                    results.append(result)
                    print(json.dumps({k: result[k] for k in ("case", "exit_code", "limit", "seconds", "session_completed")}), flush=True)
            except BaseException:
                cancel_event.set()
                for future in futures:
                    future.cancel()
                raise
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
        (output / "runs.json").write_text(json.dumps(sorted(results, key=lambda r: r["case"]), indent=2) + "\n")
        if received_signals:
            metadata['interrupted_signal'] = received_signals[0]
            metadata['unrecorded_cases'] = sorted(selected - {r['case'] for r in results})
            (output / 'environment.json').write_text(json.dumps(metadata, indent=2) + '\n')
    if received_signals:
        raise SystemExit(128 + received_signals[0])


if __name__ == "__main__":
    main()
