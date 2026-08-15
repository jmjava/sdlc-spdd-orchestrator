"""CLI command handlers for sdlc-engine."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import __version__
from .adf_templates import AdfTemplateLibrary, TemplateError
from .adf_work import AdfWorkService
from .archive import ArchiveService
from .commit_message import CommitMessageError, CommitMessageService
from .context_store import ContextStore
from .db import LocalIndex, format_rows
from .issues import IssueSyncService
from .local_sessions import LocalSessionService
from .pointer import PointerError, PointerStore
from .project import Project
from .registry import TeamRegistry
from .sunset import SunsetError, SunsetService
from .sync_local import LocalSyncService
from .workflow import WorkflowEngine


def _project(args: argparse.Namespace) -> Project:
    return Project.resolve(getattr(args, "root", None))


def cmd_next(args: argparse.Namespace) -> int:
    print(WorkflowEngine(_project(args)).next_text(), end="")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    eng = WorkflowEngine(_project(args))
    if args.json:
        print(eng.status_json(args.work_id))
    else:
        wid = args.work_id or eng.pointer.get() or "(none)"
        print(f"Pointer: {eng.pointer.get() or '(none)'}")
        print(f"Work ID: {wid}")
        if eng.pointer.get() or args.work_id:
            print(eng.status_json(args.work_id))
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    state = WorkflowEngine(_project(args)).resume(args.work_id, phase=args.phase, force=args.force)
    print(f"Resumed {state.work_id} at phase: {state.phase}")
    return 0


def cmd_advance(args: argparse.Namespace) -> int:
    try:
        state = WorkflowEngine(_project(args)).advance(
            to=args.to, force=getattr(args, "force", False)
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Advanced to phase: {state.phase}")
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    eng = WorkflowEngine(_project(args))
    work_id = args.work_id or eng.pointer.get()
    if not work_id:
        print(
            "gate: no Work ID (pass --work-id or set the pointer via claim/resume)",
            file=sys.stderr,
        )
        return 2
    try:
        ok, failures = eng.gate_check(work_id, args.phase)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(
            json.dumps(
                {"work_id": work_id, "phase": args.phase, "ok": ok, "failures": failures},
                indent=2,
            )
        )
    else:
        if ok:
            print(f"gate {args.phase}: OK for {work_id}")
        else:
            print(f"gate {args.phase}: BLOCKED for {work_id}", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
    return 0 if ok else 1


def cmd_skip(args: argparse.Namespace) -> int:
    state = WorkflowEngine(_project(args)).skip(args.phase, reason=args.reason)
    print(f"Skipped {args.phase}; now at {state.phase}")
    return 0


def cmd_shelf(args: argparse.Namespace) -> int:
    project = _project(args)
    eng = WorkflowEngine(project)
    wid = eng.pointer.get()
    if wid and wid.upper().startswith("LOCAL-"):
        session = LocalSessionService(project).shelf(args.reason, session_id=wid)
        print(f"Shelved local session {session.id}: {args.reason}")
        return 0
    state = eng.shelf(reason=args.reason)
    if state is None:
        print("No active pointer to shelf", file=sys.stderr)
        return 1
    print(f"Shelved {state.work_id}: {args.reason}")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    state = WorkflowEngine(_project(args)).sync(args.work_id)
    print(f"Synced {state.work_id} -> phase {state.phase}")
    return 0


def cmd_list_shelved(args: argparse.Namespace) -> int:
    rows = WorkflowEngine(_project(args)).list_shelved()
    if not rows:
        print("(no shelved work)")
        return 0
    for wid, phase, at, reason in rows:
        print(f"{wid}\t{phase}\t{at}\t{reason}")
    return 0


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


def cmd_pointer(args: argparse.Namespace) -> int:
    store = PointerStore(_project(args))
    try:
        if args.pointer_cmd == "get":
            print(store.get())
        elif args.pointer_cmd == "set":
            store.set(args.work_id)
            print(f"pointer set to: {args.work_id}")
        elif args.pointer_cmd == "reset":
            store.reset()
            print("pointer cleared")
        else:
            return 2
    except PointerError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    from .lessons_ledger import LEDGER_KINDS

    store = ContextStore(_project(args))
    action = args.context_cmd
    if action == "persist-lesson":
        body = args.body
        if body == "-":
            body = sys.stdin.read()
        keywords = [k.strip() for k in (args.keywords or "").split(",") if k.strip()]
        result = store.persist_lesson(
            kind=args.kind,
            work_id=args.work_id,
            body=body,
            title=getattr(args, "title", "") or "",
            area=args.area or "",
            source=args.source or "cli",
            phase=args.phase or "",
            keywords=keywords or None,
            accept=bool(getattr(args, "accept", False)),
            project_guide=not args.no_guide,
        )
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
            work_id=args.work_id,
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
                    include_staged=not bool(getattr(args, "no_staged", False)),
                    limit=int(getattr(args, "limit", 50) or 50),
                ),
                indent=2,
            )
        )
        return 0
    if action == "coverage":
        from .db import LocalIndex

        print(json.dumps(LocalIndex(_project(args)).capability_coverage(), indent=2))
        return 0
    if action == "backends":
        from .persistence import load_config, save_config, status_dict

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
        from .guide_client import GuideClient, resolve_guide_base_url
        from .guide_query import format_guide_answer, run_guide_query
        from .persistence import load_config as load_persist_cfg

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
        from .guide_client import GuideClient, resolve_guide_base_url
        from .persistence import load_config as load_persist_cfg

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


def cmd_storage(args: argparse.Namespace) -> int:
    from .storage_migrate import StorageMigration

    mig = StorageMigration(_project(args))
    if args.storage_cmd == "status":
        print(json.dumps(mig.detect(), indent=2))
        return 0
    if args.storage_cmd == "migrate":
        print(json.dumps(mig.run(dry_run=bool(args.dry_run)), indent=2))
        return 0
    return 2


def cmd_agent_context(args: argparse.Namespace) -> int:
    """Upgrade/re-init and quiet-mode helpers for agent-context cleanup."""
    from .agent_context_upgrade import AgentContextUpgrade
    from .quiet import is_quiet, quiet_resume_blurb

    project = _project(args)
    action = args.agent_context_cmd
    if action == "detect":
        print(json.dumps(AgentContextUpgrade(project).detect(), indent=2))
        return 0
    if action == "upgrade":
        result = AgentContextUpgrade(project).run(
            dry_run=bool(args.dry_run),
            rebuild_db=not bool(args.no_rebuild),
        )
        print(json.dumps(result.as_dict(), indent=2))
        return 0 if result.ok else 1
    if action == "quiet-status":
        quiet = is_quiet(project, quiet_flag=bool(getattr(args, "quiet", False)))
        print(
            json.dumps(
                {
                    "quiet": quiet,
                    "blurb": quiet_resume_blurb(guide_live=bool(args.guide_live)),
                    "hot_session_dir": str(project.hot_session_dir()),
                    "current_session": str(project.current_session_path()),
                },
                indent=2,
            )
        )
        return 0
    return 2


def cmd_version(_: argparse.Namespace) -> int:
    print(__version__)
    return 0


def cmd_shell(args: argparse.Namespace) -> int:
    """Bridge to remaining v1 shell scripts under scripts/."""
    root = _project(args).root
    script = root / "scripts" / args.script
    if not script.is_file():
        # also allow bare names that live in scripts/
        candidate = root / "scripts" / f"{args.script}.sh"
        script = candidate if candidate.is_file() else script
    if not script.is_file():
        print(f"shell bridge: script not found: {args.script}", file=sys.stderr)
        return 1
    return subprocess.call([str(script), *args.script_args], cwd=root)


def cmd_links(args: argparse.Namespace) -> int:
    print(LocalSyncService(_project(args)).links_report(args.work_id), end="")
    return 0


def cmd_sync_links(args: argparse.Namespace) -> int:
    svc = LocalSyncService(_project(args))
    work_id = args.work_id or getattr(args, "work_id_pos", None)
    if args.repair:
        actions = svc.repair_links(work_id, dry_run=args.dry_run)
        if not actions:
            print("sync-links: nothing to repair")
        else:
            for a in actions:
                print(a)
        return 0
    findings = svc.check_links(work_id)
    if not findings:
        print("sync-links: no drift detected")
        return 0
    repairable = [f for f in findings if f.repairable]
    manual = [f for f in findings if not f.repairable]
    for f in findings:
        flag = "repairable" if f.repairable else "manual"
        print(f"[{flag}] {f.work_id}: {f.code} — {f.message}")
    if repairable:
        print(
            f"\n{len(findings)} finding(s) ({len(repairable)} repairable). "
            "Re-run with --repair to apply safe fixes."
        )
        return 1
    print(
        f"\n{len(manual)} manual finding(s) (TBD keys / planning gaps). "
        "Use `issues draft|push` or edit milestone ## Jira / ## GitHub."
    )
    return 0


def cmd_sync_roadmap(args: argparse.Namespace) -> int:
    block = LocalSyncService(_project(args)).sync_roadmap(
        roadmap=args.roadmap, dry_run=args.dry_run
    )
    if args.dry_run:
        print(block)
    else:
        print(f"Updated {args.roadmap} SDLC-SPDD summary from canvases.")
    return 0


def cmd_issues(args: argparse.Namespace) -> int:
    svc = IssueSyncService(_project(args))
    action = args.issues_cmd
    if action == "draft":
        fmt = getattr(args, "format", "markdown") or "markdown"
        for draft in svc.draft(args.work_id, system=args.system):
            print(f"=== {draft.system} draft for {draft.work_id} ===")
            print(f"title: {draft.title}")
            print(f"labels: {', '.join(draft.labels) or '-'}")
            if draft.system == "jira":
                print(f"description_format: {draft.extra.get('description_format', 'adf')}")
                if fmt == "adf":
                    print("body (ADF):")
                    print(json.dumps(draft.extra.get("description_adf"), indent=2))
                elif fmt == "wiki":
                    print("body (wiki markup):")
                    print(draft.extra.get("description_wiki") or "")
                else:
                    print("body (markdown — source for ADF/wiki conversion):")
                    print(draft.body)
            else:
                print(f"extra: {draft.extra}")
                print("body:")
                print(draft.body)
            print()
        return 0
    if action == "push":
        if args.system == "both":
            print("issues push requires --system jira|github", file=sys.stderr)
            return 2
        desc_fmt = getattr(args, "description_format", None)
        print(
            svc.push(
                args.work_id,
                args.system,
                apply=args.apply,
                description_format=desc_fmt,
            )
        )
        return 0
    if action == "pull":
        if args.system == "both":
            print("issues pull requires --system jira|github", file=sys.stderr)
            return 2
        print(svc.pull(args.work_id, args.system, apply=args.apply))
        return 0
    if action == "upload-adf":
        issue_key = getattr(args, "issue", None) or args.work_id
        adf_file = getattr(args, "adf_file", None)
        if not adf_file:
            print("issues upload-adf requires --file PATH", file=sys.stderr)
            return 2
        print(
            svc.upload_adf(
                issue_key,
                Path(adf_file),
                apply=args.apply,
                description_format=getattr(args, "description_format", None),
            )
        )
        return 0
    if action == "download-adf":
        issue_key = getattr(args, "issue", None) or args.work_id
        adf_file = getattr(args, "adf_file", None)
        print(
            svc.download_adf(
                issue_key,
                adf_path=Path(adf_file) if adf_file else None,
                apply=args.apply,
            )
        )
        return 0
    if action == "link":
        jira_key = getattr(args, "jira_key", None) or ""
        if not jira_key:
            print("issues link requires JIRA-KEY positional argument", file=sys.stderr)
            return 2
        result = svc.link_jira_local(
            args.work_id,
            jira_key,
            summary=getattr(args, "summary", None) or None,
            issue_type=getattr(args, "issue_type", None) or None,
            apply=args.apply,
        )
        for line in result.get("actions") or []:
            print(line)
        if not args.apply:
            print("\nRe-run with --apply to write local links.")
        return 0
    return 2


def cmd_commit_message(args: argparse.Namespace) -> int:
    svc = CommitMessageService(_project(args))
    try:
        if args.json:
            print(
                svc.report_json(
                    base=args.base,
                    work_id=args.work_id or "",
                    hint=args.hint or "",
                    max_diff_chars=args.max_diff,
                ),
                end="",
            )
        else:
            print(
                svc.report_text(
                    base=args.base,
                    work_id=args.work_id or "",
                    hint=args.hint or "",
                    max_diff_chars=args.max_diff,
                ),
                end="",
            )
    except CommitMessageError as exc:
        print(f"commit-message: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_sunset(args: argparse.Namespace) -> int:
    svc = SunsetService(_project(args))
    try:
        if args.json:
            print(
                svc.report_json(
                    args.work_id or None,
                    apply=bool(args.apply),
                    accept=bool(args.accept),
                ),
                end="",
            )
        else:
            print(
                svc.report_text(
                    args.work_id or None,
                    apply=bool(args.apply),
                    accept=bool(args.accept),
                ),
                end="",
            )
    except SunsetError as exc:
        print(f"sunset: {exc}", file=sys.stderr)
        return 1
    return 0


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
    print(f"Brief: .sdlc/current-local-session.md")
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
        from .viewer.app import run_viewer
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
        from .installer.app import run_installer
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
        from .installer.playground import materialize_playground

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
