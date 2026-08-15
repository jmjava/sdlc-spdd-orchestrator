"""Shared engine helpers extracted during the tighten/polish pass."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from sdlc_engine import __version__
from sdlc_engine.installer.process_util import pid_alive, run_cmd, tcp_open
from sdlc_engine.io_util import clear_file, load_json_dict, rel_to, save_json_dict
from sdlc_engine.links import _normalize_github, _normalize_jira_key
from sdlc_engine.placeholders import PLACEHOLDER_TOKENS, is_placeholder
from sdlc_engine.project import Project
from sdlc_engine.timeutil import (
    COMPACT_STAMP,
    ISO_DATE,
    ISO_INSTANT,
    utc_date,
    utc_from_timestamp,
    utc_now,
    utc_stamp,
)

REPO = Path(__file__).resolve().parents[2]


def test_package_version_matches_pyproject() -> None:
    data = tomllib.loads((REPO / "engine" / "pyproject.toml").read_text(encoding="utf-8"))
    assert __version__ == data["project"]["version"] == "2.0.0a6"


def test_utc_helpers_use_stable_formats() -> None:
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", utc_now())
    assert re.fullmatch(r"\d{8}T\d{6}Z", utc_stamp())
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", utc_date())
    assert ISO_INSTANT == "%Y-%m-%dT%H:%M:%SZ"
    assert COMPACT_STAMP == "%Y%m%dT%H%M%SZ"
    assert ISO_DATE == "%Y-%m-%d"
    assert utc_from_timestamp(0) == "1970-01-01T00:00:00Z"


def test_placeholders_treat_na_as_empty() -> None:
    assert PLACEHOLDER_TOKENS == frozenset({"TBD", "TODO", "NONE", "N/A"})
    for raw in ("", "  ", "TBD", "todo", "None", "n/a"):
        assert is_placeholder(raw)
    assert not is_placeholder("PROJ-12")
    assert not is_placeholder("#7")


def test_link_normalizers_share_placeholder_set() -> None:
    assert _normalize_jira_key("N/A") == ("", True)
    assert _normalize_github("N/A") == ""
    assert _normalize_github("TODO") == ""
    assert _normalize_github("#12") == "12"


def test_project_rel_and_json_io(tmp_path: Path) -> None:
    project = Project(tmp_path)
    inside = tmp_path / "spdd" / "memory" / "lessons.jsonl"
    inside.parent.mkdir(parents=True)
    inside.write_text("{}\n", encoding="utf-8")
    assert project.rel(inside) == "spdd/memory/lessons.jsonl"
    assert rel_to(tmp_path, Path("/tmp/outside-engine-rel")) == "/tmp/outside-engine-rel"

    cfg = tmp_path / ".sdlc" / "runtime.json"
    assert load_json_dict(cfg) == {}
    save_json_dict(cfg, {"ok": True})
    assert load_json_dict(cfg) == {"ok": True}
    cfg.write_text("not-json", encoding="utf-8")
    assert load_json_dict(cfg) == {}
    clear_file(cfg)
    assert not cfg.exists()


def test_process_util_pid_and_run() -> None:
    assert pid_alive(2_147_483_647) is False
    result = run_cmd(["python3", "-c", "print('hi')"], timeout=10)
    assert result["ok"] is True
    assert "hi" in result["log"]
    assert tcp_open("127.0.0.1", 1, timeout=0.05) is False
