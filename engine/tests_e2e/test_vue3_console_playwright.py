"""Playwright GUI tests for the Vue3 ops console (`console-ui`).

Covers every shipped Vue3 tab: Dashboard (status/suggestions/goto), Persistence
(load+save+parity), Templates (feature/spike/bug + write-to-disk), Install, SQLite,
Rollback (list + dry-run restore), Guide (probe+save), Issues (integrations save
+ link/sync dry-run), and ADF (viewer lifecycle + init).

Requires optional extras + a Vite build of ``console-ui``::

    pip install -e './engine[dev,viewer-e2e]'
    playwright install chromium
    cd console-ui && npm ci && npm run build

    Run::

    ./scripts/run-test-suites.sh e2e
    pytest -q engine/tests_e2e/test_vue3_console_playwright.py
"""

from __future__ import annotations

import json
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

from sdlc_engine.installer import app as installer_app
from sdlc_engine.installer import viewer_runtime as vr
from sdlc_engine.installer.app import create_app
from sdlc_engine.installer.runner import orchestrator_root


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _ensure_vue_dist() -> Path:
    ui = orchestrator_root() / "console-ui"
    dist = ui / "dist"
    if (dist / "index.html").is_file() and os.environ.get("SDLC_VUE_FORCE_BUILD") != "1":
        return dist

    npm = os.environ.get("NPM_BIN", "npm")
    if not (ui / "package.json").is_file():
        pytest.skip(f"console-ui missing at {ui}")

    install = subprocess.run(
        [npm, "ci"], cwd=ui, capture_output=True, text=True, check=False
    )
    if install.returncode != 0:
        install = subprocess.run(
            [npm, "install"], cwd=ui, capture_output=True, text=True, check=False
        )
    if install.returncode != 0:
        pytest.skip(
            "npm install failed for console-ui:\n"
            f"{install.stdout[-2000:]}\n{install.stderr[-2000:]}"
        )

    build = subprocess.run(
        [npm, "run", "build"], cwd=ui, capture_output=True, text=True, check=False
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


def _seed_work(root: Path, work_id: str, summary: str) -> None:
    milestones = root / "requirements" / "milestones"
    milestones.mkdir(parents=True, exist_ok=True)
    (milestones / f"{work_id}.md").write_text(
        f"## Summary\n\n{summary}\n",
        encoding="utf-8",
    )


def _seed_issue_work(root: Path, work_id: str) -> None:
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(
        f"""---
work_id: "{work_id}"
jira_key: ""
github_number: ""
---

# Requirement: {work_id}

## Summary

Vue3 Playwright issue-link seed.

## Jira

- Key: TBD
- Summary: Demo summary
- Issue type: Story

### Description
Local description

## GitHub

- Number: TBD
""",
        encoding="utf-8",
    )
    canvas = root / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"""# REASONS Canvas: {work_id} - Demo

## Metadata

- Work ID: {work_id}
- Source System:
- Source Issue:
- Source URL:
""",
        encoding="utf-8",
    )
    (root / "spdd" / "memory").mkdir(parents=True, exist_ok=True)
    reg = root / "spdd" / "memory" / "registry.jsonl"
    if not reg.is_file():
        reg.write_text("", encoding="utf-8")


@pytest.fixture()
def live_vue_console(tmp_path: Path, vue_dist: Path, monkeypatch: pytest.MonkeyPatch):
    """Start Flask serving Vue3 dist + JSON API; stub ADF viewer process lifecycle."""
    from werkzeug.serving import make_server

    works = {
        "feature": "FEAT-920-vue3-playwright",
        "spike": "SPIKE-921-vue3-playwright",
        "bug": "BUG-922-vue3-playwright",
    }
    for combo, work_id in works.items():
        _seed_work(tmp_path, work_id, f"Vue3 Playwright {combo} work.")

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

    monkeypatch.setattr(
        installer_app,
        "_gh_auth_status",
        lambda timeout=3.0: {
            "installed": True,
            "authenticated": False,
            "detail": "gh not authenticated (run: gh auth login)",
        },
    )
    monkeypatch.setattr(
        installer_app,
        "probe_guide",
        lambda host, port, timeout=1.5: {
            "host": host,
            "port": port,
            "tcp_open": False,
            "http_ok": False,
            "detail": "TCP closed (test stub)",
            "sse_url": "",
        },
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
        "works": works,
        "state": state,
    }
    server.shutdown()


