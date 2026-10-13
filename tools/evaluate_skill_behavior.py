#!/usr/bin/env python3
"""Run frozen offline cases in fresh Codex CLI sessions; never auto-grade prose.

Raw traces stay in validation/. Sessions see only the request and project
fixture, not the routing rubric. A completed CLI process is not a passed case.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
import tomllib
import re
import selectors

ROOT = Path(__file__).resolve().parents[1]


def cli_command(codex: str) -> list[str]:
    # CPU affinity bounds runtime thread pools on Linux without touching other
    # users' training processes. Use the same two cores for paired variants.
    if hasattr(os, "sched_getaffinity") and shutil.which("taskset"):
        cores = sorted(os.sched_getaffinity(0))[:2]
        return ["taskset", "-c", ",".join(map(str, cores)), codex]
    return [codex]


def selection_config(selector: str) -> list[str]:
    settings = []
    for name in ("evo-inquiry@evo-inquiry", "evo-inquiry@evo-inquiry-eval-beta3", "evo-inquiry@evo-inquiry-eval-beta4", "evo-inquiry@evo-inquiry-eval-beta5"):
        settings += ["-c", 'plugins.' + json.dumps(name) + '.enabled=false']
    # skills/list includes skills from installed but disabled plugins in this
    # CLI version. Disable other variants by their exact skill paths as well,
    # so their descriptions cannot enter selection context or shadow an alias.
    cache = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "plugins/cache"
    marketplace = selector.split("@", 1)[1]
    excluded = sorted(p for p in cache.glob("*/evo-inquiry/*/skills/skills-codex/*/SKILL.md")
                      if p.parents[5].name != marketplace)
    if excluded:
        entries = ",".join("{path=" + json.dumps(str(p)) + ",enabled=false}" for p in excluded)
        settings += ["-c", "skills.config=[" + entries + "]"]
    return settings + ["-c", 'plugins.' + json.dumps(selector) + '.enabled=true']


def model_config(settings: dict | None) -> list[str]:
    """Pin the recorded model choices instead of re-reading mutable defaults."""
    return [part for key in ("model", "model_reasoning_effort", "model_provider")
            if isinstance((settings or {}).get(key), str) and settings[key]
            for part in ("-c", key + "=" + json.dumps(settings[key]))]


def discover_variant(toolkit: Path, selector: str, codex: str, model_settings: dict | None = None) -> dict:
    """Reject an empty or mixed discovery context before running paid sessions."""
    command = cli_command(codex) + ["app-server", "--listen", "stdio://"] + selection_config(selector) + model_config(model_settings)
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
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
    helper = toolkit / 'tools/checkpoint_retention.py'
    if helper.is_file():
        resources.append(helper)
    resources.extend(p for name in ('state_paths', 'registry_common', 'project_registry',
                                    'artifact_registry', 'environment_registry',
                                    'execution_registry', 'code_map', 'filesystem_doctor')
                     if (p := toolkit / 'tools' / (name + '.py')).is_file())
    resources.extend(sorted((toolkit / 'tools/schemas').glob('*.schema.json')))
    resource_hashes = {}
    for resource in resources:
        relative = resource.relative_to(toolkit)
        expected_hash = hashlib.sha256(resource.read_bytes()).hexdigest()
        for skill in skills:
            installed = Path(skill['path']).parents[3] / relative
            if not installed.is_file() or hashlib.sha256(installed.read_bytes()).hexdigest() != expected_hash:
                raise RuntimeError(f'Installed support resource differs from the evaluation source: {relative}')
        resource_hashes[str(relative)] = expected_hash
    return {"entrypoints": len(skills), "selector": selector, "version": version,
            "skill_paths": [s["path"] for s in skills],
            "skill_sha256": hashes, "common_reference_sha256": common_hash,
            "support_resource_sha256": resource_hashes}


def run_case(case: dict, fixture_root: Path, output: Path, toolkit: Path, codex: str, selector: str, model_settings: dict | None = None) -> dict:
    destination = output / case["id"]
    if destination.exists():
        raise ValueError(f"Refusing to overwrite evaluation evidence: {destination}")
    workspace = destination / "project"
    shutil.copytree(fixture_root / case["fixture"], workspace)
    before = {str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in workspace.rglob("*") if p.is_file()}
    (destination / "prompt.txt").write_text(case["prompt"] + "\n", encoding="utf-8")
    command = cli_command(codex) + ["-a", "never", "exec", "--ephemeral", "--json",
               "--skip-git-repo-check", "-s", "workspace-write", "-C", str(workspace),
               "-o", str(destination / "answer.md")] + selection_config(selector) + model_config(model_settings) + ["-"]
    started = time.monotonic()
    with (destination / "events.jsonl").open("w") as stdout, (destination / "stderr.txt").open("w") as stderr:
        # Keep parallel CLI instances within thread limits on shared runners.
        environment = dict(os.environ, TOKIO_WORKER_THREADS="2")
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                text=True, start_new_session=True, env=environment, cwd=workspace)
        assert proc.stdin is not None
        proc.stdin.write(case["prompt"] + "\n")
        proc.stdin.close()
        limit = None
        while proc.poll() is None:
            if time.monotonic() - started > case["timeout_seconds"]:
                limit = "time_limit"
                break
            events = read_events(destination / "events.jsonl")
            actions = [e for e in events if e.get("type") == "item.started"
                       and e.get("item", {}).get("type") not in ("agent_message", "reasoning", "error")]
            if len(actions) > case["max_tool_actions"]:
                limit = "tool_limit"
                break
            time.sleep(0.5)
        if limit:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
    events = read_events(destination / "events.jsonl")
    startup_failure = (proc.returncode != 0 and not events and
                       'failed to initialize in-process app-server client' in
                       (destination / 'stderr.txt').read_text(errors='replace'))
    action_count = sum(e.get("type") == "item.started" and
                       e.get("item", {}).get("type") not in ("agent_message", "reasoning", "error") for e in events)
    if limit is None and action_count > case["max_tool_actions"]:
        limit = "tool_limit"
    commands = [e["item"] for e in events if e.get("type") == "item.completed"
                and e.get("item", {}).get("type") == "command_execution"]
    cache_variants = sorted({match for c in commands for match in
                             re.findall(r'/plugins/cache/([^/]+)/evo-inquiry/([^/\s\"\']+)', c.get("command", ""))})
    expected_version = json.loads((toolkit / ".codex-plugin/plugin.json").read_text())["version"]
    expected_variant = (selector.split("@", 1)[1], expected_version)
    after = {str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in workspace.rglob("*") if p.is_file()}
    result = {"case": case["id"], "exit_code": proc.returncode, "limit": limit,
              "seconds": round(time.monotonic() - started, 2),
              "tool_actions": action_count,
              "commands": [{k: c.get(k) for k in ("command", "exit_code", "status")} for c in commands],
              "changed_or_created_files": sorted(k for k, v in after.items() if before.get(k) != v),
              "deleted_files": sorted(before.keys() - after.keys()),
              "session_completed": any(e.get("type") == "turn.completed" for e in events),
              "failure_kind": "runtime_startup" if startup_failure else None,
              "observed_cache_variants": cache_variants,
              "variant_mismatch": any(tuple(v) != expected_variant for v in cache_variants),
              "model_settings": dict(model_settings or {}),
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
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    config_path = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml"
    config = tomllib.loads(config_path.read_text()) if config_path.exists() else {}
    model_settings = {key: config.get(key) for key in ("model", "model_reasoning_effort", "model_provider")}
    if args.model is not None:
        model_settings["model"] = args.model
    if args.reasoning_effort is not None:
        model_settings["model_reasoning_effort"] = args.reasoning_effort
    discovery = discover_variant(args.toolkit.resolve(), args.selector, args.codex, model_settings)
    metadata = {"toolkit": str(args.toolkit.resolve()), "codex": subprocess.check_output([args.codex, "--version"], text=True).strip(),
                "case_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                "settings": "Recorded model/provider/effort pinned as CLI overrides for every session; unspecified fields use Codex defaults; TOKIO_WORKER_THREADS=2",
                "runtime_command_prefix": cli_command(args.codex),
                "model_settings": model_settings,
                "model_override_arguments": model_config(model_settings),
                "plugin_selector": args.selector,
                "timeout_seconds_override": args.timeout_seconds,
                "discovery": discovery,
                "cases": sorted(selected), "grading": "Manual trace and artifact assessment against frozen rubric"}
    (output / "environment.json").write_text(json.dumps(metadata, indent=2) + "\n")
    results = []
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = [executor.submit(run_case, c, manifest_path.parent, output, args.toolkit.resolve(), args.codex, args.selector, model_settings) for c in cases]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(json.dumps({k: result[k] for k in ("case", "exit_code", "limit", "seconds", "session_completed")}), flush=True)
    (output / "runs.json").write_text(json.dumps(sorted(results, key=lambda r: r["case"]), indent=2) + "\n")


if __name__ == "__main__":
    main()
