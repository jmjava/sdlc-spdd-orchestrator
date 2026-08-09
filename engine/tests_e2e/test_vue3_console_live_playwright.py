"""Live dual-repo Playwright: Vue3 Guide stack + real ADF viewer.

Opt-in (slow; needs dual-repo checkout + Neo4j Bolt + Chromium)::

    cd console-ui && npm ci && npm run build && cd ..
    pip install -e './engine[dev,viewer-e2e]'
    playwright install chromium

    # Guide JVM + projection (uses native /opt Neo4j when Bolt is open)
    SDLC_GUIDE_STACK_LIVE=1 \\
      pytest -q engine/tests_e2e/test_vue3_console_live_playwright.py -m guide_live

    # Real ADF viewer process (not stubbed)
    SDLC_ADF_VIEWER_LIVE=1 \\
      pytest -q engine/tests_e2e/test_vue3_console_live_playwright.py -m adf_viewer_live
"""

from __future__ import annotations

import os
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("flask")
pytest.importorskip("playwright")
pytest.importorskip("pytest_playwright")

from sdlc_engine.installer.app import create_app
from sdlc_engine.installer.guide import save_config
from sdlc_engine.installer.runner import orchestrator_root


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _tcp_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _ensure_vue_dist() -> Path:
    ui = orchestrator_root() / "console-ui"
    dist = ui / "dist"
    if (dist / "index.html").is_file() and os.environ.get("SDLC_VUE_FORCE_BUILD") != "1":
        return dist
    npm = os.environ.get("NPM_BIN", "npm")
    install = subprocess.run(
        [npm, "ci"], cwd=ui, capture_output=True, text=True, check=False
    )
    if install.returncode != 0:
        install = subprocess.run(
            [npm, "install"], cwd=ui, capture_output=True, text=True, check=False
        )
    if install.returncode != 0:
        pytest.skip(f"npm install failed:\n{install.stderr[-1500:]}")
    build = subprocess.run(
        [npm, "run", "build"], cwd=ui, capture_output=True, text=True, check=False
    )
    if build.returncode != 0 or not (dist / "index.html").is_file():
        pytest.fail(f"vite build failed:\n{build.stderr[-1500:]}")
    return dist


def _sibling_guide() -> Path:
    guide = orchestrator_root().parent / "guide"
    if not (guide / "scripts" / "append-ingest.sh").is_file():
        pytest.skip("dual-repo guide checkout missing (expected ../guide)")
    return guide.resolve()


@pytest.fixture(scope="session")
def vue_dist() -> Path:
    return _ensure_vue_dist()


