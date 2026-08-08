"""Viewer GitHub Issue pull/push endpoints — fake gh runner, no network."""

from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess
from urllib.parse import quote

import pytest

pytest.importorskip("flask")

from sdlc_engine.viewer.app import create_app
from sdlc_engine.viewer.store import AdfStore

ISSUE_BODY_MD = "# Order status\n\nExpose order status.\n\n- item one\n- item two\n"


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    store = AdfStore(tmp_path)
    store.ensure_dir()
    store.save(
        "GH-1.adf.json",
        {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": "Local title"}],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Local body"}],
                },
            ],
        },
    )
    return tmp_path


@pytest.fixture()
def client(repo: Path, monkeypatch):
    """Flask test client with a fake gh runner (records gh + git calls)."""
    monkeypatch.delenv("SDLC_GITHUB_REPO", raising=False)
    monkeypatch.delenv("GH_REPO", raising=False)
    calls: list[list[str]] = []

    def fake_gh(cmd: list[str], cwd: Path) -> CompletedProcess:
        calls.append(cmd)
        if cmd[:2] == ["git", "remote"]:
            return CompletedProcess(cmd, 0, stdout="https://github.com/acme/widgets.git\n", stderr="")
        if cmd[:3] == ["gh", "issue", "view"]:
            num = cmd[3]
            if num == "404":
                return CompletedProcess(cmd, 1, stdout="", stderr="GraphQL: Could not resolve to an Issue")
            payload = {
                "number": int(num),
                "title": "Remote issue title",
                "state": "OPEN",
                "url": f"https://github.com/acme/widgets/issues/{num}",
                "body": ISSUE_BODY_MD,
            }
            return CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")
        if cmd[:3] == ["gh", "issue", "edit"]:
            num = cmd[3]
            if num == "404":
                return CompletedProcess(cmd, 1, stdout="", stderr="issue not found")
            return CompletedProcess(
                cmd, 0, stdout=f"https://github.com/acme/widgets/issues/{num}\n", stderr=""
            )
        return CompletedProcess(cmd, 1, stdout="", stderr=f"unexpected command: {cmd}")

    app = create_app(repo, gh_runner=fake_gh)
    app.config["TESTING"] = True
    app.gh_calls = calls  # type: ignore[attr-defined]
    with app.test_client() as c:
        yield c, app


def _adf_path(repo: Path) -> str:
    return str((repo / "adf" / "GH-1.adf.json").resolve())


def test_github_pull_prepare_returns_adf_without_writing(client, repo: Path) -> None:
    c, app = client
    before = (repo / "adf" / "GH-1.adf.json").read_text(encoding="utf-8")
    resp = c.post("/api/github/pull", json={"issue": "42", "path": _adf_path(repo)})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["apply"] is False
    assert data["number"] == 42
    assert data["repo"] == "acme/widgets"
    assert data["markdown"] == ISSUE_BODY_MD
    # markdown -> ADF for the WYSIWYG
    assert data["adf"]["content"][0]["type"] == "heading"
    assert "Order status" in data["html"]
    # dry-run: local file untouched
    assert (repo / "adf" / "GH-1.adf.json").read_text(encoding="utf-8") == before
    # repo resolved from git remote origin
    assert any(cmd[:2] == ["git", "remote"] for cmd in app.gh_calls)
    view = next(cmd for cmd in app.gh_calls if cmd[:3] == ["gh", "issue", "view"])
    assert "--repo" in view and "acme/widgets" in view


