"""Team registry and archive commands."""

from __future__ import annotations

import argparse
import sys
from ..archive import ArchiveService
from ..registry import TeamRegistry

from .state import _project


def cmd_claim(args: argparse.Namespace) -> int:
    reg = TeamRegistry(_project(args))
    try:
        row = reg.claim(
            args.work_id,
            force=args.force,
            phase=args.phase,
            branch=args.branch or "",
            pr=args.pr or "",
            jira=args.jira or "",
            note=args.note or "",
        )
    except PermissionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Claimed {row.work_id} as {row.owner} (phase={row.phase})")
    print("Team registry updated — commit spdd/memory/registry.jsonl to share with teammates.")
    return 0


def cmd_release(args: argparse.Namespace) -> int:
    TeamRegistry(_project(args)).release(reason=args.reason)
    print("Released / shelved active work")
    return 0


def cmd_team(args: argparse.Namespace) -> int:
    print(TeamRegistry(_project(args)).team_text(), end="")
    return 0


def cmd_list_work(args: argparse.Namespace) -> int:
    print(TeamRegistry(_project(args)).list_work_text(), end="")
    return 0


def cmd_sync_team(args: argparse.Namespace) -> int:
    TeamRegistry(_project(args)).refresh_done_status()
    print("Team registry refreshed from canvas Final Status.")
    return 0


def cmd_archive(args: argparse.Namespace) -> int:
    svc = ArchiveService(_project(args))
    try:
        if args.all:
            svc.archive_eligible(dry_run=args.dry_run)
        else:
            svc.archive_work(args.work_id, dry_run=args.dry_run, force=args.force)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0
