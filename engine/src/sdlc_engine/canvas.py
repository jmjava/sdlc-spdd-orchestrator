"""REASONS Canvas helpers: Final Status, operations, and review-time Files: scope."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


def final_status_text(canvas_path: Path) -> str:
    if not canvas_path.is_file():
        return ""
    text = canvas_path.read_text(encoding="utf-8")
    in_final = False
    for line in text.splitlines():
        if line.startswith("## Final Status"):
            in_final = True
            continue
        if in_final and line.startswith("## "):
            break
        if in_final and line.startswith("- Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def final_kind(canvas_path: Path) -> str:
    """Return complete | cancelled | other."""
    line = final_status_text(canvas_path).lower()
    if not line:
        return "other"
    if "cancel" in line:
        return "cancelled"
    if "complete" in line and "in progress" not in line:
        return "complete"
    return "other"


def is_archivable(canvas_path: Path) -> bool:
    return final_kind(canvas_path) in {"complete", "cancelled"}


_OP_HEADER = re.compile(r"^###\s+(T\d+)\s*[-–—:]\s*(.+)$")
_OP_STATUS = re.compile(r"^- Status:\s*(.+)$", re.IGNORECASE)
_OP_STATUS_ANY = re.compile(r"^- Status:\s*\S", re.IGNORECASE)
_YAML_READINESS = re.compile(r"^readiness:\s*(.+)$", re.IGNORECASE)
_META_READINESS = re.compile(r"^-+\s*Readiness:\s*(.+)$", re.IGNORECASE)

# Mirror scripts/lib/readiness.sh — keep these lists in sync.
READINESS_CANONICAL = (
    "needs-analysis",
    "needs-clarification",
    "needs-redesign",
    "ready-for-coding",
    "blocked",
    "reviewed",
    "complete",
)
CODING_ALLOWED_READINESS = frozenset({"ready-for-coding", "reviewed", "complete"})


def section_body(text: str, heading: str) -> str:
    """Body under ``## {heading}`` until the next ``## `` heading."""
    lines = text.splitlines()
    collecting = False
    body: list[str] = []
    needle = f"## {heading}"
    for line in lines:
        if line.startswith(needle):
            collecting = True
            continue
        if collecting and line.startswith("## "):
            break
        if collecting:
            body.append(line)
    return "\n".join(body)


