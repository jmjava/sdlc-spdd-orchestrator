"""Unit tests for AdfStore."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sdlc_engine.viewer.store import AdfStore, AdfStoreError


@pytest.fixture()
def store(tmp_path: Path) -> AdfStore:
    s = AdfStore(tmp_path)
    s.ensure_dir()
    return s


def _doc(text: str = "hello") -> dict:
    return {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }


def test_save_load_roundtrip(store: AdfStore) -> None:
    store.save("ORCH-1.adf.json", _doc("alpha"))
    loaded = store.load("ORCH-1.adf.json")
    assert loaded["content"][0]["content"][0]["text"] == "alpha"


def test_list_files(store: AdfStore) -> None:
    store.save("A.adf.json", _doc("a"))
    store.save("B.json", _doc("b"))
    (store.adf_dir / "notes.md").write_text("# not adf\n")
    (store.adf_dir / "bad.json").write_text("{not json")
    names = store.list_files()
    assert "A.adf.json" in names
    assert "B.json" in names
    assert "notes.md" not in names


def test_browse_any_directory(store: AdfStore, tmp_path: Path) -> None:
    other = tmp_path / "elsewhere"
    other.mkdir()
    doc_path = other / "X.adf.json"
    store.save_path(str(doc_path), _doc("x"))
    listing = store.browse(str(other))
    assert listing["path"] == str(other.resolve())
    assert any(f["name"] == "X.adf.json" and f["valid"] for f in listing["files"])


def test_absolute_path_outside_start_root(tmp_path: Path) -> None:
    start = tmp_path / "start"
    outside = tmp_path / "outside"
    start.mkdir()
    outside.mkdir()
    store = AdfStore(start)
    store.ensure_dir()
    target = outside / "Z.adf.json"
    store.save_path(str(target), _doc("z"))
    assert store.load_path(str(target))["content"][0]["content"][0]["text"] == "z"


def test_reject_nul_path(store: AdfStore) -> None:
    with pytest.raises(AdfStoreError):
        store.resolve_path("bad\x00name.json")


def test_malformed_json_on_load(store: AdfStore) -> None:
    path = store.adf_dir / "broken.adf.json"
    path.write_text("{")
    with pytest.raises(AdfStoreError, match="invalid JSON"):
        store.load("broken.adf.json")


def test_invalid_adf_rejected_on_save(store: AdfStore) -> None:
    with pytest.raises(AdfStoreError):
        store.save("x.adf.json", {"type": "paragraph"})


def test_save_malformed_leaves_file_unchanged(store: AdfStore) -> None:
    store.save("keep.adf.json", _doc("keep"))
    before = (store.adf_dir / "keep.adf.json").read_text()
    with pytest.raises(AdfStoreError):
        store.save("keep.adf.json", {"nope": True})
    assert (store.adf_dir / "keep.adf.json").read_text() == before


def test_issue_key_from_name(store: AdfStore) -> None:
    assert store.issue_key_from_name("ORCH-123.adf.json") == "ORCH-123"
    assert store.issue_key_from_name("/tmp/foo/ORCH-demo.adf.json") == "ORCH-demo"


def test_create_path(store: AdfStore, tmp_path: Path) -> None:
    p = store.create_path(str(tmp_path / "new" / "Ticket.adf.json"), title="Ticket")
    assert p.is_file()
    doc = store.load_path(str(p))
    assert doc["content"][0]["content"][0]["text"] == "Ticket"


def test_repo_fixtures_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    store = AdfStore(root)
    names = store.list_files()
    assert "ORCH-demo.adf.json" in names
    assert store.load("ORCH-demo.adf.json")["version"] == 1
