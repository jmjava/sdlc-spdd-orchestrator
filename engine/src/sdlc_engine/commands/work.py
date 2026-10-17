"""sdlc-engine work."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    work = sub.add_parser("work", help="Create / bootstrap Work IDs (engine-backed helpers)")
    work_sub = work.add_subparsers(dest="work_cmd", required=True)
    wia = work_sub.add_parser(
        "init-from-adf",
        help="Create draft REASONS canvas + requirement from a local ADF file",
    )
    wia.add_argument("--path", required=True, help="Path to .adf.json / ADF JSON file")
    wia.add_argument("--type", default="feature", help="feature|spike|bug|refactor|chore|...")
    wia.add_argument("--title", help="Override title (default: first ADF heading or filename)")
    wia.add_argument("--work-id", help="Explicit Work ID (default: auto FEAT-NNN-slug)")
    wia.add_argument("--no-claim", action="store_true", help="Create artifacts without claiming")
    wia.add_argument("--dry-run", action="store_true")
    wia.set_defaults(func=run)


def _init_from_adf(args: argparse.Namespace) -> CommandResult:
    from ..adf_work import AdfWorkService

    try:
        result = AdfWorkService(project_from(args)).init_from_adf(
            args.path,
            work_type=args.type,
            title=args.title or "",
            work_id=args.work_id or "",
            claim=not args.no_claim,
            dry_run=args.dry_run,
        )
    except (OSError, ValueError, PermissionError, FileExistsError) as exc:
        return CommandResult.error(str(exc))
    prefix = "[dry-run] would create" if result.dry_run else "Created"
    lines = [
        f"{prefix} {result.work_id} from {result.adf_path}",
        f"  title: {result.title}",
        f"  canvas: {result.canvas_path}",
        f"  requirement: {result.requirement_path}",
    ]
    if result.source_issue:
        lines.append(f"  source issue: {result.source_issue}")
    lines.append(f"  next: {result.next_command}")
    return CommandResult.ok("\n".join(lines))


def run(args: argparse.Namespace) -> CommandResult:
    handlers = {"init-from-adf": _init_from_adf}
    handler = handlers.get(args.work_cmd)
    if handler is None:
        return CommandResult(exit_code=2)
    return handler(args)
