#!/usr/bin/env python3
"""PR-diff complexity gate.

Fails when a *changed* file introduces a new function with CCN > 10 or NLOC > 80,
or when an existing function's CCN rises. Untouched hotspots do not fail.
Docs-only diffs exit 0.
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


def changed_files(repo: Path, base: str, paths: list[str], exts: set[str]) -> list[str]:
    rels = git("diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD", "--", *paths, cwd=repo)
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
    try:
        return git("show", f"{rev}:{rel}", cwd=repo)
    except subprocess.CalledProcessError:
        return None


def index_funcs(rows: list[dict[str, str]]) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    for row in rows:
        out[row["name"]] = (int(row["ccn"]), int(row["nloc"]))
    return out


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

    failures: list[str] = []
    for rel in files:
        language = EXTS[Path(rel).suffix]
        head = file_at(repo, "HEAD", rel)
        if head is None:
            continue
        base_src = file_at(repo, args.base, rel)
        head_funcs = index_funcs(lizard_rows(head, rel, language))
        base_funcs = index_funcs(lizard_rows(base_src, rel, language)) if base_src is not None else {}
        for name, (ccn, nloc) in sorted(head_funcs.items()):
            if name not in base_funcs:
                if ccn > args.ccn or nloc > args.nloc:
                    failures.append(
                        f"NEW {rel}::{name} CCN={ccn} NLOC={nloc} (limits {args.ccn}/{args.nloc})"
                    )
                continue
            old_ccn, _old_nloc = base_funcs[name]
            if ccn > old_ccn:
                failures.append(f"RISE {rel}::{name} CCN {old_ccn} -> {ccn}")

    if failures:
        print("check-complexity: FAIL", file=sys.stderr)
        for line in failures:
            print(line, file=sys.stderr)
        return 1
    print(f"check-complexity: PASS ({len(files)} file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
