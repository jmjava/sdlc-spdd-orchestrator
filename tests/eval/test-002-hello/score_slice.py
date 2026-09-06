"""TEST-002 first-slice scorer (symbol proxy for C-DRIFT, not git hunks).

Counts added top-level ``def`` names versus the frozen gold ``src/hello.py``.
A def is mapped if its name appears in the eval operation description
(T01). Extra defs are unmapped. This is **not** hunk-level C-DRIFT
(FEAT-016 remainder). n=1 slices must be labeled protocol incomplete.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOLD_SRC = ROOT / "src" / "hello.py"
CANVAS = ROOT / "canvas" / "TEST-002-hello.md"
RUNS = ROOT / "runs"


def top_level_defs(text: str) -> set[str]:
    return set(re.findall(r"^def ([A-Za-z_][A-Za-z0-9_]*)\s*\(", text, re.MULTILINE))


def eval_op_text(canvas: str) -> str:
    match = re.search(r"### T01 -.+$", canvas, re.MULTILINE)
    if not match:
        return ""
    start = match.start()
    nxt = re.search(r"^### T", canvas[start + 1 :], re.MULTILINE)
    end = start + 1 + nxt.start() if nxt else len(canvas)
    return canvas[start:end]


def score_run(name: str) -> dict:
    gold_defs = top_level_defs(GOLD_SRC.read_text(encoding="utf-8"))
    run_src = RUNS / name / "src" / "hello.py"
    run_defs = top_level_defs(run_src.read_text(encoding="utf-8"))
    added = sorted(run_defs - gold_defs)
    op = eval_op_text(CANVAS.read_text(encoding="utf-8")).lower()
    mapped = [d for d in added if d.lower() in op]
    unmapped = [d for d in added if d.lower() not in op]
    unimplemented = 0 if "farewell" in {d.lower() for d in added} else 1
    n_hunks = len(added)
    n_ops = 1
    numer = len(unmapped) + unimplemented
    denom = n_hunks + n_ops
    rate = numer / denom if denom else 0.0
    return {
        "condition": name,
        "added_defs": added,
        "mapped_defs": mapped,
        "unmapped_defs": unmapped,
        "n_unmapped_hunks": len(unmapped),
        "n_unimplemented_ops": unimplemented,
        "n_hunks": n_hunks,
        "n_ops": n_ops,
        "scope_deviation_rate": rate,
        "proxy": "top-level-def (not git hunks)",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = {
        "gold": str(GOLD_SRC.relative_to(ROOT)),
        "canvas": str(CANVAS.relative_to(ROOT)),
        "n": 1,
        "protocol": "incomplete",
        "c_port_reported": False,
        "runs": [score_run("unstructured"), score_run("method")],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