def _goto_vue(page, live_vue_console: dict[str, Any]) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_vue_console["base"] + "/")
    page.get_by_test_id("console-shell").wait_for()
    page.wait_for_function(
        """() => {
          const el = document.querySelector('[data-testid="health-status"]');
          return el && el.textContent && el.textContent.includes('API ok');
        }"""
    )


def _open_tab(page, tab_id: str) -> None:  # type: ignore[no-untyped-def]
    page.get_by_test_id(f"tab-{tab_id}").click()


# --- Shell -----------------------------------------------------------------


def test_vue3_shell_loads_health_and_target(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    assert "SDLC-SPDD" in page.get_by_test_id("console-brand").inner_text()
    assert "API ok" in page.get_by_test_id("health-status").inner_text()
    assert page.get_by_test_id("target-input").input_value() == str(
        live_vue_console["target"].resolve()
    )
    page.get_by_test_id("dashboard-panel").wait_for(state="visible")
    assert page.get_by_test_id("tab-dashboard").get_attribute("class") is not None
    assert "active" in (page.get_by_test_id("tab-dashboard").get_attribute("class") or "")
    page.get_by_test_id("refresh-health").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="health-status"]')?.textContent || '')
          .includes('API ok')"""
    )


# --- Dashboard -------------------------------------------------------------


def test_vue3_dashboard_refresh_loads(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    page.get_by_test_id("dashboard-panel").wait_for(state="visible")
    page.get_by_test_id("btn-dash-refresh").click()
    page.wait_for_function(
        """() => {
          const t = document.querySelector('[data-testid="dash-status"]')?.textContent || '';
          return t.includes('Loaded');
        }"""
    )
    suggestions = page.get_by_test_id("dash-suggestions").inner_text()
    assert "Refresh to load" not in suggestions
    assert page.get_by_test_id("dw-id").inner_text().strip()
    assert page.get_by_test_id("dm-accepted").inner_text().strip() != ""


def test_vue3_dashboard_configure_opens_issues(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    page.get_by_test_id("dashboard-panel").wait_for(state="visible")
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="dash-status"]')?.textContent || '')
          .includes('Loaded')"""
    )
    page.get_by_test_id("dash-goto-issues").click()
    page.get_by_test_id("issues-panel").wait_for(state="visible")
    assert page.get_by_test_id("int-tracker").count() == 1


# --- Persistence -----------------------------------------------------------


