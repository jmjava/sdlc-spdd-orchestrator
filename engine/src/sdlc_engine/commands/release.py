"""sdlc-engine release."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    rel = sub.add_parser("release", help="Release/shelf active claim")
    rel.add_argument("--reason", default="released")
    rel.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..registry import TeamRegistry

    TeamRegistry(project_from(args)).release(reason=args.reason)
    return CommandResult.ok("Released / shelved active work")
