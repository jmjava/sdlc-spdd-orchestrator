from pathlib import Path

import pytest

from sdlc_engine.pointer import PointerError, PointerStore
from sdlc_engine.project import Project


def test_pointer_round_trip(tmp_path: Path) -> None:
    store = PointerStore(Project(tmp_path))
    assert store.get() == ""
    store.set("FEAT-001-demo")
    assert store.get() == "FEAT-001-demo"
    store.reset()
    assert store.get() == ""


def test_pointer_rejects_empty(tmp_path: Path) -> None:
    store = PointerStore(Project(tmp_path))
    with pytest.raises(PointerError):
        store.set("")
