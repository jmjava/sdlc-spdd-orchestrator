#!/usr/bin/env python3
"""Hotspot gate for changed Python files.

Fails only when a changed Python file is both complex and in the top
git change-frequency set. Complex means a function over the same CCN / NLOC
limits as scripts/check-complexity.py. That diff gate stays the Clean as You
Code check; this script does not replace it.

A complex file outside the top churn set does not fail. A frequently changed
file that is not complex does not fail. Untouched files do not fail.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import subprocess
import sys
from pathlib import Path


def git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).rstrip("\n")


def load_complexity():
    path = Path(__file__).with_name("check-complexity.py")
    spec = importlib.util.spec_from_file_location("check_complexity", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def python_change_counts(repo: Path, paths: list[str]) -> dict[str, int]:
    log = git("log", "--name-only", "--pretty=format:", "--", *paths, cwd=repo)
    counts: dict[str, int] = {}
    for line in log.splitlines():
        rel = line.strip().replace("\\", "/")
        if not rel.endswith(".py"):
            continue
        counts[rel] = counts.get(rel, 0) + 1
    return counts


def top_change_set(counts: dict[str, int], fraction: float) -> tuple[set[str], int]:
    ranked = sorted(
        ((count, path) for path, count in counts.items() if count > 0),
        key=lambda item: (-item[0], item[1]),
    )
    if not ranked:
        return set(), 0
    cutoff_index = max(1, math.ceil(len(ranked) * fraction)) - 1
    threshold = ranked[cutoff_index][0]
    return {path for count, path in ranked if count >= threshold}, threshold


def max_metrics(rows: list[dict[str, str]]) -> tuple[int, int]:
    max_ccn = 0
    max_nloc = 0
    for row in rows:
        max_ccn = max(max_ccn, int(row["ccn"]))
        max_nloc = max(max_nloc, int(row["nloc"]))
    return max_ccn, max_nloc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="origin/main", help="git ref to compare against")
    parser.add_argument("--repo", default=".", help="repository root")
    parser.add_argument("--ccn", type=int, default=10)
    parser.add_argument("--nloc", type=int, default=80)
    parser.add_argument(
        "--fraction",
        type=float,
        default=0.10,
        help="top fraction of Python files by commit count (ties at the cutoff are included)",
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        default=["."],
        help="pathspecs to diff and to rank by change frequency",
    )
    args = parser.parse_args()
    if args.fraction <= 0 or args.fraction > 1:
        print("check-hotspots: --fraction must be in (0, 1]", file=sys.stderr)
        return 2
    repo = Path(args.repo).resolve()
    failures: list[str] = []
    files: list[str] = []
    try:
        complexity = load_complexity()
        files = complexity.changed_files(repo, args.base, args.paths, {".py"})
        counts = python_change_counts(repo, args.paths)
        hot, threshold = top_change_set(counts, args.fraction)
        for rel in sorted(set(files) & hot):
            src = complexity.file_at(repo, "HEAD", rel) or ""
            rows = complexity.lizard_rows(src, rel, "python")
            max_ccn, max_nloc = max_metrics(rows)
            if max(max_ccn - args.ccn, max_nloc - args.nloc) > 0:
                failures.append(
                    f"HOT {rel} commits={counts.get(rel, 0)} "
                    f"maxCCN={max_ccn} maxNLOC={max_nloc} "
                    f"(top {args.fraction:.0%} threshold {threshold} commits)"
                )
    except (subprocess.CalledProcessError, OSError, RuntimeError) as exc:
        print(f"check-hotspots: {exc}", file=sys.stderr)
        return 2
    if not files:
        print("check-hotspots: no changed Python files")
        return 0

    if failures:
        print("check-hotspots: FAIL", file=sys.stderr)
        for line in failures:
            print(line, file=sys.stderr)
        return 1
    print(f"check-hotspots: PASS ({len(files)} changed Python file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
