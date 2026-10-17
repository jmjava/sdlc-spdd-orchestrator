"""sdlc-engine status."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    st = sub.add_parser("status", help="Show workflow status")
    st.add_argument("--json", action="store_true")
    st.add_argument("--work-id")
    st.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..workflow import WorkflowEngine

    eng = WorkflowEngine(project_from(args))
    if args.json:
        return CommandResult.ok(eng.status_json(args.work_id))
    wid = args.work_id or eng.pointer.get() or "(none)"
    lines = [f"Pointer: {eng.pointer.get() or '(none)'}", f"Work ID: {wid}"]
    if eng.pointer.get() or args.work_id:
        lines.append(eng.status_json(args.work_id))
    return CommandResult.ok("\n".join(lines))
