#!/usr/bin/env python3
"""Resumable run-state for ARIS multi-phase workflows.

A long ARIS workflow (research-pipeline, paper-writing, idea-discovery) can fail
mid-run, and today there is no record of *which phase* already finished — a
resume restarts from scratch. This helper models a run as an ordered list of
phases with status, so resume can pick up where it left off.

The ARIS increment over a naive "resume = reopen" (which is all Hermes does):
the phase status enum SPLITS execution from acceptance —

    done      executor (Claude) finished writing the artifact.
              EXECUTION-COMPLETENESS — a safe SAME-MODEL self-report.
    accepted  a CROSS-MODEL reviewer (codex/gemini) OR a deterministic verifier
              returned a positive verdict, recorded with a verdict id + reviewer.
    provisional a fresh SAME-FAMILY reviewer returned a positive verdict. This
              is terminal for resume so a Codex-only workflow can advance, but
              remains explicitly distinct from accepted.
    skipped   the phase does not apply to this run (e.g. paper-writing when
              AUTO_WRITE=false) — a deterministic config decision, terminal.

Resume resolves FORWARD to the first phase that is NOT terminal ({accepted,
provisional, skipped}) — never the first non-`done`. So a phase the executor self-considered
"done" but that crashed before its cross-model audit is RE-VALIDATED on resume,
never silently skipped. Acceptance-gate rule made operational: a loop can DRIVE
resume, it cannot ACQUIT a phase past itself.

Structurally enforced: `set` may only write pending/running/done/failed/skipped;
only `accept` writes `accepted`; `mark-provisional` writes `provisional`. Both
REQUIRE a verdict id + reviewer AND that
the phase already be `done` (use --force to override) — you cannot acquit a phase
that never ran, nor mark one accepted without recording who acquitted it.

State at ``<root>/.ei/runs/<run_id>.json`` (file-based, no DB). The single-writer
contract (one orchestrator per run) remains; a portable exclusive OS lock
serializes cooperating updates inside the shared namespace guard. See
shared-references/resumable-runs.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator, Optional

try:
    from .state_paths import resolve_state_root, state_writer
    from .registry_common import file_lock, verify_ref
except ImportError:
    from state_paths import resolve_state_root, state_writer
    from registry_common import file_lock, verify_ref

try:
    from provenance import model_family
except ImportError:  # package import: ``from tools import run_state``
    from tools.provenance import model_family

EXECUTOR_STATUSES = {"pending", "running", "done", "failed", "skipped"}
GATE_VERDICTS = {"PASS", "BLOCKED"}
# Statuses resume ALWAYS skips. `provisional` is deliberately NOT here: whether a
# same-family provisional verdict may advance a run is a PER-RUN POLICY
# (`policy.provisional_advances`, default False). The Codex-native mirror sets it
# true at start_run; mainline runs keep the historical guarantee that only a
# cross-family acceptance (or an explicit skip) closes a phase.
TERMINAL_STATUSES = {"accepted", "skipped"}
ALL_STATUSES = EXECUTOR_STATUSES | {"accepted", "provisional"}


def _terminal_statuses(state: dict) -> set:
    base = set(TERMINAL_STATUSES)
    if (state.get("policy") or {}).get("provisional_advances") is True:
        base.add("provisional")
    return base


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_path(root: str, run_id: str, mode: str = 'read') -> Path:
    safe = "".join(c for c in run_id if c.isalnum() or c in "-_.")
    if not safe or safe != run_id or run_id in (".", ".."):
        raise ValueError(f"invalid run_id {run_id!r} (use [A-Za-z0-9-_.])")
    return resolve_state_root(root, mode) / "runs" / f"{run_id}.json"


@contextmanager
def _lock(root: str, run_id: str) -> Iterator[None]:
    """Hold namespace protection and one exclusive run lock for load-modify-save."""
    with state_writer(root):
        with _run_file_lock(root, run_id):
            yield


@contextmanager
def _run_file_lock(root: str, run_id: str) -> Iterator[None]:
    p = _run_path(root, run_id, 'write')
    with file_lock(p.with_suffix('.lock')):
        yield


def _load(root: str, run_id: str, mode: str = 'read') -> dict:
    p = _run_path(root, run_id, mode)
    if not p.exists():
        raise FileNotFoundError(f"no run state at {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _save(root: str, run_id: str, state: dict) -> None:
    p = _run_path(root, run_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    state["updated"] = _now()
    # Unique temp in the same dir → atomic replace, no shared-tmp clobber.
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=f".{run_id}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, p)
    except BaseException:
        try:
            os.unlink(tmp)
        finally:
            raise


def start_run(root: str, run_id: str, phases: list[str], executor: Optional[str] = "claude",
              provisional_advances: bool = False, workflow_contract: Optional[str] = None) -> dict:
    """Create a run with ordered phases, all `pending` (idempotent: won't clobber).

    ``claude`` is the historical mainline executor default. Codex-native callers
    must record ``--executor codex-gpt-6-astra`` (or their actual executor) so a
    same-family review cannot be misclassified as independent acceptance.
    ``provisional_advances`` is the per-run policy that lets a same-family
    provisional verdict close a phase for RESUME purposes (Codex-native mirror:
    true; mainline default: false — only cross-family acceptance advances).
    """
    if workflow_contract not in (None, 'idea-discovery/v1', 'idea-discovery/v2'):
        raise ValueError('Unknown workflow contract')
    if workflow_contract == 'idea-discovery/v2':
        required = ['problem-framing', 'research-lit', 'idea-creator', 'novelty-check', 'research-review', 'research-refine-pipeline']
        if phases != required:
            raise ValueError('idea-discovery/v2 requires its ordered phase contract')
    with _lock(root, run_id):
        if _run_path(root, run_id).exists():
            existing = _load(root, run_id)
            if workflow_contract is not None and existing.get('workflow_contract', 'idea-discovery/v1') != workflow_contract:
                raise ValueError('Existing run keeps its original workflow contract; do not migrate by restarting')
            return existing
        state = {
            "run_id": run_id,
            "executor_model": executor,
            "executor_family": model_family(executor) if executor else None,
            "policy": {"provisional_advances": bool(provisional_advances)},
            "created": _now(),
            "updated": _now(),
            "gates": {},
            "phases": [{"phase": ph, "status": "pending", "artifact": None,
                        "verdict_id": None, "reviewer": None,
                        "reviewer_family": None, "review_independence": None,
                        "acceptance_status": None, "executor_model": executor,
                        "executor_family": model_family(executor) if executor else None,
                        "updated": _now()} for ph in phases],
        }
        if workflow_contract is not None:
            state['workflow_contract'] = workflow_contract
        _save(root, run_id, state)
        return state


def record_gate_result(
    root: str,
    run_id: str,
    gate: str,
    verdict: str,
    reasons: list[str],
) -> dict:
    """Persist a deterministic gate result alongside phase state.

    Gates do not replace per-phase acceptance. They make workflow-level checks
    auditable, including a visible BLOCKED result when required evidence is
    missing.
    """
    if not gate:
        raise ValueError("gate name must be non-empty")
    if verdict not in GATE_VERDICTS:
        raise ValueError(f"gate verdict must be one of {sorted(GATE_VERDICTS)}")
    with _lock(root, run_id):
        state = _load(root, run_id)
        gates = state.setdefault("gates", {})
        gates[gate] = {
            "verdict": verdict,
            "reasons": list(reasons),
            "updated": _now(),
        }
        _save(root, run_id, state)
        return state


def load_run(root: str, run_id: str, *, legacy_read: bool = False) -> dict:
    """Return the persisted state for a run without mutating it."""
    return _load(root, run_id, 'legacy-read' if legacy_read else 'read')


@contextmanager
def coordination_guard(root: str, run_id: str) -> Iterator[None]:
    """Serialize the final dispatch decision with coordination updates.

    Hold only through process creation/identity recording, never while waiting
    for training. Lock order is namespace, run, then execution registry.
    """
    with _lock(root, run_id):
        yield


def update_coordination(root: str, run_id: str,
                        transition: Callable[[dict, dict], dict]) -> dict:
    """Atomically update optional coordination metadata, preserving phase gates.

    ``transition(metadata, run_snapshot)`` receives JSON copies under the existing
    run/namespace locks and returns a JSON object. Only ``coordination`` is saved;
    changes to the snapshot cannot accept phases or alter policy. Exceptions leave
    the run unchanged. Example consumer: research_control.configure / claim_action.
    The existing single-orchestrator contract and state-root resolver still apply.
    """
    with _lock(root, run_id):
        state = _load(root, run_id)
        snapshot = json.loads(json.dumps(state, allow_nan=False))
        metadata = snapshot.pop('coordination', {})
        updated = transition(metadata, snapshot)
        if not isinstance(updated, dict):
            raise ValueError('Coordination transition must return an object')
        json.dumps(updated, allow_nan=False)
        state['coordination'] = updated
        _save(root, run_id, state)
        return state


def first_open_phase(state: dict) -> Optional[dict]:
    """Select the original resume target from a loaded run without writing it.

    Respect per-run provisional policy; executor ``done`` is not acceptance.
    The returned phase belongs to the supplied snapshot, not live state.
    """
    terminal = _terminal_statuses(state)
    return next((phase for phase in state['phases'] if phase['status'] not in terminal), None)


def attach_references(root: str, run_id: str, phase: str, *, artifact_refs=(), execution_refs=(), spec_refs=()) -> dict:
    """Attach fixed identities without changing phase status, policy or review provenance."""
    for reference in [*artifact_refs, *execution_refs, *spec_refs]:
        verify_ref(root, reference)
    with _lock(root, run_id):
        state = _load(root, run_id)
        item = _find_phase(state, phase)
        for key, refs in [('artifact_refs', artifact_refs), ('execution_refs', execution_refs), ('spec_refs', spec_refs)]:
            collection = item.setdefault(key, [])
            for reference in refs:
                if reference not in collection:
                    collection.append(reference)
        _save(root, run_id, state)
        return state


def _find_phase(state: dict, phase: str) -> dict:
    for ph in state["phases"]:
        if ph["phase"] == phase:
            return ph
    raise KeyError(f"phase {phase!r} not in run (have: {[p['phase'] for p in state['phases']]})")


def set_status(root: str, run_id: str, phase: str, status: str, artifact: Optional[str] = None) -> dict:
    """Executor-side status; acceptance statuses use their dedicated APIs."""
    if status not in EXECUTOR_STATUSES:
        raise ValueError(
            f"set_status may only write {sorted(EXECUTOR_STATUSES)}; "
            "'accepted' and 'provisional' require recorded review provenance.")
    with _lock(root, run_id):
        state = _load(root, run_id)
        ph = _find_phase(state, phase)
        ph["status"] = status
        if artifact is not None:
            ph["artifact"] = artifact
        ph["updated"] = _now()
        _save(root, run_id, state)
        return state


def accept(root: str, run_id: str, phase: str, verdict_id: str, reviewer: str, force: bool = False) -> dict:
    """Mark a phase `accepted` — REQUIRES a recorded verdict id + reviewer, and
    (unless force) that the phase already be `done`.

    Call ONLY from a cross-model reviewer verdict (codex/gemini) or a deterministic
    verifier (verify_papers.py, verify_paper_audits.sh, a passing test, exit 0).
    The executor (Claude) must never call this on its own self-report.

    `verdict_id` should be a durable handle: the reviewer thread/trace id, or the
    path/sha of the verifier's report — not just a label.
    """
    if not verdict_id or not reviewer:
        raise ValueError("accept requires a non-empty verdict_id AND reviewer — "
                         "a phase cannot be accepted without recording who acquitted it.")
    with _lock(root, run_id):
        state = _load(root, run_id)
        ph = _find_phase(state, phase)
        if not force and ph["status"] not in ("done", "accepted", "provisional"):
            raise ValueError(
                f"phase {phase!r} is {ph['status']!r}, not 'done' — cannot accept a phase that "
                f"has not completed execution. Set it 'done' first, or pass force=True.")
        # (provisional -> accepted is the intended monotonic upgrade: a later
        # cross-family overlay acquits a phase a same-family review only drove.)
        reviewer_family = model_family(reviewer)
        # Older state files predate executor provenance. They belonged to the
        # Claude mainline, whose historical executor was Claude; retain that
        # compatibility default rather than letting an absent value bless an
        # arbitrary reviewer as cross-family.
        executor_model = ph.get("executor_model") or state.get("executor_model") or "claude"
        executor_family = model_family(executor_model)
        if reviewer_family != "deterministic":
            if executor_family == "unknown" or reviewer_family == "unknown":
                raise ValueError(
                    f"cannot classify acceptance families: executor={executor_model!r} "
                    f"({executor_family}), reviewer={reviewer!r} ({reviewer_family})")
            if executor_family == reviewer_family:
                raise ValueError(
                    "accept refuses known same-family review; use mark_provisional "
                    "so the phase can advance without claiming cross-family acceptance.")
        ph["status"] = "accepted"
        ph["verdict_id"] = verdict_id
        ph["reviewer"] = reviewer
        ph["reviewer_family"] = reviewer_family
        ph["review_independence"] = (
            "deterministic" if reviewer_family == "deterministic" else "cross-family"
        )
        ph["acceptance_status"] = "accepted"
        ph["executor_model"] = executor_model
        ph["executor_family"] = executor_family
        ph["updated"] = _now()
        _save(root, run_id, state)
        return state


def mark_provisional(root: str, run_id: str, phase: str, verdict_id: str,
                     reviewer: str, executor: Optional[str] = None) -> dict:
    """Record a same-family review as terminal-but-not-accepted progress.

    The executor defaults to the model recorded by :func:`start_run`. Both
    model names must resolve to the same non-deterministic family. This lets a
    Codex-only workflow resume past a reviewed phase while keeping the absence
    of cross-family acceptance machine-readable.
    """
    if not verdict_id or not reviewer:
        raise ValueError(
            "mark_provisional requires a non-empty verdict_id AND reviewer.")
    with _lock(root, run_id):
        state = _load(root, run_id)
        ph = _find_phase(state, phase)
        if ph["status"] not in ("done", "provisional"):
            raise ValueError(
                f"phase {phase!r} is {ph['status']!r}, not 'done' — cannot mark a "
                "phase provisional before execution completes.")
        executor_model = executor or ph.get("executor_model") or state.get("executor_model")
        if not executor_model:
            raise ValueError(
                "mark_provisional requires an executor model, either from start_run "
                "or the executor argument.")
        executor_family = model_family(executor_model)
        reviewer_family = model_family(reviewer)
        if executor_family == "unknown" or reviewer_family == "unknown":
            raise ValueError(
                f"cannot classify provisional executor/reviewer families: "
                f"{executor_model!r}={executor_family}, {reviewer!r}={reviewer_family}")
        if reviewer_family == "deterministic" or executor_family != reviewer_family:
            raise ValueError(
                "mark_provisional is only for same-family model review; use accept "
                "for cross-family or deterministic verdicts.")
        ph["status"] = "provisional"
        ph["verdict_id"] = verdict_id
        ph["reviewer"] = reviewer
        ph["reviewer_family"] = reviewer_family
        ph["review_independence"] = "same-family"
        ph["acceptance_status"] = "provisional"
        ph["executor_model"] = executor_model
        ph["executor_family"] = executor_family
        ph["updated"] = _now()
        _save(root, run_id, state)
        return state


def resume_point(root: str, run_id: str) -> Optional[dict]:
    """First phase whose status is NOT terminal — the resume
    target — or None if the run is complete.

    A `done`-but-not-`accepted` phase IS a resume target: its cross-model audit is
    still owed and must run before the next phase proceeds.
    """
    return first_open_phase(_load(root, run_id))


def _print_status(state: dict) -> None:
    print(f"run {state['run_id']}  (updated {state.get('updated', '?')})")
    glyph = {"pending": "·", "running": "▶", "done": "✓(unaccepted)",
             "failed": "✗", "accepted": "✅", "provisional": "⚠ provisional",
             "skipped": "⊘(skipped)"}
    for ph in state["phases"]:
        line = f"  {glyph.get(ph['status'], '?'):>14}  {ph['phase']}  [{ph['status']}]"
        if ph["status"] in ("accepted", "provisional"):
            line += f"  ← {ph['reviewer']} / {ph['verdict_id']}"
        elif ph["artifact"]:
            line += f"  → {ph['artifact']}"
        print(line)
    rp = next((p for p in state["phases"] if p["status"] not in _terminal_statuses(state)), None)
    print(f"  resume → {rp['phase'] if rp else 'COMPLETE (all phases terminal; provisional is not accepted)'}")


def main() -> int:
    ap = argparse.ArgumentParser(description="ARIS resumable run-state (done vs accepted).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start"); s.add_argument("root"); s.add_argument("run_id"); s.add_argument("--phases", required=True, help="comma-separated phase names"); s.add_argument("--executor", default="claude"); s.add_argument("--provisional-advances", action="store_true", help="per-run policy: let a same-family provisional verdict close a phase for resume (Codex-native mirror only; mainline default keeps cross-family-only advance)")
    s.add_argument('--workflow-contract', choices=['idea-discovery/v1', 'idea-discovery/v2'])
    s = sub.add_parser("set"); s.add_argument("root"); s.add_argument("run_id"); s.add_argument("phase"); s.add_argument("status", choices=sorted(EXECUTOR_STATUSES)); s.add_argument("--artifact")
    s = sub.add_parser("accept"); s.add_argument("root"); s.add_argument("run_id"); s.add_argument("phase"); s.add_argument("--verdict-id", required=True); s.add_argument("--reviewer", required=True); s.add_argument("--force", action="store_true")
    s = sub.add_parser("mark-provisional"); s.add_argument("root"); s.add_argument("run_id"); s.add_argument("phase"); s.add_argument("--verdict-id", required=True); s.add_argument("--reviewer", required=True); s.add_argument("--executor")
    s = sub.add_parser("resume"); s.add_argument("root"); s.add_argument("run_id")
    s = sub.add_parser("status"); s.add_argument("root"); s.add_argument("run_id"); s.add_argument('--legacy-read', action='store_true')
    s = sub.add_parser("list"); s.add_argument("root")
    s = sub.add_parser('attach-refs'); s.add_argument('root'); s.add_argument('run_id'); s.add_argument('phase'); s.add_argument('--record', required=True)
    a = ap.parse_args()

    try:
        if a.cmd == "start":
            _print_status(start_run(a.root, a.run_id, [p.strip() for p in a.phases.split(",") if p.strip()], executor=a.executor, provisional_advances=a.provisional_advances, workflow_contract=a.workflow_contract))
        elif a.cmd == "set":
            _print_status(set_status(a.root, a.run_id, a.phase, a.status, a.artifact))
        elif a.cmd == "accept":
            _print_status(accept(a.root, a.run_id, a.phase, a.verdict_id, a.reviewer, force=a.force))
        elif a.cmd == "mark-provisional":
            _print_status(mark_provisional(a.root, a.run_id, a.phase, a.verdict_id, a.reviewer, executor=a.executor))
        elif a.cmd == "resume":
            rp = resume_point(a.root, a.run_id)
            if rp is None:
                print("COMPLETE"); return 0
            print(rp["phase"])  # machine-readable: the resume target phase name
            print(json.dumps(rp), file=sys.stderr)
        elif a.cmd == "status":
            _print_status(load_run(a.root, a.run_id, legacy_read=a.legacy_read))
        elif a.cmd == "list":
            d = resolve_state_root(a.root, 'read') / "runs"
            for f in sorted(d.glob("*.json")) if d.exists() else []:
                print(f.stem)
        elif a.cmd == 'attach-refs':
            refs = json.loads(Path(a.record).read_text())
            _print_status(attach_references(a.root, a.run_id, a.phase,
                                           artifact_refs=refs.get('artifact_refs', []),
                                           execution_refs=refs.get('execution_refs', []),
                                           spec_refs=refs.get('spec_refs', [])))
    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr); return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
