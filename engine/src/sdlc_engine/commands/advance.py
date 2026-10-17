"""sdlc-engine advance."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    adv = sub.add_parser("advance", help="Advance workflow phase (gated; --force bypasses)")
    adv.add_argument("--to")
    adv.add_argument(
        "--force",
        action="store_true",
        help="Bypass gate checks (a human decision, never the agent's)",
    )
    adv.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..workflow import WorkflowEngine

    try:
        state = WorkflowEngine(project_from(args)).advance(
            to=args.to, force=getattr(args, "force", False)
        )
    except ValueError as exc:
        return CommandResult.error(str(exc))
    return CommandResult.ok(f"Advanced to phase: {state.phase}")
