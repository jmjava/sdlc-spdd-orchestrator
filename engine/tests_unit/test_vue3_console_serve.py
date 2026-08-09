"""Unit coverage for serving Vue3 dist from the ops console Flask app."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("flask")

from sdlc_engine.installer.app import create_app


def test_create_app_serves_vue_dist_index(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text(
        "<!doctype html><html><body><div id='app'>vue</div></body></html>",
        encoding="utf-8",
    )
    (assets / "app.js").write_text("console.log('ok')", encoding="utf-8")

    app = create_app(tmp_path, vue_dist=dist)
    client = app.test_client()

    res = client.get("/")
    assert res.status_code == 200
    assert b"id='app'" in res.data or b'id="app"' in res.data or b"vue" in res.data

    res = client.get("/assets/app.js")
    assert res.status_code == 200
    assert b"console.log" in res.data

    # API still works beside the SPA
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


def test_create_app_rejects_missing_vue_dist(tmp_path: Path) -> None:
    missing = tmp_path / "missing-dist"
    with pytest.raises(FileNotFoundError, match="index.html"):
        create_app(tmp_path, vue_dist=missing)
