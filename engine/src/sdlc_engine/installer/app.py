"""Flask application for the SDLC-SPDD ops console (install, SQLite, rollback, Guide)."""

from __future__ import annotations

import json
import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Any

from sdlc_engine.adf_templates import AdfTemplateLibrary, TemplateError
from sdlc_engine.adf_work import AdfWorkService
from sdlc_engine.context_store import ContextStore
from sdlc_engine.db import LocalIndex
from sdlc_engine.integration_config import save_config as save_integrations_config
from sdlc_engine.integration_config import status_dict as integration_status
from sdlc_engine.issue_tracker import (
    load_config as load_tracker_config,
    save_config as save_tracker_config,
    status_dict as tracker_status_dict,
)
from sdlc_engine.issues import IssueSyncService
from sdlc_engine.lessons_ledger import LessonsLedger
from sdlc_engine.persistence import (
    ALL_BACKENDS,
    load_config as load_persistence_config,
    save_config as save_persistence_config,
    status_dict as persistence_status,
)
from sdlc_engine.phases import GATE_LABELS, gates_for_phase
from sdlc_engine.project import Project
from sdlc_engine.registry import TeamRegistry
from sdlc_engine.viewer.store import AdfStore, AdfStoreError
from sdlc_engine.workflow import WorkflowEngine

from .detect import detect_target
from .guide import checklist, ingest_command, load_config, probe_guide, save_config
from .guide_compliance import (
    embabel_mechanics_checklist,
    ensure_spdd_profile,
    load_spdd_projection,
    named_entity_module_present,
    probe_mcp_sse,
    projection_stats,
)
from .guide_ops import (
    default_operator_directories,
    guide_stats,
    load_references,
    purge_all_content_elements_docker,
    purge_content,
    purge_preview,
    reset_git_revision,
)
from .guide_runtime import (
    ensure_guide_repo,
    start_guide,
    start_neo4j,
    stop_guide,
    stop_neo4j,
    stack_status,
)
from .pages import PAGE
from .rollback import list_backups, restore_backup
from .runner import orchestrator_root, run_action
from .viewer_runtime import (
    DEFAULT_HOST as ADF_DEFAULT_HOST,
    DEFAULT_PORT as ADF_DEFAULT_PORT,
    restart_viewer,
    start_viewer,
    stop_viewer,
    viewer_payload,
    viewer_process_status,
)


# --- Dashboard (landing tab) helpers ---------------------------------------
# Module-level so tests can patch _gh_auth_status / probe_guide /
# viewer_process_status without touching the Flask closures.


def _gh_auth_status(timeout: float = 3.0) -> dict[str, Any]:
    """Report `gh auth status` as booleans only.

    The raw command output can contain (masked) tokens and account names, so
    it is never echoed into the payload.
    """
    try:
        proc = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {"installed": False, "authenticated": False, "detail": "gh not installed"}
    except subprocess.TimeoutExpired:
        return {"installed": True, "authenticated": False, "detail": "gh auth status timed out"}
    except OSError as exc:
        return {"installed": False, "authenticated": False, "detail": f"gh check failed: {exc}"}
    if proc.returncode == 0:
        return {"installed": True, "authenticated": True, "detail": "gh authenticated"}
    return {
        "installed": True,
        "authenticated": False,
        "detail": "gh not authenticated (run: gh auth login)",
    }


