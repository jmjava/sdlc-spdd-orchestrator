"""CLI entrypoint: sdlc-engine / python -m sdlc_engine."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import __version__
from .archive import ArchiveService
from .commit_message import CommitMessageError, CommitMessageService
from .context_store import ContextStore
from .db import LocalIndex, format_rows
from .issues import IssueSyncService
from .adf_templates import AdfTemplateLibrary, TemplateError
from .adf_work import AdfWorkService
from .local_sessions import LocalSessionService
from .pointer import PointerError, PointerStore
from .project import Project
from .registry import TeamRegistry
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
    import sys

    from .lessons_ledger import LEDGER_KINDS

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


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-engine",
        description="SDLC-SPDD Python orchestration engine (v2)",
    )
    p.add_argument("--root", help="Project root (default: SDLC_ROOT or git toplevel)")
    p.add_argument("--version", action="store_true", help="Print engine version")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("next", help="Show what to do now").set_defaults(func=cmd_next)

    qk = sub.add_parser(
        "quick",
        help='Start a LOCAL-* offline session from intent (zero ceremony)',
    )
    qk.add_argument("intent", help='One-line why this scratch work exists')
    qk.set_defaults(func=cmd_quick)

    st = sub.add_parser("status", help="Show workflow status")
    st.add_argument("--json", action="store_true")
    st.add_argument("--work-id")
    st.set_defaults(func=cmd_status)

    rs = sub.add_parser("resume", help="Resume a Work ID")
    rs.add_argument("work_id")
    rs.add_argument("--phase")
    rs.add_argument("--force", action="store_true")
    rs.set_defaults(func=cmd_resume)

    adv = sub.add_parser("advance", help="Advance workflow phase (gated; --force bypasses)")
    adv.add_argument("--to")
    adv.add_argument(
        "--force",
        action="store_true",
        help="Bypass gate checks (a human decision, never the agent's)",
    )
    adv.set_defaults(func=cmd_advance)

    gt = sub.add_parser(
        "gate",
        help="Check prerequisites to enter a phase (exit 0 ok / 1 blocked)",
    )
    gt.add_argument("--phase", required=True)
    gt.add_argument("--work-id", help="Work ID (default: active pointer)")
    gt.add_argument("--json", action="store_true")
    gt.set_defaults(func=cmd_gate)

    sk = sub.add_parser("skip", help="Skip a phase")
    sk.add_argument("phase")
    sk.add_argument("--reason", default="manual skip")
    sk.set_defaults(func=cmd_skip)

    sh = sub.add_parser("shelf", help="Shelf active work")
    sh.add_argument("--reason", default="manual shelf")
    sh.set_defaults(func=cmd_shelf)

    sy = sub.add_parser("sync", help="Sync workflow state from artifacts")
    sy.add_argument("--work-id")
    sy.set_defaults(func=cmd_sync)

    sub.add_parser("list-shelved", help="List shelved work").set_defaults(func=cmd_list_shelved)

    cl = sub.add_parser("claim", help="Claim a Work ID")
    cl.add_argument("work_id")
    cl.add_argument("--force", action="store_true")
    cl.add_argument("--phase")
    cl.add_argument("--branch")
    cl.add_argument("--pr")
    cl.add_argument("--jira", help="Override; default auto-reads ## Jira Key from milestone requirement")
    cl.add_argument("--note")
    cl.set_defaults(func=cmd_claim)

    lk = sub.add_parser("links", help="Show Jira/GitHub/registry/canvas link map")
    lk.add_argument("work_id", nargs="?")
    lk.set_defaults(func=cmd_links)

    sl = sub.add_parser(
        "sync-links",
        help="Check or repair drift across milestones, canvas Metadata, and registry",
    )
    sl.add_argument("work_id_pos", nargs="?", help="Optional Work ID (same as --work-id)")
    sl.add_argument("--work-id")
    sl.add_argument("--repair", action="store_true")
    sl.add_argument("--dry-run", action="store_true")
    sl.set_defaults(func=cmd_sync_links)

    sr = sub.add_parser("sync-roadmap", help="Refresh ROADMAP.md managed summary from canvases")
    sr.add_argument("--roadmap", default="ROADMAP.md")
    sr.add_argument("--dry-run", action="store_true")
    sr.set_defaults(func=cmd_sync_roadmap)

    iss = sub.add_parser(
        "issues",
        help=(
            "Draft/push/pull/link/upload-adf/download-adf for Jira or GitHub "
            "(explicit CLI; never auto-sync)"
        ),
    )
    iss.add_argument(
        "issues_cmd",
        choices=["draft", "push", "pull", "link", "upload-adf", "download-adf"],
    )
    iss.add_argument(
        "work_id",
        help=(
            "Work ID for draft/push/pull/link, Jira key for link second arg, "
            "or Jira issue key for upload-adf/download-adf"
        ),
    )
    iss.add_argument(
        "jira_key",
        nargs="?",
        default=None,
        help="For link: manually created Jira issue key (PROJECT-123)",
    )
    iss.add_argument(
        "--system",
        default="both",
        choices=["jira", "github", "both"],
        help="Target system (push/pull require jira|github)",
    )
    iss.add_argument(
        "--format",
        default="markdown",
        choices=["markdown", "adf", "wiki"],
        help="For `issues draft --system jira`: render body as markdown, ADF JSON, or wiki markup",
    )
    iss.add_argument(
        "--description-format",
        choices=["adf", "wiki"],
        default=None,
        help=(
            "For push/upload-adf: send raw ADF (default on Cloud v3) or run the "
            "optional ADF→wiki shim. Env: JIRA_DESCRIPTION_FORMAT. "
            "Auto-fallback ADF→wiki is off unless JIRA_DESCRIPTION_FALLBACK=1."
        ),
    )
    iss.add_argument(
        "--file",
        dest="adf_file",
        help="For upload-adf/download-adf: path to ADF JSON file",
    )
    iss.add_argument(
        "--issue",
        help=(
            "For upload-adf/download-adf: Jira issue key "
            "(defaults to work_id positional)"
        ),
    )
    iss.add_argument(
        "--summary",
        default=None,
        help="For link: optional local Summary bullet",
    )
    iss.add_argument(
        "--issue-type",
        dest="issue_type",
        default=None,
        help="For link: optional local Issue type bullet",
    )
    iss.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Actually create/update remote issue, write pulled milestone fields, "
            "or overwrite local ADF on download-adf (default is dry-run)"
        ),
    )
    iss.set_defaults(func=cmd_issues)

    loc = sub.add_parser(
        "local",
        help="Local/offline work sessions (machine-private until promoted)",
    )
    loc_sub = loc.add_subparsers(dest="local_cmd", required=True)

    ls = loc_sub.add_parser("start", help="Start a LOCAL-* offline session and set pointer")
    ls.add_argument("--name", help="Slug fragment (default from title/intent)")
    ls.add_argument("--title", help="Human title")
    ls.add_argument("--intent", help="One-line why this scratch work exists")
    ls.add_argument("--branch", help="Optional git branch name note")
    ls.set_defaults(func=cmd_local)

    ll = loc_sub.add_parser("list", help="List local/offline sessions on this machine")
    ll.add_argument("--all", action="store_true", help="Include promoted/abandoned")
    ll.set_defaults(func=cmd_local)

    lst = loc_sub.add_parser("status", help="Show active or named local session")
    lst.add_argument("--session", help="LOCAL-* id (default: pointer)")
    lst.set_defaults(func=cmd_local)

    lc = loc_sub.add_parser("capture", help="Append a note into the local session")
    lc.add_argument("--summary", required=True)
    lc.add_argument("--session")
    lc.set_defaults(func=cmd_local)

    lsh = loc_sub.add_parser("shelf", help="Park a local session (clear pointer)")
    lsh.add_argument("--reason", default="manual shelf")
    lsh.add_argument("--session")
    lsh.set_defaults(func=cmd_local)

    lr = loc_sub.add_parser("resume", help="Resume a shelved local session")
    lr.add_argument("session_id")
    lr.set_defaults(func=cmd_local)

    la = loc_sub.add_parser("abandon", help="Mark a local session abandoned")
    la.add_argument("--session")
    la.add_argument("--force", action="store_true")
    la.set_defaults(func=cmd_local)

    lp = loc_sub.add_parser(
        "promote",
        help="Promote LOCAL session into a documented Work ID (canvas + requirement)",
    )
    lp.add_argument("--type", default="feature", help="feature|spike|bug|refactor|chore|...")
    lp.add_argument("--name", help="Title/slug for the new Work ID (default: session title)")
    lp.add_argument("--session")
    lp.add_argument("--milestone", help="Optional milestone-*.md to append Linked Work")
    lp.add_argument("--no-claim", action="store_true", help="Create artifacts without claiming")
    lp.add_argument("--dry-run", action="store_true")
    lp.add_argument(
        "--from-git",
        help="Backfill session notes from git log range before promote (e.g. main..HEAD)",
    )
    lp.set_defaults(func=cmd_local)

    work = sub.add_parser(
        "work",
        help="Create / bootstrap Work IDs (engine-backed helpers)",
    )
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
    wia.set_defaults(func=cmd_work)

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
    cm.set_defaults(func=cmd_commit_message)

    db = sub.add_parser(
        "db",
        help="Local regenerable SQLite index (query cache before GUIDE/Neo4j)",
    )
    db_sub = db.add_subparsers(dest="db_cmd", required=True)

    db_sub.add_parser("rebuild", help="Rebuild .sdlc/index.sqlite from repo artifacts").set_defaults(
        func=cmd_db
    )
    db_sub.add_parser("status", help="Show index path, counts, rebuild metadata").set_defaults(
        func=cmd_db
    )
    db_sub.add_parser("path", help="Print absolute path to the SQLite file").set_defaults(func=cmd_db)

    dq = db_sub.add_parser("query", help="Query work_items (filters or read-only SQL SELECT)")
    dq.add_argument("sql", nargs="?", help="Optional SELECT … (read-only)")
    dq.add_argument("--work-id")
    dq.add_argument("--status", help="Match registry_status, canvas_status, or final_status")
    dq.add_argument("--search", help="Full-text (FTS5) or LIKE search")
    dq.add_argument("--limit", type=int, default=50)
    dq.add_argument("--columns", help="Comma-separated columns for table output")
    dq.add_argument("--json", action="store_true")
    dq.set_defaults(func=cmd_db)

    dl = db_sub.add_parser(
        "lookup",
        help="Machine-readable Work ID snapshot for session briefs (JSON or markdown)",
    )
    dl.add_argument("--work-id", required=True, help="Work ID to look up")
    dl.add_argument("--search", default="", help="Optional related FTS/LIKE hits")
    dl.add_argument("--limit", type=int, default=5, help="Max related search hits (default: 5)")
    dl.add_argument(
        "--markdown",
        action="store_true",
        help="Emit markdown section for embedding into a session brief",
    )
    dl.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON (default when --markdown is not set)",
    )
    dl.set_defaults(func=cmd_db)

    de = db_sub.add_parser("export", help="Export index as JSON or SQL dump (not for live multi-user sync)")
    de.add_argument("--format", choices=["json", "sql"], default="json")
    de.add_argument("--output", "-o", help="Write to file (default: stdout)")
    de.set_defaults(func=cmd_db)

    rel = sub.add_parser("release", help="Release/shelf active claim")
    rel.add_argument("--reason", default="released")
    rel.set_defaults(func=cmd_release)

    sub.add_parser("team", help="Show team registry").set_defaults(func=cmd_team)
    sub.add_parser("list-work", help="List Work IDs").set_defaults(func=cmd_list_work)
    sub.add_parser("sync-team", help="Refresh done/cancelled from canvases").set_defaults(func=cmd_sync_team)

    ar = sub.add_parser("archive", help="Archive completed/cancelled work")
    ar.add_argument("work_id", nargs="?")
    ar.add_argument("--all", action="store_true")
    ar.add_argument("--dry-run", action="store_true")
    ar.add_argument("--force", action="store_true")
    ar.set_defaults(func=cmd_archive)

    ptr = sub.add_parser("pointer", help="Pointer get/set/reset")
    ptr.add_argument("pointer_cmd", choices=["get", "set", "reset"])
    ptr.add_argument("work_id", nargs="?")
    ptr.set_defaults(func=cmd_pointer)

    ctx = sub.add_parser(
        "context",
        help="Ledger-first context store (git ledger + optional SQLite + Guide)",
    )
    ctx_sub = ctx.add_subparsers(dest="context_cmd", required=True)
    from .lessons_ledger import LEDGER_KINDS as _LEDGER_KINDS

    cpl = ctx_sub.add_parser(
        "persist-lesson",
        help="Stage or accept a lesson record in the ledger",
    )
    cpl.add_argument("--kind", required=True, choices=list(_LEDGER_KINDS))
    cpl.add_argument(
        "--work-id",
        default="",
        help="Work ID (optional when --area is set; omit on an ad hoc day)",
    )
    cpl.add_argument("--body", required=True, help="Body text or '-' for stdin")
    cpl.add_argument("--title", default="")
    cpl.add_argument(
        "--area",
        default="",
        help="Code area (required when --work-id is omitted)",
    )
    cpl.add_argument("--source", default="cli")
    cpl.add_argument("--phase", default="")
    cpl.add_argument("--keywords", default="", help="Comma-separated keywords")
    cpl.add_argument("--accept", action="store_true", help="Land directly in committed ledger")
    cpl.add_argument("--no-guide", action="store_true", help="Skip Guide projection fan-out")
    cpl.set_defaults(func=cmd_context)
    cpe = ctx_sub.add_parser(
        "persist-entry",
        help="Deprecated alias for persist-lesson",
    )
    cpe.add_argument("--kind", required=True)
    cpe.add_argument("--work-id", default="")
    cpe.add_argument("--body", required=True)
    cpe.add_argument("--area", default="")
    cpe.add_argument("--phase", default="")
    cpe.add_argument("--source", default="cli")
    cpe.add_argument("--no-guide", action="store_true")
    cpe.set_defaults(func=cmd_context)
    cacc = ctx_sub.add_parser("accept", help="Promote staged lessons to committed ledger")
    cacc.add_argument("--work-id", default="")
    cacc.add_argument("--ids", default="", help="Comma-separated record ids")
    cacc.add_argument("--discard-rest", action="store_true")
    cacc.add_argument("--no-guide", action="store_true")
    cacc.set_defaults(func=cmd_context)
    cshow = ctx_sub.add_parser("show", help="Show one lesson record by id")
    cshow.add_argument("record_id")
    cshow.set_defaults(func=cmd_context)
    cpar = ctx_sub.add_parser("parity", help="Diff ledger vs SQLite/Guide; optional repair")
    cpar.add_argument("--repair", action="store_true")
    cpar.set_defaults(func=cmd_context)
    cdig = ctx_sub.add_parser("digest", help="Bounded session-start digest")
    cdig.add_argument("--work-id", default="")
    cdig.add_argument("--areas", default="", help="Comma-separated areas")
    cdig.add_argument("--keywords", default="", help="Comma-separated keywords")
    cdig.add_argument("--limit", type=int, default=8)
    cdig.set_defaults(func=cmd_context)
    cre = ctx_sub.add_parser("retrieve", help="Assemble retrieve from ledger + projections")
    cre.add_argument("--work-id", default="")
    cre.add_argument("--area", default="")
    cre.add_argument("--kind", default="")
    cre.add_argument("--keyword", default="")
    cre.add_argument("--limit", type=int, default=50)
    cre.add_argument("--no-staged", action="store_true")
    cre.set_defaults(func=cmd_context)
    ctx_sub.add_parser(
        "coverage", help="Report CONTEXT_KINDS capability coverage in SQLite"
    ).set_defaults(func=cmd_context)
    cb = ctx_sub.add_parser(
        "backends",
        help="Show or set CONTEXT_BACKENDS persistence options",
    )
    cb.add_argument(
        "--set",
        dest="set_backends",
        default=None,
        help="Comma-separated backends: git-pointers,sqlite,guide-dice",
    )
    cb.add_argument("--guide-base-url", default=None)
    cb.add_argument("--notes", default=None)
    cb.set_defaults(func=cmd_context)
    cgq = ctx_sub.add_parser(
        "guide-query",
        help="Delegate a retrieval question to Guide spdd_* tools (HTTP parity with MCP)",
    )
    cgq.add_argument("--work-id", default="", help="Active Work ID → spdd_workSubgraph")
    cgq.add_argument("--area", default="", help="Code area → spdd_areaLessons")
    cgq.add_argument("--lesson-id", default="", help="Lesson entity id → spdd_getLesson")
    cgq.add_argument("--label", default="", help="Entity label → spdd_findByLabel")
    cgq.add_argument(
        "--question",
        default="",
        help="Natural-language hint (routes to work/area/stats when flags omitted)",
    )
    cgq.add_argument("--stats", action="store_true", help="Projection freshness counts")
    cgq.add_argument("--tool", default="", help="Explicit spdd_* tool name")
    cgq.add_argument("--tool-json", default="", help="JSON object of tool arguments")
    cgq.add_argument("--limit", type=int, default=20)
    cgq.add_argument("--guide-url", default="", help="Override GUIDE_BASE_URL")
    cgq.add_argument("--timeout", type=float, default=30.0)
    cgq.add_argument(
        "--text",
        action="store_true",
        help="Human-readable answer for Cursor/Copilot chat (default: JSON)",
    )
    cgq.set_defaults(func=cmd_context)
    cmc = ctx_sub.add_parser(
        "mcp-call",
        help="Call one Guide spdd_* MCP tool by name (REST parity; for agents/scripts)",
    )
    cmc.add_argument(
        "--tool",
        required=True,
        help="spdd_workSubgraph | spdd_areaLessons | spdd_findByLabel | spdd_projectionStats | spdd_getLesson",
    )
    cmc.add_argument(
        "--json",
        default="{}",
        help='Tool arguments JSON, e.g. {"workId":"FEAT-001-order-status-api"}',
    )
    cmc.add_argument("--guide-url", default="")
    cmc.add_argument("--timeout", type=float, default=30.0)
    cmc.set_defaults(func=cmd_context)

    st = sub.add_parser("storage", help="Storage v3 migration and status")
    st_sub = st.add_subparsers(dest="storage_cmd", required=True)
    st_sub.add_parser("status", help="Detect legacy layout / migration state").set_defaults(
        func=cmd_storage
    )
    stm = st_sub.add_parser("migrate", help="Migrate legacy agent-context to ledger v3")
    stm.add_argument("--dry-run", action="store_true")
    stm.set_defaults(func=cmd_storage)

    ac = sub.add_parser(
        "agent-context",
        help="Upgrade/re-init noisy agent-context runtime + quiet mode (#80/#91)",
    )
    ac_sub = ac.add_subparsers(dest="agent_context_cmd", required=True)
    ac_sub.add_parser("detect", help="Detect legacy sessions/features noise").set_defaults(
        func=cmd_agent_context
    )
    acu = ac_sub.add_parser(
        "upgrade",
        help="Archive sessions/features to .sdlc/legacy-export and seed lean runtime",
    )
    acu.add_argument("--dry-run", action="store_true")
    acu.add_argument("--no-rebuild", action="store_true")
    acu.set_defaults(func=cmd_agent_context)
    aqs = ac_sub.add_parser("quiet-status", help="Show quiet/product-test mode status")
    aqs.add_argument("--quiet", action="store_true", help="Treat as --quiet flag set")
    aqs.add_argument("--guide-live", action="store_true")
    aqs.set_defaults(func=cmd_agent_context)

    shell = sub.add_parser("shell", help="Run a v1 scripts/*.sh via bridge")
    shell.add_argument("script")
    shell.add_argument("script_args", nargs=argparse.REMAINDER)
    shell.set_defaults(func=cmd_shell)

    sub.add_parser("version", help="Print version").set_defaults(func=cmd_version)

    vw = sub.add_parser(
        "viewer",
        help="ADF WYSIWYG ticket viewer (Flask; requires optional [viewer] extra)",
    )
    vw.add_argument("--host", default="127.0.0.1", help="Bind address (default 127.0.0.1)")
    vw.add_argument("--port", type=int, default=5050)
    vw.add_argument("--debug", action="store_true")
    vw.add_argument(
        "--lan",
        action="store_true",
        help="Bind 0.0.0.0 for LAN access (opt-in)",
    )
    vw.set_defaults(func=cmd_viewer)

    def _add_console_parser(name: str, help_text: str) -> None:
        inst = sub.add_parser(name, help=help_text)
        inst.add_argument(
            "--target",
            default=None,
            help="Default target project path shown in the UI (default: --root / cwd)",
        )
        inst.add_argument("--host", default="127.0.0.1", help="Bind address (default 127.0.0.1)")
        inst.add_argument("--port", type=int, default=5051)
        inst.add_argument("--debug", action="store_true")
        inst.add_argument(
            "--lan",
            action="store_true",
            help="Bind 0.0.0.0 for LAN access (opt-in)",
        )
        inst.add_argument(
            "--no-browser",
            action="store_true",
            help="Do not open a browser tab automatically",
        )
        inst.set_defaults(func=cmd_installer)

    _add_console_parser(
        "installer",
        "EXPERIMENTAL ops console: install/upgrade, SQLite, rollback, Guide "
        "(Flask; [viewer] extra) — not a stable consumer install path",
    )
    _add_console_parser(
        "console",
        "EXPERIMENTAL alias for installer — ops console UI",
    )
    _add_console_parser(
        "dashboard",
        "EXPERIMENTAL alias for installer — ops console UI",
    )

    tmpl = sub.add_parser(
        "template",
        help="ADF template library: list/render/validate combos (header/body/footer)",
    )
    tmpl_sub = tmpl.add_subparsers(dest="template_cmd", required=True)
    tl = tmpl_sub.add_parser("list", help="List stock combo manifests")
    tl.add_argument("--json", action="store_true")
    tl.set_defaults(func=cmd_template)
    tmpl_sub.add_parser(
        "validate", help="Validate stock combo manifests + ADF schema"
    ).set_defaults(func=cmd_template)
    tr = tmpl_sub.add_parser(
        "render",
        help="Render planning artifacts for a Work ID into ADF JSON",
    )
    tr.add_argument("--work-id", required=True, help="Work ID to bind variables from")
    tr.add_argument(
        "--combo",
        default="",
        help="Combo id (feature|spike|bug); default: infer from Work ID prefix",
    )
    tr.add_argument(
        "--type",
        default="",
        help="Optional work-type override (feature|spike|bug|…)",
    )
    tr.add_argument(
        "-o",
        "--output",
        help="Write ADF JSON to this path (relative to --root unless absolute)",
    )
    tr.add_argument("--json", action="store_true", help="Emit full RenderResult JSON")
    tr.set_defaults(func=cmd_template)

    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "version", False) and not getattr(args, "command", None):
        return cmd_version(args)
    if not getattr(args, "command", None):
        # default to next for parity with sdlc.sh
        args.command = "next"
        args.func = cmd_next
    try:
        return int(args.func(args))
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"sdlc-engine: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
