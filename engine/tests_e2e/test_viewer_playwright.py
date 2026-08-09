"""Playwright GUI tests for the ADF viewer (all primary editor features).

Requires optional extras::

    pip install -e './engine[dev,viewer-e2e]'
    playwright install chromium

Run::

    ./scripts/run-test-suites.sh e2e
    pytest -q engine/tests_e2e/test_viewer_playwright.py
"""

from __future__ import annotations

import json
import socket
import threading
import time
from pathlib import Path
from urllib.parse import quote

import pytest

pytest.importorskip("flask")
pytest.importorskip("playwright")
pytest.importorskip("pytest_playwright")

from sdlc_engine.viewer.app import create_app
from sdlc_engine.viewer.store import AdfStore


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture()
def viewer_repo(tmp_path: Path) -> Path:
    store = AdfStore(tmp_path)
    store.ensure_dir()
    store.save(
        "ORCH-1.adf.json",
        {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": "Hello"}],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Body text"}],
                },
            ],
        },
    )
    return tmp_path


@pytest.fixture()
def live_viewer(viewer_repo: Path):
    """Start Flask on a free port with mocked Jira upload/download."""
    from werkzeug.serving import make_server

    upload_calls: list[dict] = []
    download_calls: list[dict] = []

    def fake_upload(
        issue_key: str,
        adf_path: Path,
        *,
        apply: bool = False,
        description_format: str | None = None,
    ) -> str:
        upload_calls.append(
            {
                "issue_key": issue_key,
                "path": str(adf_path),
                "apply": apply,
                "format": description_format,
            }
        )
        if apply:
            return f"Updated Jira issue {issue_key}"
        return f"[dry-run] would update {issue_key} as {description_format}"

    def fake_download(
        issue_key: str,
        adf_path: Path,
        *,
        apply: bool = False,
    ) -> str:
        download_calls.append(
            {"issue_key": issue_key, "path": str(adf_path), "apply": apply}
        )
        remote = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "From Jira hand edit"}],
                }
            ],
        }
        if apply:
            adf_path.parent.mkdir(parents=True, exist_ok=True)
            adf_path.write_text(json.dumps(remote, indent=2) + "\n", encoding="utf-8")
            return f"Wrote {adf_path} from Jira {issue_key}\nremote vs local: differ\n"
        return (
            f"[dry-run] would write {adf_path}\n"
            "remote vs local: differ\n"
            "--- diff ---\n"
            "- Body text\n+ From Jira hand edit\n"
        )

    app = create_app(
        viewer_repo, upload_adf=fake_upload, download_adf=fake_download
    )
    port = _free_port()
    server = make_server("127.0.0.1", port, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # Wait until accepting connections
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)
    else:
        server.shutdown()
        raise RuntimeError("viewer server failed to start")

    base = f"http://127.0.0.1:{port}"
    yield {
        "base": base,
        "repo": viewer_repo,
        "upload_calls": upload_calls,
        "download_calls": download_calls,
        "edit_url": (
            f"{base}/edit?path="
            + quote(str((viewer_repo / "adf" / "ORCH-1.adf.json").resolve()))
        ),
    }
    server.shutdown()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):  # type: ignore[no-untyped-def]
    """Grant clipboard for Copy ADF coverage."""
    return {
        **browser_context_args,
        "permissions": ["clipboard-read", "clipboard-write"],
    }


def _jira_sync_panel(page):  # type: ignore[no-untyped-def]
    return page.locator("section.sync-box details").filter(
        has=page.locator("summary", has_text="Jira sync (explicit apply)")
    )


def _open_sync_panel(page) -> None:  # type: ignore[no-untyped-def]
    details = _jira_sync_panel(page)
    if not details.evaluate("el => el.open"):
        details.locator("summary").click()


