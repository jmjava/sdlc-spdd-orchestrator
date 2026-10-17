"""sdlc-engine team."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    sub.add_parser("team", help="Show team registry").set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..registry import TeamRegistry

    return CommandResult.raw(TeamRegistry(project_from(args)).team_text())
