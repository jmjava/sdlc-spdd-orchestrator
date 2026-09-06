#!/usr/bin/env python3
"""Structured checks for the committed dogfood lessons ledger (CHORE-003).

An empty file, a token stub that only names kinds, or a missing decision /
pitfall / pattern record must fail. This is a C-MEMORY *precondition*
(memory exists to retrieve), not an RQ4 usefulness result.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LIVE_LEDGER = REPO_ROOT / "sdlc-spdd" / "spdd" / "memory" / "lessons.jsonl"
REQUIRED_KINDS = ("decision", "pitfall", "pattern")
MIN_BODY = 40


def parse_records(text: str) -> list[dict]:
    out: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def issues_for_dogfood_ledger(text: str) -> list[str]:
    issues: list[str] = []
    if not text.strip():
        return ["dogfood ledger is empty"]
    records = parse_records(text)
    if not records:
        return ["dogfood ledger has no parseable JSONL records"]
    by_kind: dict[str, list[dict]] = {k: [] for k in REQUIRED_KINDS}
    for rec in records:
        kind = str(rec.get("kind") or "").strip().lower()
        if kind in by_kind:
            by_kind[kind].append(rec)
    for kind in REQUIRED_KINDS:
        rows = by_kind[kind]
        if not rows:
            issues.append(f"dogfood ledger missing kind {kind}")
            continue
        if not any(len(str(r.get("body") or "").strip()) >= MIN_BODY for r in rows):
            issues.append(f"{kind} records have stub bodies (<{MIN_BODY} chars)")
        if not any(str(r.get("title") or "").strip() for r in rows):
            issues.append(f"{kind} records missing titles")
    return issues


def check_live() -> list[str]:
    if not LIVE_LEDGER.is_file():
        return [f"missing {LIVE_LEDGER.relative_to(REPO_ROOT)}"]
    return issues_for_dogfood_ledger(LIVE_LEDGER.read_text(encoding="utf-8"))


def main() -> int:
    issues = check_live()
    if issues:
        for item in issues:
            print(f"FAIL: {item}", file=sys.stderr)
        return 1
    print(f"PASS: dogfood ledger {LIVE_LEDGER.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