def _dashboard_status(target: Path) -> dict[str, Any]:
    """Status + config cards for the Dashboard tab (one round-trip)."""
    project = Project.resolve(target)
    engine = WorkflowEngine(project)
    status = json.loads(engine.status_json())
    open_gates: list[dict[str, str]] = []
    if status.get("work_id"):
        gates = status.get("gates") or {}
        for gate in gates_for_phase(str(status.get("phase") or "")):
            if gates.get(gate) != "passed":
                open_gates.append({"gate": gate, "label": GATE_LABELS.get(gate, gate)})
    work = {
        "pointer": status.get("pointer") or "",
        "phase": status.get("phase") or "",
        "operation": status.get("operation") or "",
        "recommended_command": status.get("recommended_command") or "",
        "open_gates": open_gates,
    }

    ledger = LessonsLedger(project)
    accepted = ledger.records(include_staged=False)
    staged_count = len(ledger.staged_ids())
    events = TeamRegistry(project, workflow=engine).lean_events()
    last = events[-1] if events else None
    memory = {
        "accepted_count": len(accepted),
        "last_accepted_ts": accepted[0].ts if accepted else "",
        "staged_count": staged_count,
        "needs_accept": staged_count > 0,
        "ledger_path": "spdd/memory/lessons.jsonl",
        "staged_path": ".sdlc/staged/lessons.jsonl",
        "registry_last_event": (
            {
                "event": last.get("event") or "",
                "work_id": last.get("work_id") or "",
                "owner": last.get("owner") or "",
                "phase": last.get("phase") or "",
                "ts": last.get("ts") or "",
                "note": last.get("note") or "",
            }
            if last
            else None
        ),
    }

    pstat = persistence_status(project)
    guide_cfg = load_config(target)
    host = str(guide_cfg.get("host") or "127.0.0.1")
    port = int(guide_cfg.get("port") or 21337)
    probe = probe_guide(host, port, timeout=1.0)
    backends = {
        "backends": list(pstat.get("backends") or []),
        "enabled": pstat.get("enabled") or {},
        "source": pstat.get("source") or "",
        "sqlite": pstat.get("sqlite") or {},
        "guide": {
            "enabled": bool((pstat.get("enabled") or {}).get("guide-dice")),
            "host": host,
            "port": port,
            "reachable": bool(probe.get("tcp_open")),
            "detail": str(probe.get("detail") or ""),
            "effective_base_url": (pstat.get("guide") or {}).get("effective_base_url") or "",
        },
        # Parity runs ContextStore.parity() — explicit button only, never on load.
        "parity_hint": "Run parity from the Persistence tab (Check ledger parity / Parity + repair).",
    }

    viewer = viewer_process_status(target)
    project = Project.resolve(target)
    integ = integration_status(project)
    gh_cli = _gh_auth_status()
    integrations = {
        "jira": {
            **integ["jira"],
            "hint": "Set in Issues tab → Integrations (.sdlc/integrations-config.json) or export JIRA_* env",
        },
        "github": {
            **integ["github"],
            "installed": gh_cli.get("installed", False),
            "authenticated": bool(integ["github"].get("configured") or gh_cli.get("authenticated")),
            "detail": gh_cli.get("detail") if not integ["github"].get("configured") else "token configured",
            "hint": "Set GH token in Issues tab or run `gh auth login`",
        },
        "tracker": integ.get("effective_tracker"),
        "viewer": {
            "running": bool(viewer.get("alive") or viewer.get("port_open")),
            "url": viewer.get("url") or "",
            "host": viewer.get("host") or ADF_DEFAULT_HOST,
            "port": viewer.get("port") or ADF_DEFAULT_PORT,
        },
    }
    return {"work": work, "memory": memory, "backends": backends, "integrations": integrations}


def _dashboard_activity(project: Project, limit: int) -> list[dict[str, Any]]:
    """Merged feed: registry events + accepted/staged records + workflow history."""
    items: list[dict[str, Any]] = []
    for ev in TeamRegistry(project).lean_events():
        wid = (ev.get("work_id") or "").strip()
        text = f"{ev.get('event') or 'update'} {wid}".strip()
        if ev.get("owner"):
            text += f" by {ev['owner']}"
        if ev.get("phase"):
            text += f" ({ev['phase']})"
        items.append({"ts": ev.get("ts") or "", "source": "registry", "text": text, "work_id": wid})
    ledger = LessonsLedger(project)
    staged_ids = ledger.staged_ids()
    for rec in ledger.records(include_staged=False):
        items.append(
            {
                "ts": rec.ts,
                "source": "ledger",
                "text": f"{rec.kind} accepted: {rec.title} [{rec.work_id}]",
                "work_id": rec.work_id,
            }
        )
    for rec in ledger.records(include_staged=True):
        if rec.id in staged_ids:
            items.append(
                {
                    "ts": rec.ts,
                    "source": "staged",
                    "text": f"staged: {rec.kind} {rec.title}",
                    "work_id": rec.work_id,
                }
            )
    workflows = project.workflows_dir
    if workflows.is_dir():
        for hist in sorted(workflows.glob("*.history")):
            try:
                lines = hist.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for line in lines:
                parts = line.split("\t", 2)
                if len(parts) < 2 or not parts[0].strip():
                    continue
                detail = parts[2].strip() if len(parts) > 2 else ""
                items.append(
                    {
                        "ts": parts[0].strip(),
                        "source": "workflow",
                        "text": parts[1].strip() + (f" {detail}" if detail else ""),
                        "work_id": hist.stem,
                    }
                )
    items.sort(key=lambda it: (it.get("ts") or "", it.get("source") or ""), reverse=True)
    return items[: max(1, limit)]


def _requirements_issue_sections(project: Project, *, max_files: int = 40) -> dict[str, bool]:
    """Cheap capped scan: do any requirements mention ## Jira / ## GitHub?"""
    found = {"jira": False, "github": False}
    req_dir = project.requirements_dir
    if not req_dir.is_dir():
        return found
    scanned = 0
    for path in sorted(req_dir.rglob("*.md")):
        if scanned >= max_files or (found["jira"] and found["github"]):
            break
        scanned += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:65536]
        except OSError:
            continue
        if "## Jira" in text:
            found["jira"] = True
        if "## GitHub" in text:
            found["github"] = True
    return found


