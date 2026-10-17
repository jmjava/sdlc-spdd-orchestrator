"""sdlc-engine resume."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    rs = sub.add_parser("resume", help="Resume a Work ID")
    rs.add_argument("work_id")
    rs.add_argument("--phase")
    rs.add_argument("--force", action="store_true")
    rs.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..workflow import WorkflowEngine

    state = WorkflowEngine(project_from(args)).resume(
        args.work_id, phase=args.phase, force=args.force
    )
    return CommandResult.ok(f"Resumed {state.work_id} at phase: {state.phase}")
