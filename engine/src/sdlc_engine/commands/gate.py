"""sdlc-engine gate."""

from __future__ import annotations

import argparse
import json

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    gt = sub.add_parser(
        "gate",
        help="Check prerequisites to enter a phase (exit 0 ok / 1 blocked)",
    )
    gt.add_argument("--phase", required=True)
    gt.add_argument("--work-id", help="Work ID (default: active pointer)")
    gt.add_argument("--json", action="store_true")
    gt.set_defaults(func=run)


def _payload(work_id: str, phase: str, ok: bool, failures: list[str]) -> dict:
    from ..phases import GATE_LABELS, advisory_gates_for_phase

    advisory = [
        {"gate": name, "label": GATE_LABELS[name], "ran": False}
        for name in advisory_gates_for_phase(phase)
    ]
    return {
        "work_id": work_id,
        "phase": phase,
        "ok": ok,
        "failures": failures,
        "advisory": advisory,
    }


def _text(work_id: str, phase: str, ok: bool, failures: list[str]) -> CommandResult:
    from ..phases import format_advisory_gate_rows

    rows = format_advisory_gate_rows(phase)
    if ok:
        lines = [f"gate {phase}: OK for {work_id}", *rows]
        return CommandResult.ok("\n".join(lines))
    err_lines = [f"gate {phase}: BLOCKED for {work_id}", *[f"  - {f}" for f in failures], *rows]
    return CommandResult(exit_code=1, stderr="\n".join(err_lines) + "\n")


def run(args: argparse.Namespace) -> CommandResult:
    from ..workflow import WorkflowEngine

    eng = WorkflowEngine(project_from(args))
    work_id = args.work_id or eng.pointer.get()
    if not work_id:
        return CommandResult.error(
            "gate: no Work ID (pass --work-id or set the pointer via claim/resume)",
            code=2,
        )
    try:
        ok, failures = eng.gate_check(work_id, args.phase)
    except ValueError as exc:
        return CommandResult.error(str(exc), code=2)
    if args.json:
        return CommandResult.ok(json.dumps(_payload(work_id, args.phase, ok, failures), indent=2))
    return _text(work_id, args.phase, ok, failures)
