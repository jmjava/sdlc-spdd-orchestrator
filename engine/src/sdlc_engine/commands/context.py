"""Context store, session bridge, and lessons ledger commands."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from ..context_store import ContextStore

from .state import _project


def cmd_context(args: argparse.Namespace) -> int:
    from ..lessons_ledger import LEDGER_KINDS

    store = ContextStore(_project(args))
    action = args.context_cmd
    if action == "persist-lesson":
        body = args.body
        if body == "-":
            body = sys.stdin.read()
        work_id = getattr(args, "work_id", "") or ""
        area = getattr(args, "area", "") or ""
        if not work_id and not area:
            print("persist-lesson: --work-id or --area is required", file=sys.stderr)
            return 2
        keywords = [k.strip() for k in (args.keywords or "").split(",") if k.strip()]
        try:
            result = store.persist_lesson(
                kind=args.kind,
                work_id=work_id,
                body=body,
                title=getattr(args, "title", "") or "",
                area=area,
                source=args.source or "cli",
                phase=args.phase or "",
                keywords=keywords or None,
                accept=bool(getattr(args, "accept", False)),
                project_guide=not args.no_guide,
                readiness=getattr(args, "readiness", "") or None,
                review_result=getattr(args, "review_result", "") or None,
                rework=getattr(args, "rework", None),
                context_files=getattr(args, "context_files", None),
                validate_cycles=getattr(args, "validate_cycles", None),
                review_cycles=getattr(args, "review_cycles", None),
            )
        except ValueError as exc:
            print(f"persist-lesson: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result.as_dict(), indent=2))
        return 0 if result.git.get("ok") else 1
    if action == "persist-entry":
        print(
            "warning: persist-entry is deprecated; use context persist-lesson",
            file=sys.stderr,
        )
        body = args.body
        if body == "-":
            body = sys.stdin.read()
        result = store.persist_lesson(
            kind=args.kind if args.kind in LEDGER_KINDS else "decision",
            work_id=getattr(args, "work_id", "") or "",
            body=body,
            area=args.area or "",
            source=args.source or "cli",
            phase=args.phase or "",
            project_guide=not args.no_guide,
        )
        print(json.dumps(result.as_dict(), indent=2))
        return 0 if result.git.get("ok") else 1
    if action == "accept":
        out = store.accept(
            work_id=getattr(args, "work_id", "") or "",
            ids=[i.strip() for i in (getattr(args, "ids", "") or "").split(",") if i.strip()]
            or None,
            discard_rest=bool(getattr(args, "discard_rest", False)),
            project_guide=not getattr(args, "no_guide", False),
        )
        print(json.dumps(out, indent=2))
        return 0
    if action == "show":
        rec = store.show(args.record_id)
        if rec is None:
            print(json.dumps({"error": "not found", "id": args.record_id}, indent=2))
            return 1
        print(json.dumps(rec, indent=2))
        return 0
    if action == "parity":
        out = store.parity(repair=bool(getattr(args, "repair", False)))
        print(json.dumps(out, indent=2))
        return 0 if out.get("ok") else 1
    if action == "digest":
        areas = [a.strip() for a in (getattr(args, "areas", "") or "").split(",") if a.strip()]
        keywords = [k.strip() for k in (getattr(args, "keywords", "") or "").split(",") if k.strip()]
        print(
            json.dumps(
                store.digest(
                    work_id=getattr(args, "work_id", "") or "",
                    areas=areas or None,
                    keywords=keywords or None,
                    limit=int(getattr(args, "limit", 8) or 8),
                ),
                indent=2,
            )
        )
        return 0
    if action == "retrieve":
        print(
            json.dumps(
                store.retrieve(
                    work_id=args.work_id or "",
                    area=args.area or "",
                    kind=getattr(args, "kind", "") or "",
                    keyword=getattr(args, "keyword", "") or "",
                    query=getattr(args, "query", "") or "",
                    rank=getattr(args, "rank", "") or "",
                    include_staged=not bool(getattr(args, "no_staged", False)),
                    limit=int(getattr(args, "limit", 50) or 50),
                ),
                indent=2,
            )
        )
        return 0
    if action == "eval-retrieve":
        from pathlib import Path

        from ..retrieve import load_and_evaluate

        fixture = Path(args.fixture)
        if not fixture.is_file():
            print(f"eval-retrieve: fixture not found: {fixture}", file=sys.stderr)
            return 2
        print(json.dumps(load_and_evaluate(fixture), indent=2))
        return 0
    if action == "metrics":
        try:
            payload = store.metrics_query(
                construct=getattr(args, "construct", "") or "",
                work_id=getattr(args, "work_id", "") or "",
                phase=getattr(args, "phase", "") or "",
                include_staged=not bool(getattr(args, "no_staged", False)),
            )
        except ValueError as exc:
            print(f"metrics: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(payload, indent=2))
        return 0
    if action == "coverage":
        from ..db import LocalIndex

        print(json.dumps(LocalIndex(_project(args)).capability_coverage(), indent=2))
        return 0
    if action == "backends":
        from ..persistence import load_config, save_config, status_dict

        project = _project(args)
        if getattr(args, "set_backends", None) is not None:
            raw = str(args.set_backends or "").strip()
            if not raw:
                print("error: --set requires a non-empty backend list", file=sys.stderr)
                return 2
            backends = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
            cfg = load_config(project)
            cfg["backends"] = backends
            if getattr(args, "guide_base_url", None):
                cfg["guide_base_url"] = args.guide_base_url
            if getattr(args, "notes", None) is not None:
                cfg["notes"] = args.notes
            try:
                print(json.dumps(save_config(project, cfg), indent=2))
            except ValueError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 2
            return 0
        print(json.dumps(status_dict(project), indent=2))
        return 0
    if action == "guide-query":
        from ..guide_client import GuideClient, resolve_guide_base_url
        from ..guide_query import format_guide_answer, run_guide_query
        from ..persistence import load_config as load_persist_cfg

        project = _project(args)
        cfg = load_persist_cfg(project)
        base = resolve_guide_base_url(
            explicit=getattr(args, "guide_url", None) or None,
            project_url=str(cfg.get("guide_base_url") or ""),
        )
        client = GuideClient(base, timeout=float(getattr(args, "timeout", 30) or 30))
        tool_args = {}
        if getattr(args, "tool_json", None):
            tool_args = json.loads(args.tool_json)
        try:
            payload = run_guide_query(
                client,
                work_id=getattr(args, "work_id", "") or "",
                area=getattr(args, "area", "") or "",
                lesson_id=getattr(args, "lesson_id", "") or "",
                label=getattr(args, "label", "") or "",
                question=getattr(args, "question", "") or "",
                stats=bool(getattr(args, "stats", False)),
                tool=getattr(args, "tool", "") or "",
                tool_args=tool_args,
                limit=int(getattr(args, "limit", 20) or 20),
            )
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if getattr(args, "text", False):
            print(format_guide_answer(payload))
        else:
            print(json.dumps(payload, indent=2))
        return 0 if payload.get("ok") else 1
    if action == "mcp-call":
        from ..guide_client import GuideClient, resolve_guide_base_url
        from ..persistence import load_config as load_persist_cfg

        project = _project(args)
        cfg = load_persist_cfg(project)
        base = resolve_guide_base_url(
            explicit=getattr(args, "guide_url", None) or None,
            project_url=str(cfg.get("guide_base_url") or ""),
        )
        client = GuideClient(base, timeout=float(getattr(args, "timeout", 30) or 30))
        tool = str(getattr(args, "tool", "") or "").strip()
        if not tool:
            print("error: --tool required (spdd_workSubgraph, …)", file=sys.stderr)
            return 2
        raw = getattr(args, "json", None) or getattr(args, "tool_json", None) or "{}"
        try:
            arguments = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"error: invalid JSON arguments: {exc}", file=sys.stderr)
            return 2
        payload = client.call_mcp_tool(tool, arguments)
        print(json.dumps(payload, indent=2))
        return 0 if payload.get("ok") else 1
    return 2


def cmd_start(args: argparse.Namespace) -> int:
    from ..session import SessionService

    return SessionService(_project(args)).start(
        work_id=getattr(args, "work_id", "") or "", phase=getattr(args, "phase", "") or ""
    )


def cmd_capture(args: argparse.Namespace) -> int:
    from ..session import SessionService

    return SessionService(_project(args)).capture(
        list(args.script_args or []),
        work_id=getattr(args, "work_id", "") or "",
        phase=getattr(args, "phase", "") or "",
    )


def cmd_complete(args: argparse.Namespace) -> int:
    from ..session import SessionService

    return SessionService(_project(args)).complete(list(args.script_args or []))


def cmd_accept(args: argparse.Namespace) -> int:
    """Promote staged lessons to the committed ledger (optionally git-commit it)."""

    from ..lessons_ledger import LessonsLedger

    project = _project(args)
    ledger = LessonsLedger(project)
    if getattr(args, "list", False):
        staged = [r for r in ledger.records(include_staged=True) if r.id in ledger.staged_ids()]
        if not staged:
            print("No staged records.")
            return 0
        for rec in staged:
            print(f"{rec.id}\t{rec.kind}\t{rec.work_id}\t{rec.title}")
        return 0
    store = ContextStore(project)
    out = store.accept(
        work_id=getattr(args, "work_id", "") or "",
        ids=[i.strip() for i in (getattr(args, "ids", "") or "").split(",") if i.strip()] or None,
        discard_rest=bool(getattr(args, "discard_rest", False)),
        project_guide=not getattr(args, "no_guide", False),
    )
    print(json.dumps(out, indent=2))
    count = int(out.get("accepted_count", 0) or 0)
    if getattr(args, "commit", False):
        if count == 0 or not project.ledger_path.is_file():
            print("Nothing to commit (no records promoted).")
            return 0
        rel = project.rel(project.ledger_path)
        wid = getattr(args, "work_id", "") or "all"
        subprocess.check_call(["git", "-C", str(project.root), "add", rel])
        subprocess.check_call(["git", "-C", str(project.root), "commit", "-m", f"memory: accept {count} lessons for {wid}"])
        print(f"Committed {rel}")
    return 0


def cmd_session(args: argparse.Namespace) -> int:
    """Engine callbacks for the shell session scripts (one workflow implementation)."""
    from ..session import SessionService, jira_ask_prompt, jira_status

    project = _project(args)
    svc = SessionService(project)
    action = args.session_cmd
    wid = getattr(args, "work_id", "") or ""
    if action == "brief":
        print(svc.brief_markdown(wid), end="")
        return 0
    if action == "touch":
        svc.touch_session(wid, args.phase, getattr(args, "milestone", "") or "")
        return 0
    if action == "record-capture":
        svc.record_capture(wid, getattr(args, "phase", "") or "resume")
        return 0
    if action == "recommend":
        print(svc.recommend(wid, args.phase, getattr(args, "operation", "") or ""))
        return 0
    if action == "jira-status":
        print(jira_status(project, wid))
        return 0
    if action == "jira-ask":
        text = jira_ask_prompt(project, wid)
        if text:
            print(text)
        return 0
    return 2