@pytest.fixture()
def live_vue_real(tmp_path: Path, vue_dist: Path):
    """Flask + Vue3 dist with real viewer/Guide backends (no process stubs)."""
    from werkzeug.serving import make_server

    guide = _sibling_guide()
    save_config(
        tmp_path,
        {
            "guide_home": str(guide),
            "guide_git_url": "https://github.com/jmjava/guide.git",
            "guide_git_ref": os.environ.get("GUIDE_GIT_REF", "sdlc-spdd-projection-v1"),
            "profile": os.environ.get("GUIDE_PROFILE", "sdlc-spdd"),
            "spring_profiles": os.environ.get(
                "SPRING_PROFILES_ACTIVE", "neo4j,local,sdlc-spdd"
            ),
            "host": "127.0.0.1",
            "port": int(os.environ.get("GUIDE_PORT", "21337")),
            "neo4j_bolt_port": int(os.environ.get("NEO4J_BOLT_PORT", "7687")),
            "neo4j_http_port": int(os.environ.get("NEO4J_HTTP_PORT", "7474")),
            "neo4j_https_port": int(os.environ.get("NEO4J_HTTPS_PORT", "7473")),
            "neo4j_username": os.environ.get("NEO4J_USERNAME", "neo4j"),
            "neo4j_password": os.environ.get("NEO4J_PASSWORD", "brahmsian"),
        },
    )

    app = create_app(tmp_path, vue_dist=vue_dist)
    port = _free_port()
    server = make_server("127.0.0.1", port, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    deadline = time.time() + 5
    while time.time() < deadline:
        if _tcp_open("127.0.0.1", port):
            break
        time.sleep(0.05)
    else:
        server.shutdown()
        raise RuntimeError("live Vue console failed to start")

    yield {
        "base": f"http://127.0.0.1:{port}",
        "target": tmp_path,
        "guide": guide,
        "guide_port": int(os.environ.get("GUIDE_PORT", "21337")),
        "adf_port": int(os.environ.get("ADF_VIEWER_PORT", "5050")),
    }
    # Best-effort teardown via API
    try:
        client = app.test_client()
        client.post("/api/guide/stop", json={"target": str(tmp_path)})
        client.post(
            "/api/adf/stop",
            json={"target": str(tmp_path), "host": "127.0.0.1", "port": 5050},
        )
    except Exception:  # noqa: BLE001
        pass
    server.shutdown()


def _goto(page, live: dict[str, Any]) -> None:  # type: ignore[no-untyped-def]
    page.goto(live["base"] + "/")
    page.get_by_test_id("console-shell").wait_for()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="health-status"]')?.textContent || '')
          .includes('API ok')"""
    )


@pytest.mark.guide_live
def test_vue3_live_guide_start_projection_stop(page, live_vue_real) -> None:  # type: ignore[no-untyped-def]
    if not _tcp_open("127.0.0.1", 7687):
        pytest.skip("Neo4j Bolt :7687 not open (start native /opt/neo4j or compose)")

    timeout_ms = int(os.environ.get("GUIDE_START_TIMEOUT_SEC", "600")) * 1000
    page.set_default_timeout(max(timeout_ms, 60_000))

    _goto(page, live_vue_real)
    page.get_by_test_id("tab-guide").click()
    page.get_by_test_id("guide-panel").wait_for(state="visible")

    # Dual-repo default should already point at sibling guide; force-save anyway.
    page.get_by_test_id("guide-home").fill(str(live_vue_real["guide"]))
    page.get_by_test_id("btn-guide-save").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="guide-action-status"]')?.textContent || '')
          .includes('Config saved')"""
    )

    page.get_by_test_id("btn-neo-start").click()
    page.wait_for_function(
        """() => {
          const t = document.querySelector('[data-testid="guide-action-status"]')?.textContent || '';
          return t.includes('Start Neo4j OK');
        }"""
    )
    assert page.get_by_test_id("st-neo").inner_text().strip() == "UP"

    page.get_by_test_id("btn-guide-profile").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="guide-action-status"]')?.textContent || '')
          .includes('Write Embabel SPDD profile OK')"""
    )

    page.get_by_test_id("btn-guide-start-noingest").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="guide-action-status"]')?.textContent || '')
          .includes('Start Guide OK')"""
    )

    # Poll probe until Guide TCP is up (Spring boot can take several minutes).
    deadline = time.time() + (timeout_ms / 1000)
    while time.time() < deadline:
        page.get_by_test_id("btn-guide-probe").click()
        page.wait_for_timeout(2500)
        if page.get_by_test_id("st-guide").inner_text().strip() == "UP":
            break
    else:
        pytest.fail(
            f"Guide did not come UP within {timeout_ms // 1000}s — check "
            f"/tmp/sdlc-guide-*.log"
        )

    page.get_by_test_id("btn-proj-load").click()
    page.wait_for_function(
        """() => {
          const t = document.querySelector('[data-testid="guide-action-status"]')?.textContent || '';
          return t.includes('Load NamedEntity projection OK');
        }""",
        timeout=120_000,
    )
    page.get_by_test_id("btn-guide-stats").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="guide-action-status"]')?.textContent || '')
          .includes('Refresh Guide stats OK')"""
    )

    page.get_by_test_id("btn-guide-stop").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="guide-action-status"]')?.textContent || '')
          .includes('Stop Guide OK')"""
    )
    page.get_by_test_id("btn-guide-probe").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="st-guide"]')?.textContent || '')
          .trim() === 'DOWN'""",
        timeout=60_000,
    )


@pytest.mark.adf_viewer_live
def test_vue3_live_adf_viewer_start_stop(page, live_vue_real) -> None:  # type: ignore[no-untyped-def]
    adf_port = live_vue_real["adf_port"]
    if _tcp_open("127.0.0.1", adf_port):
        pytest.skip(f"port {adf_port} already in use — free it for live viewer test")

    _goto(page, live_vue_real)
    page.get_by_test_id("tab-adf").click()
    page.get_by_test_id("adf-panel").wait_for(state="visible")
    page.get_by_test_id("adf-port").fill(str(adf_port))

    page.get_by_test_id("btn-adf-start").click()
    page.wait_for_function(
        """() => {
          const meta = document.querySelector('[data-testid="adf-meta"]')?.textContent || '';
          return meta.includes('HTTP ok') || meta.includes('TCP open');
        }""",
        timeout=60_000,
    )
    assert _tcp_open("127.0.0.1", adf_port)

    page.get_by_test_id("btn-adf-stop").click()
    page.wait_for_function(
        """() => {
          const meta = document.querySelector('[data-testid="adf-meta"]')?.textContent || '';
          const status = document.querySelector('[data-testid="adf-status"]')?.textContent || '';
          return meta.includes('process stopped') || status.toLowerCase().includes('not running');
        }""",
        timeout=60_000,
    )
    # Port should release shortly after stop.
    deadline = time.time() + 15
    while time.time() < deadline and _tcp_open("127.0.0.1", adf_port):
        time.sleep(0.5)
    assert not _tcp_open("127.0.0.1", adf_port)