def test_vue3_persistence_load_and_save(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    target = Path(live_vue_console["target"])
    _goto_vue(page, live_vue_console)
    _open_tab(page, "persistence")
    page.get_by_test_id("persistence-panel").wait_for(state="visible")
    page.wait_for_function(
        """() => {
          const el = document.querySelector('[data-testid="persistence-status"]');
          return el && (el.textContent || '').includes('Loaded persistence options');
        }"""
    )
    assert page.get_by_test_id("ps-git").inner_text().strip() == "ON"

    page.get_by_test_id("pb-sqlite").check()
    page.get_by_test_id("pb-guide").uncheck()
    page.get_by_test_id("persist-guide-url").fill("http://127.0.0.1:21337")
    page.get_by_test_id("persist-notes").fill("vue3-playwright-persist")
    page.get_by_test_id("persistence-save").click()
    page.wait_for_function(
        """() => {
          const el = document.querySelector('[data-testid="persistence-status"]');
          return el && (el.textContent || '').includes('Saved persistence options');
        }"""
    )
    assert page.get_by_test_id("ps-guide").inner_text().strip() == "OFF"
    cfg = json.loads((target / ".sdlc" / "persistence-config.json").read_text(encoding="utf-8"))
    assert "git-pointers" in cfg["backends"]
    assert "sqlite" in cfg["backends"]
    assert "guide-dice" not in cfg["backends"]
    assert cfg["notes"] == "vue3-playwright-persist"


def test_vue3_persistence_parity_check(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    _open_tab(page, "persistence")
    page.get_by_test_id("persistence-panel").wait_for(state="visible")
    page.get_by_test_id("persistence-parity").click()
    page.wait_for_function(
        """() => {
          const t = document.querySelector('[data-testid="persistence-status"]')?.textContent || '';
          return t.startsWith('Parity OK') || t.startsWith('Parity drift')
            || t.includes('Parity check failed');
        }""",
        timeout=60000,
    )
    status = page.get_by_test_id("persistence-status").inner_text()
    assert "Parity OK" in status or "Parity drift" in status, status
    assert page.get_by_test_id("persistence-parity-repair").count() == 1


# --- Templates -------------------------------------------------------------


def test_vue3_templates_lists_combos(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    _open_tab(page, "templates")
    page.get_by_test_id("templates-panel").wait_for(state="visible")
    page.wait_for_function(
        """() => {
          const el = document.querySelector('[data-testid="templates-status"]');
          return el && /\\d+ combo\\(s\\) available/.test(el.textContent || '');
        }"""
    )
    labels = "\n".join(
        page.get_by_test_id("templates-combo").locator("option").all_inner_texts()
    )
    assert "feature" in labels and "spike" in labels and "bug" in labels


def test_vue3_templates_render_requires_work_id(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    _open_tab(page, "templates")
    page.wait_for_function(
        """() => /combo\\(s\\) available/.test(
          document.querySelector('[data-testid="templates-status"]')?.textContent || '')"""
    )
    page.get_by_test_id("templates-render").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="templates-status"]')?.textContent || '')
          .includes('Work ID is required')"""
    )


@pytest.mark.parametrize("combo", ["feature", "spike", "bug"])
def test_vue3_templates_render_each_combo(page, live_vue_console, combo: str) -> None:  # type: ignore[no-untyped-def]
    work_id = live_vue_console["works"][combo]
    _goto_vue(page, live_vue_console)
    _open_tab(page, "templates")
    page.wait_for_function(
        """() => /combo\\(s\\) available/.test(
          document.querySelector('[data-testid="templates-status"]')?.textContent || '')"""
    )
    page.get_by_test_id("templates-combo").select_option(combo)
    page.get_by_test_id("templates-work-id").fill(work_id)
    page.get_by_test_id("templates-render").click()
    page.wait_for_function(
        f"""() => (document.querySelector('[data-testid="templates-status"]')?.textContent || '')
          .includes('Rendered {combo} for {work_id}')"""
    )
    log = page.get_by_test_id("templates-log").inner_text()
    assert work_id in log
    assert '"type": "doc"' in log or '"type":"doc"' in log


def test_vue3_templates_write_adf_to_disk(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    target = Path(live_vue_console["target"])
    work_id = live_vue_console["works"]["feature"]
    out = target / "adf" / f"{work_id}.adf.json"
    assert not out.exists()

    _goto_vue(page, live_vue_console)
    _open_tab(page, "templates")
    page.wait_for_function(
        """() => /combo\\(s\\) available/.test(
          document.querySelector('[data-testid="templates-status"]')?.textContent || '')"""
    )
    page.get_by_test_id("templates-combo").select_option("feature")
    page.get_by_test_id("templates-work-id").fill(work_id)
    page.get_by_test_id("templates-write").check()
    page.get_by_test_id("templates-render").click()
    page.wait_for_function(
        f"""() => (document.querySelector('[data-testid="templates-status"]')?.textContent || '')
          .includes('wrote') && (document.querySelector('[data-testid="templates-status"]')?.textContent || '')
          .includes('{work_id}')"""
    )
    assert out.is_file()
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["type"] == "doc"


# --- Install / SQLite / Rollback -------------------------------------------


def test_vue3_install_detect_and_dry_run(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    _open_tab(page, "install")
    page.get_by_test_id("install-panel").wait_for(state="visible")
    page.get_by_test_id("btn-detect").click()
    page.wait_for_function(
        """() => {
          const t = document.querySelector('[data-testid="mode-pill"]')?.textContent || '';
          return t.trim() && t.trim() !== 'idle';
        }"""
    )
    assert page.get_by_test_id("mode-pill").inner_text().strip().lower() == "fresh"

    page.get_by_test_id("opt-dry").check()
    page.get_by_test_id("btn-run").click()
    page.wait_for_function(
        """() => {
          const t = document.querySelector('[data-testid="install-log"]')?.textContent || '';
          return t.length > 0 && !t.includes('Awaiting action');
        }"""
    )
    log = page.get_by_test_id("install-log").inner_text()
    assert log.strip()
    assert "dry" in log.lower() or "setup-agent-prompts" in log or "Would" in log


def test_vue3_sqlite_refresh_and_rebuild(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    _open_tab(page, "sqlite")
    page.get_by_test_id("sqlite-panel").wait_for(state="visible")
    page.wait_for_function(
        """() => {
          const t = document.querySelector('[data-testid="sqlite-meta"]')?.textContent || '';
          return t && t !== 'Not loaded.';
        }"""
    )
    page.get_by_test_id("btn-sqlite-rebuild").click()
    page.wait_for_function(
        """() => {
          const t = document.querySelector('[data-testid="sqlite-status"]')?.textContent || '';
          return t.includes('Index rebuilt') || t.includes('SQLite status loaded');
        }"""
    )
    assert page.get_by_test_id("sq-work").inner_text() != "—"
    assert page.get_by_test_id("sqlite-stats").count() == 1


def test_vue3_rollback_backups_pane_loads(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    _open_tab(page, "rollback")
    page.get_by_test_id("rollback-panel").wait_for(state="visible")
    page.get_by_test_id("btn-backups-refresh").click()
    page.wait_for_function(
        """() => {
          const t = document.querySelector('[data-testid="backup-rows"]')?.textContent || '';
          return t.includes('No backups') || t.includes('Restore') || t.trim() !== '';
        }"""
    )
    rows = page.get_by_test_id("backup-rows").inner_text()
    assert "No backups" in rows or "Restore" in rows


def test_vue3_rollback_dry_run_restore(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    target = Path(live_vue_console["target"])
    backup_id = "20260101T000000Z"
    backup = target / ".sdlc-spdd-upgrade-backups" / backup_id
    backup.mkdir(parents=True)
    (backup / "README.md").write_text("vue3 rollback seed\n", encoding="utf-8")

    _goto_vue(page, live_vue_console)
    _open_tab(page, "rollback")
    page.get_by_test_id("rollback-panel").wait_for(state="visible")
    page.get_by_test_id("btn-backups-refresh").click()
    page.get_by_test_id(f"btn-restore-{backup_id}").wait_for(state="visible")
    assert page.get_by_test_id("opt-rollback-dry").is_checked()
    page.get_by_test_id(f"btn-restore-{backup_id}").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="rollback-status"]')?.textContent || '')
          .includes('Dry-run: would restore')"""
    )
    assert "1" in page.get_by_test_id("rollback-status").inner_text()
    assert not (target / "README.md").exists()


# --- Issues ----------------------------------------------------------------


def _select_tracker(page, tracker: str) -> None:  # type: ignore[no-untyped-def]
    page.get_by_test_id("int-tracker").select_option(tracker)
    page.get_by_test_id("int-tracker").dispatch_event("change")
    panel = "issues-link-jira" if tracker == "jira" else "issues-link-github"
    if tracker in {"jira", "github"}:
        page.get_by_test_id(panel).wait_for(state="visible")


def _wait_vue_issues_tracker_saved(page, tracker: str) -> None:  # type: ignore[no-untyped-def]
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="int-status"]')?.textContent || '')
          .includes('Saved')"""
    )
    panel = "issues-link-jira" if tracker == "jira" else "issues-link-github"
    if tracker in {"jira", "github"}:
        page.get_by_test_id(panel).wait_for(state="visible")


def test_vue3_issues_integrations_save_and_tracker_toggle(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    _open_tab(page, "issues")
    page.get_by_test_id("issues-panel").wait_for(state="visible")
    _select_tracker(page, "jira")
    page.get_by_test_id("int-jira-url").fill("https://example.atlassian.net")
    page.get_by_test_id("int-jira-email").fill("ci@example.com")
    page.get_by_test_id("int-jira-project").fill("PROJ")
    page.get_by_test_id("btn-int-save").click()
    _wait_vue_issues_tracker_saved(page, "jira")
    assert page.get_by_test_id("issues-link-jira").is_visible()
    assert not page.get_by_test_id("issues-link-github").is_visible()

    _select_tracker(page, "github")
    page.get_by_test_id("int-gh-repo").fill("org/repo")
    page.get_by_test_id("btn-int-save").click()
    _wait_vue_issues_tracker_saved(page, "github")
    assert page.get_by_test_id("issues-link-github").is_visible()
    assert not page.get_by_test_id("issues-link-jira").is_visible()
    cfg = json.loads(
        (Path(live_vue_console["target"]) / ".sdlc" / "integrations-config.json").read_text(
            encoding="utf-8"
        )
    )
    assert cfg["tracker"] == "github"
    assert cfg["github"]["repo"] == "org/repo"
    assert cfg["jira"]["project"] == "PROJ"


def test_vue3_issues_jira_link_preview(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    work_id = "FEAT-pw-vue-jira-link"
    _seed_issue_work(Path(live_vue_console["target"]), work_id)
    _goto_vue(page, live_vue_console)
    _open_tab(page, "issues")
    _select_tracker(page, "jira")
    page.get_by_test_id("btn-int-save").click()
    _wait_vue_issues_tracker_saved(page, "jira")
    page.get_by_test_id("jira-work-id").fill(work_id)
    page.get_by_test_id("jira-key").fill("PROJ-999")
    page.get_by_test_id("btn-jira-link-dry").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="jira-link-status"]')?.textContent || '')
          .includes('Preview OK')"""
    )
    log = page.get_by_test_id("jira-link-log").inner_text()
    assert "PROJ-999" in log or "dry_run" in log


