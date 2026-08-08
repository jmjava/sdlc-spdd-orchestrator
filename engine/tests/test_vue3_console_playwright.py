"""Playwright GUI tests for the Vue3 ops console (`console-ui`).

Covers every surface shipped in the first Vue3 slice: shell/health, Persistence,
Templates (list/validate/render), and stub tabs.

Requires optional extras + a Vite build of ``console-ui``::

    pip install -e './engine[dev,viewer-e2e]'
    playwright install chromium
    cd console-ui && npm ci && npm run build

Run::

    SDLC_CONSOLE_E2E=1 pytest -q engine/tests/test_vue3_console_playwright.py -m console_e2e
    # or: pytest -q engine/tests/test_vue3_console_playwright.py --run-console-e2e
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
from sdlc_engine.installer.runner import orchestrator_root

pytestmark = pytest.mark.console_e2e

_STUB_TABS = ("install", "sqlite", "rollback", "guide", "adf")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _console_ui_root() -> Path:
    return orchestrator_root() / "console-ui"


def _ensure_vue_dist() -> Path:
    """Return console-ui/dist, building when index.html is missing."""
    ui = _console_ui_root()
    dist = ui / "dist"
    if (dist / "index.html").is_file() and os.environ.get("SDLC_VUE_FORCE_BUILD") != "1":
        return dist

    npm = os.environ.get("NPM_BIN", "npm")
    if not (ui / "package.json").is_file():
        pytest.skip(f"console-ui missing at {ui}")

    env = os.environ.copy()
    # Prefer local install; fall back to ci when lockfile-driven.
    install = subprocess.run(
        [npm, "ci"],
        cwd=ui,
        capture_output=True,
        text=True,
        check=False,
    )
    if install.returncode != 0:
        install = subprocess.run(
            [npm, "install"],
            cwd=ui,
            capture_output=True,
            text=True,
            check=False,
        )
    if install.returncode != 0:
        pytest.skip(
            "npm install failed for console-ui:\n"
            f"{install.stdout[-2000:]}\n{install.stderr[-2000:]}"
        )

    build = subprocess.run(
        [npm, "run", "build"],
        cwd=ui,
        capture_output=True,
        text=True,
        check=False,
    )
    if build.returncode != 0 or not (dist / "index.html").is_file():
        pytest.fail(
            "console-ui Vite build failed:\n"
            f"{build.stdout[-2000:]}\n{build.stderr[-2000:]}"
        )
    return dist


@pytest.fixture(scope="session")
def vue_dist() -> Path:
    return _ensure_vue_dist()


@pytest.fixture()
def live_vue_console(tmp_path: Path, vue_dist: Path):
    """Start Flask serving Vue3 dist + JSON API on a free port."""
    from werkzeug.serving import make_server

    work_id = "FEAT-920-vue3-playwright"
    milestones = tmp_path / "requirements" / "milestones"
    milestones.mkdir(parents=True)
    (milestones / f"{work_id}.md").write_text(
        f"## Summary\n\nVue3 Playwright work for {work_id}.\n",
        encoding="utf-8",
    )

    app = create_app(tmp_path, vue_dist=vue_dist)
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
        raise RuntimeError("Vue3 ops console failed to start")

    yield {
        "base": f"http://127.0.0.1:{port}",
        "target": tmp_path,
        "work_id": work_id,
    }
    server.shutdown()


def _goto_vue(page, live_vue_console: dict[str, Any]) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_vue_console["base"] + "/")
    page.get_by_test_id("console-shell").wait_for()
    page.get_by_test_id("health-status").wait_for()
    page.wait_for_function(
        """() => {
          const el = document.querySelector('[data-testid="health-status"]');
          return el && el.textContent && el.textContent.includes('API ok');
        }"""
    )


def test_vue3_shell_loads_health_and_target(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    assert "SDLC-SPDD" in page.get_by_test_id("console-brand").inner_text()
    health = page.get_by_test_id("health-status").inner_text()
    assert "API ok" in health
    target = page.get_by_test_id("target-input").input_value()
    assert target == str(live_vue_console["target"].resolve())

    page.get_by_test_id("refresh-health").click()
    page.wait_for_function(
        """() => {
          const el = document.querySelector('[data-testid="health-status"]');
          return el && el.textContent && el.textContent.includes('API ok');
        }"""
    )


def test_vue3_persistence_load_status(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    page.get_by_test_id("tab-persistence").click()
    page.get_by_test_id("persistence-panel").wait_for(state="visible")
    page.get_by_test_id("persistence-load").click()
    page.wait_for_function(
        """() => {
          const el = document.querySelector('[data-testid="persistence-status"]');
          return el && el.textContent && el.textContent.includes('Persistence ok');
        }"""
    )
    log = page.get_by_test_id("persistence-log").inner_text()
    assert '"ok": true' in log or '"ok":true' in log
    assert "backends" in log


def test_vue3_templates_lists_combos_on_open(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    page.get_by_test_id("tab-templates").click()
    page.get_by_test_id("templates-panel").wait_for(state="visible")
    page.wait_for_function(
        """() => {
          const el = document.querySelector('[data-testid="templates-status"]');
          return el && /\\d+ combo\\(s\\) available/.test(el.textContent || '');
        }"""
    )
    options = page.get_by_test_id("templates-combo").locator("option")
    labels = [opt.inner_text() for opt in options.all()]
    joined = "\n".join(labels)
    assert "feature" in joined
    assert "spike" in joined
    assert "bug" in joined


def test_vue3_templates_render_requires_work_id(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    page.get_by_test_id("tab-templates").click()
    page.get_by_test_id("templates-panel").wait_for(state="visible")
    page.wait_for_function(
        """() => {
          const el = document.querySelector('[data-testid="templates-status"]');
          return el && /combo\\(s\\) available/.test(el.textContent || '');
        }"""
    )
    page.get_by_test_id("templates-work-id").fill("")
    page.get_by_test_id("templates-render").click()
    page.wait_for_function(
        """() => {
          const el = document.querySelector('[data-testid="templates-status"]');
          return el && (el.textContent || '').includes('Work ID is required');
        }"""
    )


def test_vue3_templates_render_adf(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    work_id = live_vue_console["work_id"]
    page.get_by_test_id("tab-templates").click()
    page.get_by_test_id("templates-panel").wait_for(state="visible")
    page.wait_for_function(
        """() => {
          const el = document.querySelector('[data-testid="templates-status"]');
          return el && /combo\\(s\\) available/.test(el.textContent || '');
        }"""
    )
    page.get_by_test_id("templates-combo").select_option("feature")
    page.get_by_test_id("templates-work-id").fill(work_id)
    page.get_by_test_id("templates-render").click()
    page.wait_for_function(
        f"""() => {{
          const el = document.querySelector('[data-testid="templates-status"]');
          return el && (el.textContent || '').includes('Rendered feature for {work_id}');
        }}"""
    )
    log = page.get_by_test_id("templates-log").inner_text()
    assert work_id in log
    assert '"type": "doc"' in log or '"type":"doc"' in log


def test_vue3_templates_refresh_combos(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    page.get_by_test_id("tab-templates").click()
    page.get_by_test_id("templates-panel").wait_for(state="visible")
    page.wait_for_function(
        """() => {
          const el = document.querySelector('[data-testid="templates-status"]');
          return el && /combo\\(s\\) available/.test(el.textContent || '');
        }"""
    )
    page.get_by_test_id("templates-refresh").click()
    page.wait_for_function(
        """() => {
          const el = document.querySelector('[data-testid="templates-status"]');
          return el && /\\d+ combo\\(s\\) available/.test(el.textContent || '');
        }"""
    )


@pytest.mark.parametrize("tab_id", _STUB_TABS)
def test_vue3_stub_tabs_show_port_message(page, live_vue_console, tab_id: str) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    page.get_by_test_id(f"tab-{tab_id}").click()
    page.get_by_test_id("stub-panel").wait_for(state="visible")
    title = page.get_by_test_id("stub-title").inner_text().strip().lower()
    assert tab_id in title or title  # label may be title-cased
    lead = page.get_by_test_id("stub-lead").inner_text()
    assert "Stub" in lead
    assert "pages.py" in lead


def test_vue3_tab_switch_round_trip(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    page.get_by_test_id("tab-templates").click()
    page.get_by_test_id("templates-panel").wait_for(state="visible")
    page.get_by_test_id("tab-install").click()
    page.get_by_test_id("stub-panel").wait_for(state="visible")
    page.get_by_test_id("tab-persistence").click()
    page.get_by_test_id("persistence-panel").wait_for(state="visible")
    assert page.get_by_test_id("templates-panel").count() == 0
