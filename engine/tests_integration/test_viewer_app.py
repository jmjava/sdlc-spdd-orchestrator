"""Flask integration tests for the ADF viewer."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

import pytest

pytest.importorskip("flask")

from sdlc_engine.viewer.app import create_app
from sdlc_engine.viewer.store import AdfStore


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
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
                    "content": [{"type": "text", "text": "Body"}],
                },
            ],
        },
    )
    return tmp_path


@pytest.fixture()
def client(repo: Path):
    calls: list[dict] = []
    download_calls: list[dict] = []

    def fake_upload(
        issue_key: str,
        adf_path: Path,
        *,
        apply: bool = False,
        description_format: str | None = None,
    ) -> str:
        calls.append(
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
                    "content": [{"type": "text", "text": "From Jira"}],
                }
            ],
        }
        if apply:
            adf_path.parent.mkdir(parents=True, exist_ok=True)
            import json

            adf_path.write_text(json.dumps(remote, indent=2) + "\n", encoding="utf-8")
            return f"Wrote {adf_path} from Jira {issue_key}"
        return f"[dry-run] would write {adf_path}\nremote vs local: differ\n"

    app = create_app(repo, upload_adf=fake_upload, download_adf=fake_download)
    app.config["TESTING"] = True
    app.upload_calls = calls  # type: ignore[attr-defined]
    app.download_calls = download_calls  # type: ignore[attr-defined]
    with app.test_client() as c:
        yield c, app


def test_index_lists_tickets(client) -> None:
    c, _app = client
    resp = c.get("/")
    assert resp.status_code == 200
    assert b"ORCH-1.adf.json" in resp.data
    assert b"Browse filesystem" in resp.data


def test_edit_page(client, repo: Path) -> None:
    c, _app = client
    path = str((repo / "adf" / "ORCH-1.adf.json").resolve())
    resp = c.get("/edit?path=" + quote(path))
    assert resp.status_code == 200
    assert b"contenteditable" in resp.data
    assert b"Hello" in resp.data
    assert b"btnScenario" in resp.data or b"+ Scenario" in resp.data
    assert b"btnAcSection" in resp.data or b"AC section" in resp.data
    assert b"browserBackdrop" in resp.data


def test_edit_legacy_redirect(client) -> None:
    c, _app = client
    resp = c.get("/edit/ORCH-1.adf.json", follow_redirects=False)
    assert resp.status_code in {301, 302}


def test_api_browse(client, repo: Path) -> None:
    c, _app = client
    resp = c.get("/api/browse?path=" + quote(str(repo / "adf")))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert any(f["name"] == "ORCH-1.adf.json" for f in data["files"])


def test_api_browse_outside_start(client, repo: Path, tmp_path: Path) -> None:
    c, _app = client
    outside = tmp_path / "other"
    outside.mkdir()
    AdfStore(repo).save_path(
        str(outside / "Y.adf.json"),
        {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "y"}]}],
        },
    )
    resp = c.get("/api/browse?path=" + quote(str(outside)))
    assert resp.status_code == 200
    assert any(f["name"] == "Y.adf.json" for f in resp.get_json()["files"])


def test_api_get_adf(client, repo: Path) -> None:
    c, _app = client
    path = str((repo / "adf" / "ORCH-1.adf.json").resolve())
    resp = c.get("/api/adf?path=" + quote(path))
    assert resp.status_code == 200
    assert resp.get_json()["type"] == "doc"


def test_api_render(client) -> None:
    c, _app = client
    resp = c.post(
        "/api/render",
        json={
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "x"}]}],
        },
    )
    assert resp.status_code == 200
    assert "<p" in resp.get_json()["html"]


def test_api_html_to_adf(client) -> None:
    c, _app = client
    resp = c.post("/api/html-to-adf", json={"html": "<h2>T</h2><p>body</p>"})
    assert resp.status_code == 200
    assert resp.get_json()["adf"]["content"][0]["type"] == "heading"


def test_api_save_html(client, repo: Path) -> None:
    c, _app = client
    path = str((repo / "adf" / "ORCH-1.adf.json").resolve())
    resp = c.post(
        "/api/save",
        json={"path": path, "html": "<h1>Updated</h1><p>new</p>"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True
    loaded = AdfStore(repo).load_path(path)
    assert loaded["content"][0]["content"][0]["text"] == "Updated"


def test_api_save_malformed_json_unchanged(client, repo: Path) -> None:
    c, _app = client
    path = repo / "adf" / "ORCH-1.adf.json"
    before = path.read_text()
    resp = c.post(
        "/api/save",
        data='{"path":"%s","nope":true}' % path,
        content_type="application/json",
    )
    # invalid ADF shape
    assert resp.status_code == 400
    assert path.read_text() == before


def test_api_create(client, repo: Path) -> None:
    c, _app = client
    new_path = str((repo / "adf" / "NEW.adf.json").resolve())
    resp = c.post("/api/create", json={"path": new_path, "title": "New"})
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True
    assert (repo / "adf" / "NEW.adf.json").is_file()


def test_sync_prepare_no_apply(client, repo: Path) -> None:
    c, app = client
    path = str((repo / "adf" / "ORCH-1.adf.json").resolve())
    resp = c.post(
        "/api/sync",
        json={"path": path, "issue_key": "ORCH-1", "description_format": "adf"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["apply"] is False
    assert "--apply" not in data["cli"]


def test_sync_apply_calls_uploader(client, repo: Path) -> None:
    c, app = client
    path = str((repo / "adf" / "ORCH-1.adf.json").resolve())
    resp = c.post(
        "/api/sync",
        json={
            "path": path,
            "apply": True,
            "issue_key": "ORCH-99",
            "description_format": "wiki",
        },
    )
    assert resp.status_code == 200
    assert any(call["apply"] and call["issue_key"] == "ORCH-99" for call in app.upload_calls)


def test_sync_apply_error_surfaces(repo: Path) -> None:
    def boom(*_a, **_k):
        raise RuntimeError("upload-adf requires JIRA_BASE_URL (or JIRA_URL) and JIRA_API_TOKEN")

    app = create_app(repo, upload_adf=boom)
    path = str((repo / "adf" / "ORCH-1.adf.json").resolve())
    with app.test_client() as c:
        resp = c.post("/api/sync", json={"path": path, "apply": True, "issue_key": "ORCH-1"})
        assert resp.status_code == 400
        assert "JIRA" in resp.get_json()["error"]


def test_download_prepare_no_apply(client, repo: Path) -> None:
    c, app = client
    path = str((repo / "adf" / "ORCH-1.adf.json").resolve())
    resp = c.post(
        "/api/download",
        json={"path": path, "issue_key": "ORCH-1"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["apply"] is False
    assert data["direction"] == "jira-to-local"
    assert "download-adf" in data["cli"]
    assert "--apply" not in data["cli"]
    assert any(not call["apply"] for call in app.download_calls)
    assert "From Jira" not in (repo / "adf" / "ORCH-1.adf.json").read_text()


def test_download_apply_writes_and_returns_adf(client, repo: Path) -> None:
    c, app = client
    path = str((repo / "adf" / "ORCH-1.adf.json").resolve())
    resp = c.post(
        "/api/download",
        json={"path": path, "issue_key": "ORCH-99", "apply": True},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["apply"] is True
    assert data["adf"]["content"][0]["content"][0]["text"] == "From Jira"
    assert any(call["apply"] and call["issue_key"] == "ORCH-99" for call in app.download_calls)
    assert "From Jira" in Path(path).read_text(encoding="utf-8")


def test_download_apply_error_surfaces(repo: Path) -> None:
    def boom(*_a, **_k):
        raise RuntimeError("download-adf requires JIRA_BASE_URL (or JIRA_URL) and JIRA_API_TOKEN")

    app = create_app(repo, download_adf=boom)
    path = str((repo / "adf" / "ORCH-1.adf.json").resolve())
    with app.test_client() as c:
        resp = c.post(
            "/api/download",
            json={"path": path, "apply": True, "issue_key": "ORCH-1"},
        )
        assert resp.status_code == 400
        assert "JIRA" in resp.get_json()["error"]


def test_edit_page_has_download_controls(client, repo: Path) -> None:
    c, _app = client
    path = str((repo / "adf" / "ORCH-1.adf.json").resolve())
    resp = c.get("/edit?path=" + quote(path))
    assert resp.status_code == 200
    assert b"prepareDownload" in resp.data
    assert b"applyDownload" in resp.data
    assert b"Jira \xe2\x86\x92 Local" in resp.data or b"Jira" in resp.data
