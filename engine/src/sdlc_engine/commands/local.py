"""sdlc-engine local."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    loc = sub.add_parser("local", help="Local/offline work sessions (machine-private until promoted)")
    loc_sub = loc.add_subparsers(dest="local_cmd", required=True)
    ls = loc_sub.add_parser("start", help="Start a LOCAL-* offline session and set pointer")
    ls.add_argument("--name", help="Slug fragment (default from title/intent)")
    ls.add_argument("--title", help="Human title")
    ls.add_argument("--intent", help="One-line why this scratch work exists")
    ls.add_argument("--branch", help="Optional git branch name note")
    ls.set_defaults(func=run)
    ll = loc_sub.add_parser("list", help="List local/offline sessions on this machine")
    ll.add_argument("--all", action="store_true", help="Include promoted/abandoned")
    ll.set_defaults(func=run)
    lst = loc_sub.add_parser("status", help="Show active or named local session")
    lst.add_argument("--session", help="LOCAL-* id (default: pointer)")
    lst.set_defaults(func=run)
    lc = loc_sub.add_parser("capture", help="Append a note into the local session")
    lc.add_argument("--summary", required=True)
    lc.add_argument("--session")
    lc.set_defaults(func=run)
    lsh = loc_sub.add_parser("shelf", help="Park a local session (clear pointer)")
    lsh.add_argument("--reason", default="manual shelf")
    lsh.add_argument("--session")
    lsh.set_defaults(func=run)
    lr = loc_sub.add_parser("resume", help="Resume a shelved local session")
    lr.add_argument("session_id")
    lr.set_defaults(func=run)
    la = loc_sub.add_parser("abandon", help="Mark a local session abandoned")
    la.add_argument("--session")
    la.add_argument("--force", action="store_true")
    la.set_defaults(func=run)
    lp = loc_sub.add_parser("promote", help="Promote LOCAL session into a documented Work ID (canvas + requirement)")
    lp.add_argument("--type", default="feature", help="feature|spike|bug|refactor|chore|...")
    lp.add_argument("--name", help="Title/slug for the new Work ID (default: session title)")
    lp.add_argument("--session")
    lp.add_argument("--milestone", help="Optional milestone-*.md to append Linked Work")
    lp.add_argument("--no-claim", action="store_true", help="Create artifacts without claiming")
    lp.add_argument("--dry-run", action="store_true")
    lp.add_argument("--from-git", help="Backfill session notes from git log range before promote (e.g. main..HEAD)")
    lp.set_defaults(func=run)


def _start(svc, args: argparse.Namespace) -> CommandResult:
    session = svc.start(
        name=args.name or "",
        title=args.title or "",
        intent=args.intent or "",
        branch=args.branch or "",
    )
    return CommandResult.ok(
        f"Started local session {session.id}\n"
        f"Pointer set. Artifacts: .sdlc/local-sessions/{session.id}/\n"
        'This work stays offline until: ./scripts/sdlc.sh local promote --type feature --name "..."'
    )


def _promote(svc, args: argparse.Namespace) -> CommandResult:
    session, work_id = svc.promote(
        work_type=args.type,
        name=args.name or "",
        session_id=args.session,
        milestone=args.milestone or "",
        claim=not args.no_claim,
        dry_run=args.dry_run,
        from_git=args.from_git or "",
    )
    if args.dry_run:
        return CommandResult.ok(f"[dry-run] would promote {session.id} -> {work_id}")
    lines = [
        f"Promoted {session.id} -> {work_id}",
        f"  canvas: spdd/canvas/{work_id}.md",
        f"  requirement: requirements/milestones/{work_id}.md",
    ]
    if not args.no_claim:
        lines.append(f"Claimed {work_id} — commit spdd/memory/registry.jsonl when sharing.")
    return CommandResult.ok("\n".join(lines))


def _list(svc, args: argparse.Namespace) -> CommandResult:
    return CommandResult.raw(svc.list_text(include_closed=args.all))


def _status(svc, args: argparse.Namespace) -> CommandResult:
    return CommandResult.raw(svc.status_text(args.session))


def _capture(svc, args: argparse.Namespace) -> CommandResult:
    session = svc.capture(args.summary, session_id=args.session)
    return CommandResult.ok(f"Captured into {session.id}")


def _shelf(svc, args: argparse.Namespace) -> CommandResult:
    session = svc.shelf(args.reason, session_id=args.session)
    return CommandResult.ok(f"Shelved local session {session.id}: {args.reason}")


def _resume(svc, args: argparse.Namespace) -> CommandResult:
    session = svc.resume(args.session_id)
    return CommandResult.ok(f"Resumed local session {session.id}")


def _abandon(svc, args: argparse.Namespace) -> CommandResult:
    session = svc.abandon(session_id=args.session, force=args.force)
    return CommandResult.ok(f"Abandoned local session {session.id}")


def run(args: argparse.Namespace) -> CommandResult:
    from ..local_sessions import LocalSessionService

    svc = LocalSessionService(project_from(args))
    handlers = {
        "start": _start,
        "list": _list,
        "status": _status,
        "capture": _capture,
        "shelf": _shelf,
        "resume": _resume,
        "abandon": _abandon,
        "promote": _promote,
    }
    handler = handlers.get(args.local_cmd)
    if handler is None:
        return CommandResult(exit_code=2)
    return handler(svc, args)
