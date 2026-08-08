"""Init REASONS canvas from local ADF documents."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sdlc_engine.adf_work import AdfWorkService, infer_issue_key
from sdlc_engine.project import Project


def _write_adf(
    path: Path,
    *,
    heading: str | None = "Summary",
    body: str = "Do the thing",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content: list[dict] = []
    if heading is not None:
        content.append(
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": heading}],
            }
        )
    content.append(
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": body}],
        }
    )
    path.write_text(
        json.dumps({"type": "doc", "version": 1, "content": content}),
        encoding="utf-8",
    )


def test_infer_issue_key() -> None:
    assert infer_issue_key(Path("ORCH-42.adf.json")) == "ORCH-42"
    assert infer_issue_key(Path("notes.adf.json"), "Ticket ABC-7 details") == "ABC-7"
    assert infer_issue_key(Path("ORCH-demo.adf.json")) == ""


def test_init_from_adf_creates_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "app"
    root.mkdir()
    (root / "agent-context").mkdir()
    adf = root / "adf" / "ORCH-99-demo.adf.json"
    _write_adf(adf, heading="Ship ADF init", body="Browse ADF and create a canvas.")

    svc = AdfWorkService(Project.resolve(root))
    result = svc.init_from_adf(adf, claim=False)

    assert result.work_id.startswith("FEAT-001-")
    assert result.title == "Ship ADF init"
    assert result.source_issue == "ORCH-99"
    assert (root / result.canvas_path).is_file()
    assert (root / result.requirement_path).is_file()
    # Stay-set only (#86): no agent-context/features mirrors.
    assert result.feature_dir == ""
    assert not (root / "agent-context" / "features" / result.work_id).exists()
    progress = root / "spdd" / "memory" / "entries" / "progress.md"
    assert progress.is_file()
    assert result.work_id in progress.read_text(encoding="utf-8")
    # --no-claim still pins the pointer so analysis can resume immediately.
    assert (root / ".sdlc" / "pointer").read_text(encoding="utf-8").strip() == result.work_id
    canvas = (root / result.canvas_path).read_text(encoding="utf-8")
    assert "Source System: ADF" in canvas
    assert "Browse ADF and create a canvas." in canvas
    assert "Readiness: Needs Analysis" in canvas
    assert "## O - Operations" in canvas
    assert "### T01 - Clarify and plan" in canvas
    req = (root / result.requirement_path).read_text(encoding="utf-8")
    assert 'jira_key: "ORCH-99"' in req
    assert "Browse ADF and create a canvas." in req
    assert result.next_command == f"/sdlc-spdd-analysis @{result.requirement_path}"


def test_init_from_adf_dry_run_and_explicit_id(tmp_path: Path) -> None:
    root = tmp_path / "app"
    root.mkdir()
    adf = root / "ticket.adf.json"
    _write_adf(adf, heading="Explicit id")

    svc = AdfWorkService(Project.resolve(root))
    dry = svc.init_from_adf(
        adf,
        work_id="FEAT-013-adf-init-reasons-canvas",
        dry_run=True,
        claim=False,
    )
    assert dry.dry_run is True
    assert dry.work_id == "FEAT-013-adf-init-reasons-canvas"
    assert not (root / dry.canvas_path).exists()

    result = svc.init_from_adf(
        adf,
        work_id="FEAT-013-adf-init-reasons-canvas",
        title="Custom title",
        claim=False,
    )
    assert result.work_id == "FEAT-013-adf-init-reasons-canvas"
    assert result.title == "Custom title"
    assert (root / result.canvas_path).is_file()

    with pytest.raises(FileExistsError):
        svc.init_from_adf(adf, work_id="FEAT-013-adf-init-reasons-canvas", claim=False)


@pytest.mark.parametrize(
    ("work_type", "prefix", "label"),
    [
        ("spike", "SPIKE", "Spike"),
        ("bug", "BUG", "Bugfix"),
        ("refactor", "REF", "Refactor"),
        ("chore", "CHORE", "Chore"),
        ("doc", "DOC", "Doc"),
        ("test", "TEST", "Test"),
    ],
)
def test_init_from_adf_type_prefixes(
    tmp_path: Path, work_type: str, prefix: str, label: str
) -> None:
    root = tmp_path / "app"
    root.mkdir()
    adf = root / f"my-cool-{work_type}.adf.json"
    _write_adf(adf, heading=None, body=f"Body for {work_type}")

    result = AdfWorkService(Project.resolve(root)).init_from_adf(
        adf, work_type=work_type, claim=False
    )
    assert result.work_id.startswith(f"{prefix}-001-")
    canvas = (root / result.canvas_path).read_text(encoding="utf-8")
    assert f"Work Type: {label}" in canvas
    assert f"Body for {work_type}" in canvas


def test_init_from_adf_filename_title_without_heading(tmp_path: Path) -> None:
    root = tmp_path / "app"
    root.mkdir()
    adf = root / "my-cool-spike.adf.json"
    _write_adf(adf, heading=None, body="No heading present")

    result = AdfWorkService(Project.resolve(root)).init_from_adf(
        adf, work_type="spike", claim=False
    )
    assert result.title == "my cool spike"
    assert "No heading present" in (root / result.canvas_path).read_text(encoding="utf-8")


def test_init_from_adf_relative_path(tmp_path: Path) -> None:
    root = tmp_path / "app"
    root.mkdir()
    adf = root / "adf" / "REL-1.adf.json"
    _write_adf(adf, heading="Relative path")

    svc = AdfWorkService(Project.resolve(root))
    result = svc.init_from_adf("adf/REL-1.adf.json", claim=False)
    assert result.adf_path == "adf/REL-1.adf.json"
    assert result.source_issue == "REL-1"
    assert (root / result.canvas_path).is_file()


def test_init_from_adf_rejects_bad_inputs(tmp_path: Path) -> None:
    root = tmp_path / "app"
    root.mkdir()
    svc = AdfWorkService(Project.resolve(root))

    with pytest.raises(FileNotFoundError):
        svc.init_from_adf(root / "missing.adf.json", claim=False)

    directory = root / "adf-dir"
    directory.mkdir()
    with pytest.raises(FileNotFoundError):
        svc.init_from_adf(directory, claim=False)

    bad = root / "bad.adf.json"
    bad.write_text('{"type":"doc","version":2,"content":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="version"):
        svc.init_from_adf(bad, claim=False)

    not_json = root / "not-json.adf.json"
    not_json.write_text("{not-json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        svc.init_from_adf(not_json, claim=False)

    ok = root / "ok.adf.json"
    _write_adf(ok, heading="ok")
    with pytest.raises(ValueError, match="Invalid work_id"):
        svc.init_from_adf(ok, work_id="not-a-work-id", claim=False)


def test_init_from_adf_same_owner_reclaim_allowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SDLC_USER", "same-owner")
    root = tmp_path / "app"
    root.mkdir()
    wid = "FEAT-013-same-owner"
    (root / "agent-context").mkdir(parents=True)
    (root / "agent-context" / "work-registry.tsv").write_text(
        "work_id\tstatus\tphase\toperation\towner\tupdated\tnote\n"
        f"{wid}\tactive\tanalysis\t\tsame-owner\t2026-01-01T00:00:00Z\tseed\n",
        encoding="utf-8",
    )
    adf = root / "same.adf.json"
    _write_adf(adf, heading="Same owner")

    result = AdfWorkService(Project.resolve(root)).init_from_adf(
        adf, work_id=wid, claim=True
    )
    assert result.work_id == wid
    assert (root / result.canvas_path).is_file()


def test_init_from_adf_allocates_next_number(tmp_path: Path) -> None:
    root = tmp_path / "app"
    root.mkdir()
    canvas_dir = root / "spdd" / "canvas"
    canvas_dir.mkdir(parents=True)
    (canvas_dir / "FEAT-002-existing.md").write_text("# existing\n", encoding="utf-8")
    adf = root / "next.adf.json"
    _write_adf(adf, heading="Next number")

    result = AdfWorkService(Project.resolve(root)).init_from_adf(adf, claim=False)
    assert result.work_id.startswith("FEAT-003-")


def test_init_from_adf_claims_and_sets_pointer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SDLC_USER", "adf-claimer")
    root = tmp_path / "app"
    root.mkdir()
    adf = root / "adf" / "ORCH-55.adf.json"
    _write_adf(adf, heading="Claimed from ADF")

    result = AdfWorkService(Project.resolve(root)).init_from_adf(
        adf,
        work_id="FEAT-013-claimed-from-adf",
        claim=True,
    )
    pointer = (root / ".sdlc" / "pointer").read_text(encoding="utf-8").strip()
    assert pointer == "FEAT-013-claimed-from-adf"
    reg = (root / "agent-context" / "work-registry.tsv").read_text(encoding="utf-8")
    assert "FEAT-013-claimed-from-adf" in reg
    assert "adf-claimer" in reg
    assert "init-from-adf:" in reg
    assert "analysis" in reg
    assert result.work_id == "FEAT-013-claimed-from-adf"


def test_init_from_adf_claim_conflict_before_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SDLC_USER", "bob")
    root = tmp_path / "app"
    root.mkdir()
    wid = "FEAT-013-claim-conflict"
    # Seed an active claim owned by alice without a canvas yet.
    (root / "agent-context").mkdir(parents=True)
    (root / "agent-context" / "work-registry.tsv").write_text(
        "work_id\tstatus\tphase\toperation\towner\tupdated\tnote\n"
        f"{wid}\tactive\tanalysis\t\talice\t2026-01-01T00:00:00Z\tseed\n",
        encoding="utf-8",
    )
    adf = root / "conflict.adf.json"
    _write_adf(adf, heading="Conflict")

    with pytest.raises(PermissionError, match="alice"):
        AdfWorkService(Project.resolve(root)).init_from_adf(
            adf, work_id=wid, claim=True
        )
    assert not (root / "spdd" / "canvas" / f"{wid}.md").exists()


def test_init_from_adf_empty_body_and_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "app"
    root.mkdir()
    outside = tmp_path / "elsewhere" / "ORCH-3.adf.json"
    outside.parent.mkdir(parents=True)
    outside.write_text(
        json.dumps({"type": "doc", "version": 1, "content": []}),
        encoding="utf-8",
    )

    result = AdfWorkService(Project.resolve(root)).init_from_adf(
        outside,
        work_id="FEAT-013-empty-outside",
        claim=False,
    )
    assert result.source_issue == "ORCH-3"
    assert result.adf_path == str(outside.resolve())
    canvas = (root / result.canvas_path).read_text(encoding="utf-8")
    assert "(empty ADF body)" in canvas
    assert str(outside.resolve()) in canvas


def test_init_from_adf_real_repo_fixture(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    demo = repo / "adf" / "ORCH-demo.adf.json"
    if not demo.is_file():
        pytest.skip("repo adf/ORCH-demo.adf.json not present")

    result = AdfWorkService(Project.resolve(tmp_path)).init_from_adf(
        demo,
        work_id="FEAT-013-orch-demo-fixture",
        title="ORCH demo fixture",
        claim=False,
    )
    assert (tmp_path / result.canvas_path).is_file()
    text = (tmp_path / result.canvas_path).read_text(encoding="utf-8")
    assert "ORCH demo fixture" in text
    assert "Source System: ADF" in text
    assert "Standardize chore Jira sync" in text or "chore" in text.lower()
