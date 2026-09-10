from pathlib import Path

from sdlc_engine.canvas import (
    coding_gate_issues,
    extract_readiness_raw,
    final_kind,
    next_operation,
    semantic_issues,
)


def test_final_kind_variants(tmp_path: Path) -> None:
    p = tmp_path / "c.md"
    p.write_text("## Final Status\n\n- Status: Complete (T01–T03)\n", encoding="utf-8")
    assert final_kind(p) == "complete"
    p.write_text("## Final Status\n\n- Status: Cancelled\n", encoding="utf-8")
    assert final_kind(p) == "cancelled"
    p.write_text("## Final Status\n\n- Status: Canceled — cut\n", encoding="utf-8")
    assert final_kind(p) == "cancelled"
    p.write_text("## Final Status\n\n- Status: In Progress\n", encoding="utf-8")
    assert final_kind(p) == "other"


def test_next_operation(tmp_path: Path) -> None:
    p = tmp_path / "ops.md"
    p.write_text(
        """# x
## Operations
### T01 - Done thing
- Status: Complete
### T02 - Next thing
- Status: Not Started
""",
        encoding="utf-8",
    )
    op, title = next_operation(p)
    assert op == "T02"
    assert "Next thing" in title


def test_false_ready_in_sync_notes_is_not_structured_readiness() -> None:
    text = """# REASONS Canvas: X

## Metadata
- Work ID: X

## R - Requirements
Do the thing.

## O - Operations
### T01 - Do
- Status: Not Started

## Sync Notes
Mark this Ready For Coding tomorrow.
"""
    assert extract_readiness_raw(text) == ""
    issues = coding_gate_issues(text)
    assert any("missing structured Readiness" in i for i in issues)


def test_headings_only_canvas_has_semantic_issues() -> None:
    text = """# REASONS Canvas: bare

## Metadata
## R - Requirements
## E - Entities
## A - Approach
## S - Structure
## O - Operations
## N - Norms
## S - Safeguards
## Review Checklist
## Sync Notes
## Final Status
"""
    issues = semantic_issues(text)
    assert "empty Requirements section" in issues
    assert "no T## operation with Status" in issues


def test_architecture_notes_readiness_does_not_count() -> None:
    text = """# REASONS Canvas: X

## Metadata
- Status: In Progress

## R - Requirements
Search orders by email.

## O - Operations
### T01 - Add endpoint
- Status: Not Started

## Architecture Notes
- Readiness: Ready For Coding
"""
    assert extract_readiness_raw(text) == ""
    assert any("missing structured Readiness" in i for i in coding_gate_issues(text))


def test_metadata_ready_with_minima_allows_coding() -> None:
    text = """# REASONS Canvas: X

## Metadata
- Readiness: Ready For Coding

## R - Requirements
Search orders by email.

## O - Operations
### T01 - Add endpoint
- Status: Not Started
- Files: src/OrderController.java
"""
    assert coding_gate_issues(text) == []
    from sdlc_engine.canvas import operation_mapping_issues

    assert operation_mapping_issues(text) == []


def test_empty_review_fails_minima() -> None:
    from sdlc_engine.canvas import review_minima_issues

    assert review_minima_issues("# Review: x\n")
    assert review_minima_issues("# Review: x\n\n**Result:** Approved\n")
    ok = """# Review: x

**Result:** Approved With Notes

Safeguards: no extra endpoints.
"""
    assert review_minima_issues(ok) == []


def test_operation_without_files_fails_mapping() -> None:
    from sdlc_engine.canvas import operation_mapping_issues

    text = """## O - Operations
### T01 - Add endpoint
- Status: Not Started
"""
    issues = operation_mapping_issues(text)
    assert any("Files" in i for i in issues)


_SCOPE_CANVAS = """## O - Operations
### T01 - Add endpoint
- Status: Complete
- Files: `src/app.py`, `src/util.py`
### T02 - Extra op
- Status: Complete
- Files: `src/extra.py`
### T03 - Not coded
- Status: Not Started
- Files: `src/future.py`
"""


