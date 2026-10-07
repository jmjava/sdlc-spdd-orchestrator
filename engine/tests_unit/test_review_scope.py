"""CASP-04: extra paths cannot produce an approved review result."""

import subprocess
from pathlib import Path

import pytest

from sdlc_engine.canvas import check_operation_diff_scope, normalize_repo_path
from sdlc_engine.review_scope import main, review_result_for_scope

_SCOPE_CANVAS = """## O - Operations
### T01 - Add endpoint
- Status: Complete
- Files: `src/app.py`, `src/util.py`
### T02 - Extra op
- Status: Complete
- Files: `src/extra.py`
"""


def test_exact_paths_pass_and_keep_approved() -> None:
    result = check_operation_diff_scope(
        _SCOPE_CANVAS,
        ["src/app.py", "src/util.py"],
        selected_ops=["T01"],
    )
    assert result.ok
    assert review_result_for_scope(result, "Approved") == "Approved"
    assert review_result_for_scope(result, "Approved With Notes") == "Approved With Notes"


def test_extra_path_cannot_be_approved() -> None:
    result = check_operation_diff_scope(
        _SCOPE_CANVAS,
        ["src/app.py", "src/unrelated.py"],
        selected_ops=["T01"],
    )
    assert not result.ok
    for proposed in ("Approved", "Approved With Notes", "", "Looks good"):
        forced = review_result_for_scope(result, proposed)
        assert forced == "Changes Requested"
    assert review_result_for_scope(result, "Blocked") == "Blocked"


def test_allowed_test_path_stays_approved() -> None:
    result = check_operation_diff_scope(
        _SCOPE_CANVAS,
        ["src/app.py", "tests/test_app.py", "docs/review.spec.md"],
        selected_ops=["T01"],
    )
    assert result.ok
    assert review_result_for_scope(result) == "Approved"


def test_absolute_and_traversal_force_changes_requested() -> None:
    assert normalize_repo_path("/etc/passwd") is None
    assert normalize_repo_path("src/../secret.py") is None
    result = check_operation_diff_scope(
        _SCOPE_CANVAS,
        ["/etc/passwd", "src/../secret.py"],
        selected_ops=["T01"],
    )
    assert not result.ok
    assert review_result_for_scope(result, "Approved With Notes") == "Changes Requested"


def test_cli_prints_non_approved_result(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    canvas = tmp_path / "canvas.md"
    canvas.write_text(_SCOPE_CANVAS, encoding="utf-8")
    rc = main(
        ["--canvas", str(canvas), "--ops", "T01", "--changed", "src/app.py", "--changed", "src/other.py"]
    )
    captured = capsys.readouterr()
    assert rc == 1
    assert "review result: Changes Requested" in captured.out
    assert "Approved With Notes" not in captured.out

    rc = main(["--canvas", str(canvas), "--ops", "T01", "--changed", "src/app.py"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "review result: scope ok" in captured.out


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def test_git_delete_passes_and_rename_destination_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    canvas_dir = root / "sdlc-spdd" / "spdd" / "canvas"
    canvas_dir.mkdir(parents=True)
    canvas = canvas_dir / "SCOPE-I2.md"
    canvas.write_text(_SCOPE_CANVAS, encoding="utf-8")
    src = root / "src"
    src.mkdir()
    (src / "app.py").write_text("print('ok')\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "init")
    current = subprocess.check_output(
        ["git", "-C", str(root), "branch", "--show-current"], text=True
    ).strip()
    if current != "main":
        _git(root, "branch", "-M", "main")

    _git(root, "checkout", "-b", "delete-app")
    _git(root, "rm", "src/app.py")
    _git(root, "commit", "-m", "delete app")
    rc = main(["--canvas", str(canvas), "--root", str(root), "--ops", "T01"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "review result: scope ok" in captured.out

    _git(root, "checkout", "main")
    _git(root, "checkout", "-b", "rename-app")
    _git(root, "mv", "src/app.py", "src/renamed.py")
    _git(root, "commit", "-m", "rename app")
    rc = main(["--canvas", str(canvas), "--root", str(root), "--ops", "T01"])
    captured = capsys.readouterr()
    assert rc == 1
    assert "review result: Changes Requested" in captured.out
    assert "src/renamed.py" in captured.out.split("extra:")[1]
