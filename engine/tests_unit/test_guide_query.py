"""Routing tests for context guide-query."""

from __future__ import annotations

import pytest

from sdlc_engine.guide_query import resolve_guide_query


def test_resolve_work_id() -> None:
    tool, args = resolve_guide_query(work_id="FEAT-001-x")
    assert tool == "spdd_workSubgraph"
    assert args["workId"] == "FEAT-001-x"


def test_resolve_area() -> None:
    tool, args = resolve_guide_query(area="engine/tests")
    assert tool == "spdd_areaLessons"
    assert args["area"] == "engine/tests"


def test_resolve_lesson_id() -> None:
    tool, args = resolve_guide_query(lesson_id="pitfall:W:engine:retro")
    assert tool == "spdd_getLesson"
    assert args["id"] == "pitfall:W:engine:retro"


def test_resolve_stats_flag() -> None:
    tool, args = resolve_guide_query(stats=True)
    assert tool == "spdd_projectionStats"
    assert args == {}


def test_resolve_explicit_tool() -> None:
    tool, args = resolve_guide_query(tool="spdd_findByLabel", tool_args={"label": "Pitfall"})
    assert tool == "spdd_findByLabel"
    assert args["label"] == "Pitfall"


def test_resolve_missing_context_raises() -> None:
    with pytest.raises(ValueError):
        resolve_guide_query(question="hello there")