def test_diff_scope_exact_pass() -> None:
    from sdlc_engine.canvas import check_operation_diff_scope

    result = check_operation_diff_scope(
        _SCOPE_CANVAS,
        ["src/app.py", "src/util.py"],
        selected_ops=["T01"],
    )
    assert result.ok
    assert result.extra_paths == ()
    assert "src/app.py" in result.allowed_files
    assert "src/util.py" in result.allowed_files


def test_diff_scope_unrelated_path_fails() -> None:
    from sdlc_engine.canvas import check_operation_diff_scope

    result = check_operation_diff_scope(
        _SCOPE_CANVAS,
        ["src/app.py", "src/unrelated.py"],
        selected_ops=["T01"],
    )
    assert not result.ok
    assert "src/unrelated.py" in result.extra_paths
    report = result.format_report()
    assert "FAIL" in report
    assert "src/unrelated.py" in report
    assert "src/app.py" in report


def test_diff_scope_allowed_test_path_passes() -> None:
    from sdlc_engine.canvas import check_operation_diff_scope

    result = check_operation_diff_scope(
        _SCOPE_CANVAS,
        [
            "src/app.py",
            "tests/test_app.py",
            "engine/tests_unit/test_canvas.py",
            "engine/tests_integration/test_flow.py",
            "engine/tests_e2e/test_live.py",
            "pkg/foo_test.py",
            "docs/review.spec.md",
        ],
        selected_ops=["T01"],
    )
    assert result.ok
    assert result.extra_paths == ()


def test_diff_scope_traversal_rejected() -> None:
    from sdlc_engine.canvas import check_operation_diff_scope, normalize_repo_path

    assert normalize_repo_path("src/../secret.py") is None
    assert normalize_repo_path("../outside.py") is None
    result = check_operation_diff_scope(
        _SCOPE_CANVAS,
        ["src/../secret.py", "../outside.py"],
        selected_ops=["T01"],
    )
    assert not result.ok
    assert "src/../secret.py" in result.traversal_rejected
    assert "../outside.py" in result.traversal_rejected
    assert "src/../secret.py" in result.extra_paths


def test_diff_scope_rename_and_delete_use_git_names() -> None:
    from sdlc_engine.canvas import check_operation_diff_scope

    deleted = check_operation_diff_scope(
        _SCOPE_CANVAS,
        ["src/app.py"],
        selected_ops=["T01"],
    )
    assert deleted.ok

    renamed_dest = check_operation_diff_scope(
        _SCOPE_CANVAS,
        ["src/renamed.py"],
        selected_ops=["T01"],
    )
    assert not renamed_dest.ok
    assert "src/renamed.py" in renamed_dest.extra_paths

    rename_pair = check_operation_diff_scope(
        _SCOPE_CANVAS,
        ["src/app.py", "src/renamed.py"],
        selected_ops=["T01"],
    )
    assert not rename_pair.ok
    assert rename_pair.extra_paths == ("src/renamed.py",)


def test_diff_scope_multiple_ops_union_files() -> None:
    from sdlc_engine.canvas import check_operation_diff_scope, operation_files

    op_map = operation_files(_SCOPE_CANVAS, selected_ops=["T01", "T02"])
    assert set(op_map) == {"T01", "T02"}
    result = check_operation_diff_scope(
        _SCOPE_CANVAS,
        ["src/app.py", "src/extra.py"],
        selected_ops=["T01", "T02"],
    )
    assert result.ok
    assert "src/app.py" in result.allowed_files
    assert "src/extra.py" in result.allowed_files
    assert "src/future.py" not in result.allowed_files

    coded_default = check_operation_diff_scope(
        _SCOPE_CANVAS,
        ["src/app.py", "src/extra.py"],
    )
    assert coded_default.ok
    assert "T03" not in coded_default.operations_used
    assert "src/future.py" not in coded_default.allowed_files