def _dashboard_suggestions(project: Project, status: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministic 'Today' checklist — plain rules over the status payload."""
    out: list[dict[str, Any]] = []
    work = status.get("work") or {}
    memory = status.get("memory") or {}
    backends = status.get("backends") or {}
    integrations = status.get("integrations") or {}

    staged = int(memory.get("staged_count") or 0)
    if staged > 0:
        wid = work.get("pointer") or "<WORK-ID>"
        out.append(
            {
                "id": "accept-staged",
                "text": (
                    f"{staged} staged record(s) await review: run /sdlc-spdd-accept "
                    f"(or ./scripts/sdlc.sh accept --work-id {wid})"
                ),
            }
        )

    pointer = work.get("pointer") or ""
    open_gates = work.get("open_gates") or []
    if pointer and open_gates:
        top = open_gates[0].get("label") or open_gates[0].get("gate") or ""
        text = f"{pointer} ({work.get('phase') or '?'}): open gate — {top}."
        if work.get("recommended_command"):
            text += f" Do now: {work['recommended_command']}"
        out.append({"id": "open-gate", "text": text})
    if not pointer:
        recent: list[str] = []
        for ev in reversed(TeamRegistry(project).lean_events()):
            wid = (ev.get("work_id") or "").strip()
            if wid and wid not in recent:
                recent.append(wid)
            if len(recent) >= 3:
                break
        text = "No active work — claim: ./scripts/sdlc.sh claim <WORK-ID>"
        if recent:
            text += " (recent: " + ", ".join(recent) + ")"
        out.append({"id": "claim-work", "text": text})

    guide = backends.get("guide") or {}
    if guide.get("enabled") and not guide.get("reachable"):
        out.append(
            {
                "id": "guide-down",
                "text": (
                    "Guide is configured but unreachable — start it from the Guide tab, "
                    "or continue files-only (normal)."
                ),
            }
        )

    jira_missing = not (integrations.get("jira") or {}).get("configured")
    gh_missing = not (integrations.get("github") or {}).get("authenticated")
    if jira_missing or gh_missing:
        sections = _requirements_issue_sections(project)
        wants: list[str] = []
        if sections.get("jira") and jira_missing:
            wants.append("configure Jira in Issues tab or set JIRA_* env")
        if sections.get("github") and gh_missing:
            wants.append("configure GitHub token in Issues tab or run `gh auth login`")
        if wants:
            out.append(
                {
                    "id": "issue-sync",
                    "text": (
                        "Requirements reference Jira/GitHub — "
                        + " and ".join(wants)
                        + " to enable issue sync."
                    ),
                }
            )
    return out


def create_app(default_target: Path | str | None = None) -> Any:
    """Create the ops console Flask app (localhost tool)."""
    try:
        from flask import Flask, jsonify, render_template_string, request
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Flask is required for the installer console. Install with: "
            "pip install -e './engine[viewer]'"
        ) from exc

    orch = orchestrator_root()
    start = Path(default_target or Path.cwd()).expanduser().resolve()

    app = Flask(__name__)
    app.config["INSTALLER_DEFAULT_TARGET"] = str(start)
    app.config["ORCHESTRATOR_ROOT"] = str(orch)

    def _target_from_body(body: dict[str, Any] | None = None) -> Path:
        body = body or {}
        raw = str(body.get("target") or request.args.get("target") or "").strip()
        if not raw:
            raw = app.config["INSTALLER_DEFAULT_TARGET"]
        return Path(raw).expanduser().resolve()

    @app.get("/")
    def index() -> str:
        return render_template_string(
            PAGE,
            default_target=app.config["INSTALLER_DEFAULT_TARGET"],
            orchestrator_root=app.config["ORCHESTRATOR_ROOT"],
        )

    @app.get("/api/health")
    def api_health() -> Any:
        return jsonify(
            {
                "ok": True,
                "orchestrator_root": app.config["ORCHESTRATOR_ROOT"],
                "default_target": app.config["INSTALLER_DEFAULT_TARGET"],
            }
        )

    @app.post("/api/detect")
    def api_detect() -> Any:
        body = request.get_json(silent=True) or {}
        target = str(body.get("target") or "").strip()
        if not target:
            return jsonify({"error": "target is required"}), 400
        try:
            return jsonify(detect_target(target))
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": str(exc), "mode": "error"}), 400

    @app.post("/api/run")
    def api_run() -> Any:
        body = request.get_json(silent=True) or {}
        action = str(body.get("action") or "").strip().lower()
        target = str(body.get("target") or "").strip()
        if action not in {"install", "upgrade", "verify"}:
            return jsonify({"error": "action must be install, upgrade, or verify"}), 400
        if not target:
            return jsonify({"error": "target is required"}), 400
        assistants = body.get("assistants") or ["cursor", "copilot"]
        if not isinstance(assistants, list):
            return jsonify({"error": "assistants must be a list"}), 400
        try:
            result = run_action(
                action=action,
                target=target,
                assistants=[str(a) for a in assistants],
                dry_run=bool(body.get("dry_run")),
                force=bool(body.get("force")),
                no_backup=bool(body.get("no_backup")),
                with_python_engine=bool(body.get("with_python_engine")),
            )
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "exit_code": 2, "log": str(exc)}), 500
        status = 200 if result.get("ok") else 400
        return jsonify(result), status

    @app.post("/api/sqlite/status")
    def api_sqlite_status() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        if not target.is_dir():
            return jsonify({"error": f"target not found: {target}"}), 400
        project = Project.resolve(target)
        index = LocalIndex(project)
        info = index.status_dict()
        recent: list[dict[str, Any]] = []
        if info.get("exists") and not info.get("error"):
            try:
                recent = index.query_sql(
                    "SELECT work_id, title, registry_status, canvas_status, jira_key "
                    "FROM work_items ORDER BY work_id LIMIT 25"
                )
            except Exception:  # noqa: BLE001
                recent = []
        info["recent"] = recent
        info["target"] = str(target)
        return jsonify(info)

    @app.post("/api/sqlite/rebuild")
    def api_sqlite_rebuild() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        if not target.is_dir():
            return jsonify({"error": f"target not found: {target}"}), 400
        project = Project.resolve(target)
        index = LocalIndex(project)
        stats = index.rebuild()
        return jsonify(
            {
                "ok": True,
                "stats": {
                    "path": stats.path,
                    "work_items": stats.work_items,
                    "artifacts": stats.artifacts,
                    "local_sessions": stats.local_sessions,
                    "rebuilt_at": stats.rebuilt_at,
                    "source_commit": stats.source_commit,
                },
                "status": index.status_dict(),
            }
        )

    @app.post("/api/persistence/status")
    def api_persistence_status() -> Any:
        """Report CONTEXT_BACKENDS / triple-path persist options (#79/#90)."""
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        if not target.is_dir():
            return jsonify({"error": f"target not found: {target}"}), 400
        project = Project.resolve(target)
        payload = persistence_status(project)
        payload["available"] = list(ALL_BACKENDS)
        payload["target"] = str(target)
        return jsonify(payload)

    @app.post("/api/persistence/save")
    def api_persistence_save() -> Any:
        """Save `.sdlc/persistence-config.json` from the ops console."""
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        if not target.is_dir():
            return jsonify({"error": f"target not found: {target}"}), 400
        backends = body.get("backends")
        if backends is None:
            return jsonify({"error": "backends is required (list or comma string)"}), 400
        if isinstance(backends, str):
            backends = [p.strip() for p in backends.replace(";", ",").split(",") if p.strip()]
        if not isinstance(backends, list):
            return jsonify({"error": "backends must be a list"}), 400
        project = Project.resolve(target)
        cfg = load_persistence_config(project)
        cfg["backends"] = backends
        if "guide_base_url" in body:
            cfg["guide_base_url"] = str(body.get("guide_base_url") or "").strip()
        if "notes" in body:
            cfg["notes"] = str(body.get("notes") or "")
        try:
            saved = save_persistence_config(project, cfg)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        # Always return status_dict shape so the Persistence tab can re-apply UI state.
        saved["available"] = list(ALL_BACKENDS)
        saved["target"] = str(target)
        return jsonify(saved)

    @app.post("/api/persistence/parity")
    def api_persistence_parity() -> Any:
        """Diff the committed lessons ledger against SQLite/Guide projections.

        Runs ``ContextStore.parity()``; ``repair=true`` re-derives drifted
        projections (SQLite rebuild + Guide reproject).
        """
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        if not target.is_dir():
            return jsonify({"error": f"target not found: {target}"}), 400
        project = Project.resolve(target)
        try:
            result = ContextStore(project).parity(repair=bool(body.get("repair")))
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "target": str(target)}), 500
        # Drift is a successful check result — report it with 200 and ok=false.
        return jsonify({"ok": bool(result.get("ok")), "target": str(target), "parity": result})

    @app.post("/api/dashboard/status")
    def api_dashboard_status() -> Any:
        """Status + config cards for the Dashboard landing tab."""
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        if not target.is_dir():
            return jsonify({"error": f"target not found: {target}"}), 400
        try:
            payload = _dashboard_status(target)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "target": str(target)}), 500
        payload["ok"] = True
        payload["target"] = str(target)
        return jsonify(payload)

    @app.post("/api/dashboard/activity")
    def api_dashboard_activity() -> Any:
        """Recent activity feed merged from registry/ledger/staged/workflow history."""
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        if not target.is_dir():
            return jsonify({"error": f"target not found: {target}"}), 400
        raw_limit = body.get("limit", request.args.get("limit"))
        try:
            limit = int(raw_limit) if raw_limit is not None else 20
        except (TypeError, ValueError):
            limit = 20
        limit = max(1, min(100, limit))
        try:
            items = _dashboard_activity(Project.resolve(target), limit)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "target": str(target)}), 500
        return jsonify({"ok": True, "target": str(target), "limit": limit, "items": items})

    @app.post("/api/dashboard/suggestions")
    def api_dashboard_suggestions() -> Any:
        """Deterministic 'Today' checklist (no LLM)."""
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        if not target.is_dir():
            return jsonify({"error": f"target not found: {target}"}), 400
        try:
            project = Project.resolve(target)
            status = _dashboard_status(target)
            suggestions = _dashboard_suggestions(project, status)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "target": str(target)}), 500
        return jsonify({"ok": True, "target": str(target), "suggestions": suggestions})

    @app.post("/api/backups")
    def api_backups() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        return jsonify({"target": str(target), "backups": list_backups(target)})

    @app.post("/api/rollback")
    def api_rollback() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        backup_id = str(body.get("backup_id") or "").strip()
        if not backup_id:
            return jsonify({"error": "backup_id is required"}), 400
        result = restore_backup(
            target,
            backup_id,
            dry_run=bool(body.get("dry_run")),
            safety_backup=not bool(body.get("no_safety_backup")),
        )
        status = 200 if result.get("ok") else 400
        return jsonify(result), status

    def _guide_payload(target: Path, cfg: dict[str, Any]) -> dict[str, Any]:
        stack = stack_status(target, cfg)
        probe = stack["guide_probe"]
        neo = stack["neo4j"]
        host = str(cfg.get("host") or "127.0.0.1")
        port = int(cfg.get("port") or 21337)
        mcp = probe_mcp_sse(host, port) if probe.get("tcp_open") else {
            "sse_url": f"http://{host}:{port}/sse",
            "reachable": False,
            "detail": "Guide TCP closed",
        }
        proj = projection_stats(host, port) if probe.get("tcp_open") else {
            "ok": False,
            "error": "Guide not up",
        }
        home_ok = bool(cfg.get("guide_home") and Path(str(cfg["guide_home"])).is_dir())
        named_ok = named_entity_module_present(str(cfg.get("guide_home") or ""))
        spring = cfg.get("spring_profiles") or f"neo4j,local,{cfg.get('profile')}"
        mechanics = embabel_mechanics_checklist(
            cfg=cfg,
            neo4j=neo,
            guide_probe=probe,
            mcp=mcp,
            projection=proj,
            guide_home_ok=home_ok,
            named_entity_module_ok=named_ok,
            spring_profiles=str(spring),
        )
        stats = guide_stats(host, port) if probe.get("tcp_open") else {
            "ok": False,
            "error": "Guide not up",
        }
        return {
            "config": cfg,
            "probe": probe,
            "neo4j": neo,
            "mcp": mcp,
            "projection": proj,
            "guide_stats": stats,
            "operator_directories": default_operator_directories(
                app.config["ORCHESTRATOR_ROOT"]
            ),
            "stack": stack,
            "checklist": checklist(cfg, probe, neo4j=neo),
            "embabel_mechanics": mechanics,
            "ingest_command": ingest_command(cfg),
            "docs": "docs/dice-projection-runbook.md",
        }

    @app.post("/api/guide")
    def api_guide_get() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = load_config(target)
        return jsonify(_guide_payload(target, cfg))

    @app.post("/api/guide/save")
    def api_guide_save() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = save_config(target, body)
        out = _guide_payload(target, cfg)
        out["ok"] = True
        return jsonify(out)

    @app.post("/api/guide/ensure")
    def api_guide_ensure() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = save_config(target, body) if body.get("save_first") else load_config(target)
        # Allow one-shot overrides from the form without requiring Save.
        for key in (
            "guide_home",
            "guide_git_url",
            "guide_git_ref",
            "profile",
            "host",
            "neo4j_username",
            "neo4j_password",
        ):
            if key in body and body[key] is not None:
                cfg[key] = str(body[key]).strip()
        for key in ("port", "neo4j_bolt_port", "neo4j_http_port", "neo4j_https_port"):
            if key in body and body[key] is not None:
                cfg[key] = int(body[key])
        result = ensure_guide_repo(cfg, pull=not bool(body.get("no_pull")))
        out = _guide_payload(target, load_config(target) if result.get("ok") else cfg)
        out["ensure"] = result
        out["ok"] = bool(result.get("ok"))
        return jsonify(out), (200 if result.get("ok") else 400)

    @app.post("/api/guide/neo4j/start")
    def api_neo4j_start() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = load_config(target)
        for key in ("neo4j_bolt_port", "neo4j_http_port", "neo4j_https_port"):
            if key in body and body[key] is not None:
                cfg[key] = int(body[key])
        result = start_neo4j(cfg)
        out = _guide_payload(target, cfg)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        return jsonify(out), (200 if result.get("ok") else 400)

    @app.post("/api/guide/neo4j/stop")
    def api_neo4j_stop() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = load_config(target)
        result = stop_neo4j(cfg)
        out = _guide_payload(target, cfg)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        return jsonify(out), (200 if result.get("ok") else 400)

    @app.post("/api/guide/start")
    def api_guide_start() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = load_config(target)
        for key in ("guide_home", "profile", "host", "neo4j_username", "neo4j_password"):
            if key in body and body[key] is not None:
                cfg[key] = str(body[key]).strip()
        for key in ("port", "neo4j_bolt_port", "neo4j_http_port", "neo4j_https_port"):
            if key in body and body[key] is not None:
                cfg[key] = int(body[key])
        result = start_guide(
            target,
            cfg,
            ingest=not bool(body.get("no_ingest")),
            ensure_neo4j=not bool(body.get("skip_neo4j")),
        )
        out = _guide_payload(target, cfg)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        return jsonify(out), (200 if result.get("ok") else 400)

    @app.post("/api/guide/stop")
    def api_guide_stop() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = load_config(target)
        result = stop_guide(target, cfg)
        out = _guide_payload(target, cfg)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        return jsonify(out)

    @app.post("/api/guide/ensure-profile")
    def api_guide_ensure_profile() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = load_config(target)
        profile = str(body.get("profile") or cfg.get("profile") or "sdlc-spdd")
        result = ensure_spdd_profile(
            str(cfg.get("guide_home") or ""),
            orchestrator_root=str(app.config["ORCHESTRATOR_ROOT"]),
            profile=profile,
        )
        saved = save_config(
            target,
            {
                "profile": profile,
                "spring_profiles": f"neo4j,local,{profile}",
            },
        )
        out = _guide_payload(target, saved)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        return jsonify(out)

    @app.post("/api/guide/projection/load")
    def api_guide_projection_load() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = load_config(target)
        host = str(cfg.get("host") or "127.0.0.1")
        port = int(cfg.get("port") or 21337)
        root = str(body.get("root_path") or app.config["ORCHESTRATOR_ROOT"])
        result = load_spdd_projection(host, port, root_path=root)
        out = _guide_payload(target, cfg)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        return jsonify(out), (200 if result.get("ok") else 400)

    def _cfg_host_port(cfg: dict[str, Any]) -> tuple[str, int]:
        return str(cfg.get("host") or "127.0.0.1"), int(cfg.get("port") or 21337)

    @app.post("/api/guide/stats")
    def api_guide_stats() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = load_config(target)
        host, port = _cfg_host_port(cfg)
        result = guide_stats(host, port)
        out = _guide_payload(target, cfg)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        return jsonify(out), (200 if result.get("ok") else 400)

    @app.post("/api/guide/ingest")
    def api_guide_ingest() -> Any:
        """Incremental ingest via POST /api/v1/data/load-references (Guide must be up)."""
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = load_config(target)
        host, port = _cfg_host_port(cfg)
        result = load_references(host, port)
        out = _guide_payload(target, cfg)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        return jsonify(out), (200 if result.get("ok") else 400)

    @app.post("/api/guide/purge/preview")
    def api_guide_purge_preview() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = load_config(target)
        host, port = _cfg_host_port(cfg)
        directory = str(body.get("directory") or "").strip() or None
        uri_prefix = str(body.get("uri_prefix") or "").strip() or None
        if not directory and not uri_prefix:
            directory = str(app.config["ORCHESTRATOR_ROOT"])
        result = purge_preview(
            host,
            port,
            directory=directory,
            uri_prefix=uri_prefix,
            sample_limit=int(body.get("sample_limit") or 15),
        )
        out = _guide_payload(target, cfg)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        return jsonify(out), (200 if result.get("ok") else 400)

    @app.post("/api/guide/purge")
    def api_guide_purge() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = load_config(target)
        host, port = _cfg_host_port(cfg)
        if not body.get("confirm"):
            return jsonify({"ok": False, "error": "confirm=true required for purge"}), 400
        directory = str(body.get("directory") or "").strip() or None
        uri_prefix = str(body.get("uri_prefix") or "").strip() or None
        if not directory and not uri_prefix:
            directory = str(app.config["ORCHESTRATOR_ROOT"])
        result = purge_content(
            host,
            port,
            directory=directory,
            uri_prefix=uri_prefix,
            confirm=True,
        )
        out = _guide_payload(target, cfg)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        return jsonify(out), (200 if result.get("ok") else 400)

    @app.post("/api/guide/git-revision/reset")
    def api_guide_git_revision_reset() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = load_config(target)
        host, port = _cfg_host_port(cfg)
        directory = str(body.get("directory") or app.config["ORCHESTRATOR_ROOT"]).strip()
        result = reset_git_revision(host, port, directory=directory)
        out = _guide_payload(target, cfg)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        return jsonify(out), (200 if result.get("ok") else 400)

    @app.post("/api/guide/purge-all-rag")
    def api_guide_purge_all_rag() -> Any:
        """Delete all ContentElement nodes in local embabel-neo4j (docker cypher-shell)."""
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        cfg = load_config(target)
        if not body.get("confirm"):
            return jsonify(
                {
                    "ok": False,
                    "error": "confirm=true required — this wipes ALL RAG ContentElement nodes",
                }
            ), 400
        result = purge_all_content_elements_docker(
            username=str(cfg.get("neo4j_username") or "neo4j"),
            password=str(cfg.get("neo4j_password") or "brahmsian"),
        )
        out = _guide_payload(target, cfg)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        return jsonify(out), (200 if result.get("ok") else 400)

    def _adf_host_port(body: dict[str, Any]) -> tuple[str, int]:
        host = str(body.get("host") or ADF_DEFAULT_HOST).strip() or ADF_DEFAULT_HOST
        try:
            port = int(body.get("port") or ADF_DEFAULT_PORT)
        except (TypeError, ValueError):
            port = ADF_DEFAULT_PORT
        return host, port

    @app.post("/api/adf")
    def api_adf_status() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        host, port = _adf_host_port(body)
        return jsonify(viewer_payload(target, host=host, port=port))

    @app.post("/api/adf/start")
    def api_adf_start() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        host, port = _adf_host_port(body)
        result = start_viewer(target, host=host, port=port)
        out = viewer_payload(target, host=host, port=port)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        if result.get("error"):
            out["error"] = result["error"]
        return jsonify(out), (200 if result.get("ok") else 400)

    @app.post("/api/adf/stop")
    def api_adf_stop() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        host, port = _adf_host_port(body)
        result = stop_viewer(target)
        out = viewer_payload(target, host=host, port=port)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        return jsonify(out)

    @app.post("/api/adf/restart")
    def api_adf_restart() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        host, port = _adf_host_port(body)
        result = restart_viewer(target, host=host, port=port)
        out = viewer_payload(target, host=host, port=port)
        out["result"] = result
        out["ok"] = bool(result.get("ok"))
        if result.get("error"):
            out["error"] = result["error"]
        return jsonify(out), (200 if result.get("ok") else 400)

    @app.post("/api/adf/browse")
    def api_adf_browse() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        path = str(body.get("path") or "").strip()
        store = AdfStore(target)
        store.ensure_dir()
        try:
            listing = store.browse(path or str(store.adf_dir))
        except AdfStoreError as exc:
            return jsonify({"ok": False, "error": str(exc), "target": str(target)}), 400
        return jsonify(
            {
                "ok": True,
                "target": str(target),
                "home": str(target),
                "adf_dir": str(store.adf_dir),
                **listing,
            }
        )

    @app.post("/api/adf/init-work")
    def api_adf_init_work() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        adf_path = str(body.get("path") or "").strip()
        if not adf_path:
            return jsonify({"ok": False, "error": "path required"}), 400
        work_type = str(body.get("type") or "feature").strip() or "feature"
        title = str(body.get("title") or "").strip()
        work_id = str(body.get("work_id") or "").strip()
        claim = body.get("claim", True) is not False
        dry_run = bool(body.get("dry_run"))
        svc = AdfWorkService(Project.resolve(target))
        try:
            result = svc.init_from_adf(
                adf_path,
                work_type=work_type,
                title=title,
                work_id=work_id,
                claim=claim,
                dry_run=dry_run,
            )
        except (OSError, ValueError, PermissionError, FileExistsError) as exc:
            return jsonify({"ok": False, "error": str(exc), "target": str(target)}), 400
        return jsonify(
            {
                "ok": True,
                "target": str(target),
                "work_id": result.work_id,
                "title": result.title,
                "adf_path": result.adf_path,
                "canvas_path": result.canvas_path,
                "requirement_path": result.requirement_path,
                "feature_dir": result.feature_dir,
                "source_issue": result.source_issue,
                "next_command": result.next_command,
                "dry_run": result.dry_run,
                "cli": (
                    f"./scripts/sdlc.sh work init-from-adf --path {adf_path}"
                    + (f" --title {title!r}" if title else "")
                    + (f" --work-id {work_id}" if work_id else "")
                    + (f" --type {work_type}" if work_type != "feature" else "")
                ),
            }
        )

    @app.post("/api/templates")
    def api_templates_list() -> Any:
        """List ADF template combos from orchestrator templates/adf."""
        try:
            lib = AdfTemplateLibrary()
            combos = [c.to_dict() for c in lib.list_combos()]
        except (TemplateError, FileNotFoundError, OSError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 500
        return jsonify({"ok": True, "combos": combos, "count": len(combos)})

    @app.post("/api/templates/render")
    def api_templates_render() -> Any:
        """Render a combo for a Work ID into ADF (+ markdown preview)."""
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        if not target.is_dir():
            return jsonify({"ok": False, "error": f"target not found: {target}"}), 400
        work_id = str(body.get("work_id") or "").strip()
        if not work_id:
            return jsonify({"ok": False, "error": "work_id is required"}), 400
        combo_id = str(body.get("combo") or "").strip()
        work_type = str(body.get("type") or "").strip()
        write = bool(body.get("write"))
        output = str(body.get("output") or "").strip()
        try:
            lib = AdfTemplateLibrary()
            if not combo_id:
                combo_id = lib.suggest_combo(work_id, work_type)
            out_path = None
            if write:
                out_path = output or f"adf/{work_id}.adf.json"
            result = lib.render(
                Project.resolve(target),
                work_id,
                combo_id,
                work_type=work_type,
                output=out_path,
            )
        except (TemplateError, FileNotFoundError, OSError, ValueError) as exc:
            return jsonify({"ok": False, "error": str(exc), "target": str(target)}), 400
        payload = result.to_dict()
        payload["target"] = str(target)
        return jsonify(payload)

    @app.post("/api/integrations/status")
    def api_integrations_status() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        if not target.is_dir():
            return jsonify({"ok": False, "error": f"target not found: {target}"}), 400
        project = Project.resolve(target)
        payload = integration_status(project)
        payload["ok"] = True
        payload["target"] = str(target)
        return jsonify(payload)

    @app.post("/api/integrations/save")
    def api_integrations_save() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        if not target.is_dir():
            return jsonify({"ok": False, "error": f"target not found: {target}"}), 400
        project = Project.resolve(target)
        try:
            saved = save_integrations_config(project, body)
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc), "target": str(target)}), 400
        out = integration_status(project)
        out["ok"] = True
        out["target"] = str(target)
        out["saved"] = saved
        return jsonify(out)

    @app.post("/api/issues/status")
    def api_issues_status() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        work_id = str(body.get("work_id") or "").strip()
        if not work_id:
            return jsonify({"ok": False, "error": "work_id required"}), 400
        system = str(body.get("system") or "").strip() or None
        svc = IssueSyncService(Project.resolve(target))
        try:
            status = svc.issue_link_status(work_id, system=system)
        except (FileNotFoundError, ValueError) as exc:
            return jsonify({"ok": False, "error": str(exc), "target": str(target)}), 400
        return jsonify({"ok": True, "target": str(target), **status})

    @app.post("/api/issues/link")
    def api_issues_link() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        work_id = str(body.get("work_id") or "").strip()
        issue_ref = str(body.get("issue_ref") or body.get("jira_key") or body.get("github_number") or "").strip()
        if not work_id or not issue_ref:
            return jsonify({"ok": False, "error": "work_id and issue_ref required"}), 400
        dry_run = body.get("dry_run") is True or body.get("apply") is not True
        svc = IssueSyncService(Project.resolve(target))
        try:
            result = svc.link_issue_local(
                work_id,
                issue_ref,
                system=str(body.get("system") or "").strip() or None,
                summary=str(body.get("summary") or "").strip() or None,
                issue_type=str(body.get("issue_type") or "").strip() or None,
                title=str(body.get("title") or body.get("summary") or "").strip() or None,
                url=str(body.get("url") or body.get("github_url") or "").strip() or None,
                apply=not dry_run,
            )
        except (FileNotFoundError, ValueError) as exc:
            return jsonify({"ok": False, "error": str(exc), "target": str(target)}), 400
        return jsonify({"ok": True, "target": str(target), **result, "dry_run": dry_run})

    @app.post("/api/issues/sync")
    def api_issues_sync() -> Any:
        body = request.get_json(silent=True) or {}
        target = _target_from_body(body)
        work_id = str(body.get("work_id") or "").strip()
        direction = str(body.get("direction") or "pull").strip().lower()
        system = str(body.get("system") or "").strip() or None
        if not work_id:
            return jsonify({"ok": False, "error": "work_id required"}), 400
        if direction not in {"pull", "push"}:
            return jsonify({"ok": False, "error": "direction must be pull or push"}), 400
        apply = body.get("apply") is True
        svc = IssueSyncService(Project.resolve(target))
        try:
            report = svc.sync_issue(
                work_id,
                system=system,
                direction=direction,
                apply=apply,
                description_format=str(body.get("description_format") or "").strip() or None,
            )
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            return jsonify({"ok": False, "error": str(exc), "target": str(target)}), 400
        tracker = system or integration_status(Project.resolve(target)).get("effective_tracker", "jira")
        cli = (
            f"./scripts/sdlc.sh issues {direction} {work_id} --system {tracker}"
            + (" --apply" if apply else "")
        )
        return jsonify(
            {
                "ok": True,
                "target": str(target),
                "work_id": work_id,
                "system": tracker,
                "direction": direction,
                "apply": apply,
                "report": report,
                "cli": cli,
            }
        )

    @app.post("/api/jira/status")
    def api_jira_status() -> Any:
        body = request.get_json(silent=True) or {}
        body["system"] = "jira"
        return api_issues_status()

    @app.post("/api/jira/link")
    def api_jira_link() -> Any:
        body = request.get_json(silent=True) or {}
        if body.get("jira_key") and not body.get("issue_ref"):
            body["issue_ref"] = body["jira_key"]
        body["system"] = "jira"
        return api_issues_link()

    @app.post("/api/jira/sync")
    def api_jira_sync() -> Any:
        body = request.get_json(silent=True) or {}
        body["system"] = "jira"
        return api_issues_sync()

    return app


def run_installer(
    default_target: Path | str | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 5051,
    debug: bool = False,
    open_browser: bool = True,
) -> None:
    """Start the ops console web UI."""
    app = create_app(default_target)
    url = f"http://{host}:{port}/"
    print(f"SDLC-SPDD ops console: {url}")
    print(f"  orchestrator: {app.config['ORCHESTRATOR_ROOT']}")
    print(f"  default target: {app.config['INSTALLER_DEFAULT_TARGET']}")
    if open_browser and host in {"127.0.0.1", "localhost"}:
        try:
            webbrowser.open(url)
        except Exception:  # pragma: no cover
            pass
    app.run(host=host, port=port, debug=debug, use_reloader=False)
