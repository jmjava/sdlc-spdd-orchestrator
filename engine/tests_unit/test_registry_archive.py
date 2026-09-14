from pathlib import Path

from sdlc_engine.archive import ArchiveService
from sdlc_engine.project import Project
from sdlc_engine.registry import TeamRegistry


def _seed(root: Path, work_id: str, status: str) -> None:
    canvas = root / "sdlc-spdd" / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"# {work_id}\n\n## Final Status\n\n- Status: {status}\n",
        encoding="utf-8",
    )
    (root / "sdlc-spdd" / "requirements" / "milestones").mkdir(parents=True, exist_ok=True)
    (root / "sdlc-spdd" / "requirements" / "milestones" / f"{work_id}.md").write_text("# m\n", encoding="utf-8")
    (root / "sdlc-spdd" / "spdd" / "analysis").mkdir(parents=True, exist_ok=True)
    (root / "sdlc-spdd" / "spdd" / "analysis" / f"{work_id}-analysis.md").write_text("# a\n", encoding="utf-8")


def test_claim_and_list_work(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "tester")
    work_id = "FEAT-020-claim"
    _seed(tmp_path, work_id, "In Progress")
    reg = TeamRegistry(Project(tmp_path))
    row = reg.claim(work_id)
    assert row.status == "active"
    assert row.owner == "tester"
    text = reg.list_work_text()
    assert work_id in text
    team = reg.team_text()
    assert "tester" in team


def test_archive_complete_removes_contracts_keeps_requirement(tmp_path: Path, monkeypatch) -> None:
    """Storage v3 (REF-002): archive deletes contract artifacts; git history is the record."""
    monkeypatch.setenv("SDLC_USER", "archiver")
    work_id = "FEAT-021-done"
    _seed(tmp_path, work_id, "Complete")
    reg = TeamRegistry(Project(tmp_path))
    reg.claim(work_id)
    svc = ArchiveService(Project(tmp_path), reg)
    svc.archive_work(work_id)
    assert not (tmp_path / "sdlc-spdd" / "spdd" / "canvas" / f"{work_id}.md").exists()
    assert not (tmp_path / "sdlc-spdd" / "spdd" / "analysis" / f"{work_id}-analysis.md").exists()
    assert not (tmp_path / "sdlc-spdd" / "spdd" / "canvas" / "archive").exists()
    assert not (tmp_path / "sdlc-spdd" / "spdd" / "analysis" / "archive").exists()
    assert (tmp_path / "sdlc-spdd" / "requirements" / "milestones" / f"{work_id}.md").is_file()
    rows = {r.work_id: r for r in reg.rows()}
    assert rows[work_id].status == "archived"


def test_archive_dry_run_removes_nothing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "archiver")
    work_id = "FEAT-025-dry"
    _seed(tmp_path, work_id, "Complete")
    svc = ArchiveService(Project(tmp_path))
    svc.archive_work(work_id, dry_run=True)
    assert (tmp_path / "sdlc-spdd" / "spdd" / "canvas" / f"{work_id}.md").is_file()
    assert (tmp_path / "sdlc-spdd" / "spdd" / "analysis" / f"{work_id}-analysis.md").is_file()


def test_archive_does_not_touch_lessons_ledger(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "archiver")
    work_id = "FEAT-024-ledger"
    _seed(tmp_path, work_id, "Complete")
    ledger = tmp_path / "sdlc-spdd" / "spdd" / "memory" / "lessons.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        '{"id":"pitfall:FEAT-024-ledger:engine:test","kind":"pitfall",'
        '"work_id":"FEAT-024-ledger","area":"engine","title":"keep me",'
        '"body":"archive must not drop this record from the dogfood ledger.",'
        '"source":"test","keywords":[],"schema":1}\n'
    )
    ledger.write_text(payload, encoding="utf-8")
    before = ledger.read_text(encoding="utf-8")
    reg = TeamRegistry(Project(tmp_path))
    reg.claim(work_id)
    svc = ArchiveService(Project(tmp_path), reg)
    svc.archive_work(work_id)
    assert not (tmp_path / "sdlc-spdd" / "spdd" / "canvas" / f"{work_id}.md").exists()
    assert ledger.read_text(encoding="utf-8") == before


def test_archive_v3_home_removes_canvas_under_sdlc_spdd(tmp_path: Path, monkeypatch) -> None:
    """Default auto (REF-001) routes archive to Python; storage v3 lives under sdlc-spdd/."""
    monkeypatch.setenv("SDLC_USER", "archiver")
    work_id = "FEAT-002-done-live"
    home = tmp_path / "sdlc-spdd"
    canvas = home / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"# {work_id}\n\n## Final Status\n\n- Status: Complete\n",
        encoding="utf-8",
    )
    req = home / "requirements" / "milestones"
    req.mkdir(parents=True, exist_ok=True)
    (req / f"{work_id}.md").write_text("# req\n", encoding="utf-8")
    proj = Project(tmp_path)
    assert proj.home == home
    svc = ArchiveService(proj)
    svc.archive_work(work_id)
    assert not canvas.exists()
    assert not (home / "spdd" / "canvas" / "archive").exists()
    assert (req / f"{work_id}.md").is_file()


def test_archive_refuses_in_progress(tmp_path: Path) -> None:
    work_id = "FEAT-022-active"
    _seed(tmp_path, work_id, "In Progress")
    svc = ArchiveService(Project(tmp_path))
    try:
        svc.archive_work(work_id)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "not Complete or Cancelled" in str(exc)


def test_sync_team_marks_cancelled(tmp_path: Path) -> None:
    work_id = "FEAT-023-cancel"
    _seed(tmp_path, work_id, "Cancelled")
    reg = TeamRegistry(Project(tmp_path))
    reg.refresh_done_status()
    rows = {r.work_id: r for r in reg.rows()}
    assert rows[work_id].status == "cancelled"
    assert (tmp_path / "sdlc-spdd" / "spdd" / "canvas" / f"{work_id}.md").is_file()


def test_registry_ignores_pre_v3_tsv(tmp_path: Path) -> None:
    tsv = tmp_path / "agent-context" / "work-registry.tsv"
    tsv.parent.mkdir(parents=True)
    tsv.write_text(
        "work_id\tstatus\tphase\toperation\towner\tupdated_at\tnote\n"
        "FEAT-099-old\tactive\tcode\tT01\talice\t2026-01-01T00:00:00Z\tstale\n",
        encoding="utf-8",
    )
    reg = TeamRegistry(Project(tmp_path))
    assert not hasattr(reg, "legacy_tsv_path")
    assert reg.rows() == []
    assert reg.path == tmp_path / "sdlc-spdd" / "spdd" / "memory" / "registry.jsonl"
