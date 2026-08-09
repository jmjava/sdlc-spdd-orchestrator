"""Unit tests for issue sync with mocked Jira HTTP and gh CLI."""

from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess

from sdlc_engine.issues import IssueSyncService
from sdlc_engine.project import Project
from sdlc_engine.sync_local import LocalSyncService


def _seed_req(root: Path, work_id: str, *, jira_key: str = "TBD", gh: str = "") -> Path:
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(
        f"""# Requirement: {work_id}

## Summary

Sync demo work for {work_id}.

## Jira

- Key: {jira_key}
- Summary: Sync demo
- Issue type: Story
- Labels: sdlc, sync

### Description
Demo description body

### Acceptance criteria
- [ ] synced

## GitHub

- Number: {gh or 'TBD'}
- Title: Sync demo GH
- Labels: sdlc
""",
        encoding="utf-8",
    )
    canvas = root / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"""# REASONS Canvas: {work_id} - Sync demo

## Metadata

- Work ID: {work_id}
- Work Type: Feature
- Status: In Progress
- Source System:
- Source Issue:
- Source URL:

## Final Status

- Status: In Progress
""",
        encoding="utf-8",
    )
    return req


class _FakeResp:
    def __init__(self, payload: dict, code: int = 201) -> None:
        self._payload = payload
        self.status = code

    def read(self) -> bytes:
        return json.dumps(self._payload).encode()

    def __enter__(self) -> "_FakeResp":
        return self

    def __exit__(self, *args) -> None:
        return None


def test_jira_push_apply_mocked(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "bot@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")
    monkeypatch.setenv("JIRA_PROJECT", "ORCH")
    work_id = "FEAT-300-jira-mock"
    _seed_req(tmp_path, work_id)

    seen: dict = {}

    def fake_urlopen(req, timeout=30):  # noqa: ANN001
        seen["url"] = req.full_url
        seen["method"] = req.get_method()
        seen["body"] = req.data
        return _FakeResp({"key": "ORCH-99", "id": "10001"})

    svc = IssueSyncService(Project(tmp_path), urlopen=fake_urlopen)
    out = svc.push(work_id, "jira", apply=True)
    assert "ORCH-99" in out
    assert seen["url"].endswith("/rest/api/3/issue")
    assert seen["method"] == "POST"
    payload = json.loads(seen["body"].decode())
    desc = payload["fields"]["description"]
    assert isinstance(desc, dict) and desc.get("type") == "doc"
    text = (tmp_path / "requirements" / "milestones" / f"{work_id}.md").read_text(
        encoding="utf-8"
    )
    assert "Key: ORCH-99" in text
    canvas = (tmp_path / "spdd" / "canvas" / f"{work_id}.md").read_text(encoding="utf-8")
    assert "Source Issue: ORCH-99" in canvas
    assert "Source System: Jira" in canvas


def test_jira_pull_apply_mocked(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "bot@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")
    work_id = "FEAT-301-jira-pull"
    _seed_req(tmp_path, work_id, jira_key="ORCH-7")

    def fake_urlopen(req, timeout=30):  # noqa: ANN001
        assert "ORCH-7" in req.full_url
        assert "/rest/api/3/issue/" in req.full_url
        return _FakeResp(
            {
                "key": "ORCH-7",
                "fields": {
                    "summary": "Pulled summary from Jira",
                    "status": {"name": "In Progress"},
                    "labels": ["sdlc"],
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Hello ADF"}],
                            }
                        ],
                    },
                },
            },
            code=200,
        )

    svc = IssueSyncService(Project(tmp_path), urlopen=fake_urlopen)
    report = svc.pull(work_id, "jira", apply=True)
    assert "Pulled summary from Jira" in report
    text = (tmp_path / "requirements" / "milestones" / f"{work_id}.md").read_text(
        encoding="utf-8"
    )
    assert "Summary: Pulled summary from Jira" in text


def test_github_push_apply_with_fake_gh(tmp_path: Path) -> None:
    work_id = "FEAT-302-gh-fake"
    _seed_req(tmp_path, work_id, gh="")

    def fake_gh(cmd: list[str], cwd: Path) -> CompletedProcess:
        assert cmd[:3] == ["gh", "issue", "create"]
        assert "--title" in cmd
        return CompletedProcess(
            cmd,
            0,
            stdout="https://github.com/example/repo/issues/4242\n",
            stderr="",
        )

    svc = IssueSyncService(Project(tmp_path), gh_runner=fake_gh)
    out = svc.push(work_id, "github", apply=True)
    assert "4242" in out
    text = (tmp_path / "requirements" / "milestones" / f"{work_id}.md").read_text(
        encoding="utf-8"
    )
    assert "Number: 4242" in text
    assert "URL: https://github.com/example/repo/issues/4242" in text
    canvas = (tmp_path / "spdd" / "canvas" / f"{work_id}.md").read_text(encoding="utf-8")
    assert "Source Issue: #4242" in canvas or "Source Issue: 4242" in canvas


def test_github_pull_apply_with_fake_gh(tmp_path: Path) -> None:
    work_id = "FEAT-303-gh-pull"
    _seed_req(tmp_path, work_id, gh="55")

    def fake_gh(cmd: list[str], cwd: Path) -> CompletedProcess:
        assert cmd[:3] == ["gh", "issue", "view"]
        assert "55" in cmd
        payload = {
            "title": "Remote GH title",
            "state": "OPEN",
            "url": "https://github.com/example/repo/issues/55",
            "labels": [{"name": "bug"}, {"name": "sdlc"}],
            "body": "hello",
        }
        return CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")

    svc = IssueSyncService(Project(tmp_path), gh_runner=fake_gh)
    report = svc.pull(work_id, "github", apply=True)
    assert "Remote GH title" in report
    text = (tmp_path / "requirements" / "milestones" / f"{work_id}.md").read_text(
        encoding="utf-8"
    )
    assert "Title: Remote GH title" in text
    assert "Labels: bug, sdlc" in text


