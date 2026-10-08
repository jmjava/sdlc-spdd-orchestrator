"""Review Result forced by the Files: path check.

The path comparison stays in ``canvas.check_operation_diff_scope``. This module
only decides the Result line. It is not ``gate_check`` and not hunk review.
``canvas.py`` stays untouched: that file is a churn hotspot.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .canvas import (
    DiffScopeResult,
    GitChangedPathsError,
    _resolve_canvas_path,
    check_operation_diff_scope,
    collect_git_changed_paths,
)
from .files_grammar import load_canvas_texts

APPROVED_REVIEW_RESULTS: frozenset[str] = frozenset({"Approved", "Approved With Notes"})
SCOPE_FAIL_REVIEW_RESULT = "Changes Requested"


def review_result_for_scope(scope: DiffScopeResult, proposed: str | None = None) -> str:
    """Result a failed path check is allowed to produce.

    Extra paths, absolute paths, and ``..`` traversal cannot yield
    ``Approved`` or ``Approved With Notes``. A proposed ``Changes Requested``
    or ``Blocked`` is kept. A passing check keeps the proposed result
    (default ``Approved``). Path names only.
    """
    text = (proposed or "").strip()
    if scope.ok:
        return text or "Approved"
    if text in ({"Changes Requested", "Blocked"} - APPROVED_REVIEW_RESULTS):
        return text
    return SCOPE_FAIL_REVIEW_RESULT


def scope_review_result_line(scope: DiffScopeResult) -> str:
    """Printed ``review result:`` line. A pass does not pick a label."""
    if scope.ok:
        return "review result: scope ok"
    return f"review result: {review_result_for_scope(scope)}"


def format_scope_report(scope: DiffScopeResult) -> str:
    report = scope.format_report()
    if not report.endswith("\n"):
        report += "\n"
    return report + scope_review_result_line(scope) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    """CLI used by check-operation-diff-scope.sh. Not gate_check."""
    parser = argparse.ArgumentParser(
        prog="python -m sdlc_engine.review_scope",
        description=(
            "Review-time path-scope check. Extra paths print "
            "review result: Changes Requested. Not gate_check."
        ),
    )
    parser.add_argument("--canvas", help="Path to the REASONS canvas")
    parser.add_argument("--work-id", help="Resolve canvas via Project.canvas_path")
    parser.add_argument("--ops", help="Comma-separated T## ids")
    parser.add_argument("--base", help="Compare committed changes to REF...HEAD")
    parser.add_argument("--root", default=".", help="Repo root (default: cwd)")
    parser.add_argument("--changed", action="append", default=[], help="Changed path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.root).expanduser()
    canvas_path = _resolve_canvas_path(args.work_id, args.canvas, root)
    if not canvas_path.is_file():
        print(f"check-diff-scope: canvas not found: {canvas_path}", file=sys.stderr)
        return 1
    selected = [part.strip() for part in (args.ops or "").split(",") if part.strip()] or None
    if args.changed:
        changed = list(args.changed)
    else:
        try:
            changed = collect_git_changed_paths(repo=root, base=args.base)
        except GitChangedPathsError as exc:
            print(f"check-diff-scope: {exc}", file=sys.stderr)
            return 1
    result = check_operation_diff_scope(
        canvas_path.read_text(encoding="utf-8"),
        changed,
        selected_ops=selected,
        related_canvases=load_canvas_texts(root),
    )
    sys.stdout.write(format_scope_report(result))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
