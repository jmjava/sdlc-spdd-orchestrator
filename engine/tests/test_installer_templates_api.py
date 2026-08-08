"""Ops console ADF template API + Vue3 persistence smoke contract."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("flask")

from sdlc_engine.installer.app import create_app


def _seed_work(root: Path, work_id: str) -> None:
    (root / "requirements" / "milestones").mkdir(parents=True)
    (root / "requirements" / "milestones" / f"{work_id}.md").write_text(
        f"## Summary\n\nTemplate API for {work_id}.\n",
        encoding="utf-8",
    )


def test_templates_list_and_render(tmp_path: Path) -> None:
    work_id = "FEAT-910-console-templates"
    _seed_work(tmp_path, work_id)
    app = create_app(tmp_path)
    client = app.test_client()

    res = client.post("/api/templates", json={})
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["count"] >= 3
    assert {c["id"] for c in data["combos"]} >= {"feature", "spike", "bug"}

    res = client.post(
        "/api/templates/render",
        json={"target": str(tmp_path), "work_id": work_id, "combo": "feature"},
    )
    assert res.status_code == 200
    rendered = res.get_json()
    assert rendered["ok"] is True
    assert rendered["adf"]["type"] == "doc"
    assert work_id in rendered["markdown"]


def test_templates_render_validation(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    client = app.test_client()

    res = client.post("/api/templates/render", json={"target": str(tmp_path)})
    assert res.status_code == 400
    assert "work_id" in (res.get_json().get("error") or "")

    res = client.post(
        "/api/templates/render",
        json={
            "target": str(tmp_path / "missing"),
            "work_id": "FEAT-911-x",
        },
    )
    assert res.status_code == 400


def test_persistence_status_smoke_for_vue_shell(tmp_path: Path) -> None:
    """Vue3 shell first-slice acceptance: live /api/persistence/status works."""
    app = create_app(tmp_path)
    client = app.test_client()
    res = client.post("/api/persistence/status", json={"target": str(tmp_path)})
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "available" in data
    assert data["target"] == str(tmp_path.resolve())