def test_vue3_issues_github_link_preview(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    work_id = "FEAT-pw-vue-gh-link"
    _seed_issue_work(Path(live_vue_console["target"]), work_id)
    _goto_vue(page, live_vue_console)
    _open_tab(page, "issues")
    _select_tracker(page, "github")
    page.get_by_test_id("btn-int-save").click()
    _wait_vue_issues_tracker_saved(page, "github")
    page.get_by_test_id("gh-work-id").fill(work_id)
    page.get_by_test_id("gh-number").fill("42")
    page.get_by_test_id("btn-gh-link-dry").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="gh-link-status"]')?.textContent || '')
          .includes('Preview OK')"""
    )
    log = page.get_by_test_id("gh-link-log").inner_text()
    assert "42" in log or "dry_run" in log


def test_vue3_issues_sync_prepare_push_dry(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    work_id = "FEAT-pw-vue-sync-dry"
    _seed_issue_work(Path(live_vue_console["target"]), work_id)
    _goto_vue(page, live_vue_console)
    _open_tab(page, "issues")
    _select_tracker(page, "github")
    page.get_by_test_id("btn-int-save").click()
    _wait_vue_issues_tracker_saved(page, "github")
    page.get_by_test_id("gh-work-id").fill(work_id)
    page.get_by_test_id("gh-number").fill("77")
    page.get_by_test_id("btn-gh-link").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="gh-link-status"]')?.textContent || '')
          .includes('Linked')"""
    )
    page.get_by_test_id("btn-jira-push-dry").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="jira-sync-status"]')?.textContent || '')
          .includes('preview OK')"""
    )
    cli = page.get_by_test_id("jira-sync-cli").inner_text()
    assert "issues push" in cli


# --- Guide / ADF -----------------------------------------------------------


def test_vue3_guide_tab_shows_config_and_probe(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    _open_tab(page, "guide")
    page.get_by_test_id("guide-panel").wait_for(state="visible")
    page.get_by_test_id("guide-home").wait_for()
    assert page.get_by_test_id("guide-port").count() == 1
    assert page.get_by_test_id("btn-guide-start").count() == 1
    assert page.get_by_test_id("btn-neo-start").count() == 1
    assert page.get_by_test_id("btn-guide-save").count() == 1
    page.get_by_test_id("btn-guide-probe").click()
    page.wait_for_function(
        """() => {
          const t = document.querySelector('[data-testid="guide-probe"]')?.textContent || '';
          return t && t !== 'Status not loaded.';
        }"""
    )


def test_vue3_guide_save_writes_config(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    target = Path(live_vue_console["target"])
    _goto_vue(page, live_vue_console)
    _open_tab(page, "guide")
    page.get_by_test_id("guide-panel").wait_for(state="visible")
    page.get_by_test_id("guide-home").wait_for()
    page.get_by_test_id("guide-notes").fill("vue3-playwright-guide")
    page.get_by_test_id("guide-port").fill("21338")
    page.get_by_test_id("btn-guide-save").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="guide-action-status"]')?.textContent || '')
          .includes('Config saved')"""
    )
    cfg = json.loads((target / ".sdlc" / "guide-config.json").read_text(encoding="utf-8"))
    assert cfg["notes"] == "vue3-playwright-guide"
    assert int(cfg["port"]) == 21338


