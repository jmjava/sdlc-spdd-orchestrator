"""sdlc-engine shelf."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    sh = sub.add_parser("shelf", help="Shelf active work")
    sh.add_argument("--reason", default="manual shelf")
    sh.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..local_sessions import LocalSessionService
    from ..workflow import WorkflowEngine

    project = project_from(args)
    eng = WorkflowEngine(project)
    wid = eng.pointer.get()
    if wid and wid.upper().startswith("LOCAL-"):
        session = LocalSessionService(project).shelf(args.reason, session_id=wid)
        return CommandResult.ok(f"Shelved local session {session.id}: {args.reason}")
    state = eng.shelf(reason=args.reason)
    if state is None:
        return CommandResult.error("No active pointer to shelf")
    return CommandResult.ok(f"Shelved {state.work_id}: {args.reason}")