def _set_codemirror_json(page, doc: dict) -> None:  # type: ignore[no-untyped-def]
    """Update raw ADF. CodeMirror ignores origin=setValue for sync, so nudge a replace."""
    page.evaluate(
        """(doc) => {
          const cm = document.querySelector('.CodeMirror').CodeMirror;
          const text = JSON.stringify(doc, null, 2);
          cm.setValue(text);
          const end = cm.posFromIndex(cm.getValue().length);
          cm.replaceRange(' ', end);
          cm.replaceRange('', end, {line: end.line, ch: end.ch + 1});
        }""",
        doc,
    )


def test_index_lists_tickets_and_browser(page, live_viewer) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_viewer["base"] + "/")
    page.get_by_role("heading", name="ADF Ticket Viewer").wait_for()
    assert page.locator("a.ticket", has_text="ORCH-1.adf.json").count() == 1
    # Index opens the filesystem browser by default
    backdrop = page.locator("#browserBackdrop")
    backdrop.wait_for(state="visible")
    assert backdrop.evaluate("el => el.classList.contains('open')")
    page.locator("#browserClose").click()
    page.wait_for_function(
        "() => !document.getElementById('browserBackdrop').classList.contains('open')"
    )


def test_open_ticket_from_index(page, live_viewer) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_viewer["base"] + "/")
    page.locator("#browserClose").click()
    page.locator("a.ticket", has_text="ORCH-1.adf.json").click()
    page.locator("#editor").wait_for()
    assert "Hello" in page.locator("#editor").inner_text()
    assert page.locator("#statusBadge").inner_text() == "Loaded"


def test_edit_page_chrome_and_panes(page, live_viewer) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_viewer["edit_url"])
    page.locator("#editor").wait_for()
    assert page.locator("#editor").get_attribute("contenteditable") == "true"
    assert page.locator(".CodeMirror").count() >= 1
    assert page.locator(".toolbar").count() == 1
    for btn_id in (
        "saveBtn",
        "undoBtn",
        "redoBtn",
        "copyAdf",
        "btnScenario",
        "btnAcSection",
        "btnPanel",
        "btnCodeBlock",
        "btnTable",
        "btnQuote",
        "prepareSync",
        "applySync",
        "prepareDownload",
        "applyDownload",
    ):
        assert page.locator(f"#{btn_id}").count() == 1


def test_wysiwyg_edit_save_and_undo(page, live_viewer) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_viewer["edit_url"])
    page.locator("#editor").wait_for()
    # Mutate DOM + fire input; wait for WYSIWYG→raw sync before Save
    # (Save prefers CodeMirror JSON when it parses).
    page.evaluate(
        """() => {
          const ed = document.getElementById('editor');
          const p = ed.querySelector('p');
          p.textContent = (p.textContent || '') + ' appended';
          ed.dispatchEvent(new InputEvent('input', {bubbles: true}));
        }"""
    )
    page.wait_for_function(
        "() => document.querySelector('.CodeMirror').CodeMirror.getValue().includes('appended')",
        timeout=5000,
    )
    page.locator("#saveBtn").click()
    page.wait_for_function(
        "() => document.getElementById('statusBadge').textContent === 'Saved'"
    )
    saved = (live_viewer["repo"] / "adf" / "ORCH-1.adf.json").read_text(encoding="utf-8")
    assert "appended" in saved

    page.locator("#undoBtn").click()
    page.wait_for_function(
        "() => !document.getElementById('editor').innerText.includes('appended')"
    )
    page.locator("#redoBtn").click()
    page.wait_for_function(
        "() => document.getElementById('editor').innerText.includes('appended')"
    )


def test_raw_json_syncs_to_wysiwyg(page, live_viewer) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_viewer["edit_url"])
    page.locator(".CodeMirror").wait_for()
    new_doc = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Raw Synced Title"}],
            }
        ],
    }
    _set_codemirror_json(page, new_doc)
    page.wait_for_function(
        "() => document.getElementById('editor').innerText.includes('Raw Synced Title')",
        timeout=5000,
    )


