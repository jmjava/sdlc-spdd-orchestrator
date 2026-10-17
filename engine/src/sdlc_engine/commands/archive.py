"""sdlc-engine archive."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    ar = sub.add_parser("archive", help="Archive completed/cancelled work")
    ar.add_argument("work_id", nargs="?")
    ar.add_argument("--all", action="store_true")
    ar.add_argument("--dry-run", action="store_true")
    ar.add_argument("--force", action="store_true")
    ar.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..archive import ArchiveService

    svc = ArchiveService(project_from(args))
    try:
        if args.all:
            svc.archive_eligible(dry_run=args.dry_run)
        else:
            svc.archive_work(args.work_id, dry_run=args.dry_run, force=args.force)
    except ValueError as exc:
        return CommandResult.error(str(exc))
    return CommandResult()
