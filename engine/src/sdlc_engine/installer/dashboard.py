"""Dashboard landing-tab helpers for the ops console.

Kept out of ``app.py`` so Flask route registration stays readable. ``app.py``
re-exports the public names so existing monkeypatches
(``_gh_auth_status``, ``probe_guide``, ``_dashboard_status``) still work.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from sdlc_engine.integration_config import status_dict as integration_status
from sdlc_engine.lessons_ledger import LessonsLedger
from sdlc_engine.persistence import status_dict as persistence_status
from sdlc_engine.phases import GATE_LABELS, gates_for_phase
from sdlc_engine.project import Project
from sdlc_engine.registry import TeamRegistry
from sdlc_engine.workflow import WorkflowEngine

from .guide import load_config
from .viewer_runtime import DEFAULT_HOST as ADF_DEFAULT_HOST
from .viewer_runtime import DEFAULT_PORT as ADF_DEFAULT_PORT

GhAuth = Callable[..., dict[str, Any]]
GuideProbe = Callable[..., dict[str, Any]]
ViewerStatus = Callable[..., dict[str, Any]]


def gh_auth_status(timeout: float = 3.0) -> dict[str, Any]:
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


def build_dashboard_status(
    target: Path,
    *,
    gh_auth: GhAuth,
    guide_probe: GuideProbe,
    viewer_status: ViewerStatus,
) -> dict[str, Any]:
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
    probe = guide_probe(host, port, timeout=1.0)
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
        "parity_hint": "Run parity from the Persistence tab (Check ledger parity / Parity + repair).",
    }

    viewer = viewer_status(target)
    integ = integration_status(project)
    gh_cli = gh_auth()
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


def dashboard_activity(project: Project, limit: int) -> list[dict[str, Any]]:
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


def requirements_issue_sections(project: Project, *, max_files: int = 40) -> dict[str, bool]:
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


def dashboard_suggestions(project: Project, status: dict[str, Any]) -> list[dict[str, Any]]:
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
                "tab": "persistence",
                "work_id": work.get("pointer") or "",
            }
        )

    pointer = work.get("pointer") or ""
    open_gates = work.get("open_gates") or []
    if pointer and open_gates:
        top = open_gates[0].get("label") or open_gates[0].get("gate") or ""
        text = f"{pointer} ({work.get('phase') or '?'}): open gate — {top}."
        if work.get("recommended_command"):
            text += f" Do now: {work['recommended_command']}"
        out.append(
            {
                "id": "open-gate",
                "text": text,
                "tab": "sqlite",
                "work_id": pointer,
            }
        )
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
        out.append({"id": "claim-work", "text": text, "tab": "sqlite", "work_id": ""})

    guide = backends.get("guide") or {}
    if guide.get("enabled") and not guide.get("reachable"):
        out.append(
            {
                "id": "guide-down",
                "text": (
                    "Guide is configured but unreachable — start it from the Guide tab, "
                    "or continue files-only (normal)."
                ),
                "tab": "guide",
                "work_id": work.get("pointer") or "",
            }
        )

    jira_missing = not (integrations.get("jira") or {}).get("configured")
    gh_missing = not (integrations.get("github") or {}).get("authenticated")
    if jira_missing or gh_missing:
        sections = requirements_issue_sections(project)
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
                    "tab": "issues",
                    "work_id": work.get("pointer") or "",
                }
            )
    return out
