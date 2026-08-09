"""Live GitHub Issues integration tests (require `gh` auth).

Default (safe): pull an existing issue into a temp milestone and verify write-back.
Create path: set SDLC_GITHUB_ISSUE_CREATE=1 (CI job with issues:write closes after).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from sdlc_engine.issues import IssueSyncService
from sdlc_engine.project import Project


def _gh_available() -> bool:
    if not shutil.which("gh"):
        return False
    proc = subprocess.run(
        ["gh", "auth", "status"],
        check=False,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def _repo() -> str:
    return (
        os.environ.get("SDLC_GITHUB_REPO")
        or os.environ.get("GH_REPO")
        or "jmjava/sdlc-spdd-orchestrator"
    )


def _seed(root: Path, work_id: str, *, number: str = "TBD") -> Path:
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(
        f"""# Requirement: {work_id}

## Summary

GitHub integration probe for SDLC issue sync.

## Jira

- Key: TBD
- Summary: unused

## GitHub

- Number: {number}
- Title:
- Labels:
- URL:
""",
        encoding="utf-8",
    )
    canvas = root / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"""# REASONS Canvas: {work_id} - GH integration

## Metadata

- Work ID: {work_id}
- Work Type: Feature
- Status: Draft
- Source System:
- Source Issue:
- Source URL:

## Final Status

- Status: Draft
""",
        encoding="utf-8",
    )
    return req


@pytest.fixture(scope="module")
def gh_ready() -> str:
    if os.environ.get("SDLC_SKIP_GITHUB_INTEGRATION", "0") == "1":
        pytest.fail("SDLC_SKIP_GITHUB_INTEGRATION=1 — unset to run GitHub integration tests")
    if not _gh_available():
        pytest.fail("gh CLI not authenticated — run `gh auth login` or set GH_TOKEN")
    return _repo()


def _list_issue_number(repo: str) -> str:
    proc = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--limit",
            "5",
            "--json",
            "number,title,state",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        pytest.fail(f"gh issue list failed: {proc.stderr.strip()}")
    rows = json.loads(proc.stdout or "[]")
    if not rows:
        pytest.fail(f"no issues in {repo} to pull against")
    return str(rows[0]["number"])


def test_github_pull_existing_issue_apply(tmp_path: Path, gh_ready: str, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_GITHUB_REPO", gh_ready)
    number = _list_issue_number(gh_ready)
    work_id = "FEAT-910-gh-pull-live"
    _seed(tmp_path, work_id, number=number)

    # Confirm remote readable
    view = subprocess.run(
        [
            "gh",
            "issue",
            "view",
            number,
            "--repo",
            gh_ready,
            "--json",
            "title,url,state",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert view.returncode == 0, view.stderr
    remote = json.loads(view.stdout)
    assert remote.get("title")

    svc = IssueSyncService(Project(tmp_path))
    report = svc.pull(work_id, "github", apply=True)
    assert f"GitHub #{number}" in report
    assert remote["title"] in report

    text = (tmp_path / "requirements" / "milestones" / f"{work_id}.md").read_text(
        encoding="utf-8"
    )
    assert f"Number: {number}" in text
    assert f"Title: {remote['title']}" in text
    assert remote["url"] in text

    canvas = (tmp_path / "spdd" / "canvas" / f"{work_id}.md").read_text(encoding="utf-8")
    assert f"#{number}" in canvas or number in canvas


def test_github_push_create_pull_roundtrip(tmp_path: Path, gh_ready: str, monkeypatch) -> None:
    if os.environ.get("SDLC_GITHUB_ISSUE_CREATE", "0") != "1":
        pytest.fail("Set SDLC_GITHUB_ISSUE_CREATE=1 to create a live GitHub issue")
    monkeypatch.setenv("SDLC_GITHUB_REPO", gh_ready)
    work_id = "FEAT-911-gh-create-live"
    _seed(tmp_path, work_id, number="TBD")
    # Avoid labels — repos may not have them.
    req = tmp_path / "requirements" / "milestones" / f"{work_id}.md"
    text = req.read_text(encoding="utf-8")
    req.write_text(text.replace("- Labels: sdlc\n", "- Labels:\n"), encoding="utf-8")
    # ensure title present without labels section issues
    req.write_text(
        req.read_text(encoding="utf-8").replace(
            "- Title:",
            "- Title: [sdlc-integration-test] engine issue sync — auto",
        ),
        encoding="utf-8",
    )

    svc = IssueSyncService(Project(tmp_path))
    created = None
    try:
        out = svc.push(work_id, "github", apply=True)
        assert "Created GitHub issue" in out
        assert "/issues/" in out
        created = out.rstrip().split("/issues/")[-1].split()[0]
        milestone = req.read_text(encoding="utf-8")
        assert f"Number: {created}" in milestone
        assert f"/issues/{created}" in milestone

        # Pull should round-trip title from GitHub
        report = svc.pull(work_id, "github", apply=True)
        assert f"GitHub #{created}" in report
        assert "OPEN" in report or "open" in report.lower() or "[" in report
    finally:
        if created:
            try:
                svc.close_github(created)
            except RuntimeError as exc:
                # Some tokens can create but not close (document leftover).
                print(f"WARN: could not close #{created}: {exc}")