def test_github_pull_apply_writes_document(client, repo: Path) -> None:
    c, _app = client
    resp = c.post(
        "/api/github/pull",
        json={"issue": "#7", "path": _adf_path(repo), "apply": True},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True and data["apply"] is True
    saved = AdfStore(repo).load_path(_adf_path(repo))
    assert saved["content"][0]["content"][0]["text"] == "Order status"


def test_github_pull_explicit_owner_repo_ref(client, repo: Path) -> None:
    c, app = client
    resp = c.post(
        "/api/github/pull",
        json={"issue": "other/project#9", "path": _adf_path(repo)},
    )
    assert resp.status_code == 200
    assert resp.get_json()["repo"] == "other/project"
    view = next(cmd for cmd in app.gh_calls if cmd[:3] == ["gh", "issue", "view"])
    assert "other/project" in view
    # inline ref wins — no need to consult git remote
    assert not any(cmd[:2] == ["git", "remote"] for cmd in app.gh_calls)


def test_github_pull_missing_issue_is_400(client, repo: Path) -> None:
    c, _app = client
    resp = c.post("/api/github/pull", json={"path": _adf_path(repo)})
    assert resp.status_code == 400
    assert "issue required" in resp.get_json()["error"]


def test_github_pull_invalid_ref_is_400(client, repo: Path) -> None:
    c, _app = client
    resp = c.post("/api/github/pull", json={"issue": "not-a-number", "path": _adf_path(repo)})
    assert resp.status_code == 400
    assert "invalid GitHub issue reference" in resp.get_json()["error"]


def test_github_pull_unknown_issue_is_400_not_500(client, repo: Path) -> None:
    c, _app = client
    resp = c.post("/api/github/pull", json={"issue": "404", "path": _adf_path(repo)})
    assert resp.status_code == 400
    assert "Could not resolve" in resp.get_json()["error"]


def test_github_push_prepare_previews_markdown_without_gh_edit(client, repo: Path) -> None:
    c, app = client
    resp = c.post("/api/github/push", json={"issue": "42", "path": _adf_path(repo)})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True and data["apply"] is False
    # ADF -> markdown preview of the local document
    assert "# Local title" in data["markdown"]
    assert "Local body" in data["markdown"]
    assert "may flatten" in data["note"]
    assert not any(cmd[:3] == ["gh", "issue", "edit"] for cmd in app.gh_calls)


def test_github_push_apply_sends_updated_body(client, repo: Path) -> None:
    c, app = client
    resp = c.post(
        "/api/github/push",
        json={"issue": "42", "path": _adf_path(repo), "apply": True},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True and data["apply"] is True
    assert "Updated GitHub issue acme/widgets#42" in data["message"]
    edit = next(cmd for cmd in app.gh_calls if cmd[:3] == ["gh", "issue", "edit"])
    body = edit[edit.index("--body") + 1]
    assert "# Local title" in body
    assert "Local body" in body


def test_github_push_missing_issue_is_400(client, repo: Path) -> None:
    c, _app = client
    resp = c.post("/api/github/push", json={"path": _adf_path(repo)})
    assert resp.status_code == 400
    assert "issue required" in resp.get_json()["error"]


def test_github_push_missing_path_is_400(client) -> None:
    c, _app = client
    resp = c.post("/api/github/push", json={"issue": "42"})
    assert resp.status_code == 400
    assert "path or adf" in resp.get_json()["error"]


def test_github_push_apply_gh_failure_is_400_not_500(client, repo: Path) -> None:
    c, _app = client
    resp = c.post(
        "/api/github/push",
        json={"issue": "404", "path": _adf_path(repo), "apply": True},
    )
    assert resp.status_code == 400
    assert "issue not found" in resp.get_json()["error"]


def test_edit_page_has_github_controls_and_caveat(client, repo: Path) -> None:
    c, _app = client
    resp = c.get("/edit?path=" + quote(_adf_path(repo)))
    assert resp.status_code == 200
    assert b"GitHub Issue #" in resp.data
    assert b"ghIssue" in resp.data
    assert b"ghPullPrepare" in resp.data
    assert b"ghPullApply" in resp.data
    assert b"ghPushPrepare" in resp.data
    assert b"ghPushApply" in resp.data
    assert b"complex ADF formatting may flatten" in resp.data
    # Jira controls preserved unchanged
    assert b"prepareSync" in resp.data
    assert b"prepareDownload" in resp.data
