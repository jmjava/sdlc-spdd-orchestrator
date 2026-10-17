"""sdlc-engine sunset."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    sun = sub.add_parser(
        "sunset",
        help=(
            "Collect GitHub PR, GitHub issue, commit, and Jira state for a Work ID "
            "and optionally stage it into the lesson ledger"
        ),
    )
    sun.add_argument("--work-id", help="Work ID (default: active pointer)")
    sun.add_argument(
        "--apply",
        action="store_true",
        help="Stage a session record (source=sunset) in the gitignored ledger",
    )
    sun.add_argument(
        "--accept",
        action="store_true",
        help="Promote the sunset record into the committed ledger (implies --apply)",
    )
    sun.add_argument("--json", action="store_true", help="Emit SunsetSnapshot JSON")
    sun.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..sunset import SunsetError, SunsetService

    svc = SunsetService(project_from(args))
    try:
        if args.json:
            text = svc.report_json(
                args.work_id or None,
                apply=bool(args.apply),
                accept=bool(args.accept),
            )
        else:
            text = svc.report_text(
                args.work_id or None,
                apply=bool(args.apply),
                accept=bool(args.accept),
            )
    except SunsetError as exc:
        return CommandResult.error(f"sunset: {exc}")
    return CommandResult.raw(text)