def test_github_repo_env_injected(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_GITHUB_REPO", "acme/widgets")
    work_id = "FEAT-304-repo"
    _seed_req(tmp_path, work_id, gh="")
    seen: list[list[str]] = []

    def fake_gh(cmd: list[str], cwd: Path) -> CompletedProcess:
        seen.append(cmd)
        return CompletedProcess(
            cmd, 0, stdout="https://github.com/acme/widgets/issues/9\n", stderr=""
        )

    IssueSyncService(Project(tmp_path), gh_runner=fake_gh).push(
        work_id, "github", apply=True
    )
    assert "--repo" in seen[0]
    assert "acme/widgets" in seen[0]


def test_empty_metadata_bullets_do_not_swallow_next_line(tmp_path: Path) -> None:
    from sdlc_engine.links import parse_canvas_metadata

    canvas = tmp_path / "spdd" / "canvas" / "FEAT-306-empty.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        """# REASONS Canvas: FEAT-306-empty - Empty bullets

## Metadata

- Work ID: FEAT-306-empty
- Source System:
- Source Issue:
- Source URL:

## Final Status

- Status: Draft
""",
        encoding="utf-8",
    )
    meta = parse_canvas_metadata(canvas)
    assert meta["source_system"] == ""
    assert meta["source_issue"] == ""
    assert meta["source_url"] == ""


def test_parse_github_issue_ref_variants() -> None:
    parse = IssueSyncService.parse_github_issue_ref
    assert parse("123") == ("", "123")
    assert parse("#123") == ("", "123")
    assert parse("acme/widgets#7") == ("acme/widgets", "7")
    import pytest

    with pytest.raises(ValueError):
        parse("not-a-ref")
    with pytest.raises(ValueError):
        parse("")


def test_resolve_github_repo_precedence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SDLC_GITHUB_REPO", raising=False)
    monkeypatch.delenv("GH_REPO", raising=False)

    def fake_gh(cmd: list[str], cwd: Path) -> CompletedProcess:
        assert cmd == ["git", "remote", "get-url", "origin"]
        return CompletedProcess(cmd, 0, stdout="git@github.com:acme/widgets.git\n", stderr="")

    svc = IssueSyncService(Project(tmp_path), gh_runner=fake_gh)
    # explicit wins
    assert svc.resolve_github_repo("other/repo") == "other/repo"
    # env beats git remote
    monkeypatch.setenv("SDLC_GITHUB_REPO", "env/repo")
    assert svc.resolve_github_repo() == "env/repo"
    # ssh remote URL parsed
    monkeypatch.delenv("SDLC_GITHUB_REPO")
    assert svc.resolve_github_repo() == "acme/widgets"


def test_fetch_github_issue_with_fake_gh(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SDLC_GITHUB_REPO", raising=False)
    monkeypatch.delenv("GH_REPO", raising=False)

    def fake_gh(cmd: list[str], cwd: Path) -> CompletedProcess:
        if cmd[:2] == ["git", "remote"]:
            return CompletedProcess(cmd, 0, stdout="https://github.com/acme/widgets\n", stderr="")
        assert cmd[:3] == ["gh", "issue", "view"]
        assert cmd[3] == "12"
        assert "--repo" in cmd and "acme/widgets" in cmd
        payload = {
            "number": 12,
            "title": "Fetched",
            "state": "OPEN",
            "url": "https://github.com/acme/widgets/issues/12",
            "body": "hello **md**",
        }
        return CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")

    svc = IssueSyncService(Project(tmp_path), gh_runner=fake_gh)
    data = svc.fetch_github_issue("#12")
    assert data["title"] == "Fetched"
    assert data["body"] == "hello **md**"
    assert data["repo"] == "acme/widgets"


def test_update_github_issue_body_with_fake_gh(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_GITHUB_REPO", "acme/widgets")
    seen: dict = {}

    def fake_gh(cmd: list[str], cwd: Path) -> CompletedProcess:
        assert cmd[:3] == ["gh", "issue", "edit"]
        seen["body"] = cmd[cmd.index("--body") + 1]
        return CompletedProcess(
            cmd, 0, stdout="https://github.com/acme/widgets/issues/12\n", stderr=""
        )

    svc = IssueSyncService(Project(tmp_path), gh_runner=fake_gh)
    out = svc.update_github_issue_body("12", "new body")
    assert "acme/widgets#12" in out
    assert seen["body"] == "new body"


def test_sync_links_after_mocked_github_push(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "syncer")
    work_id = "FEAT-305-roundtrip"
    _seed_req(tmp_path, work_id, gh="")

    def fake_gh(cmd: list[str], cwd: Path) -> CompletedProcess:
        return CompletedProcess(
            cmd,
            0,
            stdout="https://github.com/example/repo/issues/777\n",
            stderr="",
        )

    svc = IssueSyncService(Project(tmp_path), gh_runner=fake_gh)
    svc.push(work_id, "github", apply=True)
    findings = LocalSyncService(Project(tmp_path)).check_links(work_id)
    # After repair_links inside push, github section + canvas source should be aligned;
    # jira TBD remains manual-only.
    codes = {f.code for f in findings}
    assert "missing_github_section" not in codes
    assert "canvas_source_issue_mismatch" not in codes