def test_toolbar_inserts_structures(page, live_viewer) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_viewer["edit_url"])
    page.locator("#editor").wait_for()
    # Batch toolbar actions in one turn so the 1.5s autosave cannot wipe
    # editor chrome mid-assertions.
    snapshot = page.evaluate(
        """() => {
          const ed = document.getElementById('editor');
          // Headless prompt() is null; keep defaults used by toolbar handlers
          window.prompt = (msg, defVal) => defVal == null ? 'info' : defVal;
          const placeCaretAtEnd = () => {
            ed.focus();
            const range = document.createRange();
            range.selectNodeContents(ed);
            range.collapse(false);
            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
          };
          // No selection → AC section appends at end (avoids nested insert)
          window.getSelection().removeAllRanges();
          document.getElementById('btnAcSection').click();
          document.getElementById('btnScenario').click();
          // execCommand insertHTML needs a caret inside the contenteditable
          placeCaretAtEnd();
          document.getElementById('btnPanel').click();
          placeCaretAtEnd();
          document.getElementById('btnCodeBlock').click();
          placeCaretAtEnd();
          document.getElementById('btnTable').click();
          placeCaretAtEnd();
          document.getElementById('btnQuote').click();
          placeCaretAtEnd();
          document.querySelector("button[data-cmd='insertHorizontalRule']").click();
          return {
            text: ed.innerText,
            scenarios: ed.querySelectorAll('.gwt-scenario').length,
            panel: !!ed.querySelector('.panel') || /Panel text/i.test(ed.innerText),
            code: !!ed.querySelector('pre, code'),
            table: !!ed.querySelector('table'),
            quote: !!ed.querySelector('blockquote'),
            hr: !!ed.querySelector('hr'),
          };
        }"""
    )
    assert "Acceptance Criteria" in snapshot["text"]
    assert snapshot["scenarios"] >= 2
    assert snapshot["panel"]  # class or inserted panel body text
    assert snapshot["code"]
    assert snapshot["table"]
    assert snapshot["quote"]
    assert snapshot["hr"]

    # Wait for raw sync, then explicit save
    page.wait_for_function(
        "() => /Acceptance Criteria/i.test("
        "document.querySelector('.CodeMirror').CodeMirror.getValue())",
        timeout=5000,
    )
    page.locator("#saveBtn").click()
    page.wait_for_function(
        "() => document.getElementById('statusBadge').textContent === 'Saved'"
    )
    on_disk = json.loads(
        (live_viewer["repo"] / "adf" / "ORCH-1.adf.json").read_text(encoding="utf-8")
    )
    blob = json.dumps(on_disk)
    assert "Acceptance Criteria" in blob or "Given" in blob
    types = {n.get("type") for n in on_disk.get("content", [])}
    assert "heading" in types or "bulletList" in types or "paragraph" in types


def test_formatting_commands_bold_and_list(page, live_viewer) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_viewer["edit_url"])
    page.locator("#editor").wait_for()
    # Select paragraph text then bold
    page.evaluate(
        """() => {
          const ed = document.getElementById('editor');
          const p = ed.querySelector('p');
          const range = document.createRange();
          range.selectNodeContents(p);
          const sel = window.getSelection();
          sel.removeAllRanges();
          sel.addRange(range);
        }"""
    )
    page.locator("button[data-cmd='bold']").click()
    page.wait_for_function(
        "() => !!document.getElementById('editor').querySelector('b, strong')"
    )

    page.locator("button[data-cmd='insertUnorderedList']").click()
    page.wait_for_function(
        "() => !!document.getElementById('editor').querySelector('ul')"
    )


