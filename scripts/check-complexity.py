#!/usr/bin/env python3
"""PR-diff complexity gate.

Fails when a *changed* file introduces a new function with CCN > 10 or NLOC > 80,
or when an existing function's CCN rises. Untouched hotspots do not fail.
Docs-only diffs exit 0.

A function that disappears from one changed/deleted file and reappears under the
same name in another changed file is a MOVE: it is judged against its old CCN
(rise fails) rather than as NEW, so splitting a module does not trip the gate.
"""

from __future__ import annotations

import argparse
import csv
import io
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_CCN = 10
DEFAULT_NLOC = 80
EXTS = {".py": "python", ".java": "java"}


def git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).rstrip("\n")


def changed_files(
    repo: Path, base: str, paths: list[str], exts: set[str], diff_filter: str = "ACMR"
) -> list[str]:
    rels = git(
        "diff", "--name-only", f"--diff-filter={diff_filter}", f"{base}...HEAD", "--", *paths, cwd=repo
    )
    files = []
    for line in rels.splitlines():
        line = line.strip()
        if not line:
            continue
        if Path(line).suffix in exts:
            files.append(line)
    return files


def lizard_rows(source: str, filename: str, language: str) -> list[dict[str, str]]:
    if not source.strip():
        return []
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / Path(filename).name
        dest.write_text(source, encoding="utf-8")
        csv_path = Path(tmp) / "out.csv"
        subprocess.run(
            ["lizard", "-l", language, "-C", "999", "-L", "999999", "-o", str(csv_path), str(dest)],
            check=True,
            capture_output=True,
            text=True,
        )
        text = csv_path.read_text(encoding="utf-8")
    rows = []
    reader = csv.reader(io.StringIO(text))
    for rec in reader:
        if len(rec) < 9:
            continue
        rows.append(
            {
                "nloc": rec[0],
                "ccn": rec[1],
                "name": rec[7],
                "file": filename,
            }
        )
    return rows


def file_at(repo: Path, rev: str, rel: str) -> str | None:
    proc = subprocess.run(
        ["git", "show", f"{rev}:{rel}"], cwd=repo, text=True, capture_output=True, check=False
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.rstrip("\n")


def index_funcs(rows: list[dict[str, str]]) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    for row in rows:
        out[row["name"]] = (int(row["ccn"]), int(row["nloc"]))
    return out


def base_index(repo: Path, base: str, rels: list[str]) -> dict[str, dict[str, tuple[int, int]]]:
    """Per-file function index at ``base`` for every path in ``rels``."""
    out: dict[str, dict[str, tuple[int, int]]] = {}
    for rel in rels:
        src = file_at(repo, base, rel)
        out[rel] = index_funcs(lizard_rows(src, rel, EXTS[Path(rel).suffix])) if src else {}
    return out


def moved_from(name: str, base_all: dict[str, dict[str, tuple[int, int]]]) -> tuple[int, int] | None:
    """Return the base (ccn, nloc) if ``name`` existed in any base file of the diff.

    When the same name existed in several files, the largest CCN is used so a
    move is never judged more harshly than its worst previous home.
    """
    hits = [funcs[name] for funcs in base_all.values() if name in funcs]
    return max(hits) if hits else None


def judge_file(
    rel: str,
    head_funcs: dict[str, tuple[int, int]],
    base_funcs: dict[str, tuple[int, int]],
    base_all: dict[str, dict[str, tuple[int, int]]],
    ccn_limit: int,
    nloc_limit: int,
) -> list[str]:
    failures: list[str] = []
    for name, (ccn, nloc) in sorted(head_funcs.items()):
        old = base_funcs.get(name)
        tag = "RISE"
        if old is None:
            old = moved_from(name, base_all)
            tag = "RISE (moved)"
        if old is None:
            if ccn > ccn_limit or nloc > nloc_limit:
                failures.append(
                    f"NEW {rel}::{name} CCN={ccn} NLOC={nloc} (limits {ccn_limit}/{nloc_limit})"
                )
        elif ccn > old[0]:
            failures.append(f"{tag} {rel}::{name} CCN {old[0]} -> {ccn}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="origin/main", help="git ref to compare against")
    parser.add_argument("--repo", default=".", help="repository root")
    parser.add_argument("--ccn", type=int, default=DEFAULT_CCN)
    parser.add_argument("--nloc", type=int, default=DEFAULT_NLOC)
    parser.add_argument(
        "--paths",
        nargs="*",
        default=["."],
        help="pathspecs to diff (default: whole tree)",
    )
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    try:
        files = changed_files(repo, args.base, args.paths, set(EXTS))
    except subprocess.CalledProcessError as exc:
        print(f"git diff failed: {exc}", file=sys.stderr)
        return 2
    if not files:
        print("check-complexity: no changed source files")
        return 0

    deleted = changed_files(repo, args.base, args.paths, set(EXTS), diff_filter="D")
    base_all = base_index(repo, args.base, [*files, *deleted])

    failures: list[str] = []
    for rel in files:
        head = file_at(repo, "HEAD", rel)
        if head is None:
            continue
        head_funcs = index_funcs(lizard_rows(head, rel, EXTS[Path(rel).suffix]))
        failures.extend(judge_file(rel, head_funcs, base_all[rel], base_all, args.ccn, args.nloc))

    if failures:
        print("check-complexity: FAIL", file=sys.stderr)
        for line in failures:
            print(line, file=sys.stderr)
        return 1
    print(f"check-complexity: PASS ({len(files)} file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
