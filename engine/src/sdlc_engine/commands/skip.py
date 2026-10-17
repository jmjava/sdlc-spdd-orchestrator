"""sdlc-engine skip."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    sk = sub.add_parser("skip", help="Skip a phase")
    sk.add_argument("phase")
    sk.add_argument("--reason", default="manual skip")
    sk.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..workflow import WorkflowEngine

    state = WorkflowEngine(project_from(args)).skip(args.phase, reason=args.reason)
    return CommandResult.ok(f"Skipped {args.phase}; now at {state.phase}")
