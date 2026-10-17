"""sdlc-engine list-work."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    sub.add_parser("list-work", help="List Work IDs").set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..registry import TeamRegistry

    return CommandResult.raw(TeamRegistry(project_from(args)).list_work_text())