def _frontmatter_readiness(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = _YAML_READINESS.match(line.strip())
        if match:
            return match.group(1).strip().strip("'\"")
    return ""


def extract_readiness_raw(text: str) -> str:
    """Structured readiness only: YAML frontmatter or Metadata ``- Readiness:``.

    A 'Ready For Coding' phrase in Sync Notes or Architecture Notes does not count.
    """
    raw = _frontmatter_readiness(text)
    if raw:
        return raw
    meta = section_body(text, "Metadata")
    for line in meta.splitlines():
        match = _META_READINESS.match(line.strip())
        if match:
            return match.group(1).strip()
    return ""


def normalize_readiness(raw: str) -> str:
    """Return a canonical readiness token, or '' if unrecognized."""
    lower = raw.strip().lower()
    lower = re.sub(r"\([^)]*\)", "", lower).strip()
    lower = re.sub(r"[\s_]+", "-", lower)
    lower = re.sub(r"[^a-z0-9-]+", "-", lower)
    lower = re.sub(r"-+", "-", lower).strip("-")
    exact = {
        "needs-analysis": "needs-analysis",
        "need-analysis": "needs-analysis",
        "needs-clarification": "needs-clarification",
        "need-clarification": "needs-clarification",
        "needs-redesign": "needs-redesign",
        "need-redesign": "needs-redesign",
        "ready-for-coding": "ready-for-coding",
        "ready-for-code": "ready-for-coding",
        "blocked": "blocked",
        "reviewed": "reviewed",
        "complete": "complete",
        "done": "complete",
        "completed": "complete",
    }
    if lower in exact:
        return exact[lower]
    if lower.startswith("ready-for-coding"):
        return "ready-for-coding"
    if lower.startswith("reviewed"):
        return "reviewed"
    if lower.startswith("complete"):
        return "complete"
    return ""


def section_has_content(text: str, heading: str) -> bool:
    """True when the section has a non-heading, non-blank line."""
    for line in section_body(text, heading).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return True
    return False


def has_operation_with_status(text: str) -> bool:
    in_ops = False
    saw_op = False
    for line in text.splitlines():
        if line.startswith("## O") or line.startswith("## Operations"):
            in_ops = True
            continue
        if in_ops and line.startswith("## ") and not line.startswith("## O"):
            break
        if not in_ops:
            continue
        if _OP_HEADER.match(line.strip()) or re.match(r"^###\s+T\d+\b", line.strip()):
            saw_op = True
            continue
        if saw_op and _OP_STATUS_ANY.match(line.strip()):
            return True
    return False


def semantic_issues(text: str, *, strict_readiness: bool = False) -> list[str]:
    """Issues for a headings-present canvas that is still semantically empty."""
    issues: list[str] = []
    if not section_has_content(text, "R - Requirements") and not section_has_content(
        text, "Requirements"
    ):
        issues.append("empty Requirements section")
    if not has_operation_with_status(text):
        issues.append("no T## operation with Status")
    if strict_readiness:
        raw = extract_readiness_raw(text)
        if raw and not normalize_readiness(raw):
            issues.append(f"unrecognized readiness {raw!r}")
    return issues


def coding_gate_issues(text: str) -> list[str]:
    """Failures that block entering the code phase (C-COMPLY semantic minima)."""
    issues = semantic_issues(text)
    raw = extract_readiness_raw(text)
    if not raw:
        issues.append(
            "missing structured Readiness field (YAML frontmatter or Metadata); "
            "a Ready For Coding phrase elsewhere does not count"
        )
        return issues
    canon = normalize_readiness(raw)
    if not canon:
        issues.append(f"unrecognized readiness {raw!r} (not Ready For Coding)")
    elif canon not in CODING_ALLOWED_READINESS:
        issues.append(f"readiness is {canon}, not Ready For Coding")
    return issues


def canvas_allows_coding(text: str) -> bool:
    return not coding_gate_issues(text)


_FILES_LINE = re.compile(r"^- Files:\s*\S", re.IGNORECASE)
_FILES_CAPTURE = re.compile(r"^- Files:\s*(.+)$", re.IGNORECASE)

# Review-time test-path allow rule (Kasana I2 / CASP-04). Documented in
# scripts/check-operation-diff-scope.sh and sdlc-spdd/docs/research/code-maps-to-ops.md.
# A changed path is an allowed test path when:
#   - it is exactly `tests` or sits under `tests/`, `engine/tests_unit/`,
#     `engine/tests_integration/`, or `engine/tests_e2e/`; or
#   - its basename matches `test_*.py`, `*_test.py`, or `*.spec.md`.
ALLOWED_TEST_DIR_PREFIXES: tuple[str, ...] = (
    "tests/",
    "engine/tests_unit/",
    "engine/tests_integration/",
    "engine/tests_e2e/",
)

_CODED_STATUS_MARKERS = ("complete", "done", "selected", "in progress")


def operation_mapping_issues(text: str) -> list[str]:
    """Automated remainder of code_maps_to_ops: each T## must name Files.

    Hunk-level mapping to those paths is still a human/TEST-002 remainder.
    """
    in_ops = False
    current: str | None = None
    saw_files = False
    missing: list[str] = []
    ops = 0
    for line in text.splitlines():
        if line.startswith("## O") or line.startswith("## Operations"):
            in_ops = True
            continue
        if in_ops and line.startswith("## ") and not line.startswith("## O"):
            if current and not saw_files:
                missing.append(current)
            break
        if not in_ops:
            continue
        header = _OP_HEADER.match(line.strip()) or re.match(r"^###\s+(T\d+)\b", line.strip())
        if header:
            if current and not saw_files:
                missing.append(current)
            current = header.group(1)
            saw_files = False
            ops += 1
            continue
        if current and _FILES_LINE.match(line.strip()):
            saw_files = True
    if current and not saw_files:
        missing.append(current)
    if ops == 0:
        return ["no T## operation with a Files: mapping"]
    if missing:
        return [f"operation {op} missing Files: mapping" for op in missing]
    return []


def review_minima_issues(text: str) -> list[str]:
    """C-COMPLY review minima: not empty, Result stated, safeguards explicit."""
    issues: list[str] = []
    stripped = text.strip()
    if len(stripped) < 40:
        issues.append("review is empty or too short to be a review")
    if not re.search(r"(?im)^\s*(?:#+\s*)?(?:\*\*)?result(?:\*\*)?\s*:", text):
        issues.append("review missing Result line")
    if not re.search(r"(?i)safeguard", text):
        issues.append("review does not mention safeguards")
    return issues



def next_operation(canvas_path: Path) -> tuple[str, str]:
    """Return (operation_id, title) for the first incomplete Operation, else ('', '')."""
    if not canvas_path.is_file():
        return "", ""
    current_op = ""
    current_title = ""
    in_ops = False
    for line in canvas_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## O") or line.startswith("## Operations"):
            in_ops = True
            continue
        if in_ops and line.startswith("## ") and not line.startswith("## O"):
            break
        if not in_ops:
            continue
        m = _OP_HEADER.match(line.strip())
        if m:
            current_op, current_title = m.group(1), m.group(2).strip()
            continue
        if current_op:
            sm = _OP_STATUS.match(line.strip())
            if sm:
                status = sm.group(1).strip().lower()
                if "complete" not in status and "done" not in status:
                    return current_op, current_title
                current_op, current_title = "", ""
    return "", ""


def normalize_repo_path(raw: str) -> str | None:
    """Return a repo-relative POSIX path, or None if empty, absolute, or ``..``.

    Does not resolve ``..`` components — any traversal token is rejected.
    """
    s = raw.strip().strip("`").strip().strip("'\"").strip()
    if not s:
        return None
    s = s.replace("\\", "/")
    if s.startswith("/") or (len(s) >= 2 and s[1] == ":"):
        return None
    parts: list[str] = []
    for part in s.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            return None
        parts.append(part)
    if not parts:
        return None
    return "/".join(parts)


def parse_files_tokens(rest: str) -> tuple[str, ...]:
    """Split a ``- Files:`` remainder into path tokens (backticks or commas)."""
    quoted = re.findall(r"`([^`]+)`", rest)
    raw_tokens = quoted if quoted else [part.strip() for part in rest.split(",")]
    out: list[str] = []
    seen: set[str] = set()
    for raw in raw_tokens:
        tok = raw.strip().strip("`").strip("'\"").strip()
        if not tok or tok.lower() in {"and", "or"}:
            continue
        if tok not in seen:
            seen.add(tok)
            out.append(tok)
    return tuple(out)


def is_allowed_test_path(rel: str) -> bool:
    """True when ``rel`` matches the documented review-time test-path rule."""
    if rel == "tests" or any(
        rel == prefix.rstrip("/") or rel.startswith(prefix)
        for prefix in ALLOWED_TEST_DIR_PREFIXES
    ):
        return True
    name = rel.rsplit("/", 1)[-1]
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if name.endswith("_test.py"):
        return True
    return name.endswith(".spec.md")


def path_allowed_by_files(rel: str, files: set[str]) -> bool:
    """Exact Files: match, or a descendant of a Files: directory entry."""
    if rel in files:
        return True
    for allowed in files:
        prefix = allowed.rstrip("/")
        if prefix and rel.startswith(prefix + "/"):
            return True
    return False


def _is_coded_status(status: str) -> bool:
    lower = status.lower()
    return any(marker in lower for marker in _CODED_STATUS_MARKERS)


def _iter_operation_records(text: str) -> list[tuple[str, str, tuple[str, ...]]]:
    """Return ``(op_id, status, files_tokens)`` for each T## under Operations."""
    in_ops = False
    current: str | None = None
    status = ""
    files: list[str] = []
    records: list[tuple[str, str, tuple[str, ...]]] = []

    def flush() -> None:
        nonlocal current, status, files
        if current:
            records.append((current, status, tuple(files)))
        current = None
        status = ""
        files = []

    for line in text.splitlines():
        if line.startswith("## O") or line.startswith("## Operations"):
            in_ops = True
            continue
        if in_ops and line.startswith("## ") and not line.startswith("## O"):
            flush()
            break
        if not in_ops:
            continue
        header = _OP_HEADER.match(line.strip()) or re.match(r"^###\s+(T\d+)\b", line.strip())
        if header:
            flush()
            current = header.group(1)
            continue
        if not current:
            continue
        sm = _OP_STATUS.match(line.strip())
        if sm:
            status = sm.group(1).strip()
            continue
        fm = _FILES_CAPTURE.match(line.strip())
        if fm:
            files.extend(parse_files_tokens(fm.group(1)))
    flush()
    return records


def operation_files(
    text: str,
    *,
    selected_ops: Sequence[str] | None = None,
) -> dict[str, tuple[str, ...]]:
    """Files: tokens for selected/completed T## ops, or all T## if none selected."""
    records = _iter_operation_records(text)
    chosen: list[tuple[str, str, tuple[str, ...]]]
    if selected_ops:
        wanted = {op.strip().upper() for op in selected_ops if op.strip()}
        chosen = [rec for rec in records if rec[0].upper() in wanted]
    else:
        coded = [rec for rec in records if _is_coded_status(rec[1])]
        chosen = coded if coded else list(records)
    return {op_id: files for op_id, _status, files in chosen}


def allowed_files_from_operations(op_map: dict[str, tuple[str, ...]]) -> set[str]:
    """Normalize Files: tokens; drop empty / absolute / ``..`` entries."""
    allowed: set[str] = set()
    for tokens in op_map.values():
        for raw in tokens:
            norm = normalize_repo_path(raw)
            if norm:
                allowed.add(norm)
    return allowed


@dataclass(frozen=True)
class DiffScopeResult:
    """Path-level Files: vs diff check. Hunk-level C-DRIFT is out of scope."""

    ok: bool
    extra_paths: tuple[str, ...]
    allowed_files: tuple[str, ...]
    changed_paths: tuple[str, ...]
    traversal_rejected: tuple[str, ...]
    operations_used: tuple[str, ...]

    def format_report(self) -> str:
        lines = [
            f"operation-diff-scope: {'PASS' if self.ok else 'FAIL'}",
            f"operations: {', '.join(self.operations_used) or '(none)'}",
            "allowed Files:",
        ]
        if self.allowed_files:
            lines.extend(f"  {path}" for path in self.allowed_files)
        else:
            lines.append("  (none)")
        lines.append(
            "allowed test paths: tests/**, engine/tests_unit/**, "
            "engine/tests_integration/**, engine/tests_e2e/**, "
            "basename test_*.py / *_test.py / *.spec.md"
        )
        lines.append("changed:")
        if self.changed_paths:
            lines.extend(f"  {path}" for path in self.changed_paths)
        else:
            lines.append("  (none)")
        if self.traversal_rejected:
            lines.append("traversal rejected:")
            lines.extend(f"  {path}" for path in self.traversal_rejected)
        if self.extra_paths:
            lines.append("extra:")
            lines.extend(f"  {path}" for path in self.extra_paths)
        return "\n".join(lines) + "\n"


def check_operation_diff_scope(
    canvas_text: str,
    changed_paths: Sequence[str],
    *,
    selected_ops: Sequence[str] | None = None,
) -> DiffScopeResult:
    """Compare changed paths to coded operations' Files: plus allowed test paths.

    Extra production paths or ``..`` traversal => ``ok`` is False. Renames and
    deletes are the path names supplied (whatever ``git diff --name-only``
    reported). Not used by ``gate_check(code)``.
    """
    op_map = operation_files(canvas_text, selected_ops=selected_ops)
    allowed = allowed_files_from_operations(op_map)
    changed_norm: list[str] = []
    traversal: list[str] = []
    extra: list[str] = []
    seen_changed: set[str] = set()
    seen_extra: set[str] = set()
    seen_trav: set[str] = set()

    for raw in changed_paths:
        display = raw.strip()
        if not display or display in seen_changed:
            continue
        seen_changed.add(display)
        norm = normalize_repo_path(raw)
        if norm is None:
            changed_norm.append(display)
            if display not in seen_trav:
                seen_trav.add(display)
                traversal.append(display)
            if display not in seen_extra:
                seen_extra.add(display)
                extra.append(display)
            continue
        changed_norm.append(norm)
        if path_allowed_by_files(norm, allowed) or is_allowed_test_path(norm):
            continue
        if norm not in seen_extra:
            seen_extra.add(norm)
            extra.append(norm)

    extra_t = tuple(extra)
    trav_t = tuple(traversal)
    return DiffScopeResult(
        ok=not extra_t and not trav_t,
        extra_paths=extra_t,
        allowed_files=tuple(sorted(allowed)),
        changed_paths=tuple(changed_norm),
        traversal_rejected=trav_t,
        operations_used=tuple(op_map.keys()),
    )


class GitChangedPathsError(Exception):
    """git path collection failed (missing git, invalid --base, no merge-base)."""


_DEFAULT_DIFF_SCOPE_BASES: tuple[str, ...] = (
    "origin/main",
    "main",
    "origin/master",
    "master",
)


def _git_output(repo: Path, *args: str, check: bool = True) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=repo,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise GitChangedPathsError("git is not available on PATH") from exc
    if check and proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip() or f"exit {proc.returncode}"
        raise GitChangedPathsError(f"git {' '.join(args)} failed: {err}")
    return proc.stdout


def resolve_diff_scope_base(repo: Path, preferred: str | None = None) -> str:
    """Return the ref used for ``<ref>...HEAD``.

    Explicit ``preferred`` must exist and share a merge-base with HEAD.
    When omitted, use the merge-base with the default branch
    (``origin/main``, ``main``, ``origin/master``, ``master``).
    """
    if preferred and preferred.strip():
        ref = preferred.strip()
        _git_output(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
        mb = _git_output(repo, "merge-base", "HEAD", ref).strip()
        if not mb:
            raise GitChangedPathsError(f"could not resolve merge-base with {ref}")
        return ref

    for ref in _DEFAULT_DIFF_SCOPE_BASES:
        parsed = _git_output(
            repo, "rev-parse", "--verify", f"{ref}^{{commit}}", check=False
        ).strip()
        if not parsed:
            continue
        mb = _git_output(repo, "merge-base", "HEAD", ref, check=False).strip()
        if mb:
            return mb
    raise GitChangedPathsError(
        "could not resolve a merge base (tried "
        + ", ".join(_DEFAULT_DIFF_SCOPE_BASES)
        + ")"
    )


def collect_git_changed_paths(
    *,
    repo: Path,
    base: str | None = None,
) -> list[str]:
    """Uncommitted vs HEAD plus committed since merge-base with ``base``.

    When ``base`` is omitted, resolve merge-base with the default branch so
    committed out-of-scope edits still appear. Invalid ``base`` raises
    ``GitChangedPathsError`` instead of returning an empty list.
    """
    effective = resolve_diff_scope_base(repo, base)
    paths: list[str] = []
    seen: set[str] = set()

    def add_from(args: list[str]) -> None:
        out = _git_output(repo, *args)
        for line in out.splitlines():
            name = line.strip()
            if name and name not in seen:
                seen.add(name)
                paths.append(name)

    add_from(["diff", "--name-only", "HEAD"])
    add_from(["diff", "--name-only", f"{effective}...HEAD"])
    return paths


def _resolve_canvas_path(work_id: str | None, canvas: str | None, root: Path) -> Path:
    if canvas:
        return Path(canvas)
    if not work_id:
        raise SystemExit("check-diff-scope: --canvas or --work-id is required")
    from .project import Project

    path = Project.resolve(root).canvas_path(work_id)
    if path.is_file():
        return path
    raise SystemExit(f"check-diff-scope: canvas not found: {path}")


def check_diff_scope_main(argv: Sequence[str] | None = None) -> int:
    """Thin CLI: compare git/changed paths to canvas Files: plus test paths."""
    parser = argparse.ArgumentParser(
        prog="python -m sdlc_engine.canvas",
        description=(
            "Review-time path-scope check: git diff paths must be a subset of "
            "coded T## Files: plus allowed test paths. Not gate_check(code)."
        ),
    )
    parser.add_argument("--canvas", help="Path to the REASONS canvas")
    parser.add_argument("--work-id", help="Resolve canvas via Project.canvas_path")
    parser.add_argument(
        "--ops",
        help="Comma-separated T## ids (default: selected/completed, else all T##)",
    )
    parser.add_argument(
        "--base",
        help=(
            "Compare committed changes to REF...HEAD (must exist). "
            "Default: merge-base with origin/main, main, origin/master, or master"
        ),
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repo root for git and canvas resolution (default: cwd)",
    )
    parser.add_argument(
        "--changed",
        action="append",
        default=[],
        help="Changed path (repeatable). When set, skip git collection.",
    )
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
    )
    sys.stdout.write(result.format_report())
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(check_diff_scope_main())
