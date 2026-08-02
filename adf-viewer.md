# ADF WYSIWYG Viewer

Team-ready editor for checked-in Atlassian Document Format (ADF) ticket descriptions.

## What it is

- **Storage:** JSON files under repo-root [`adf/`](../adf/) (e.g. `ORCH-123.adf.json`).
- **Editor:** Local Flask app with a **split pane**: WYSIWYG (left) + editable raw ADF JSON (right, CodeMirror). Sticky formatting toolbar (including **+ Scenario**), debounced autosave, and Jira sync prepare/apply (upload and download).
- **Filesystem browse:** Open any local folder (not limited to `adf/`). `--root` is only the default start directory.
- **Live sync:** Edits in either pane update the other (~350–400ms). Click a WYSIWYG block to jump to matching text in raw JSON; move the cursor in raw to highlight the matching WYSIWYG block. Scroll position stays proportionally linked.
- **Concurrency:** No locks. Last write wins; recover overwrites with git.
- **Bind:** `127.0.0.1` by default. Pass `--lan` to bind `0.0.0.0`. Local-only tool.

## Install

```bash
python3 -m pip install -e './engine[dev,viewer]'
```

Flask is an optional extra so the core engine stays stdlib-only.

## Run

```bash
# Preferred wrappers
./scripts/sdlc.sh viewer --port 5050
# or
SDLC_ENGINE=python ./scripts/sdlc.sh viewer --port 5050

# Direct
python3 -m sdlc_engine.viewer --root . --port 5050
# LAN opt-in
python3 -m sdlc_engine.viewer --root . --lan --port 5050
```

Open `http://127.0.0.1:5050/`.

From the experimental ops console (`./scripts/sdlc.sh console`), the **ADF** tab can
**Start / Stop / Restart** this viewer for the current target and open the URL — editing
and Jira sync still happen only in the viewer UI.

## Workflow

1. Add or edit an ADF file under `adf/` (seed examples: `ORCH-demo.adf.json`, `ORCH-rich.adf.json`).
2. Open the file in the viewer. Use the toolbar for common formatting (H1–H3, bold/italic/strike/underline, link, lists, panel, code block, GWT, table, image-by-URL, quote, clear format).
3. Add, delete, or rewrite text in the WYSIWYG pane — the raw ADF pane updates automatically. Or edit the JSON directly — the WYSIWYG re-renders.
4. Click either pane to navigate: block click ↔ raw cursor sync helps you verify structure while editing.
5. Autosave writes the checked-in file after ~1.5s (or click **Save**). Prefer saving when JSON is valid.
6. Commit the `adf/*.json` change like any other source file.

## Sync with Jira (explicit apply)

Sync never runs automatically. Directions are labeled in the editor:

| Direction | Action | Behavior |
|-----------|--------|----------|
| Local → Jira | **Prepare upload** | Suggested `./scripts/sdlc.sh issues upload-adf …` + engine dry-run. No network write. |
| Local → Jira | **Apply upload** | Calls `IssueSyncService.upload_adf(..., apply=True)` (`adf` or `wiki`). Requires `JIRA_*`. |
| Jira → Local | **Prepare download** | Fetches remote description ADF and diffs vs the open file. No local write. |
| Jira → Local | **Apply download** | Overwrites the local `adf/<KEY>.adf.json` from Jira (last write wins; use git to roll back). Requires `JIRA_*`. |

Equivalent CLI:

```bash
# Local → Jira
./scripts/sdlc.sh issues upload-adf ORCH-1 --file adf/ORCH-1.adf.json \
  --description-format adf
# then with --apply when ready

# Jira → Local (hand-edits on the ticket → checked-in file)
./scripts/sdlc.sh issues download-adf ORCH-1 --file adf/ORCH-1.adf.json
./scripts/sdlc.sh issues download-adf ORCH-1 --file adf/ORCH-1.adf.json --apply
```

Host and auth come only from environment (`JIRA_*`) — nothing is hardcoded in the viewer.

**Repo hygiene:** keep framework seed tickets (e.g. `ORCH-demo`) here. Project-specific ticket ADF bodies belong in the consuming project, not this orchestrator repo.

## Git rollback

If two people save the same file, the later save wins. Use `git checkout -- adf/<file>` or `git revert` to recover.

## Tests

```bash
python3 -m pip install -e './engine[dev,viewer]'
pytest -q engine/tests/test_viewer_*.py
```

**Playwright GUI (optional):** covers index, browser, WYSIWYG/raw sync, toolbar inserts, save/undo, and Jira upload/download prepare+apply (mocked).

```bash
python3 -m pip install -e './engine[dev,viewer-e2e]'
playwright install chromium
SDLC_VIEWER_E2E=1 pytest -q engine/tests/test_viewer_playwright.py -m viewer_e2e
# or: pytest … --run-viewer-e2e
```

Skipped by default unless `SDLC_VIEWER_E2E=1` or `--run-viewer-e2e`. Live Jira sync via the viewer is gated by marker `viewer_integration` and `SDLC_VIEWER_JIRA_INTEGRATION=1` (not run in default CI).

## Related

- Ops console launch + two-GUI map: [ops-console.md](ops-console.md)
- Research notes: [`docs/research/jira-adf-and-requirements-sync.md`](research/jira-adf-and-requirements-sync.md)
- Engine module: `engine/src/sdlc_engine/viewer/`
- Upload path: `issues upload-adf` / `IssueSyncService.upload_adf`
- Download path: `issues download-adf` / `IssueSyncService.download_adf`