def test_file_browser_create_and_open(page, live_viewer) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_viewer["edit_url"])
    page.locator("#openBrowserBtn").click()
    backdrop = page.locator("#browserBackdrop")
    backdrop.wait_for(state="visible")
    page.locator("#browserAdf").click()
    page.locator("#browserNewName").fill("ORCH-NEW.adf.json")
    page.locator("#browserCreate").click()
    page.locator("#editor").wait_for()
    page.wait_for_url("**/edit?path=**ORCH-NEW.adf.json**")
    assert (live_viewer["repo"] / "adf" / "ORCH-NEW.adf.json").is_file()


def test_sync_prepare_upload(page, live_viewer) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_viewer["edit_url"])
    _open_sync_panel(page)
    page.locator("#issueKey").fill("ORCH-1")
    page.locator("#prepareSync").click()
    sync_out = page.locator("#syncOut")
    sync_out.wait_for(state="visible")
    page.wait_for_function(
        "() => document.getElementById('syncOut').textContent.includes('upload-adf') "
        "|| document.getElementById('syncOut').textContent.includes('dry-run')"
    )
    assert any(not c["apply"] for c in live_viewer["upload_calls"])


def test_sync_apply_upload_confirms(page, live_viewer) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_viewer["edit_url"])
    _open_sync_panel(page)
    page.locator("#issueKey").fill("ORCH-42")
    page.once("dialog", lambda d: d.accept())
    page.locator("#applySync").click()
    page.wait_for_function(
        "() => document.getElementById('syncOut').textContent.includes('ORCH-42') "
        "|| document.getElementById('statusBadge').textContent === 'Uploaded'"
    )
    assert any(
        c["apply"] and c["issue_key"] == "ORCH-42" for c in live_viewer["upload_calls"]
    )


def test_sync_prepare_download(page, live_viewer) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_viewer["edit_url"])
    _open_sync_panel(page)
    page.locator("#issueKey").fill("ORCH-1")
    page.locator("#prepareDownload").click()
    page.locator("#syncOut").wait_for(state="visible")
    page.wait_for_function(
        "() => document.getElementById('syncOut').textContent.includes('download-adf') "
        "|| document.getElementById('syncOut').textContent.includes('differ')"
    )
    assert any(not c["apply"] for c in live_viewer["download_calls"])
    # Local file unchanged on prepare
    assert "From Jira hand edit" not in (
        live_viewer["repo"] / "adf" / "ORCH-1.adf.json"
    ).read_text(encoding="utf-8")


def test_sync_apply_download_reloads_editor(page, live_viewer) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_viewer["edit_url"])
    _open_sync_panel(page)
    page.locator("#issueKey").fill("ORCH-1")
    page.once("dialog", lambda d: d.accept())
    page.locator("#applyDownload").click()
    page.wait_for_function(
        "() => document.getElementById('editor').innerText.includes('From Jira hand edit')",
        timeout=5000,
    )
    assert "From Jira hand edit" in (
        live_viewer["repo"] / "adf" / "ORCH-1.adf.json"
    ).read_text(encoding="utf-8")
    assert any(c["apply"] for c in live_viewer["download_calls"])


def test_copy_adf_writes_clipboard(page, live_viewer) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_viewer["edit_url"])
    page.locator("#copyAdf").click()
    page.wait_for_function(
        "() => /adf copied/i.test(document.getElementById('statusBadge').textContent || '')"
    )
    clip = page.evaluate("() => navigator.clipboard.readText()")
    data = json.loads(clip)
    assert data["type"] == "doc"
    assert data["version"] == 1


def test_invalid_raw_json_shows_error(page, live_viewer) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_viewer["edit_url"])
    page.locator(".CodeMirror").wait_for()
    page.evaluate(
        """() => {
          const cm = document.querySelector('.CodeMirror').CodeMirror;
          cm.setValue('{ not valid json');
          // setValue origin is ignored — nudge a replace to fire the change handler
          cm.replaceRange('x', {line: 0, ch: 0});
        }"""
    )
    page.wait_for_function(
        "() => document.getElementById('jsonError').textContent.length > 0",
        timeout=5000,
    )
