"""sdlc-engine sync-roadmap."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    sr = sub.add_parser("sync-roadmap", help="Refresh ROADMAP.md managed summary from canvases")
    sr.add_argument("--roadmap", default="", help="Roadmap path (default: <home>/ROADMAP.md)")
    sr.add_argument("--dry-run", action="store_true")
    sr.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..sync_local import LocalSyncService

    block = LocalSyncService(project_from(args)).sync_roadmap(
        roadmap=args.roadmap, dry_run=args.dry_run
    )
    if args.dry_run:
        return CommandResult.ok(block)
    return CommandResult.ok(f"Updated {args.roadmap} SDLC-SPDD summary from canvases.")
