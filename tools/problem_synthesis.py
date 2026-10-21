#!/usr/bin/env python3
"""Validate and record a problem-level research reflection.

This helper is deliberately a gate and recorder, not a scientific judge.  It
checks that a proposed merge or abstraction pivot is tied to observations,
explicit joint predictions and a discriminating check.  A valid record is
appended to the existing ``iteration_log.py`` ledger; it never creates a
second scheduler, run-state file or exploration database.

The input format is intentionally compact and JSON-oriented so a long-running
workflow can produce it from a Markdown reflection without inventing another
state protocol.  The CLI is useful to skills and to deterministic tests:

    python3 problem_synthesis.py validate request.json
    python3 problem_synthesis.py record ROOT RUN_ID PHASE request.json
    python3 problem_synthesis.py due context.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:  # direct invocation from tools/
    from .registry_common import configure_utf8_output
except ImportError:  # pragma: no cover - direct script execution
    from registry_common import configure_utf8_output


SCHEMA_VERSION = 1
DECISIONS = frozenset({
    "MERGE",
    "KEEP_SEPARATE",
    "ABSTRACTION_PIVOT",
    "DEFER",
    "BLOCKED",
})
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
_FORBIDDEN_VERDICT_KEYS = frozenset({
    "accepted",
    "claim_status",
    "scientific_verdict",
    "verdict",
})


class SynthesisError(ValueError):
    """Raised when a reflection does not meet the synthesis contract."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SynthesisError(f"{field} must be a non-empty string")
    return value.strip()


def _list(value: Any, field: str, *, allow_empty: bool = False) -> list[Any]:
    if not isinstance(value, list) or (not allow_empty and not value):
        suffix = "" if allow_empty else " and non-empty"
        raise SynthesisError(f"{field} must be a list{suffix}")
    return value


