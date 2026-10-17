"""sdlc-engine claim."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    cl = sub.add_parser("claim", help="Claim a Work ID")
    cl.add_argument("work_id")
    cl.add_argument("--force", action="store_true")
    cl.add_argument("--phase")
    cl.add_argument("--branch")
    cl.add_argument("--pr")
    cl.add_argument(
        "--jira",
        help="Override; default auto-reads ## Jira Key from milestone requirement",
    )
    cl.add_argument("--note")
    cl.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..registry import TeamRegistry

    try:
        row = TeamRegistry(project_from(args)).claim(
            args.work_id,
            force=args.force,
            phase=args.phase,
            branch=args.branch or "",
            pr=args.pr or "",
            jira=args.jira or "",
            note=args.note or "",
        )
    except PermissionError as exc:
        return CommandResult.error(str(exc))
    return CommandResult.ok(
        f"Claimed {row.work_id} as {row.owner} (phase={row.phase})\n"
        "Team registry updated — commit spdd/memory/registry.jsonl to share with teammates."
    )
