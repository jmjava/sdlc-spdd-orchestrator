"""sdlc-engine sync-team."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    sub.add_parser("sync-team", help="Refresh done/cancelled from canvases").set_defaults(
        func=run
    )


def run(args: argparse.Namespace) -> CommandResult:
    from ..registry import TeamRegistry

    TeamRegistry(project_from(args)).refresh_done_status()
    return CommandResult.ok("Team registry refreshed from canvas Final Status.")
