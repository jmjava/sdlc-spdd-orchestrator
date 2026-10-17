"""sdlc-engine commit-message."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    cm = sub.add_parser(
        "commit-message",
        help="Collect staged/unstaged/ahead-of-base diff for drafting a commit message (does not commit)",
    )
    cm.add_argument("--hint", help="Optional short intent for the draft")
    cm.add_argument("--work-id", help="Optional Work ID (default: active pointer)")
    cm.add_argument("--base", help="Preferred base ref (default: origin/main)")
    cm.add_argument(
        "--max-diff",
        type=int,
        default=80_000,
        help="Truncate unified diff text to this many characters (default: 80000)",
    )
    cm.add_argument("--json", action="store_true", help="Emit DiffSnapshot JSON")
    cm.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..commit_message import CommitMessageError, CommitMessageService

    svc = CommitMessageService(project_from(args))
    try:
        if args.json:
            text = svc.report_json(
                base=args.base,
                work_id=args.work_id or "",
                hint=args.hint or "",
                max_diff_chars=args.max_diff,
            )
        else:
            text = svc.report_text(
                base=args.base,
                work_id=args.work_id or "",
                hint=args.hint or "",
                max_diff_chars=args.max_diff,
            )
    except CommitMessageError as exc:
        return CommandResult.error(f"commit-message: {exc}")
    return CommandResult.raw(text)
