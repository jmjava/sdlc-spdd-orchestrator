"""Unit tests for feature sunset (PR + commit + Jira → ledger)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from subprocess import CompletedProcess

from sdlc_engine.cli import main
from sdlc_engine.lessons_ledger import LessonsLedger
from sdlc_engine.project import Project
from sdlc_engine.sunset import SunsetError, SunsetService, normalize_pr_number


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _init_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("# demo\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")
    return root


def _seed_work(root: Path, work_id: str) -> None:
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(
        f"""# Requirement: {work_id}

## Summary

Sunset demo for {work_id}.

## Jira

- Key: ORCH-42
- Summary: Sunset demo
- Issue type: Story

## GitHub

- Number: 99
- Title: Sunset demo GH
- URL: https://github.com/example/repo/issues/99
""",
        encoding="utf-8",
    )
    canvas = root / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"""# REASONS Canvas: {work_id} - Sunset demo

## Metadata

- Work ID: {work_id}
- Status: Complete
- Related PR: https://github.com/example/repo/pull/7

## Final Status

- Status: Complete
""",
        encoding="utf-8",
    )
    (root / "spdd" / "memory").mkdir(parents=True, exist_ok=True)
    (root / "spdd" / "memory" / "registry.jsonl").write_text(
        json.dumps(
            {
                "event": "claim",
                "work_id": work_id,
                "status": "active",
                "phase": "sync",
                "operation": "",
                "owner": "tester",
                "note": "pr:#7 jira:ORCH-42",
                "ts": "2026-08-14T00:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _fake_gh(cmd: list[str], cwd: Path) -> CompletedProcess:
    if cmd[:3] == ["gh", "pr", "list"]:
        payload = [
            {
                "number": 7,
                "title": "Sunset PR",
                "state": "MERGED",
                "url": "https://github.com/example/repo/pull/7",
            }
        ]
        return CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")
    if cmd[:3] == ["gh", "pr", "view"]:
        if "--json" in cmd and cmd[3] == "--json":
            # current-branch view
            return CompletedProcess(cmd, 0, stdout=json.dumps({"number": 7}), stderr="")
        payload = {
            "number": 7,
            "title": "Sunset PR",
            "state": "MERGED",
            "url": "https://github.com/example/repo/pull/7",
            "mergedAt": "2026-08-13T12:00:00Z",
            "headRefName": "feat/sunset",
            "baseRefName": "main",
            "author": {"login": "octocat"},
            "commits": [
                {
                    "oid": "abc1234deadbeef",
                    "messageHeadline": "FEAT-014-feature-sunset: wire engine",
                    "committedDate": "2026-08-13T11:00:00Z",
                    "authors": [{"name": "Octo Cat"}],
                }
            ],
        }
        return CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")
    if cmd[:3] == ["gh", "issue", "view"]:
        payload = {
            "title": "Sunset demo GH",
            "state": "CLOSED",
            "url": "https://github.com/example/repo/issues/99",
            "labels": [],
            "body": "issue body",
        }
        return CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")
    return CompletedProcess(cmd, 1, stdout="", stderr=f"unexpected: {cmd}")


def test_normalize_pr_number() -> None:
    assert normalize_pr_number("#7") == "7"
    assert normalize_pr_number("7") == "7"
    assert normalize_pr_number("https://github.com/acme/widgets/pull/42") == "42"
    assert normalize_pr_number("pr:#9") == "9"
    assert normalize_pr_number("TBD") == ""


def test_collect_prs_commits_and_local_jira(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SDLC_GITHUB_REPO", raising=False)
    monkeypatch.delenv("GH_REPO", raising=False)
    root = _init_repo(tmp_path)
    work_id = "FEAT-014-feature-sunset"
    _seed_work(root, work_id)
    (root / "feat.txt").write_text("x\n", encoding="utf-8")
    _git(root, "add", "feat.txt")
    _git(root, "commit", "-m", f"{work_id}: add feat")

    snap = SunsetService(Project(root), gh_runner=_fake_gh).collect(work_id)
    assert snap.work_id == work_id
    assert snap.jira is not None
    assert snap.jira.key == "ORCH-42"
    assert any("Jira pull skipped" in w for w in snap.warnings)
    assert snap.github_issue is not None
    assert snap.github_issue["number"] == "99"
    assert snap.github_issue["state"] == "CLOSED"
    assert len(snap.prs) == 1
    assert snap.prs[0].number == "7"
    assert snap.prs[0].state == "MERGED"
    assert any(work_id in c.subject for c in snap.commits)
    assert any(c.sha.startswith("abc1234") for c in snap.commits)


def test_apply_stages_session_record(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    work_id = "FEAT-014-feature-sunset"
    _seed_work(root, work_id)
    svc = SunsetService(Project(root), gh_runner=_fake_gh)
    snap = svc.run(work_id, apply=True)
    assert snap.staged is True
    assert snap.accepted is False
    assert snap.ledger_id.startswith("session:")
    ledger = LessonsLedger(Project(root))
    rec = ledger.get(snap.ledger_id)
    assert rec is not None
    assert rec.kind == "session"
    assert rec.source == "sunset"
    assert rec.work_id == work_id
    assert "ORCH-42" in rec.body
    assert "#7" in rec.body
    staged = Project(root).staged_ledger_path
    assert staged.is_file()
    assert snap.ledger_id in staged.read_text(encoding="utf-8")


def test_accept_promotes_to_committed_ledger(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    work_id = "FEAT-014-feature-sunset"
    _seed_work(root, work_id)
    snap = SunsetService(Project(root), gh_runner=_fake_gh).run(work_id, accept=True)
    assert snap.accepted is True
    committed = Project(root).ledger_path.read_text(encoding="utf-8")
    assert snap.ledger_id in committed
    assert "Sunset snapshot" in committed


def test_missing_work_id_fails(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    try:
        SunsetService(Project(root), gh_runner=_fake_gh).collect()
        assert False, "expected SunsetError"
    except SunsetError as exc:
        assert "no Work ID" in str(exc)


def test_cli_sunset_text_and_json(tmp_path: Path, capsys) -> None:
    root = _init_repo(tmp_path)
    work_id = "FEAT-014-feature-sunset"
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(
        f"# Requirement: {work_id}\n\n## Jira\n\n- Key: ORCH-42\n- Summary: CLI sunset\n",
        encoding="utf-8",
    )
    assert main(["--root", str(root), "sunset", "--work-id", work_id]) == 0
    out = capsys.readouterr().out
    assert f"sunset: {work_id}" in out
    assert "ORCH-42" in out
    assert "ledger: (dry-run" in out
    assert main(["--root", str(root), "sunset", "--work-id", work_id, "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["work_id"] == work_id
    assert payload["staged"] is False
