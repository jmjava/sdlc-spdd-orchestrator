"""sdlc-engine db."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    db = sub.add_parser("db", help="Local regenerable SQLite index (query cache before GUIDE/Neo4j)")
    db_sub = db.add_subparsers(dest="db_cmd", required=True)
    db_sub.add_parser("rebuild", help="Rebuild .sdlc/index.sqlite from repo artifacts").set_defaults(func=run)
    db_sub.add_parser("status", help="Show index path, counts, rebuild metadata").set_defaults(func=run)
    db_sub.add_parser("path", help="Print absolute path to the SQLite file").set_defaults(func=run)
    dq = db_sub.add_parser("query", help="Query work_items (filters or read-only SQL SELECT)")
    dq.add_argument("sql", nargs="?", help="Optional SELECT … (read-only)")
    dq.add_argument("--work-id")
    dq.add_argument("--status", help="Match registry_status, canvas_status, or final_status")
    dq.add_argument("--search", help="Full-text (FTS5) or LIKE search")
    dq.add_argument("--limit", type=int, default=50)
    dq.add_argument("--columns", help="Comma-separated columns for table output")
    dq.add_argument("--json", action="store_true")
    dq.set_defaults(func=run)
    dl = db_sub.add_parser("lookup", help="Machine-readable Work ID snapshot for session briefs (JSON or markdown)")
    dl.add_argument("--work-id", required=True, help="Work ID to look up")
    dl.add_argument("--search", default="", help="Optional related FTS/LIKE hits")
    dl.add_argument("--limit", type=int, default=5, help="Max related search hits (default: 5)")
    dl.add_argument("--markdown", action="store_true", help="Emit markdown section for embedding into a session brief")
    dl.add_argument("--json", action="store_true", help="Emit JSON (default when --markdown is not set)")
    dl.set_defaults(func=run)
    de = db_sub.add_parser("export", help="Export index as JSON or SQL dump (not for live multi-user sync)")
    de.add_argument("--format", choices=["json", "sql"], default="json")
    de.add_argument("--output", "-o", help="Write to file (default: stdout)")
    de.set_defaults(func=run)


def _rebuild(idx, _args: argparse.Namespace) -> CommandResult:
    return CommandResult.raw(idx.rebuild().as_text())


def _status(idx, _args: argparse.Namespace) -> CommandResult:
    return CommandResult.raw(idx.status_text())


def _path(idx, _args: argparse.Namespace) -> CommandResult:
    return CommandResult.ok(str(idx.db_path))


def _query(idx, args: argparse.Namespace) -> CommandResult:
    from ..db import format_rows

    rows = idx.query_sql(args.sql) if args.sql else idx.find(
        work_id=args.work_id or "",
        status=args.status or "",
        search=args.search or "",
        limit=args.limit,
    )
    cols = [c.strip() for c in args.columns.split(",") if c.strip()] if args.columns else None
    if args.json:
        return CommandResult.ok(json.dumps(rows, indent=2))
    return CommandResult.raw(format_rows(rows, cols))


def _lookup(idx, args: argparse.Namespace) -> CommandResult:
    work_id = (args.work_id or "").strip()
    if not work_id:
        return CommandResult.error("db lookup: --work-id is required", code=2)
    search = args.search or ""
    if args.markdown:
        return CommandResult.raw(idx.lookup_markdown(work_id, search=search, search_limit=args.limit))
    return CommandResult.ok(json.dumps(idx.lookup(work_id, search=search, search_limit=args.limit), indent=2))


def _export(idx, args: argparse.Namespace) -> CommandResult:
    out = Path(args.output) if args.output else None
    text = idx.export_sql(out) if args.format == "sql" else idx.export_json(out)
    if out:
        return CommandResult.ok(f"Wrote {args.format} export to {out}")
    return CommandResult.raw(text)


def run(args: argparse.Namespace) -> CommandResult:
    from ..db import LocalIndex

    idx = LocalIndex(project_from(args))
    handlers = {
        "rebuild": _rebuild,
        "status": _status,
        "path": _path,
        "query": _query,
        "lookup": _lookup,
        "export": _export,
    }
    handler = handlers.get(args.db_cmd)
    if handler is None:
        return CommandResult(exit_code=2)
    return handler(idx, args)
