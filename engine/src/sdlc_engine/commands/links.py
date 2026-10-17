"""sdlc-engine links."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    lk = sub.add_parser("links", help="Show Jira/GitHub/registry/canvas link map")
    lk.add_argument("work_id", nargs="?")
    lk.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..sync_local import LocalSyncService

    return CommandResult.raw(LocalSyncService(project_from(args)).links_report(args.work_id))