def _refs(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    values = _list(value, field, allow_empty=allow_empty)
    if not all(isinstance(ref, str) and ref.strip() for ref in values):
        raise SynthesisError(f"{field} must contain non-empty evidence references")
    return [ref.strip() for ref in values]


def _ids(value: Any, field: str, *, minimum: int = 1) -> list[str]:
    values = _list(value, field)
    if len(values) < minimum:
        raise SynthesisError(f"{field} must contain at least {minimum} ids")
    if not all(isinstance(identifier, str) and _ID.fullmatch(identifier) for identifier in values):
        raise SynthesisError(f"{field} contains an invalid stable id")
    if len(set(values)) != len(values):
        raise SynthesisError(f"{field} contains duplicate ids")
    return values


def _reject_verdict_keys(value: Any, path: str = "request") -> None:
    """Keep empirical acceptance in result-to-claim/review gates."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key in _FORBIDDEN_VERDICT_KEYS:
                raise SynthesisError(
                    f"{path}.{key} is outside problem-synthesis; use a claim/review gate"
                )
            _reject_verdict_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_verdict_keys(child, f"{path}[{index}]")


def validate_request(request: Any) -> dict[str, Any]:
    """Validate and normalize one reflection request.

    Parameters
    ----------
    request:
        JSON-compatible mapping with ``problems``, ``candidates`` and a
        problem-level ``decision``.  Each problem and candidate must retain
        evidence references; merge-like decisions additionally require a
        joint prediction and a minimal discriminating check.

    Returns
    -------
    dict
        A shallow normalized copy suitable for the existing iteration ledger.
        The function never infers a scientific conclusion.
    """
    if not isinstance(request, dict):
        raise SynthesisError("request must be an object")
    _reject_verdict_keys(request)
    version = request.get("schema_version", SCHEMA_VERSION)
    if type(version) is not int or version != SCHEMA_VERSION:
        raise SynthesisError(f"schema_version must be {SCHEMA_VERSION}")
    if request.get('kind', 'synthesis') != 'synthesis':
        raise SynthesisError('kind must be synthesis; ordinary checkpoints belong to the workflow owner')
    gate_id = request.get('gate_id')
    if gate_id is not None and (not isinstance(gate_id, str) or not re.fullmatch(r'[a-f0-9]{32}', gate_id)):
        raise SynthesisError('gate_id must identify the active reflection checkpoint')

    raw_problems = _list(request.get("problems"), "problems")
    if len(raw_problems) < 2:
        raise SynthesisError("problem synthesis requires at least two open problems")
    problems: list[dict[str, Any]] = []
    problem_ids: list[str] = []
    for index, problem in enumerate(raw_problems):
        if not isinstance(problem, dict):
            raise SynthesisError(f"problems[{index}] must be an object")
        identifier = _text(problem.get("id"), f"problems[{index}].id")
        if not _ID.fullmatch(identifier):
            raise SynthesisError(f"problems[{index}].id is not a stable id")
        if identifier in problem_ids:
            raise SynthesisError(f"duplicate problem id: {identifier}")
        problem_ids.append(identifier)
        observation = _text(problem.get("observation"), f"problems[{index}].observation")
        evidence = _refs(problem.get("evidence_refs"), f"problems[{index}].evidence_refs")
        status = problem.get("status", "open")
        if status not in ("open", "uncertain", "deferred"):
            raise SynthesisError(f"problems[{index}].status must be open, uncertain or deferred")
        problems.append({"id": identifier, "observation": observation,
                         "evidence_refs": evidence, "status": status})

    raw_candidates = _list(request.get("candidates"), "candidates", allow_empty=True)
    candidates: list[dict[str, Any]] = []
    candidate_ids: list[str] = []
    for index, candidate in enumerate(raw_candidates):
        if not isinstance(candidate, dict):
            raise SynthesisError(f"candidates[{index}] must be an object")
        identifier = _text(candidate.get("id"), f"candidates[{index}].id")
        if not _ID.fullmatch(identifier):
            raise SynthesisError(f"candidates[{index}].id is not a stable id")
        if identifier in candidate_ids:
            raise SynthesisError(f"duplicate candidate id: {identifier}")
        candidate_ids.append(identifier)
        affected = _ids(candidate.get("affected_problem_ids"),
                        f"candidates[{index}].affected_problem_ids", minimum=2)
        unknown = sorted(set(affected) - set(problem_ids))
        if unknown:
            raise SynthesisError(f"candidates[{index}] references unknown problems: {unknown}")
        shared_cause = _text(candidate.get("shared_cause"), f"candidates[{index}].shared_cause")
        joint_prediction = _text(candidate.get("joint_prediction"),
                                  f"candidates[{index}].joint_prediction")
        discriminating_test = _text(candidate.get("discriminating_test"),
                                     f"candidates[{index}].discriminating_test")
        supporting = _refs(candidate.get("supporting_evidence_refs", []),
                           f"candidates[{index}].supporting_evidence_refs", allow_empty=True)
        contradicting = _refs(candidate.get("contradicting_evidence_refs", []),
                              f"candidates[{index}].contradicting_evidence_refs", allow_empty=True)
        complexity = _text(candidate.get("complexity_assessment"),
                           f"candidates[{index}].complexity_assessment")
        candidates.append({
            "id": identifier,
            "affected_problem_ids": affected,
            "shared_cause": shared_cause,
            "joint_prediction": joint_prediction,
            "discriminating_test": discriminating_test,
            "supporting_evidence_refs": supporting,
            "contradicting_evidence_refs": contradicting,
            "complexity_assessment": complexity,
        })

    decision = _text(request.get("decision"), "decision").upper()
    if decision not in DECISIONS:
        raise SynthesisError(f"decision must be one of {sorted(DECISIONS)}")
    selected = request.get("selected_candidate")
    reason = _text(request.get("reason"), "reason")
    if decision in {"MERGE", "ABSTRACTION_PIVOT"}:
        if not isinstance(selected, str) or selected not in candidate_ids:
            raise SynthesisError(f"{decision} requires selected_candidate from candidates")
        selected_candidate = next(candidate for candidate in candidates if candidate["id"] == selected)
        if not selected_candidate["supporting_evidence_refs"]:
            raise SynthesisError(
                f"{decision} requires supporting evidence references; contradictions alone do not support a merge"
            )
    elif selected is not None:
        if not isinstance(selected, str) or selected not in candidate_ids:
            raise SynthesisError("selected_candidate must reference candidates")
    if decision == "KEEP_SEPARATE":
        actions = _list(request.get("next_actions"), "next_actions")
        action_ids = []
        for index, action in enumerate(actions):
            if not isinstance(action, dict):
                raise SynthesisError(f"next_actions[{index}] must be an object")
            action_ids.append(_text(action.get("problem_id"), f"next_actions[{index}].problem_id"))
            _text(action.get("action"), f"next_actions[{index}].action")
        unknown = sorted(set(action_ids) - set(problem_ids))
        if unknown:
            raise SynthesisError(f"next_actions references unknown problems: {unknown}")
        if set(action_ids) != set(problem_ids) or len(action_ids) != len(set(action_ids)):
            raise SynthesisError("KEEP_SEPARATE requires one next action for every problem")
    if decision in {"DEFER", "BLOCKED"}:
        _text(request.get("blocker"), "blocker")
    next_action = request.get("next_action")
    if decision in {'MERGE', 'ABSTRACTION_PIVOT'} and next_action is None:
        raise SynthesisError(f'{decision} requires next_action to the planning owner')
    if next_action is not None:
        if not isinstance(next_action, dict):
            raise SynthesisError("next_action must be an object")
        _text(next_action.get("skill"), "next_action.skill")
        _text(next_action.get("description"), "next_action.description")

    normalized: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "kind": "synthesis",
        "problems": problems,
        "candidates": candidates,
        "decision": decision,
        "reason": reason,
    }
    if selected is not None:
        normalized["selected_candidate"] = selected
    for optional in ("next_actions", "next_action", "blocker", "gate_id"):
        if optional in request:
            normalized[optional] = request[optional]
    return normalized


def reflection_due(context: Any) -> dict[str, Any]:
    """Return deterministic cadence signals without judging research quality.

    The caller supplies counts and explicit boundaries from the existing
    workflow.  A signal requests a reflection; it never says which hypothesis
    is correct.  This keeps scheduling in the existing pipeline/queue owner.
    """
    if not isinstance(context, dict):
        raise SynthesisError("context must be an object")
    for signal in ('user_requested', 'milestone_complete', 'direction_boundary', 'fairness_drift'):
        if signal in context and type(context[signal]) is not bool:
            raise SynthesisError(f'{signal} must be a boolean')

    def count(name: str) -> int:
        value = context.get(name, 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SynthesisError(f"{name} must be a non-negative integer")
        return value

    reasons: list[str] = []
    if context.get("user_requested") is True:
        reasons.append("user_requested")
    if context.get("milestone_complete") is True:
        reasons.append("milestone_complete")
    if context.get("direction_boundary") is True:
        reasons.append("direction_boundary")
    open_problems = count("open_problem_count")
    completed_blocks = count("completed_blocks")
    if open_problems >= 2 and completed_blocks >= 1:
        reasons.append("multiple_open_problems")
    if count("local_repairs") >= 2:
        reasons.append("repeated_local_repairs")
    if count("stale_count") >= 2:
        reasons.append("stale_progress")
    if count("branch_count") >= 3:
        reasons.append("branch_growth")
    if count("overlapping_failures") >= 2:
        reasons.append("overlapping_failures")
    if context.get("fairness_drift") is True:
        reasons.append("fairness_drift")
    level = "milestone" if context.get("milestone_complete") else (
        "direction" if context.get("direction_boundary") else "block"
    )
    # Ordinary reflection stays with the caller; research-guide is Codex-only.
    skill = ('experiment-audit' if context.get('fairness_drift') else
             'problem-synthesis' if open_problems >= 2 else None)
    return {"due": bool(reasons), "level": level, "reasons": reasons,
            'skill': skill, 'kind': 'synthesis' if skill == 'problem-synthesis' else 'checkpoint'}


def record(root: str, run_id: str, phase: str, request: Any) -> dict[str, Any]:
    """Validate and append a reflection to the existing iteration ledger."""
    normalized = validate_request(request)
    try:
        from .research_control import record_reflection
    except ImportError:  # pragma: no cover - direct script execution
        from research_control import record_reflection
    return record_reflection(root, run_id, phase, normalized)


def _load_json(path: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SynthesisError(f"cannot read JSON input {path}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="validate or record a problem-level reflection")
    sub = parser.add_subparsers(dest="command", required=True)
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("request_json")
    record_parser = sub.add_parser("record")
    record_parser.add_argument("root")
    record_parser.add_argument("run_id")
    record_parser.add_argument("phase")
    record_parser.add_argument("request_json")
    due_parser = sub.add_parser("due")
    due_parser.add_argument("context_json")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            result: Any = validate_request(_load_json(args.request_json))
        elif args.command == "due":
            result = reflection_due(_load_json(args.context_json))
        else:
            result = record(args.root, args.run_id, args.phase, _load_json(args.request_json))
    except (SynthesisError, ValueError, OSError) as exc:
        print(f"problem-synthesis error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
