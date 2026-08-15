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