def test_vue3_guide_dual_repo_defaults_and_native_neo4j(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    """Dual-repo Cloud Agent: sibling GUIDE_HOME + already-running /opt Neo4j Bolt."""
    sibling = orchestrator_root().parent / "guide"
    if not (sibling / "scripts" / "append-ingest.sh").is_file():
        pytest.skip("dual-repo guide checkout not present")

    import socket as _socket

    bolt_open = False
    try:
        with _socket.create_connection(("127.0.0.1", 7687), timeout=0.4):
            bolt_open = True
    except OSError:
        bolt_open = False

    _goto_vue(page, live_vue_console)
    _open_tab(page, "guide")
    page.get_by_test_id("guide-panel").wait_for(state="visible")
    page.wait_for_function(
        f"""() => {{
          const el = document.querySelector('[data-testid="guide-home"]');
          return el && el.value && el.value.includes({sibling.name!r});
        }}"""
    )
    home_val = page.get_by_test_id("guide-home").input_value()
    assert Path(home_val).resolve() == sibling.resolve()

    page.get_by_test_id("btn-guide-probe").click()
    page.wait_for_function(
        """() => {
          const t = document.querySelector('[data-testid="guide-probe"]')?.textContent || '';
          return t.includes('Guide ') && t.includes('Neo4j');
        }"""
    )
    if bolt_open:
        page.wait_for_function(
            """() => (document.querySelector('[data-testid="st-neo"]')?.textContent || '')
              .trim() === 'UP'"""
        )
        page.get_by_test_id("btn-neo-start").click()
        page.wait_for_function(
            """() => {
              const t = document.querySelector('[data-testid="guide-action-status"]')?.textContent || '';
              return t.includes('OK') || t.includes('already');
            }"""
        )
        assert page.get_by_test_id("st-neo").inner_text().strip() == "UP"


def test_vue3_adf_start_status_stop(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    _open_tab(page, "adf")
    page.get_by_test_id("adf-panel").wait_for(state="visible")
    assert page.get_by_test_id("btn-adf-open").count() == 1

    page.get_by_test_id("btn-adf-start").click()
    page.wait_for_function(
        """() => {
          const meta = document.querySelector('[data-testid="adf-meta"]')?.textContent || '';
          return meta.includes('process alive') || meta.includes('url http');
        }"""
    )
    assert live_vue_console["state"]["alive"] is True

    page.get_by_test_id("btn-adf-stop").click()
    page.wait_for_function(
        """() => {
          const meta = document.querySelector('[data-testid="adf-meta"]')?.textContent || '';
          return meta.includes('process stopped');
        }"""
    )
    assert live_vue_console["state"]["alive"] is False


def test_vue3_adf_init_requires_selection(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    _open_tab(page, "adf")
    page.get_by_test_id("adf-init-panel").wait_for(state="visible")
    page.get_by_test_id("btn-adf-init").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="adf-init-status"]')?.textContent || '')
          .includes('Select an ADF file first')"""
    )


def test_vue3_adf_browse_select_and_init(page, live_vue_console, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SDLC_USER", "playwright-vue3-adf")
    target = Path(live_vue_console["target"])
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
                        "content": [{"type": "text", "text": "End-to-end from Vue3 console"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    _goto_vue(page, live_vue_console)
    _open_tab(page, "adf")
    page.get_by_test_id("btn-adf-browse-adf").click()
    page.wait_for_function(
        """() => {
          const list = document.querySelector('[data-testid="adf-browser-list"]');
          return list && list.textContent && list.textContent.includes('ORCH-77.adf.json');
        }"""
    )
    page.locator('[data-testid="adf-browser-list"] .browser-row', has_text="ORCH-77.adf.json").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="adf-selected"]')?.textContent || '')
          .includes('ORCH-77.adf.json')"""
    )
    page.get_by_test_id("adf-work-id").fill("FEAT-013-playwright-adf-init")
    page.get_by_test_id("adf-work-title").fill("Playwright title")
    page.get_by_test_id("btn-adf-init-dry").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="adf-init-status"]')?.textContent || '')
          .includes('Would create FEAT-013-playwright-adf-init')"""
    )
    assert not (target / "spdd" / "canvas" / "FEAT-013-playwright-adf-init.md").exists()

    page.get_by_test_id("btn-adf-init").click()
    page.wait_for_function(
        """() => (document.querySelector('[data-testid="adf-init-status"]')?.textContent || '')
          .includes('Created FEAT-013-playwright-adf-init')"""
    )
    canvas = target / "spdd" / "canvas" / "FEAT-013-playwright-adf-init.md"
    assert canvas.is_file()
    text = canvas.read_text(encoding="utf-8")
    assert "Playwright title" in text
    assert "End-to-end from Vue3 console" in text


def test_vue3_tab_round_trip_all_panels(page, live_vue_console) -> None:  # type: ignore[no-untyped-def]
    _goto_vue(page, live_vue_console)
    for tab_id, panel in [
        ("dashboard", "dashboard-panel"),
        ("templates", "templates-panel"),
        ("install", "install-panel"),
        ("sqlite", "sqlite-panel"),
        ("rollback", "rollback-panel"),
        ("guide", "guide-panel"),
        ("issues", "issues-panel"),
        ("adf", "adf-panel"),
        ("persistence", "persistence-panel"),
    ]:
        _open_tab(page, tab_id)
        page.get_by_test_id(panel).wait_for(state="visible")
