"""Playwright GUI tests for the ops console (critical path per tab).

Requires optional extras::

    pip install -e './engine[dev,viewer-e2e]'
    playwright install chromium

Run::

    pytest -q engine/tests/test_console_playwright.py -m console_e2e
    # or: SDLC_CONSOLE_E2E=1 pytest -q engine/tests/test_console_playwright.py
"""

from __future__ import annotations

import json
import socket
import threading
import time
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("flask")
pytest.importorskip("playwright")
pytest.importorskip("pytest_playwright")

from sdlc_engine.installer import app as installer_app
from sdlc_engine.installer import viewer_runtime as vr
from sdlc_engine.installer.app import create_app

pytestmark = pytest.mark.console_e2e


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture()
def live_console(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Start ops console on a free port; stub ADF viewer process lifecycle."""
    from werkzeug.serving import make_server

    state: dict[str, Any] = {"alive": False, "pid": 424242, "host": "127.0.0.1", "port": 5050}

    def _save(target: Path | str, host: str, port: int) -> None:
        root = Path(target).expanduser().resolve()
        (root / ".sdlc").mkdir(parents=True, exist_ok=True)
        vr._save_runtime(
            root,
            {
                "pid": state["pid"],
                "port": int(port),
                "host": host,
                "log_path": f"/tmp/sdlc-adf-viewer-{port}.log",
                "started_at": "2026-01-01T00:00:00Z",
                "target": str(root),
            },
        )
        state["alive"] = True
        state["host"] = host
        state["port"] = int(port)

    def fake_start(target: Path | str, *, host: str = "127.0.0.1", port: int = 5050) -> dict[str, Any]:
        if state["alive"]:
            return {"ok": False, "error": "ADF Viewer already running", "log": ""}
        _save(target, host, port)
        return {"ok": True, "log": "stub start", "pid": state["pid"]}

    def fake_stop(target: Path | str) -> dict[str, Any]:
        root = Path(target).expanduser().resolve()
        vr._clear_runtime(root)
        state["alive"] = False
        return {"ok": True, "log": "stub stop"}

    def fake_restart(target: Path | str, *, host: str = "127.0.0.1", port: int = 5050) -> dict[str, Any]:
        fake_stop(target)
        return fake_start(target, host=host, port=port)

    monkeypatch.setattr(vr, "_pid_alive", lambda pid: bool(state["alive"]))
    monkeypatch.setattr(vr, "_tcp_open", lambda *a, **k: bool(state["alive"]))
    monkeypatch.setattr(
        vr,
        "probe_viewer",
        lambda host="127.0.0.1", port=5050, **k: {
            "host": host,
            "port": int(port),
            "tcp_open": bool(state["alive"]),
            "http_ok": bool(state["alive"]),
            "url": f"http://{host}:{int(port)}/",
            "detail": "HTTP 200" if state["alive"] else "closed",
        },
    )
    for mod in (vr, installer_app):
        monkeypatch.setattr(mod, "start_viewer", fake_start)
        monkeypatch.setattr(mod, "stop_viewer", fake_stop)
        monkeypatch.setattr(mod, "restart_viewer", fake_restart)

    app = create_app(tmp_path)
    port = _free_port()
    server = make_server("127.0.0.1", port, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)
    else:
        server.shutdown()
        raise RuntimeError("ops console failed to start")

    yield {"base": f"http://127.0.0.1:{port}", "target": tmp_path, "state": state}
    server.shutdown()


def _goto_console(page, live_console: dict[str, Any]) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_console["base"] + "/")
    page.locator(".brand").wait_for()
    assert "Ops Console" in page.locator(".brand").inner_text()
    page.locator("#target").fill(str(live_console["target"]))


def test_install_detect_and_dry_run(page, live_console) -> None:  # type: ignore[no-untyped-def]
    _goto_console(page, live_console)
    page.locator("#btn-detect").click()
    page.wait_for_function(
        "() => document.getElementById('mode-pill').textContent.trim() !== 'idle'"
    )
    assert page.locator("#mode-pill").inner_text().strip().lower() == "fresh"
    assert "install" in page.locator("#detect-detail").inner_text().lower()

    page.locator("#opt-dry").check()
    page.locator("#btn-run").click()
    page.wait_for_function(
        "() => {\n"
        "  const t = document.getElementById('log').textContent || '';\n"
        "  return t.length > 0 && !t.includes('Awaiting action');\n"
        "}"
    )
    log = page.locator("#log").inner_text()
    assert log.strip()
    assert "dry" in log.lower() or "setup-agent-prompts" in log or "Would" in log


def test_sqlite_refresh_renders_stats(page, live_console) -> None:  # type: ignore[no-untyped-def]
    _goto_console(page, live_console)
    page.locator(".tab[data-tab='sqlite']").click()
    page.locator("#pane-sqlite").wait_for(state="visible")
    page.locator("#btn-sqlite-refresh").click()
    page.wait_for_function(
        "() => document.getElementById('sqlite-meta').textContent !== 'Not loaded.'"
    )
    assert page.locator("#sq-work").inner_text() != "—"
    assert page.locator("#sqlite-stats").count() == 1


def test_rollback_backups_pane_loads(page, live_console) -> None:  # type: ignore[no-untyped-def]
    _goto_console(page, live_console)
    page.locator(".tab[data-tab='rollback']").click()
    page.locator("#pane-rollback").wait_for(state="visible")
    page.locator("#btn-backups-refresh").click()
    page.wait_for_function(
        "() => !document.getElementById('backup-rows').textContent.includes('Refresh to load')"
    )
    rows = page.locator("#backup-rows").inner_text()
    assert "No backups" in rows or "Restore" in rows or rows.strip() != ""


def test_guide_tab_shows_config_and_controls(page, live_console) -> None:  # type: ignore[no-untyped-def]
    _goto_console(page, live_console)
    page.locator(".tab[data-tab='guide']").click()
    page.locator("#pane-guide").wait_for(state="visible")
    page.locator("#guide-home").wait_for()
    assert page.locator("#guide-port").count() == 1
    assert page.locator("#btn-guide-start").count() == 1
    assert page.locator("#btn-neo-start").count() == 1
    assert page.locator("#btn-guide-save").count() == 1
    # Status strip present without starting live Guide/Java
    page.locator("#btn-guide-probe").click()
    page.wait_for_function(
        "() => document.getElementById('guide-probe').textContent !== 'Status not loaded.'"
    )


def test_adf_start_status_open_stop(page, live_console) -> None:  # type: ignore[no-untyped-def]
    _goto_console(page, live_console)
    page.locator(".tab[data-tab='adf']").click()
    page.locator("#pane-adf").wait_for(state="visible")
    assert page.locator("#btn-adf-open").count() == 1

    page.locator("#btn-adf-start").click()
    page.wait_for_function(
        """() => {
          const meta = document.getElementById('adf-meta').textContent || '';
          return meta.includes('process alive') || meta.includes('url http');
        }"""
    )
    meta = page.locator("#adf-meta").inner_text()
    assert "5050" in meta or "http://127.0.0.1" in meta
    assert live_console["state"]["alive"] is True

    page.locator("#btn-adf-stop").click()
    page.wait_for_function(
        """() => {
          const meta = document.getElementById('adf-meta').textContent || '';
          return meta.includes('process stopped');
        }"""
    )
    assert live_console["state"]["alive"] is False


def test_adf_init_requires_selection(page, live_console) -> None:  # type: ignore[no-untyped-def]
    _goto_console(page, live_console)
    page.locator(".tab[data-tab='adf']").click()
    page.locator("#pane-adf").wait_for(state="visible")
    page.locator("#btn-adf-init").click()
    page.wait_for_function(
        """() => (document.getElementById('adf-init-status').textContent || '')
          .includes('Select an ADF file first')"""
    )


def test_adf_browse_select_and_init_work(page, live_console, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SDLC_USER", "playwright-adf")
    target = Path(live_console["target"])
    adf_dir = target / "adf"
    adf_dir.mkdir(parents=True, exist_ok=True)
    adf = adf_dir / "ORCH-77.adf.json"
    adf.write_text(
        json.dumps(
            {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "heading",
                        "attrs": {"level": 1},
                        "content": [{"type": "text", "text": "Playwright ADF init"}],
                    },
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "End-to-end from console"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    _goto_console(page, live_console)
    page.locator(".tab[data-tab='adf']").click()
    page.locator("#pane-adf").wait_for(state="visible")
    page.locator("#btn-adf-browse-adf").click()
    page.wait_for_function(
        """() => {
          const list = document.getElementById('adf-browser-list');
          return list && list.textContent && list.textContent.includes('ORCH-77.adf.json');
        }"""
    )
    page.locator("#adf-browser-list .browser-row", has_text="ORCH-77.adf.json").click()
    page.wait_for_function(
        """() => (document.getElementById('adf-selected').textContent || '')
          .includes('ORCH-77.adf.json')"""
    )
    page.locator("#adf-work-id").fill("FEAT-013-playwright-adf-init")
    page.locator("#adf-work-title").fill("Playwright title")
    page.locator("#btn-adf-init-dry").click()
    page.wait_for_function(
        """() => (document.getElementById('adf-init-status').textContent || '')
          .includes('Would create FEAT-013-playwright-adf-init')"""
    )
    assert not (target / "spdd" / "canvas" / "FEAT-013-playwright-adf-init.md").exists()

    page.locator("#btn-adf-init").click()
    page.wait_for_function(
        """() => (document.getElementById('adf-init-status').textContent || '')
          .includes('Created FEAT-013-playwright-adf-init')"""
    )
    status = page.locator("#adf-init-status").inner_text()
    assert "sdlc-spdd-analysis" in status
    canvas = target / "spdd" / "canvas" / "FEAT-013-playwright-adf-init.md"
    assert canvas.is_file()
    text = canvas.read_text(encoding="utf-8")
    assert "Playwright title" in text
    assert "End-to-end from console" in text
    assert "Source System: ADF" in text
    assert (target / "requirements" / "milestones" / "FEAT-013-playwright-adf-init.md").is_file()
    # storage v3: claims append to the committed JSONL registry event log.
    reg = (target / "spdd" / "memory" / "registry.jsonl").read_text(encoding="utf-8")
    assert "playwright-adf" in reg
    assert "FEAT-013-playwright-adf-init" in reg
