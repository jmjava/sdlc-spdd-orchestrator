from pathlib import Path

from sdlc_engine.cli import main
from sdlc_engine.local_sessions import LocalSessionService, is_local_id
from sdlc_engine.project import Project
from sdlc_engine.registry import TeamRegistry
from sdlc_engine.workflow import WorkflowEngine


def test_local_start_capture_promote(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "local-dev")
    project = Project(tmp_path)
    svc = LocalSessionService(project)
    session = svc.start(name="scratch-sync", intent="Explore detached agent capture")
    assert is_local_id(session.id)
    assert session.id.startswith("LOCAL-")
    assert (tmp_path / ".sdlc" / "pointer").read_text(encoding="utf-8").strip() == session.id
    assert (tmp_path / ".sdlc" / "local-sessions" / session.id / "session.json").is_file()
    assert (tmp_path / ".sdlc" / "local-sessions" / session.id / "brief.md").is_file()
    assert (tmp_path / ".sdlc" / "current-local-session.md").is_file()
    assert not (tmp_path / "agent-context" / "sessions" / "current-session.md").is_file()

    svc.capture("Tried a detached approach")
    notes = (tmp_path / ".sdlc" / "local-sessions" / session.id / "notes.md").read_text(
        encoding="utf-8"
    )
    assert "Tried a detached approach" in notes

    session, work_id = svc.promote(
        work_type="feature",
        name="Detached Agent Capture",
        milestone="",
        claim=True,
    )
    assert session.status == "promoted"
    assert session.promoted_to == work_id
    assert work_id.startswith("FEAT-")
    assert (tmp_path / "spdd" / "canvas" / f"{work_id}.md").is_file()
    assert (tmp_path / "requirements" / "milestones" / f"{work_id}.md").is_file()
    # Stay-set only (#86) — promote must not create feature mirrors.
    assert not (tmp_path / "agent-context" / "features" / work_id).exists()
    progress = (tmp_path / ".sdlc" / "staged" / "lessons.jsonl").read_text(
        encoding="utf-8"
    )
    assert work_id in progress
    assert session.id in progress
    pointer = (tmp_path / ".sdlc" / "pointer").read_text(encoding="utf-8").strip()
    assert pointer == work_id
    reg = (tmp_path / "spdd" / "memory" / "registry.jsonl").read_text(encoding="utf-8")
    assert work_id in reg
    assert f"promoted-from:{session.id}" in reg


def test_claim_refuses_local_id(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "local-dev")
    svc = LocalSessionService(Project(tmp_path))
    session = svc.start(name="no-claim")
    try:
        TeamRegistry(Project(tmp_path)).claim(session.id)
        assert False, "expected PermissionError"
    except PermissionError as exc:
        assert "local/offline" in str(exc)


def test_next_shows_local_session(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "local-dev")
    svc = LocalSessionService(Project(tmp_path))
    session = svc.start(name="next-hint", intent="Stay offline")
    text = WorkflowEngine(Project(tmp_path)).next_text()
    assert session.id in text
    assert "machine-private" in text.lower() or "offline" in text.lower()


def test_next_without_pointer_hints_local_start(tmp_path: Path) -> None:
    text = WorkflowEngine(Project(tmp_path)).next_text()
    assert "local start" in text


def test_cli_local_aliases(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "cli")
    assert (
        main(
            [
                "--root",
                str(tmp_path),
                "local",
                "start",
                "--name",
                "cli-session",
                "--intent",
                "via cli",
            ]
        )
        == 0
    )
    assert main(["--root", str(tmp_path), "local", "list"]) == 0
    assert (
        main(
            [
                "--root",
                str(tmp_path),
                "local",
                "capture",
                "--summary",
                "note one",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "--root",
                str(tmp_path),
                "local",
                "promote",
                "--type",
                "spike",
                "--name",
                "Offline Spike",
                "--dry-run",
            ]
        )
        == 0
    )


def test_promote_appends_linked_work(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "local-dev")
    ms = tmp_path / "milestone-1.md"
    ms.write_text(
        "# Milestone\n\n## Linked Work\n\n"
        "| Work ID | Canvas | Requirement | Status | Notes |\n"
        "|---------|--------|-------------|--------|-------|\n"
        "| FEAT-001-demo | a | b | Complete | x |\n",
        encoding="utf-8",
    )
    svc = LocalSessionService(Project(tmp_path))
    svc.start(name="link-me", intent="link row")
    _session, work_id = svc.promote(
        work_type="chore",
        name="Linked Chore",
        milestone="milestone-1.md",
        claim=False,
    )
    text = ms.read_text(encoding="utf-8")
    assert work_id in text
    assert work_id.startswith("CHORE-")
