"""In-process Guide / Jira / GitHub fakes for the Vue ops-console playground.

Playground trees never clone Guide, start Neo4j, or call Jira/GitHub. These
helpers return the same JSON shapes the Vue tabs already consume so the UI
looks live.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..io_util import load_json_dict, save_json_dict
from ..project import Project
from ..timeutil import utc_now
from .guide import checklist, ingest_command, save_config
from .guide_compliance import (
    embabel_mechanics_checklist,
    ensure_spdd_profile,
    named_entity_module_present,
)
from .guide_ops import default_operator_directories
from .playground import WORKS, is_playground
from .runner import orchestrator_root

RUNTIME_NAME = "playground-runtime.json"
FAKE_GUIDE_DIRNAME = "fake-guide"
FAKE_PID = 93001
DEFAULT_CHUNKS = 42
FAKE_JIRA_TOKEN = "playground-jira-token"
FAKE_GH_TOKEN = "playground-gh-token"


def runtime_path(target: Path | str) -> Path:
    return Path(target).expanduser().resolve() / ".sdlc" / RUNTIME_NAME


def fake_guide_home(target: Path | str) -> Path:
    return Path(target).expanduser().resolve() / ".sdlc" / FAKE_GUIDE_DIRNAME


def issue_refs(work_id: str) -> tuple[str, str]:
    """Return (Jira key, GitHub number) derived from a playground Work ID."""
    num = next((part for part in work_id.split("-") if part.isdigit()), "930")
    return f"PLAY-{num}", num


def default_runtime(target: Path | str) -> dict[str, Any]:
    home = fake_guide_home(target)
    return {
        "guide_up": True,
        "neo4j_up": True,
        "pid": FAKE_PID,
        "chunks": DEFAULT_CHUNKS,
        "work_id_count": len(WORKS),
        "canvas_count": len(WORKS),
        "area_count": 2,
        "projection_loaded": True,
        "log_path": str(home / "playground-guide.log"),
        "started_at": utc_now(),
        "mode": "playground-fake",
    }


def load_runtime(target: Path | str) -> dict[str, Any]:
    data = dict(default_runtime(target))
    path = runtime_path(target)
    if path.is_file():
        stored = load_json_dict(path)
        if isinstance(stored, dict):
            data.update(stored)
    return data


def save_runtime(target: Path | str, updates: dict[str, Any]) -> dict[str, Any]:
    data = load_runtime(target)
    data.update(updates)
    save_json_dict(runtime_path(target), data)
    return data


def seed_fake_guide_tree(target: Path | str) -> Path:
    """Write a stub Guide checkout so checklist items pass without a clone."""
    home = fake_guide_home(target)
    scripts = home / "scripts" / "user-config"
    domain = home / "src" / "main" / "kotlin" / "com" / "embabel" / "guide" / "spdd" / "domain"
    scripts.mkdir(parents=True, exist_ok=True)
    domain.mkdir(parents=True, exist_ok=True)
    (home / "compose.yaml").write_text(
        "services:\n  neo4j:\n    image: neo4j:5\n    container_name: embabel-neo4j\n",
        encoding="utf-8",
    )
    (home / "scripts" / "append-ingest.sh").write_text(
        "#!/bin/sh\necho playground-fake-ingest\n",
        encoding="utf-8",
    )
    (scripts / "application-sdlc-spdd.yml").write_text(
        "guide:\n  reload-content-on-startup: false\n  spdd-projection:\n    enabled: true\n",
        encoding="utf-8",
    )
    (domain / "WorkId.kt").write_text(
        "package com.embabel.guide.spdd.domain\n\nclass WorkId\n",
        encoding="utf-8",
    )
    dictionary = (
        home / "src" / "main" / "kotlin" / "com" / "embabel" / "guide" / "spdd" / "SpddEntityDictionary.kt"
    )
    dictionary.write_text(
        "package com.embabel.guide.spdd\n\n"
        "object SpddEntityDictionary {\n"
        "    val dictionary = DataDictionary.fromClasses(WorkId::class)\n"
        "}\n",
        encoding="utf-8",
    )
    (home / "playground-guide.log").write_text(
        "playground fake Guide process (no JVM)\n",
        encoding="utf-8",
    )
    return home


def fake_gh_auth_status(timeout: float = 3.0) -> dict[str, Any]:
    """Dashboard `gh auth` stand-in — never runs the gh CLI."""
    del timeout
    return {
        "installed": True,
        "authenticated": True,
        "detail": "playground fake — gh CLI not contacted",
    }


def playground_guide_probe(
    target: Path | str,
    host: str,
    port: int,
    timeout: float = 1.0,
) -> dict[str, Any]:
    """Dashboard Guide probe stand-in — no TCP."""
    del timeout
    rt = load_runtime(target)
    up = bool(rt.get("guide_up"))
    return {
        "host": host,
        "port": int(port),
        "tcp_open": up,
        "http_ok": up,
        "detail": "playground fake Guide UP" if up else "playground fake Guide DOWN",
        "sse_url": f"http://{host}:{int(port)}/sse",
    }


def fake_guide_payload(
    target: Path | str,
    cfg: dict[str, Any],
    *,
    orch: Path | str | None = None,
) -> dict[str, Any]:
    """Match ``_guide_payload`` so Vue ``applyGuide`` can render UP/DOWN."""
    root = Path(target).expanduser().resolve()
    rt = load_runtime(root)
    host = str(cfg.get("host") or "127.0.0.1")
    port = int(cfg.get("port") or 21337)
    bolt = int(cfg.get("neo4j_bolt_port") or 7687)
    http = int(cfg.get("neo4j_http_port") or 7474)
    guide_up = bool(rt.get("guide_up"))
    neo_up = bool(rt.get("neo4j_up"))
    probe = playground_guide_probe(root, host, port)
    neo = {
        "bolt_port": bolt,
        "http_port": http,
        "bolt_open": neo_up,
        "http_open": neo_up,
        "bolt_url": f"bolt://localhost:{bolt}",
        "browser_url": f"http://localhost:{http}",
        "container": "embabel-neo4j",
    }
    pid = int(rt.get("pid") or FAKE_PID) if guide_up else None
    stack = {
        "guide_home": cfg.get("guide_home"),
        "guide_git_url": cfg.get("guide_git_url"),
        "neo4j": neo,
        "guide_process": {
            "pid": pid,
            "alive": guide_up,
            "log_path": rt.get("log_path"),
            "started_at": rt.get("started_at"),
            "mode": rt.get("mode") or "playground-fake",
            "port_open": guide_up,
            "runtime_path": str(runtime_path(root)),
        },
        "guide_probe": probe,
    }
    mcp = {
        "sse_url": probe["sse_url"],
        "reachable": guide_up,
        "detail": "playground fake MCP SSE" if guide_up else "Guide TCP closed",
    }
    work_count = int(rt.get("work_id_count") or 0)
    canvas_count = int(rt.get("canvas_count") or 0)
    area_count = int(rt.get("area_count") or 0)
    proj_ok = guide_up and bool(rt.get("projection_loaded")) and work_count > 0
    proj: dict[str, Any] = (
        {
            "ok": True,
            "status": 200,
            "data": {
                "workIdCount": work_count,
                "canvasCount": canvas_count,
                "areaCount": area_count,
            },
        }
        if proj_ok
        else {"ok": False, "error": "Guide not up"}
    )
    chunks = int(rt.get("chunks") or 0)
    stats: dict[str, Any] = (
        {
            "ok": True,
            "status": 200,
            "data": {"contentElementCount": chunks},
            "url": f"http://{host}:{port}/api/v1/data/stats",
        }
        if guide_up
        else {"ok": False, "error": "Guide not up", "data": {}}
    )
    home_ok = bool(cfg.get("guide_home") and Path(str(cfg["guide_home"])).is_dir())
    named_ok = named_entity_module_present(str(cfg.get("guide_home") or ""))
    spring = cfg.get("spring_profiles") or f"neo4j,local,{cfg.get('profile')}"
    orch_root = Path(orch) if orch is not None else orchestrator_root()
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
    return {
        "config": cfg,
        "probe": probe,
        "neo4j": neo,
        "mcp": mcp,
        "projection": proj,
        "guide_stats": stats,
        "operator_directories": default_operator_directories(orch_root),
        "stack": stack,
        "checklist": checklist(cfg, probe, neo4j=neo),
        "embabel_mechanics": mechanics,
        "ingest_command": ingest_command(cfg),
        "docs": "docs/dice-projection-runbook.md",
        "playground": True,
    }


def _require_guide_up(rt: dict[str, Any]) -> dict[str, Any] | None:
    if rt.get("guide_up"):
        return None
    return {"ok": False, "error": "playground fake Guide is DOWN — Start Guide first"}


def fake_guide_action(
    target: Path | str,
    cfg: dict[str, Any],
    action: str,
    body: dict[str, Any] | None = None,
    *,
    orch: Path | str | None = None,
) -> dict[str, Any]:
    """Mutate playground runtime and return a Vue ``result`` / ``ensure`` object."""
    root = Path(target).expanduser().resolve()
    body = body or {}
    rt = load_runtime(root)
    orch_root = Path(orch) if orch is not None else orchestrator_root()

    if action == "ensure":
        home = seed_fake_guide_tree(root)
        if not str(cfg.get("guide_home") or "").strip():
            save_config(root, {"guide_home": str(home)})
        return {
            "ok": True,
            "action": "playground-stub",
            "guide_home": str(home),
            "log": "playground: stub Guide home ready (no git clone)",
        }

    if action == "neo4j_start":
        save_runtime(root, {"neo4j_up": True})
        return {"ok": True, "action": "playground-neo4j-start", "log": "playground: Neo4j UP"}

    if action == "neo4j_stop":
        save_runtime(root, {"neo4j_up": False, "guide_up": False, "pid": None})
        return {"ok": True, "action": "playground-neo4j-stop", "log": "playground: Neo4j DOWN"}

    if action == "start":
        if not body.get("skip_neo4j") and not rt.get("neo4j_up"):
            save_runtime(root, {"neo4j_up": True})
        started = utc_now()
        updates: dict[str, Any] = {
            "guide_up": True,
            "pid": FAKE_PID,
            "started_at": started,
            "mode": "playground-fake",
        }
        if not body.get("no_ingest"):
            updates["chunks"] = int(rt.get("chunks") or 0) + 7
            updates["projection_loaded"] = True
        save_runtime(root, updates)
        return {
            "ok": True,
            "action": "playground-guide-start",
            "pid": FAKE_PID,
            "log": "playground: Guide UP (no JVM)",
        }

    if action == "stop":
        save_runtime(root, {"guide_up": False, "pid": None})
        return {"ok": True, "action": "playground-guide-stop", "log": "playground: Guide DOWN"}

    if action == "ensure_profile":
        home = Path(str(cfg.get("guide_home") or seed_fake_guide_tree(root)))
        if not home.is_dir():
            home = seed_fake_guide_tree(root)
        profile = str(body.get("profile") or cfg.get("profile") or "sdlc-spdd")
        return ensure_spdd_profile(
            home,
            orchestrator_root=orch_root,
            profile=profile,
        )

    down = _require_guide_up(rt)
    if down and action in {
        "projection_load",
        "stats",
        "ingest",
        "purge_preview",
        "purge",
        "git_reset",
        "purge_all_rag",
    }:
        return down

    if action == "projection_load":
        save_runtime(
            root,
            {
                "projection_loaded": True,
                "work_id_count": len(WORKS),
                "canvas_count": len(WORKS),
                "area_count": 2,
            },
        )
        return {
            "ok": True,
            "status": 200,
            "data": {
                "workIdCount": len(WORKS),
                "canvasCount": len(WORKS),
                "areaCount": 2,
            },
        }

    if action == "stats":
        return {
            "ok": True,
            "status": 200,
            "data": {"contentElementCount": int(rt.get("chunks") or 0)},
        }

    if action == "ingest":
        chunks = int(rt.get("chunks") or 0) + 7
        save_runtime(root, {"chunks": chunks})
        return {
            "ok": True,
            "status": 200,
            "data": {"ingested": 7, "contentElementCount": chunks},
            "log": "playground: incremental ingest (+7 chunks)",
        }

    if action == "purge_preview":
        directory = str(body.get("directory") or orch_root)
        uri_prefix = str(body.get("uri_prefix") or "").strip()
        sample = [
            f"file://{directory}/spdd/canvas/{WORKS[0][0]}.md",
            f"file://{directory}/spdd/analysis/{WORKS[0][0]}-analysis.md",
        ]
        if uri_prefix:
            sample = [uri for uri in sample if uri.startswith(uri_prefix) or uri_prefix in uri]
        return {
            "ok": True,
            "status": 200,
            "data": {
                "matchCount": len(sample),
                "sample": sample,
                "directory": directory,
                "uriPrefix": uri_prefix or None,
            },
        }

    if action == "purge":
        chunks = max(0, int(rt.get("chunks") or 0) - 10)
        save_runtime(root, {"chunks": chunks})
        return {
            "ok": True,
            "status": 200,
            "data": {"deleted": 10, "contentElementCount": chunks},
            "log": "playground: purged matching ContentElements",
        }

    if action == "git_reset":
        directory = str(body.get("directory") or orch_root).strip()
        return {
            "ok": True,
            "status": 200,
            "data": {"directory": directory, "reset": True},
            "log": f"playground: git revision reset for {directory}",
        }

    if action == "purge_all_rag":
        save_runtime(root, {"chunks": 0})
        return {
            "ok": True,
            "status": 200,
            "data": {"deleted": int(rt.get("chunks") or 0), "contentElementCount": 0},
            "log": "playground: purged ALL RAG ContentElements",
        }

    return {"ok": False, "error": f"unknown playground guide action: {action}"}


def fake_issue_sync(
    target: Path | str,
    *,
    work_id: str,
    system: str | None,
    direction: str,
    apply: bool,
) -> dict[str, Any]:
    """Jira/GitHub sync stand-in — local report only, never hits APIs."""
    root = Path(target).expanduser().resolve()
    if not is_playground(root):
        raise ValueError("fake_issue_sync is only for playground targets")
    project = Project.resolve(root)
    req = project.milestone_path(work_id)
    if not req.is_file():
        raise FileNotFoundError(f"missing requirements/milestones/{work_id}.md")
    from ..integration_config import status_dict as integration_status

    tracker = (system or "").strip() or str(
        integration_status(project).get("effective_tracker") or "github"
    )
    if tracker not in {"jira", "github"}:
        raise ValueError("issue tracker disabled (SDLC_ISSUE_TRACKER=none)")
    jira_key, gh_num = issue_refs(work_id)
    ref = jira_key if tracker == "jira" else f"#{gh_num}"
    verb = "update" if apply else "would update"
    mode = "applied" if apply else "dry-run"
    title = req.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip() or work_id
    if apply:
        stamp = utc_now()
        text = req.read_text(encoding="utf-8")
        marker = f"Playground {tracker} {direction} at {stamp}"
        if "Playground " not in text:
            req.write_text(text.rstrip() + f"\n\n> {marker}\n", encoding="utf-8")
        else:
            req.write_text(text + f"\n> {marker}\n", encoding="utf-8")
    report = (
        f"[playground] [{mode}] {verb} {tracker} issue {ref} for {work_id}\n"
        f"title: {title}\n"
        f"{'existing_key: ' + jira_key if tracker == 'jira' else 'existing_number: #' + gh_num}\n"
        "No network — playground fake.\n"
    )
    cli = (
        f"./scripts/sdlc.sh issues {direction} {work_id} --system {tracker}"
        + (" --apply" if apply else "")
    )
    return {
        "ok": True,
        "target": str(root),
        "work_id": work_id,
        "system": tracker,
        "direction": direction,
        "apply": apply,
        "report": report,
        "cli": cli,
        "playground": True,
    }
