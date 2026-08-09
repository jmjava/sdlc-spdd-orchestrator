from pathlib import Path

from sdlc_engine.cli import main
from sdlc_engine.issues import IssueSyncService
from sdlc_engine.project import Project
from sdlc_engine.registry import TeamRegistry
from sdlc_engine.sync_local import LocalSyncService


def _seed(root: Path, work_id: str, *, jira_key: str = "ORCH-42", gh: str = "99") -> None:
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(
        f"""# Requirement: {work_id}

## Summary

Demo work.

## Jira

- Key: {jira_key}
- Summary: Demo summary
- Labels: sdlc, feature

### Description
Body text

## GitHub

- Number: {gh}
- Title: Demo GH
- URL: https://github.com/example/repo/issues/{gh}
""",
        encoding="utf-8",
    )
    canvas = root / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"""# REASONS Canvas: {work_id} - Demo

## Metadata

- Work ID: {work_id}
- Work Type: Feature
- Status: In Progress
- Source System:
- Source Issue:
- Source URL:
- Milestone: milestone-1.md

## Final Status

- Status: In Progress
""",
        encoding="utf-8",
    )
    ms = root / "milestone-1.md"
    ms.write_text(
        f"""# Milestone 1

## Linked Work

| Work ID | Canvas | Requirement | Status | Notes |
|---------|--------|-------------|--------|-------|
| {work_id} | spdd/canvas/{work_id}.md | requirements/milestones/{work_id}.md | Draft | seed |
""",
        encoding="utf-8",
    )


def test_claim_auto_reads_jira_and_github(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "syncer")
    work_id = "FEAT-200-links"
    _seed(tmp_path, work_id)
    reg = TeamRegistry(Project(tmp_path))
    row = reg.claim(work_id)
    assert "jira:ORCH-42" in row.note
    assert "github:#99" in row.note


def test_sync_links_detects_and_repairs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "syncer")
    work_id = "FEAT-201-repair"
    _seed(tmp_path, work_id)
    reg = TeamRegistry(Project(tmp_path))
    reg.claim(work_id)
    # Clear canvas source to force drift after claim (claim doesn't write canvas yet)
    svc = LocalSyncService(Project(tmp_path), reg)
    findings = svc.check_links(work_id)
    codes = {f.code for f in findings}
    assert "canvas_source_issue_mismatch" in codes or "linked_work_status_drift" in codes
    actions = svc.repair_links(work_id)
    assert actions
    canvas = (tmp_path / "spdd" / "canvas" / f"{work_id}.md").read_text(encoding="utf-8")
    assert "Source Issue: ORCH-42" in canvas
    assert "Source System: Jira" in canvas
    ms = (tmp_path / "milestone-1.md").read_text(encoding="utf-8")
    assert "In Progress" in ms


def test_sync_roadmap_updates_markers(tmp_path: Path) -> None:
    work_id = "FEAT-202-roadmap"
    _seed(tmp_path, work_id)
    roadmap = tmp_path / "ROADMAP.md"
    roadmap.write_text(
        "# Roadmap\n\n<!-- SDLC-SPDD-ROADMAP-SUMMARY:START -->\nold\n<!-- SDLC-SPDD-ROADMAP-SUMMARY:END -->\n",
        encoding="utf-8",
    )
    LocalSyncService(Project(tmp_path)).sync_roadmap()
    text = roadmap.read_text(encoding="utf-8")
    assert work_id in text
    assert "SDLC-SPDD Work Summary" in text


def test_issues_draft_and_push_dry_run(tmp_path: Path) -> None:
    work_id = "FEAT-203-issues"
    _seed(tmp_path, work_id, jira_key="TBD")
    svc = IssueSyncService(Project(tmp_path))
    drafts = svc.draft(work_id, system="both")
    assert {d.system for d in drafts} == {"jira", "github"}
    out = svc.push(work_id, "github", apply=False)
    assert "[dry-run]" in out
    assert main(["--root", str(tmp_path), "issues", "draft", work_id, "--system", "github"]) == 0


def test_cli_sync_links_check(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "cli")
    work_id = "FEAT-204-cli"
    _seed(tmp_path, work_id)
    # positional work id accepted; repairable drift exits 1
    rc = main(["--root", str(tmp_path), "sync-links", work_id])
    assert rc in {0, 1}
    assert main(["--root", str(tmp_path), "links", work_id]) == 0


def test_sync_links_manual_only_exits_zero(tmp_path: Path) -> None:
    work_id = "FEAT-205-manual"
    _seed(tmp_path, work_id, jira_key="TBD", gh="")
    # Ensure Linked Work matches canvas so only manual TBD findings remain after repair of sections
    ms = tmp_path / "milestone-1.md"
    text = ms.read_text(encoding="utf-8").replace("| Draft |", "| In Progress |")
    ms.write_text(text, encoding="utf-8")
    canvas = tmp_path / "spdd" / "canvas" / f"{work_id}.md"
    # clear github number by rewriting req without number
    req = tmp_path / "requirements" / "milestones" / f"{work_id}.md"
    req.write_text(
        f"""# Requirement: {work_id}

## Summary

Demo.

## Jira

- Key: TBD
- Summary: Demo

## GitHub

- Number: TBD
""",
        encoding="utf-8",
    )
    assert canvas.is_file()
    rc = main(["--root", str(tmp_path), "sync-links", work_id])
    assert rc == 0
