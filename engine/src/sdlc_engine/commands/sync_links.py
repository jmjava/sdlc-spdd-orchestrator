"""sdlc-engine sync-links."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    sl = sub.add_parser(
        "sync-links",
        help="Check or repair drift across milestones, canvas Metadata, and registry",
    )
    sl.add_argument("work_id_pos", nargs="?", help="Optional Work ID (same as --work-id)")
    sl.add_argument("--work-id")
    sl.add_argument("--repair", action="store_true")
    sl.add_argument("--dry-run", action="store_true")
    sl.set_defaults(func=run)


def _repair(svc, work_id, dry_run: bool) -> CommandResult:
    actions = svc.repair_links(work_id, dry_run=dry_run)
    if not actions:
        return CommandResult.ok("sync-links: nothing to repair")
    return CommandResult.ok("\n".join(actions))


def _check(svc, work_id) -> CommandResult:
    findings = svc.check_links(work_id)
    if not findings:
        return CommandResult.ok("sync-links: no drift detected")
    repairable = [f for f in findings if f.repairable]
    manual = [f for f in findings if not f.repairable]
    lines = [
        f"[{'repairable' if f.repairable else 'manual'}] {f.work_id}: {f.code} — {f.message}"
        for f in findings
    ]
    if repairable:
        lines.append(
            f"\n{len(findings)} finding(s) ({len(repairable)} repairable). "
            "Re-run with --repair to apply safe fixes."
        )
        return CommandResult(exit_code=1, stdout="\n".join(lines) + "\n")
    lines.append(
        f"\n{len(manual)} manual finding(s) (TBD keys / planning gaps). "
        "Use `issues draft|push` or edit milestone ## Jira / ## GitHub."
    )
    return CommandResult.ok("\n".join(lines))


def run(args: argparse.Namespace) -> CommandResult:
    from ..sync_local import LocalSyncService

    svc = LocalSyncService(project_from(args))
    work_id = args.work_id or getattr(args, "work_id_pos", None)
    if args.repair:
        return _repair(svc, work_id, args.dry_run)
    return _check(svc, work_id)
