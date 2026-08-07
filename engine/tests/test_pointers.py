"""Tests for lean git pointer ledger (path 1 / SPIKE-087)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sdlc_engine.pointers import POINTER_REL, PointerLedger, PointerRecord
from sdlc_engine.project import Project


def _project(tmp_path: Path) -> Project:
    # Minimal stay-set layout so ledger paths resolve under a fake repo root.
    (tmp_path / "spdd" / "memory").mkdir(parents=True, exist_ok=True)
    return Project(tmp_path)


def test_append_and_list_committed(tmp_path: Path) -> None:
    ledger = PointerLedger(_project(tmp_path))
    rec = ledger.append(
        PointerRecord(
            id="",
            kind="lesson",
            work_id="FEAT-013-demo",
            subtype="pitfall",
            intent="Never open PRs against embabel/guide",
            commit_sha="deadbeef",
            paths=["spdd/memory/lessons/pitfalls.md"],
            links={"areas": ["com.embabel.guide.spdd"], "lesson_id": "pitfall:FEAT-013-demo:x:capture"},
        )
    )
    assert rec.id.startswith("ptr_")
    assert rec.ts
    assert ledger.path.is_file()
    assert ledger.path.relative_to(tmp_path) == POINTER_REL

    rows = ledger.list(work_id="FEAT-013-demo")
    assert len(rows) == 1
    assert rows[0].kind == "lesson"
    assert rows[0].intent.startswith("Never open")
    assert rows[0].links["areas"] == ["com.embabel.guide.spdd"]

    line = ledger.path.read_text(encoding="utf-8").strip()
    payload = json.loads(line)
    assert payload["schema"] == 1
    assert payload["work_id"] == "FEAT-013-demo"


def test_filter_by_kind_and_area(tmp_path: Path) -> None:
    ledger = PointerLedger(_project(tmp_path))
    ledger.append(
        PointerRecord(
            id="ptr_a",
            kind="lesson",
            work_id="W1",
            links={"areas": ["area-a"]},
            intent="a",
        )
    )
    ledger.append(
        PointerRecord(
            id="ptr_b",
            kind="claim",
            work_id="W1",
            links={"areas": ["area-b"]},
            intent="b",
        )
    )
    ledger.append(
        PointerRecord(
            id="ptr_c",
            kind="lesson",
            work_id="W2",
            links={"areas": ["area-a"]},
            intent="c",
        )
    )

    assert [r.id for r in ledger.list(kind="lesson")] == ["ptr_a", "ptr_c"]
    assert [r.id for r in ledger.list(area="area-a")] == ["ptr_a", "ptr_c"]
    assert [r.id for r in ledger.list(work_id="W1", kind="claim")] == ["ptr_b"]


def test_staging_excluded_unless_requested(tmp_path: Path) -> None:
    ledger = PointerLedger(_project(tmp_path))
    ledger.append(
        PointerRecord(id="ptr_hot", kind="resume", work_id="W1", intent="draft"),
        staging=True,
    )
    assert ledger.list() == []
    staged = ledger.list(include_staging=True)
    assert len(staged) == 1
    assert staged[0].id == "ptr_hot"
    assert ledger.staging_path.is_file()
    # Staging must live under .sdlc, not the stay-set tree.
    assert ledger.staging_path.parent.name == ".sdlc"


def test_skips_corrupt_jsonl_lines(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project.root / POINTER_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "not-json",
                json.dumps(
                    {
                        "id": "ptr_ok",
                        "kind": "reasons",
                        "work_id": "W1",
                        "intent": "ok",
                        "paths": ["spdd/canvas/W1.md"],
                        "links": {},
                        "schema": 1,
                        "ts": "2026-08-07T00:00:00Z",
                    }
                ),
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rows = PointerLedger(project).list()
    assert len(rows) == 1
    assert rows[0].id == "ptr_ok"


def test_round_trip_json_dataclass() -> None:
    rec = PointerRecord(
        id="ptr_x",
        kind="product",
        work_id="FEAT-001",
        intent="ship",
        commit_sha="abc",
        paths=["src/Foo.kt"],
        links={"t": "T01"},
        ts="2026-08-07T12:00:00Z",
    )
    again = PointerRecord.from_json(rec.to_json())
    assert again == rec
