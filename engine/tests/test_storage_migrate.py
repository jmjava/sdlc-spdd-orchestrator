"""Storage v3 migration: legacy fixture → ledger records + export."""

from __future__ import annotations

from pathlib import Path

from sdlc_engine.lessons_ledger import LessonsLedger
from sdlc_engine.project import Project
from sdlc_engine.storage_migrate import StorageMigration


def _legacy_fixture(root: Path) -> None:
    mem = root / "agent-context" / "memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "context-index.md").write_text(
        """# Context Index

| Area | Kind | Work ID | Phase | Timestamp | Source | Entry |
|------|------|---------|-------|-----------|--------|-------|
| engine | pitfall | FEAT-LEG | code | 2026-08-08T00:00:00Z | test | Legacy pitfall text |
""",
        encoding="utf-8",
    )
    (mem / "known-pitfalls.md").write_text(
        "## FEAT-LEG — 2026-08-08\n\n- Area: engine\n\nBody from file\n",
        encoding="utf-8",
    )
    (root / "agent-context" / "work-registry.tsv").write_text(
        "# header\nwork_id\tstatus\tphase\toperation\towner\tupdated\tnote\n"
        "FEAT-LEG\tavailable\tinit\t\tdev\t2026-08-08T00:00:00Z\t\n",
        encoding="utf-8",
    )


def test_migration_dry_run_detects_legacy(tmp_path: Path) -> None:
    _legacy_fixture(tmp_path)
    mig = StorageMigration(Project(tmp_path))
    detect = mig.detect()
    assert detect["needs_migration"] is True
    assert "agent-context/memory" in detect["legacy_present"]


def test_migration_appends_records_and_exports(tmp_path: Path) -> None:
    _legacy_fixture(tmp_path)
    mig = StorageMigration(Project(tmp_path))
    out = mig.run(dry_run=False)
    assert out["ok"] is True
    assert out["records_migrated"]["context_index"] >= 1
    ledger = LessonsLedger(Project(tmp_path))
    ids = ledger.accepted_ids()
    assert any("FEAT-LEG" in i for i in ids)
    assert (tmp_path / ".sdlc" / "storage-v3-migrated").is_file()
    assert not (tmp_path / "agent-context" / "memory").exists()
