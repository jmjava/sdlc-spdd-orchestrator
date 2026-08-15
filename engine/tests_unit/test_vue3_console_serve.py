"""Unit coverage for serving Vue3 dist from the ops console Flask app."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("flask")

from sdlc_engine.installer.app import create_app
from sdlc_engine.installer import vue_console as vc


def _write_dist(root: Path) -> Path:
    dist = root / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text(
        "<!doctype html><html><body><div id='app'>vue</div></body></html>",
        encoding="utf-8",
    )
    (assets / "app.js").write_text("console.log('ok')", encoding="utf-8")
    return dist


def test_create_app_serves_vue_dist_index(tmp_path: Path) -> None:
    dist = _write_dist(tmp_path)
    app = create_app(tmp_path, vue_dist=dist)
    client = app.test_client()

    res = client.get("/")
    assert res.status_code == 200
    assert b"id='app'" in res.data or b'id="app"' in res.data or b"vue" in res.data

    res = client.get("/assets/app.js")
    assert res.status_code == 200
    assert b"console.log" in res.data

    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


def test_create_app_rejects_missing_vue_dist(tmp_path: Path) -> None:
    missing = tmp_path / "missing-dist"
    with pytest.raises(FileNotFoundError, match="index.html"):
        create_app(tmp_path, vue_dist=missing)


def test_create_app_stub_when_vue_disabled(tmp_path: Path) -> None:
    app = create_app(tmp_path, vue_dist=False)
    res = app.test_client().get("/")
    assert res.status_code == 200
    assert b"SDLC-SPDD Ops Console" in res.data
    assert b"Vue3 console dist is not built" in res.data
    assert b"/api/health" in res.data


def test_resolve_vue_console_dist_explicit_and_auto(tmp_path: Path) -> None:
    dist = _write_dist(tmp_path)
    assert vc.resolve_vue_console_dist(dist) == dist.resolve()
    assert vc.resolve_vue_console_dist(False) is None
    assert vc.resolve_vue_console_dist(env={"SDLC_CONSOLE_UI": "stub"}) is None
    assert vc.resolve_vue_console_dist(env={"SDLC_VUE_CONSOLE_DIST": str(dist)}) == dist.resolve()

    orch = tmp_path / "orch"
    auto = orch / "console-ui" / "dist"
    auto.mkdir(parents=True)
    (auto / "index.html").write_text("<html></html>", encoding="utf-8")
    assert vc.resolve_vue_console_dist(orch=orch) == auto
    assert vc.resolve_vue_console_dist(orch=tmp_path / "empty") is None


def test_resolve_vue_console_dist_env_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="index.html"):
        vc.resolve_vue_console_dist(env={"SDLC_VUE_CONSOLE_DIST": str(tmp_path / "nope")})


def test_ensure_vue_console_dist_skips_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        calls.append(cmd)
        raise AssertionError("npm should not run when build=False")

    monkeypatch.setattr(vc.subprocess, "run", fake_run)
    assert vc.ensure_vue_console_dist(build=False, orch=tmp_path) is None
    assert calls == []


def test_ensure_vue_console_dist_builds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ui = tmp_path / "console-ui"
    ui.mkdir()
    (ui / "package.json").write_text("{}", encoding="utf-8")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        if cmd[-1] == "build":
            dist = ui / "dist"
            dist.mkdir()
            (dist / "index.html").write_text("<html>ok</html>", encoding="utf-8")
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(vc.subprocess, "run", fake_run)
    found = vc.ensure_vue_console_dist(build=True, orch=tmp_path, npm="npm")
    assert found is not None
    assert vc.vue_dist_ready(found)


def test_create_app_autodetects_orch_dist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ui_dist = tmp_path / "console-ui" / "dist" / "assets"
    ui_dist.mkdir(parents=True)
    (tmp_path / "console-ui" / "dist" / "index.html").write_text(
        "<html>auto-vue</html>", encoding="utf-8"
    )
    monkeypatch.setattr("sdlc_engine.installer.app.orchestrator_root", lambda: tmp_path)
    app = create_app(tmp_path)
    assert app.config["VUE_CONSOLE_DIST"]
    assert b"auto-vue" in app.test_client().get("/").data


def test_ensure_vue_console_dist_skip_build_env(tmp_path: Path) -> None:
    ui = tmp_path / "console-ui"
    ui.mkdir()
    (ui / "package.json").write_text("{}", encoding="utf-8")
    assert (
        vc.ensure_vue_console_dist(
            build=True, orch=tmp_path, env={"SDLC_VUE_SKIP_BUILD": "1"}
        )
        is None
    )
