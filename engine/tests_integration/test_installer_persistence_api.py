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
    # Save must return status_dict shape so the Persistence tab can re-apply UI.
    assert saved["backends"] == ["git-pointers", "sqlite"]
    assert saved["enabled"]["sqlite"] is True
    assert saved["enabled"]["guide-dice"] is False
    assert saved["notes"] == "installer-api"
    assert saved.get("config_path")
    assert saved.get("saved") is True
    assert (tmp_path / ".sdlc" / "persistence-config.json").is_file()

    # Second save from the returned shape must not silently drop backends.
    res = client.post(
        "/api/persistence/save",
        json={
            "target": str(tmp_path),
            "backends": saved["backends"],
            "guide_base_url": saved.get("guide", {}).get("base_url") or "",
            "notes": saved["notes"],
        },
    )
    assert res.status_code == 200
    again = res.get_json()
    assert again["backends"] == ["git-pointers", "sqlite"]
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

    res = client.post(
        "/api/persistence/save",
        json={"target": str(tmp_path), "backends": ["git-pointers", "sqllite"]},
    )
    assert res.status_code == 400
    assert "unknown" in (res.get_json().get("error") or "").lower()


def test_persistence_parity_endpoint(tmp_path: Path) -> None:
    from sdlc_engine.context_store import ContextStore
    from sdlc_engine.persistence import save_config
    from sdlc_engine.project import Project

    app = create_app(tmp_path)
    client = app.test_client()

    res = client.post("/api/persistence/parity", json={"target": str(tmp_path / "missing")})
    assert res.status_code == 400

    # Ledger + sqlite cache only (no live Guide in tests).
    save_config(tmp_path, {"backends": ["git-pointers", "sqlite"]})
    res = client.post("/api/persistence/parity", json={"target": str(tmp_path)})
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["parity"]["ledger"]["count"] == 0
    assert data["parity"]["sqlite"]["enabled"] is True
    assert data["parity"]["guide"]["enabled"] is False

    store = ContextStore(Project(tmp_path), guide_base_url="http://127.0.0.1:9")
    store.persist_lesson(
        kind="pattern",
        work_id="FEAT-900-console-parity",
        body="Console parity lesson",
        source="test",
        project_guide=False,
    )
    store.accept(work_id="FEAT-900-console-parity", project_guide=False)
    # Corrupt the cache to force drift (a missing db would just be rebuilt).
    import sqlite3

    with sqlite3.connect(tmp_path / ".sdlc" / "index.sqlite") as conn:
        conn.execute("DELETE FROM lessons")
    res = client.post("/api/persistence/parity", json={"target": str(tmp_path)})
    assert res.status_code == 200
    drift = res.get_json()
    assert drift["ok"] is False
    assert drift["parity"]["sqlite"]["missing"]

    # Repair re-derives the sqlite cache from the committed ledger.
    res = client.post(
        "/api/persistence/parity", json={"target": str(tmp_path), "repair": True}
    )
    assert res.status_code == 200
    assert res.get_json()["parity"]["repaired"] is True

    res = client.post("/api/persistence/parity", json={"target": str(tmp_path)})
    after = res.get_json()
    assert after["ok"] is True
    assert after["parity"]["ledger"]["count"] == 1


def test_persistence_tab_in_console_html(tmp_path: Path) -> None:
    from sdlc_engine.installer.runner import orchestrator_root

    ui = orchestrator_root() / "console-ui" / "src"
    app_vue = (ui / "App.vue").read_text(encoding="utf-8")
    persist = (ui / "components" / "PersistenceTab.vue").read_text(encoding="utf-8")
    assert 'id: "persistence"' in app_vue
    assert "/api/persistence/status" in persist
    assert "/api/persistence/save" in persist
    assert "/api/persistence/parity" in persist
    assert "persistence-parity" in persist
    assert "pb-sqlite" in persist
    assert "spdd/memory/lessons.jsonl" in persist
    assert "persistence-config.json" in persist
