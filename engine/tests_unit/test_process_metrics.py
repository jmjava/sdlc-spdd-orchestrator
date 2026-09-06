"""FEAT-015: structured capture metrics round-trip into the query surface.

These tests fail if `context metrics` parses `session.body` instead of
`record.metrics`. A body tag `rework=99` with structured rework=2 must
yield 2.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from sdlc_engine.cli import main
from sdlc_engine.lessons_ledger import LessonRecord, LessonsLedger
from sdlc_engine.metrics import ProcessMetrics, query_metrics
from sdlc_engine.persistence import save_config
from sdlc_engine.project import Project

REPO = Path(__file__).resolve().parents[2]


def _seed(root: Path, work_id: str) -> None:
    (root / "requirements" / "milestones").mkdir(parents=True, exist_ok=True)
    (root / "requirements" / "milestones" / f"{work_id}.md").write_text(
        f"# Requirement: {work_id}\n\n## Summary\nMetrics.\n",
        encoding="utf-8",
    )
    (root / "spdd" / "canvas").mkdir(parents=True, exist_ok=True)
    (root / "spdd" / "canvas" / f"{work_id}.md").write_text(
        f"# REASONS Canvas: {work_id}\n\n## Metadata\n\n- Work ID: {work_id}\n",
        encoding="utf-8",
    )
    (root / "spdd" / "memory").mkdir(parents=True, exist_ok=True)


def test_query_uses_structured_fields_not_body() -> None:
    rec = LessonRecord(
        id="",
        kind="session",
        work_id="FEAT-015-body-trap",
        phase="code",
        body="Summary: misleading rework=99 in prose\nMetrics: rework=99",
        source="test",
        metrics=ProcessMetrics(rework=2, validate_cycles=1, review_cycles=3),
    )
    out = query_metrics([rec], construct="C-REWORK")
    assert out["source"] == "record.metrics"
    assert out["query"] == "rework_by_phase"
    assert out["rows"][0]["rework"] == 2
    assert out["by_phase"]["code"]["rework_sum"] == 2
    assert 99 not in {row["rework"] for row in out["rows"]}
    # Body still contains the trap; the query must ignore it.
    assert "rework=99" in rec.body


def test_schema1_record_without_metrics_round_trips() -> None:
    rec = LessonRecord.from_json(
        {
            "id": "session:FEAT-OLD:engine:capture",
            "kind": "session",
            "work_id": "FEAT-OLD",
            "area": "engine",
            "phase": "code",
            "body": "rework=7",
            "source": "capture",
            "schema": 1,
        }
    )
    assert rec.metrics.is_empty()
    assert "metrics" not in rec.to_json()
    assert rec.to_json()["schema"] == 1
    out = query_metrics([rec], construct="C-REWORK")
    assert out["rows"] == []


def test_non_capture_constructs_are_documented_empty() -> None:
    rec = LessonRecord(
        id="",
        kind="session",
        work_id="FEAT-015-x",
        body="n/a",
        metrics=ProcessMetrics(rework=1),
    )
    drift = query_metrics([rec], construct="C-DRIFT")
    port = query_metrics([rec], construct="C-PORT")
    assert drift["source"] == "not_capture_metrics"
    assert port["source"] == "not_capture_metrics"
    assert drift["rows"] == []
    assert port["rows"] == []


def test_cli_persist_flags_round_trip_metrics_query(tmp_path: Path) -> None:
    wid = "FEAT-015-cli-roundtrip"
    _seed(tmp_path, wid)
    save_config(tmp_path, {"backends": ["git-pointers"]})
    rc = main(
        [
            "--root",
            str(tmp_path),
            "context",
            "persist-lesson",
            "--kind",
            "session",
            "--work-id",
            wid,
            "--phase",
            "code",
            "--body",
            "Summary with trap rework=99 and context-files=999",
            "--readiness",
            "Ready For Coding",
            "--review-result",
            "pass",
            "--rework",
            "2",
            "--context-files",
            "15",
            "--validate-cycles",
            "1",
            "--review-cycles",
            "4",
            "--no-guide",
        ]
    )
    assert rc == 0
    staged = (tmp_path / ".sdlc" / "staged" / "lessons.jsonl").read_text(
        encoding="utf-8"
    )
    rec = json.loads(staged.splitlines()[0])
    assert rec["metrics"]["rework"] == 2
    assert rec["metrics"]["context_files"] == 15
    assert rec["schema"] == 2
    assert "rework=99" in rec["body"]

    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(
            [
                "--root",
                str(tmp_path),
                "context",
                "metrics",
                "--construct",
                "C-REWORK",
                "--work-id",
                wid,
            ]
        )
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["source"] == "record.metrics"
    assert payload["rows"][0]["rework"] == 2
    assert payload["by_phase"]["code"]["rework_sum"] == 2

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(
            [
                "--root",
                str(tmp_path),
                "context",
                "metrics",
                "--construct",
                "C-COMPLY",
                "--work-id",
                wid,
            ]
        )
    assert rc == 0
    comply = json.loads(buf.getvalue())
    assert comply["rows"][0]["review_result"] == "pass"
    assert comply["rows"][0]["readiness"] == "Ready For Coding"

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(
            [
                "--root",
                str(tmp_path),
                "context",
                "metrics",
                "--construct",
                "C-CONTEXT",
                "--work-id",
                wid,
            ]
        )
    assert rc == 0
    ctx = json.loads(buf.getvalue())
    assert ctx["rows"][0]["context_files"] == 15


def test_capture_script_writes_metrics_object_round_trip(tmp_path: Path) -> None:
    wid = "FEAT-015-capture-roundtrip"
    _seed(tmp_path, wid)
    script = REPO / "scripts" / "capture-session-memory.sh"
    proc = subprocess.run(
        [
            "bash",
            str(script),
            "--target",
            str(tmp_path),
            "--work-id",
            wid,
            "--phase",
            "review",
            "--summary",
            "Captured with trap rework=99",
            "--readiness",
            "Ready For Coding",
            "--review-result",
            "fail",
            "--rework",
            "2",
            "--context-files",
            "7",
            "--validate-cycles",
            "3",
            "--review-cycles",
            "1",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    staged = tmp_path / ".sdlc" / "staged" / "lessons.jsonl"
    sessions = [
        json.loads(line)
        for line in staged.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line).get("kind") == "session"
    ]
    assert sessions
    rec = sessions[-1]
    assert rec["metrics"]["rework"] == 2
    assert rec["metrics"]["validate_cycles"] == 3
    assert rec["metrics"]["review_cycles"] == 1
    assert rec["metrics"]["context_files"] == 7
    assert rec["metrics"]["review_result"] == "fail"
    assert rec["schema"] == 2
    assert "rework=99" in rec["body"]
    # Human-readable copy may still mention the structured value.
    assert "rework=2" in rec["body"]

    project = Project(tmp_path)
    out = LessonsLedger(project).metrics_query(construct="C-MEMORY", work_id=wid)
    assert out["source"] == "record.metrics"
    assert out["rows"][0]["rework"] == 2
    assert out["by_phase"]["review"]["validate_cycles_sum"] == 3


def test_invalid_review_result_rejected_by_cli(tmp_path: Path) -> None:
    wid = "FEAT-015-bad-rr"
    _seed(tmp_path, wid)
    rc = main(
        [
            "--root",
            str(tmp_path),
            "context",
            "persist-lesson",
            "--kind",
            "session",
            "--work-id",
            wid,
            "--body",
            "nope",
            "--review-result",
            "ship-it",
            "--no-guide",
        ]
    )
    assert rc == 2
