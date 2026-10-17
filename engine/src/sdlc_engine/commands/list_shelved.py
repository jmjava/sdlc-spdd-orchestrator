"""sdlc-engine list-shelved."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    sub.add_parser("list-shelved", help="List shelved work").set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..workflow import WorkflowEngine

    rows = WorkflowEngine(project_from(args)).list_shelved()
    if not rows:
        return CommandResult.ok("(no shelved work)")
    lines = [f"{wid}\t{phase}\t{at}\t{reason}" for wid, phase, at, reason in rows]
    return CommandResult.ok("\n".join(lines))
