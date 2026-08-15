"""Ops console APIs against a materialized playground tree."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("flask")

from sdlc_engine.installer.app import create_app
from sdlc_engine.installer.playground import WORKS, materialize_playground


def test_playground_dashboard_templates_sqlite_rollback(tmp_path: Path) -> None:
    dest = materialize_playground(tmp_path / "play")
    app = create_app(dest, vue_dist=False)
    client = app.test_client()
    active = WORKS[0][0]
    body = {"target": str(dest)}

    health = client.get("/api/health").get_json()
    assert health["playground"] is True

    dash = client.post("/api/dashboard/status", json=body).get_json()
    assert dash["ok"] is True
    assert dash["work"]["pointer"] == active
    assert dash["memory"]["accepted_count"] >= 1
    assert dash["memory"]["staged_count"] >= 1
    assert dash["backends"]["enabled"]["sqlite"] is True

    sugg = client.post("/api/dashboard/suggestions", json=body).get_json()
    assert sugg["ok"] is True
    assert sugg["suggestions"]

    tmpl = client.post(
        "/api/templates/render", json={**body, "work_id": active, "combo": "feature"}
    )
    assert tmpl.status_code == 200
    tmpl_body = tmpl.get_json()
    assert tmpl_body.get("ok") is not False
    assert active in json.dumps(tmpl_body)

    sqlite = client.post("/api/sqlite/rebuild", json=body).get_json()
    assert sqlite["ok"] is True
    status = client.post("/api/sqlite/status", json=body).get_json()
    assert status.get("exists") is True
    assert int(status.get("work_items") or 0) >= 1

    backups = client.post("/api/backups", json=body).get_json()
    assert backups["backups"]

    issues = client.post("/api/issues/status", json={**body, "work_id": active})
    assert issues.status_code == 200

    browse = client.post("/api/adf/browse", json={**body, "path": str(dest / "adf")}).get_json()
    assert browse["ok"] is True


def test_playground_guide_jira_github_fakes(tmp_path: Path) -> None:
    dest = materialize_playground(tmp_path / "play")
    app = create_app(dest, vue_dist=False)
    client = app.test_client()
    body = {"target": str(dest)}
    active = WORKS[0][0]

    dash = client.post("/api/dashboard/status", json=body).get_json()
    assert dash["integrations"]["jira"]["configured"] is True
    assert dash["integrations"]["github"]["configured"] is True
    assert dash["integrations"]["github"]["authenticated"] is True

    guide = client.post("/api/guide", json=body).get_json()
    assert guide["playground"] is True
    assert guide["probe"]["tcp_open"] is True
    assert guide["neo4j"]["bolt_open"] is True
    assert guide["guide_stats"]["data"]["contentElementCount"] == 42
    assert any(item.get("ok") for item in guide["checklist"] if item.get("id") == "guide_home")

    stopped = client.post("/api/guide/stop", json=body)
    assert stopped.status_code == 200
    assert stopped.get_json()["probe"]["tcp_open"] is False

    ingest_down = client.post("/api/guide/ingest", json=body)
    assert ingest_down.status_code == 400

    started = client.post("/api/guide/start", json={**body, "no_ingest": True})
    assert started.status_code == 200
    assert started.get_json()["probe"]["tcp_open"] is True

    ensure = client.post("/api/guide/ensure", json=body)
    assert ensure.status_code == 200
    assert ensure.get_json()["ensure"]["action"] == "playground-stub"

    neo = client.post("/api/guide/neo4j/start", json=body)
    assert neo.status_code == 200
    profile = client.post("/api/guide/ensure-profile", json=body)
    assert profile.status_code == 200
    proj = client.post("/api/guide/projection/load", json=body)
    assert proj.status_code == 200

    stats = client.post("/api/guide/stats", json=body).get_json()
    assert stats["ok"] is True
    assert stats["result"]["data"]["contentElementCount"] >= 42

    wipe = client.post("/api/guide/purge-all-rag", json={**body, "confirm": True})
    assert wipe.status_code == 200
    assert wipe.get_json()["guide_stats"]["data"]["contentElementCount"] == 0

    preview = client.post("/api/guide/purge/preview", json=body)
    assert preview.status_code == 200

    deny = client.post("/api/guide/purge", json=body)
    assert deny.status_code == 400
    assert "confirm" in deny.get_json()["error"]

    integ = client.post("/api/integrations/status", json=body).get_json()
    assert integ["jira"]["token_set"] is True
    assert integ["github"]["token_set"] is True

    jira = client.post(
        "/api/issues/sync",
        json={**body, "work_id": active, "system": "jira", "direction": "pull"},
    )
    assert jira.status_code == 200
    jira_body = jira.get_json()
    assert jira_body["ok"] is True
    assert jira_body["playground"] is True
    assert "PLAY-930" in jira_body["report"]

    gh = client.post(
        "/api/jira/sync",
        json={**body, "work_id": active, "direction": "push", "apply": True},
    )
    # /api/jira/sync forces system=jira
    assert gh.status_code == 200
    assert gh.get_json()["system"] == "jira"
    assert gh.get_json()["apply"] is True

    github = client.post(
        "/api/issues/sync",
        json={
            **body,
            "work_id": active,
            "system": "github",
            "direction": "pull",
            "apply": True,
        },
    )
    assert github.status_code == 200
    assert github.get_json()["system"] == "github"
    assert "playground" in github.get_json()["report"]

    missing = client.post(
        "/api/issues/sync",
        json={**body, "work_id": "NOPE-000", "system": "jira", "direction": "pull"},
    )
    assert missing.status_code == 400
