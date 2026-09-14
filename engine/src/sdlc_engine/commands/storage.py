"""SQLite index, local sessions, work items, viewer, installer, templates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from ..adf_templates import AdfTemplateLibrary, TemplateError
from ..adf_work import AdfWorkService
from ..db import LocalIndex, format_rows
from ..local_sessions import LocalSessionService

from .state import _project


def cmd_db(args: argparse.Namespace) -> int:
    idx = LocalIndex(_project(args))
    action = args.db_cmd
    if action == "rebuild":
        print(idx.rebuild().as_text(), end="")
        return 0
    if action == "status":
        print(idx.status_text(), end="")
        return 0
    if action == "path":
        print(idx.db_path)
        return 0
    if action == "query":
        if args.sql:
            rows = idx.query_sql(args.sql)
        else:
            rows = idx.find(
                work_id=args.work_id or "",
                status=args.status or "",
                search=args.search or "",
                limit=args.limit,
            )
        cols = args.columns.split(",") if args.columns else None
        if cols:
            cols = [c.strip() for c in cols if c.strip()]
        if args.json:
            print(json.dumps(rows, indent=2))
        else:
            print(format_rows(rows, cols), end="")
        return 0
    if action == "lookup":
        work_id = (args.work_id or "").strip()
        if not work_id:
            print("db lookup: --work-id is required", file=sys.stderr)
            return 2
        search = args.search or ""
        if args.markdown:
            print(
                idx.lookup_markdown(
                    work_id,
                    search=search,
                    search_limit=args.limit,
                ),
                end="",
            )
        else:
            print(
                json.dumps(
                    idx.lookup(
                        work_id,
                        search=search,
                        search_limit=args.limit,
                    ),
                    indent=2,
                )
            )
        return 0
    if action == "export":
        out = Path(args.output) if args.output else None
        if args.format == "sql":
            text = idx.export_sql(out)
        else:
            text = idx.export_json(out)
        if out:
            print(f"Wrote {args.format} export to {out}")
        else:
            print(text, end="")
        return 0
    return 2


def cmd_quick(args: argparse.Namespace) -> int:
    """Zero-ceremony LOCAL-* session start (alias for local start)."""
    intent = (args.intent or "").strip()
    if not intent:
        print("quick requires an intent string", file=sys.stderr)
        return 2
    svc = LocalSessionService(_project(args))
    session = svc.start(intent=intent, title=intent)
    print(f"Started local session {session.id}")
    print(f"Pointer set. Artifacts: .sdlc/local-sessions/{session.id}/")
    print("Brief: .sdlc/current-local-session.md")
    print("This work stays offline until: ./scripts/sdlc.sh local promote --type feature --name \"...\"")
    return 0


def cmd_local(args: argparse.Namespace) -> int:
    svc = LocalSessionService(_project(args))
    action = args.local_cmd
    if action == "start":
        session = svc.start(
            name=args.name or "",
            title=args.title or "",
            intent=args.intent or "",
            branch=args.branch or "",
        )
        print(f"Started local session {session.id}")
        print(f"Pointer set. Artifacts: .sdlc/local-sessions/{session.id}/")
        print("This work stays offline until: ./scripts/sdlc.sh local promote --type feature --name \"...\"")
        return 0
    if action == "list":
        print(svc.list_text(include_closed=args.all), end="")
        return 0
    if action == "status":
        print(svc.status_text(args.session), end="")
        return 0
    if action == "capture":
        session = svc.capture(args.summary, session_id=args.session)
        print(f"Captured into {session.id}")
        return 0
    if action == "shelf":
        session = svc.shelf(args.reason, session_id=args.session)
        print(f"Shelved local session {session.id}: {args.reason}")
        return 0
    if action == "resume":
        session = svc.resume(args.session_id)
        print(f"Resumed local session {session.id}")
        return 0
    if action == "abandon":
        session = svc.abandon(session_id=args.session, force=args.force)
        print(f"Abandoned local session {session.id}")
        return 0
    if action == "promote":
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
            print(f"[dry-run] would promote {session.id} -> {work_id}")
            return 0
        print(f"Promoted {session.id} -> {work_id}")
        print(f"  canvas: spdd/canvas/{work_id}.md")
        print(f"  requirement: requirements/milestones/{work_id}.md")
        if not args.no_claim:
            print(f"Claimed {work_id} — commit spdd/memory/registry.jsonl when sharing.")
        return 0
    return 2


def cmd_work(args: argparse.Namespace) -> int:
    """Work helpers that are engine-backed (init from ADF, etc.)."""
    action = args.work_cmd
    if action == "init-from-adf":
        svc = AdfWorkService(_project(args))
        try:
            result = svc.init_from_adf(
                args.path,
                work_type=args.type,
                title=args.title or "",
                work_id=args.work_id or "",
                claim=not args.no_claim,
                dry_run=args.dry_run,
            )
        except (OSError, ValueError, PermissionError, FileExistsError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        prefix = "[dry-run] would create" if result.dry_run else "Created"
        print(f"{prefix} {result.work_id} from {result.adf_path}")
        print(f"  title: {result.title}")
        print(f"  canvas: {result.canvas_path}")
        print(f"  requirement: {result.requirement_path}")
        if result.source_issue:
            print(f"  source issue: {result.source_issue}")
        print(f"  next: {result.next_command}")
        return 0
    return 2


def cmd_viewer(args: argparse.Namespace) -> int:
    """Launch the ADF WYSIWYG viewer (binds localhost by default)."""
    try:
        from ..viewer.app import run_viewer
    except ImportError as exc:
        print(
            "viewer requires Flask. Install with: python3 -m pip install -e './engine[viewer]'",
            file=sys.stderr,
        )
        print(str(exc), file=sys.stderr)
        return 1
    project = _project(args)
    host = "0.0.0.0" if getattr(args, "lan", False) else args.host
    run_viewer(project.root, host=host, port=args.port, debug=bool(args.debug))
    return 0


def cmd_installer(args: argparse.Namespace) -> int:
    """Launch the ops console (install/upgrade, SQLite, rollback, Guide)."""
    try:
        from ..installer.app import run_installer
    except ImportError as exc:
        print(
            "installer/console requires Flask. Install with: "
            "python3 -m pip install -e './engine[viewer]'",
            file=sys.stderr,
        )
        print(str(exc), file=sys.stderr)
        return 1
    project = _project(args)
    host = "0.0.0.0" if getattr(args, "lan", False) else args.host
    target = getattr(args, "target", None) or str(project.root)
    if getattr(args, "playground", False):
        from ..installer.playground import materialize_playground

        dest = materialize_playground(getattr(args, "playground_dir", None))
        print(f"Playground seeded at {dest}")
        target = str(dest)
    run_installer(
        target,
        host=host,
        port=args.port,
        debug=bool(args.debug),
        open_browser=not bool(getattr(args, "no_browser", False)),
    )
    return 0


def cmd_template(args: argparse.Namespace) -> int:
    """List / render / validate ADF template combos."""
    lib = AdfTemplateLibrary()
    action = args.template_cmd
    try:
        if action == "list":
            combos = [c.to_dict() for c in lib.list_combos()]
            if args.json:
                print(json.dumps({"ok": True, "combos": combos}, indent=2))
            else:
                for c in combos:
                    parts = ",".join(c["parts"])
                    print(f"{c['id']}\t{c['title']}\tparts={parts}")
            return 0
        if action == "validate":
            combos = lib.list_combos()
            errors: list[str] = []
            for combo in combos:
                try:
                    lib.load_combo(combo.id)
                except TemplateError as exc:
                    errors.append(str(exc))
            # Also validate stock schemas exist and accept a trivial doc
            try:
                sample = {"type": "doc", "version": 1, "content": [{"type": "paragraph"}]}
                schema_errs = lib.validate_adf(sample)
                errors.extend(schema_errs)
            except TemplateError as exc:
                errors.append(str(exc))
            if errors:
                print(json.dumps({"ok": False, "errors": errors}, indent=2))
                return 1
            print(json.dumps({"ok": True, "combos": len(combos)}, indent=2))
            return 0
        if action == "render":
            project = _project(args)
            work_id = (args.work_id or "").strip()
            if not work_id:
                print("template render requires --work-id", file=sys.stderr)
                return 1
            combo_id = (args.combo or "").strip() or lib.suggest_combo(
                work_id, getattr(args, "type", "") or ""
            )
            result = lib.render(
                project,
                work_id,
                combo_id,
                work_type=getattr(args, "type", "") or "",
                output=args.output,
            )
            if args.json:
                print(json.dumps(result.to_dict(), indent=2))
            elif args.output:
                print(result.output_path)
            else:
                print(json.dumps(result.adf, indent=2))
            return 0
    except (TemplateError, FileNotFoundError, OSError) as exc:
        print(f"sdlc-engine template: {exc}", file=sys.stderr)
        return 1
    print(f"unknown template command: {action}", file=sys.stderr)
    return 1
