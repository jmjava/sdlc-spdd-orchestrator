#!/usr/bin/env python3
"""Classify environment.json agentCanUpdateSnapshot per Cursor schema.

Cursor schema (https://cursor.com/schemas/environment.schema.json):

    Whether the agent can update the snapshot. Defaults to true for
    snapshot-based and default-base environments; always false when the
    base is `build` or `image`.

Public Cloud Agent Setup and Builds docs do not say this flag enables
Builds. Omitted or false is valid schema; do not treat either as a
product-switch failure.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

SCHEMA_MEANING = "Whether the agent can update the snapshot."


class SnapshotFlagError(ValueError):
    """Present key is not a JSON boolean."""


def classify_flag(data: dict[str, Any]) -> str:
    if "agentCanUpdateSnapshot" not in data:
        return "omitted"
    value = data["agentCanUpdateSnapshot"]
    if not isinstance(value, bool):
        raise SnapshotFlagError(
            f"agentCanUpdateSnapshot must be a JSON boolean; got {type(value).__name__}"
        )
    return "true" if value else "false"


def schema_effective_can_update(data: dict[str, Any]) -> bool:
    """Apply published schema defaults. Not a Builds on/off switch."""
    if data.get("build") or data.get("image"):
        return False
    status = classify_flag(data)
    if status == "omitted":
        return True
    return status == "true"


def _load(path: str) -> dict[str, Any]:
    data = json.loads(open(path, encoding="utf-8").read())
    if not isinstance(data, dict):
        raise SnapshotFlagError("environment.json must be an object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=SCHEMA_MEANING)
    parser.add_argument("path", help="path to environment.json")
    args = parser.parse_args(argv)
    try:
        data = _load(args.path)
        status = classify_flag(data)
    except (OSError, json.JSONDecodeError, SnapshotFlagError) as exc:
        print(f"error={exc}", file=sys.stderr)
        return 1
    print(f"status={status}")
    print(f"meaning={SCHEMA_MEANING}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
