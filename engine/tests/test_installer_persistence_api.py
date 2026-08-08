"""Ops console persistence options API coverage (#79/#90)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("flask")

from sdlc_engine.installer.app import create_app


def test_persistence_status_and_save(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    client = app.test_client()

    res = client.post("/api/persistence/status", json={"target": str(tmp_path)})
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["enabled"]["git-pointers"] is True
    assert "git-pointers" in data["available"]

    res = client.post(
        "/api/persistence/save",
        json={
            "target": str(tmp_path),
            "backends": "git-pointers,sqlite",
            "guide_base_url": "http://127.0.0.1:21337",
            "notes": "installer-api",
        },
    )
    assert res.status_code == 200
    saved = res.get_json()
    assert saved["backends"] == ["git-pointers", "sqlite"]
    assert saved["notes"] == "installer-api"
    assert (tmp_path / ".sdlc" / "persistence-config.json").is_file()

    res = client.post("/api/persistence/status", json={"target": str(tmp_path)})
    assert res.status_code == 200
    again = res.get_json()
    assert again["enabled"]["guide-dice"] is False
    assert again["config_exists"] is True


def test_persistence_save_validation(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    client = app.test_client()

    res = client.post("/api/persistence/status", json={"target": str(tmp_path / "missing")})
    assert res.status_code == 400

    res = client.post("/api/persistence/save", json={"target": str(tmp_path)})
    assert res.status_code == 400
    assert "backends" in (res.get_json().get("error") or "")

    res = client.post(
        "/api/persistence/save",
        json={"target": str(tmp_path), "backends": {"nope": True}},
    )
    assert res.status_code == 400

    res = client.post(
        "/api/persistence/save",
        json={
            "target": str(tmp_path / "nope"),
            "backends": ["git-pointers"],
        },
    )
    assert res.status_code == 400


def test_persistence_tab_in_console_html(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    client = app.test_client()
    html = client.get("/").data.decode("utf-8")
    assert 'data-tab="persist"' in html
    assert "/api/persistence/status" in html
    assert "/api/persistence/save" in html
    assert "pb-sqlite" in html
