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
