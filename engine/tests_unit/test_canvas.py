import subprocess
from pathlib import Path

import pytest

from sdlc_engine.canvas import (
    GitChangedPathsError,
    check_diff_scope_main,
    coding_gate_issues,
    collect_git_changed_paths,
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
    from sdlc_engine.canvas import check_operation_diff_scope, is_allowed_test_path

    assert is_allowed_test_path("docs/review.spec.md")
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


def test_diff_scope_random_spec_md_is_not_an_allowed_test_path() -> None:
    from sdlc_engine.canvas import check_operation_diff_scope, is_allowed_test_path

    assert not is_allowed_test_path("spec/commands/lifecycle-code.spec.md")
    assert not is_allowed_test_path("engine/src/sdlc_engine/evil.spec.md")
    assert not is_allowed_test_path("docs/other.spec.md")

    result = check_operation_diff_scope(
        _SCOPE_CANVAS,
        [
            "src/app.py",
            "spec/commands/lifecycle-code.spec.md",
            "engine/src/sdlc_engine/evil.spec.md",
        ],
        selected_ops=["T01"],
    )
    assert not result.ok
    assert "spec/commands/lifecycle-code.spec.md" in result.extra_paths
    assert "engine/src/sdlc_engine/evil.spec.md" in result.extra_paths
    report = result.format_report()
    assert "FAIL" in report
    assert "*.spec.md" not in report


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

    # Leftover #8: no --ops is the T## under review (last completed = T02),
    # not the union of every completed T##.
    coded_default = check_operation_diff_scope(
        _SCOPE_CANVAS,
        ["src/extra.py"],
    )
    assert coded_default.ok
    assert coded_default.operations_used == ("T02",)
    assert "src/app.py" not in coded_default.allowed_files
    assert "src/future.py" not in coded_default.allowed_files
    assert "T01" not in coded_default.operations_used
    assert "T03" not in coded_default.operations_used


def _finished_twelve_op_canvas() -> str:
    """Finished canvas with twelve completed T## — leftover #8 proving fixture."""
    lines = ["## O - Operations"]
    for i in range(1, 13):
        lines.append(f"### T{i:02d} - Op {i}")
        lines.append("- Status: Complete")
        lines.append(f"- Files: `src/op{i:02d}.py`")
    return "\n".join(lines) + "\n"


def test_finished_canvas_default_ops_narrows_to_t_under_review() -> None:
    """Leftover #8: finished canvas without --ops is last T##, not twelve paths."""
    from sdlc_engine.canvas import check_operation_diff_scope

    canvas = _finished_twelve_op_canvas()
    under_review = check_operation_diff_scope(canvas, ["src/op12.py"])
    assert under_review.ok
    assert under_review.operations_used == ("T12",)
    assert under_review.allowed_files == ("src/op12.py",)
    assert len(under_review.allowed_files) == 1

    earlier = check_operation_diff_scope(canvas, ["src/op01.py"])
    assert not earlier.ok
    assert earlier.operations_used == ("T12",)
    assert "src/op01.py" in earlier.extra_paths
    assert "src/op01.py" not in earlier.allowed_files

    unioned = check_operation_diff_scope(
        canvas,
        ["src/op01.py", "src/op12.py"],
        selected_ops=["T01", "T12"],
    )
    assert unioned.ok
    assert set(unioned.operations_used) == {"T01", "T12"}


def test_default_ops_prefers_in_progress_over_completed() -> None:
    """Leftover #8: in-progress/selected is the T## under review."""
    from sdlc_engine.canvas import check_operation_diff_scope

    canvas = """## O - Operations
### T01 - Done
- Status: Complete
- Files: `src/done.py`
### T02 - Current
- Status: In Progress
- Files: `src/current.py`
### T03 - Later
- Status: Not Started
- Files: `src/later.py`
"""
    current = check_operation_diff_scope(canvas, ["src/current.py"])
    assert current.ok
    assert current.operations_used == ("T02",)
    assert current.allowed_files == ("src/current.py",)

    prior = check_operation_diff_scope(canvas, ["src/done.py"])
    assert not prior.ok
    assert "src/done.py" in prior.extra_paths


def test_check_diff_scope_finished_canvas_without_ops_is_last_t(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Leftover #8 CLI: no --ops on a finished canvas is T12, not twelve paths."""
    canvas = tmp_path / "FINISHED.md"
    canvas.write_text(_finished_twelve_op_canvas(), encoding="utf-8")
    rc = check_diff_scope_main(
        [
            "--canvas",
            str(canvas),
            "--changed",
            "src/op12.py",
            "--changed",
            "src/op01.py",
        ]
    )
    captured = capsys.readouterr()
    assert rc != 0
    assert "FAIL" in captured.out
    assert "operations: T12" in captured.out
    allowed_block = captured.out.split("allowed Files:")[1].split("allowed test paths:")[0]
    assert "src/op12.py" in allowed_block
    assert "src/op01.py" not in allowed_block
    assert allowed_block.count("src/op") == 1
    extra_block = captured.out.split("extra:")[1]
    assert "src/op01.py" in extra_block


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _init_scope_repo(tmp_path: Path) -> Path:
    """Temp git repo with a scoped canvas on main. Not an orchestrator Work ID."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("# demo\n", encoding="utf-8")
    canvas_dir = root / "spdd" / "canvas"
    canvas_dir.mkdir(parents=True)
    (canvas_dir / "SCOPE-I2.md").write_text(_SCOPE_CANVAS, encoding="utf-8")
    _git(root, "add", "README.md", "spdd/canvas/SCOPE-I2.md")
    _git(root, "commit", "-m", "init")
    current = subprocess.check_output(
        ["git", "-C", str(root), "branch", "--show-current"],
        text=True,
    ).strip()
    if current != "main":
        _git(root, "branch", "-M", "main")
    return root


def _commit_out_of_scope_on_feature(root: Path) -> None:
    _git(root, "checkout", "-b", "feature")
    (root / "src").mkdir()
    (root / "src" / "unrelated.py").write_text("x\n", encoding="utf-8")
    _git(root, "add", "src/unrelated.py")
    _git(root, "commit", "-m", "out of scope")


def test_collect_git_changed_paths_includes_committed_vs_default_base(
    tmp_path: Path,
) -> None:
    """Leftover #1: after commit, default collection is not HEAD-only."""
    root = _init_scope_repo(tmp_path)
    _commit_out_of_scope_on_feature(root)
    paths = collect_git_changed_paths(repo=root)
    assert "src/unrelated.py" in paths


def test_check_diff_scope_work_id_only_fails_after_committed_out_of_scope(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Leftover #1: --work-id only must FAIL committed extras, not PASS (none)."""
    root = _init_scope_repo(tmp_path)
    _commit_out_of_scope_on_feature(root)
    rc = check_diff_scope_main(["--work-id", "SCOPE-I2", "--root", str(root)])
    captured = capsys.readouterr()
    assert rc != 0
    assert "FAIL" in captured.out
    assert "src/unrelated.py" in captured.out
    assert "changed:\n  (none)" not in captured.out


def test_collect_git_changed_paths_invalid_base_raises(tmp_path: Path) -> None:
    """Leftover #2: bad --base must not become an empty path list."""
    root = _init_scope_repo(tmp_path)
    with pytest.raises(GitChangedPathsError, match="does-not-exist"):
        collect_git_changed_paths(repo=root, base="origin/does-not-exist")


def test_check_diff_scope_invalid_base_exits_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Leftover #2: --base origin/does-not-exist must exit non-zero, not PASS."""
    root = _init_scope_repo(tmp_path)
    rc = check_diff_scope_main(
        [
            "--work-id",
            "SCOPE-I2",
            "--root",
            str(root),
            "--base",
            "origin/does-not-exist",
        ]
    )
    captured = capsys.readouterr()
    assert rc != 0
    assert "PASS" not in captured.out
    assert "does-not-exist" in captured.err
