"""Ops console Dashboard landing tab API coverage (storage v3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("flask")

import sdlc_engine.installer.app as app_module
from sdlc_engine.installer.app import create_app

WID = "FEAT-001-dash"
OLD_WID = "FEAT-000-old"


@pytest.fixture(autouse=True)
def _deterministic_env(monkeypatch: pytest.MonkeyPatch):
    """Keep dashboard tests offline and independent of the dev machine."""
    for var in (
        "CONTEXT_BACKENDS",
        "SDLC_HOME",
        "SDLC_QUIET",
        "JIRA_BASE_URL",
        "JIRA_EMAIL",
        "JIRA_API_TOKEN",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(
        app_module,
        "_gh_auth_status",
        lambda timeout=3.0: {
            "installed": True,
            "authenticated": False,
            "detail": "gh not authenticated (run: gh auth login)",
        },
    )
    monkeypatch.setattr(
        app_module,
        "probe_guide",
        lambda host, port, timeout=1.5: {
            "host": host,
            "port": port,
            "tcp_open": False,
            "http_ok": False,
            "detail": "TCP closed (test stub)",
            "sse_url": "",
        },
    )
    monkeypatch.setattr(
        app_module,
        "viewer_process_status",
        lambda target, host="127.0.0.1", port=5050: {
            "pid": None,
            "alive": False,
            "host": host,
            "port": port,
            "port_open": False,
            "url": f"http://{host}:{port}/",
        },
    )


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _lesson(kind: str, work_id: str, ts: str, title: str, source: str = "retro") -> dict:
    return {
        "id": f"{kind}:{work_id}:engine:{source}",
        "kind": kind,
        "work_id": work_id,
        "area": "engine",
        "phase": "retro",
        "ts": ts,
        "title": title,
        "body": f"{title} detail",
        "source": source,
        "keywords": [],
        "commit": "",
        "schema": 1,
    }


def _seed_project(root: Path) -> None:
    """Populated project: accepted + staged records, registry events, workflow history."""
    _write_jsonl(
        root / "spdd" / "memory" / "lessons.jsonl",
        [
            _lesson("decision", OLD_WID, "2026-08-01T10:00:00Z", "Old decision"),
            _lesson("pitfall", OLD_WID, "2026-08-03T10:00:00Z", "Old pitfall"),
        ],
    )
    _write_jsonl(
        root / "spdd" / "memory" / "registry.jsonl",
        [
            {
                "event": "claim",
                "work_id": WID,
                "status": "active",
                "phase": "plan",
                "operation": "",
                "owner": "jm",
                "note": "",
                "ts": "2026-08-02T09:00:00Z",
            },
            {
                "event": "release",
                "work_id": OLD_WID,
                "status": "shelved",
                "phase": "retro",
                "operation": "",
                "owner": "jm",
                "note": "parked",
                "ts": "2026-08-04T09:00:00Z",
            },
        ],
    )
    _write_jsonl(
        root / ".sdlc" / "staged" / "lessons.jsonl",
        [_lesson("session", WID, "2026-08-05T10:00:00Z", "Working session", source="capture")],
    )
    workflows = root / ".sdlc" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    (workflows / f"{WID}.history").write_text(
        "2026-08-02T09:00:00Z\tcreate\twork_id=" + WID + "\n"
        "2026-08-06T10:00:00Z\tadvance\tphase=plan\n",
        encoding="utf-8",
    )
    (root / ".sdlc" / "pointer").write_text(WID, encoding="utf-8")
    milestone = root / "requirements" / "milestones" / f"{WID}.md"
    milestone.parent.mkdir(parents=True, exist_ok=True)
    milestone.write_text(
        f"# {WID}\n\n## Jira\n\n- PROJ-1\n\n## GitHub\n\n- #12\n", encoding="utf-8"
    )
    analysis = root / "spdd" / "analysis" / f"{WID}-analysis.md"
    analysis.parent.mkdir(parents=True, exist_ok=True)
    analysis.write_text(f"# {WID} analysis\n", encoding="utf-8")


def test_dashboard_status_fresh_empty(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    client = app.test_client()

    res = client.post("/api/dashboard/status", json={"target": str(tmp_path / "missing")})
    assert res.status_code == 400

    res = client.post("/api/dashboard/status", json={"target": str(tmp_path)})
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["work"]["pointer"] == ""
    assert data["work"]["open_gates"] == []
    assert data["memory"]["accepted_count"] == 0
    assert data["memory"]["staged_count"] == 0
    assert data["memory"]["needs_accept"] is False
    assert data["memory"]["registry_last_event"] is None
    assert data["backends"]["enabled"]["git-pointers"] is True
    assert data["backends"]["sqlite"]["exists"] is False
    assert data["backends"]["guide"]["reachable"] is False
    assert "Persistence tab" in data["backends"]["parity_hint"]
    assert data["integrations"]["jira"]["configured"] is False
    assert data["integrations"]["github"]["authenticated"] is False
    assert data["integrations"]["viewer"]["running"] is False

    res = client.post("/api/dashboard/activity", json={"target": str(tmp_path)})
    assert res.status_code == 200
    feed = res.get_json()
    assert feed["ok"] is True
    assert feed["items"] == []
    assert feed["limit"] == 20

    res = client.post("/api/dashboard/suggestions", json={"target": str(tmp_path)})
    assert res.status_code == 200
    ids = [s["id"] for s in res.get_json()["suggestions"]]
    assert "claim-work" in ids
    assert "accept-staged" not in ids
    # Default backends include guide-dice; the stubbed probe reports it down.
    assert "guide-down" in ids


def test_dashboard_status_populated(tmp_path: Path) -> None:
    _seed_project(tmp_path)
    app = create_app(tmp_path)
    client = app.test_client()

    res = client.post("/api/dashboard/status", json={"target": str(tmp_path)})
    assert res.status_code == 200
    data = res.get_json()
    work = data["work"]
    assert work["pointer"] == WID
    assert work["phase"] == "plan"
    assert WID in work["recommended_command"]
    gates = [g["gate"] for g in work["open_gates"]]
    assert "canvas_exists" in gates
    assert "requirement_documented" not in gates  # analysis file passes it

    mem = data["memory"]
    assert mem["accepted_count"] == 2
    assert mem["last_accepted_ts"] == "2026-08-03T10:00:00Z"
    assert mem["staged_count"] == 1
    assert mem["needs_accept"] is True
    last = mem["registry_last_event"]
    assert last["event"] == "release"
    assert last["work_id"] == OLD_WID
    assert last["owner"] == "jm"
    assert last["ts"] == "2026-08-04T09:00:00Z"


def test_dashboard_activity_merge_order_and_cap(tmp_path: Path) -> None:
    _seed_project(tmp_path)
    app = create_app(tmp_path)
    client = app.test_client()

    res = client.post("/api/dashboard/activity", json={"target": str(tmp_path)})
    assert res.status_code == 200
    items = res.get_json()["items"]
    # 2 registry + 2 accepted + 1 staged + 2 workflow history lines.
    assert len(items) == 7
    assert {it["source"] for it in items} == {"registry", "ledger", "staged", "workflow"}
    ts_list = [it["ts"] for it in items]
    assert ts_list == sorted(ts_list, reverse=True)
    assert items[0]["source"] == "workflow"
    assert items[0]["text"] == "advance phase=plan"
    assert items[0]["work_id"] == WID
    assert items[1]["source"] == "staged"
    assert "Working session" in items[1]["text"]
    registry_texts = [it["text"] for it in items if it["source"] == "registry"]
    assert f"claim {WID} by jm (plan)" in registry_texts
    ledger_texts = [it["text"] for it in items if it["source"] == "ledger"]
    assert f"pitfall accepted: Old pitfall [{OLD_WID}]" in ledger_texts

    # Cap: explicit limit, clamped max, and garbage falls back to default.
    res = client.post("/api/dashboard/activity", json={"target": str(tmp_path), "limit": 3})
    body = res.get_json()
    assert body["limit"] == 3
    assert len(body["items"]) == 3
    res = client.post("/api/dashboard/activity", json={"target": str(tmp_path), "limit": 500})
    assert res.get_json()["limit"] == 100
    res = client.post("/api/dashboard/activity?limit=2", json={"target": str(tmp_path)})
    assert len(res.get_json()["items"]) == 2
    res = client.post("/api/dashboard/activity", json={"target": str(tmp_path), "limit": "junk"})
    assert res.get_json()["limit"] == 20


def test_dashboard_suggestions_populated(tmp_path: Path) -> None:
    _seed_project(tmp_path)
    app = create_app(tmp_path)
    client = app.test_client()

    res = client.post("/api/dashboard/suggestions", json={"target": str(tmp_path)})
    assert res.status_code == 200
    suggestions = res.get_json()["suggestions"]
    by_id = {s["id"]: s["text"] for s in suggestions}

    assert "accept-staged" in by_id
    assert "1 staged record" in by_id["accept-staged"]
    assert "/sdlc-spdd-accept" in by_id["accept-staged"]
    assert WID in by_id["accept-staged"]
    by_meta = {s["id"]: s for s in suggestions}
    assert by_meta["accept-staged"]["tab"] == "persistence"
    assert by_meta["accept-staged"]["work_id"] == WID
    assert by_meta["open-gate"]["tab"] == "sqlite"
    assert by_meta["issue-sync"]["tab"] == "issues"

    assert "open-gate" in by_id
    assert "REASONS Canvas exists" in by_id["open-gate"]
    assert "/sdlc-spdd-plan" in by_id["open-gate"]

    assert "claim-work" not in by_id  # pointer is active
    assert "guide-down" in by_id

    # Requirements have ## Jira / ## GitHub and neither integration is ready.
    assert "issue-sync" in by_id
    assert "Issues tab" in by_id["issue-sync"] or "JIRA_*" in by_id["issue-sync"]
    assert "gh auth login" in by_id["issue-sync"]


def test_dashboard_suggestions_quiet_when_configured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_project(tmp_path)
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "op@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "not-a-real-token")
    monkeypatch.setattr(
        app_module,
        "_gh_auth_status",
        lambda timeout=3.0: {"installed": True, "authenticated": True, "detail": "gh authenticated"},
    )
    monkeypatch.setattr(
        app_module,
        "probe_guide",
        lambda host, port, timeout=1.5: {
            "host": host,
            "port": port,
            "tcp_open": True,
            "http_ok": True,
            "detail": "HTTP 200",
            "sse_url": "",
        },
    )
    app = create_app(tmp_path)
    client = app.test_client()
    res = client.post("/api/dashboard/suggestions", json={"target": str(tmp_path)})
    ids = [s["id"] for s in res.get_json()["suggestions"]]
    assert "issue-sync" not in ids
    assert "guide-down" not in ids


def test_dashboard_never_echoes_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_project(tmp_path)
    secret_token = "SECRET-JIRA-TOKEN-a1b2c3"
    secret_email = "secret-user@example.com"
    secret_url = "https://secret-tenant.atlassian.net"
    monkeypatch.setenv("JIRA_BASE_URL", secret_url)
    monkeypatch.setenv("JIRA_EMAIL", secret_email)
    monkeypatch.setenv("JIRA_API_TOKEN", secret_token)
    app = create_app(tmp_path)
    client = app.test_client()

    for endpoint in (
        "/api/dashboard/status",
        "/api/dashboard/activity",
        "/api/dashboard/suggestions",
    ):
        res = client.post(endpoint, json={"target": str(tmp_path)})
        assert res.status_code == 200
        raw = res.data.decode("utf-8")
        assert secret_token not in raw
        assert secret_email not in raw
        assert secret_url not in raw

    status = client.post("/api/dashboard/status", json={"target": str(tmp_path)}).get_json()
    jira = status["integrations"]["jira"]
    assert jira["base_url_set"] is True
    assert jira["email_set"] is True
    assert jira["token_set"] is True
    assert jira["configured"] is True


def test_dashboard_tab_in_console_html(tmp_path: Path) -> None:
    from sdlc_engine.installer.runner import orchestrator_root

    ui = orchestrator_root() / "console-ui" / "src"
    app_vue = (ui / "App.vue").read_text(encoding="utf-8")
    dash = (ui / "components" / "DashboardTab.vue").read_text(encoding="utf-8")
    assert 'id: "dashboard"' in app_vue
    assert 'id: "install"' in app_vue
    assert 'active = ref("dashboard")' in app_vue
    assert "/api/dashboard/status" in dash
    assert "/api/dashboard/activity" in dash
    assert "/api/dashboard/suggestions" in dash
    assert "dash-suggestions" in dash
    assert "dash-activity" in dash
    assert "btn-dash-refresh" in dash
    assert "dash-open-templates" in dash
    assert "dash-suggestion-" in dash
