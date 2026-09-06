"""Structured process metrics on ledger records (FEAT-015).

Capture flags (--readiness, --review-result, --rework, --context-files,
--validate-cycles, --review-cycles) live on ``LessonRecord.metrics``.
Queries MUST read these fields, never ``session.body`` prose.

DOC-001 constructs that use capture metrics:

- C-COMPLY  → readiness, review_result
- C-CONTEXT → context_files
- C-REWORK  → rework, validate_cycles, review_cycles
- C-MEMORY  → same fields as C-REWORK (follow-on rework)

C-DRIFT and C-PORT are not capture-flag constructs.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, fields
from typing import Any, Iterable

REVIEW_RESULTS = ("pass", "fail", "mixed", "blocked")

# Ledger schema bump when a record carries a metrics object.
SCHEMA_WITH_METRICS = 2

CAPTURE_CONSTRUCTS = ("C-COMPLY", "C-CONTEXT", "C-REWORK", "C-MEMORY")
NON_CAPTURE_CONSTRUCTS = ("C-DRIFT", "C-PORT")

CONSTRUCT_FIELDS: dict[str, tuple[str, ...]] = {
    "C-COMPLY": ("readiness", "review_result"),
    "C-CONTEXT": ("context_files",),
    "C-REWORK": ("rework", "validate_cycles", "review_cycles"),
    "C-MEMORY": ("rework", "validate_cycles", "review_cycles"),
}

CONSTRUCT_QUERIES: dict[str, str] = {
    "C-COMPLY": "readiness_and_review_result",
    "C-CONTEXT": "context_files_by_phase",
    "C-REWORK": "rework_by_phase",
    "C-MEMORY": "rework_on_follow_on",
}

METRIC_FIELD_NAMES = (
    "readiness",
    "review_result",
    "rework",
    "context_files",
    "validate_cycles",
    "review_cycles",
)

INT_FIELDS = frozenset({"rework", "context_files", "validate_cycles", "review_cycles"})


def parse_nonneg_int(value: Any, *, name: str) -> int:
    if isinstance(value, bool) or value is None or value == "":
        raise ValueError(f"{name} must be a non-negative integer")
    try:
        n = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a non-negative integer") from exc
    if n < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return n


def parse_review_result(value: str) -> str:
    token = (value or "").strip().lower()
    if token not in REVIEW_RESULTS:
        raise ValueError(
            f"review_result must be one of {'|'.join(REVIEW_RESULTS)}"
        )
    return token


@dataclass
class ProcessMetrics:
    readiness: str | None = None
    review_result: str | None = None
    rework: int | None = None
    context_files: int | None = None
    validate_cycles: int | None = None
    review_cycles: int | None = None

    def is_empty(self) -> bool:
        return all(getattr(self, f.name) is None for f in fields(self))

    def has_any(self, names: Iterable[str]) -> bool:
        return any(getattr(self, name, None) is not None for name in names)

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for name in METRIC_FIELD_NAMES:
            val = getattr(self, name)
            if val is not None:
                out[name] = val
        return out

    @classmethod
    def from_json(cls, data: Any) -> "ProcessMetrics":
        if not data or not isinstance(data, dict):
            return cls()
        kwargs: dict[str, Any] = {}
        readiness = data.get("readiness")
        if readiness not in (None, ""):
            kwargs["readiness"] = str(readiness)
        raw_rr = data.get("review_result")
        if raw_rr not in (None, ""):
            try:
                kwargs["review_result"] = parse_review_result(str(raw_rr))
            except ValueError:
                pass
        for name in INT_FIELDS:
            raw = data.get(name)
            if raw in (None, ""):
                continue
            try:
                kwargs[name] = parse_nonneg_int(raw, name=name)
            except ValueError:
                continue
        return cls(**kwargs)

    @classmethod
    def from_capture(
        cls,
        *,
        readiness: str | None = None,
        review_result: str | None = None,
        rework: Any = None,
        context_files: Any = None,
        validate_cycles: Any = None,
        review_cycles: Any = None,
        strict: bool = True,
    ) -> "ProcessMetrics":
        """Build from CLI / capture flags. ``strict`` raises on bad values."""
        kwargs: dict[str, Any] = {}
        if readiness not in (None, ""):
            kwargs["readiness"] = str(readiness).strip()
        if review_result not in (None, ""):
            try:
                kwargs["review_result"] = parse_review_result(str(review_result))
            except ValueError:
                if strict:
                    raise
        ints = {
            "rework": rework,
            "context_files": context_files,
            "validate_cycles": validate_cycles,
            "review_cycles": review_cycles,
        }
        for name, raw in ints.items():
            if raw in (None, ""):
                continue
            try:
                kwargs[name] = parse_nonneg_int(raw, name=name)
            except ValueError:
                if strict:
                    raise
        return cls(**kwargs)


def query_metrics(
    records: Iterable[Any],
    *,
    construct: str = "",
    work_id: str = "",
    phase: str = "",
) -> dict[str, Any]:
    """Aggregate structured metrics. Never reads record.body."""
    construct = (construct or "").strip().upper()
    if not construct:
        return {
            "source": "record.metrics",
            "constructs": {
                name: query_metrics(
                    records, construct=name, work_id=work_id, phase=phase
                )
                for name in CAPTURE_CONSTRUCTS
            },
        }
    if construct in NON_CAPTURE_CONSTRUCTS:
        return {
            "construct": construct,
            "query": None,
            "source": "not_capture_metrics",
            "note": (
                f"{construct} is not a capture-flag construct. "
                "C-DRIFT uses operation/hunk mapping (FEAT-016); "
                "C-PORT uses assistant comparison (TEST-002)."
            ),
            "rows": [],
            "by_phase": {},
        }
    if construct not in CONSTRUCT_FIELDS:
        known = ", ".join(CAPTURE_CONSTRUCTS + NON_CAPTURE_CONSTRUCTS)
        raise ValueError(f"unknown construct {construct!r}; expected one of {known}")

    field_names = CONSTRUCT_FIELDS[construct]
    rows: list[dict[str, Any]] = []
    for rec in records:
        if work_id and getattr(rec, "work_id", "") != work_id:
            continue
        if phase and getattr(rec, "phase", "") != phase:
            continue
        metrics = getattr(rec, "metrics", None)
        if metrics is None or not metrics.has_any(field_names):
            continue
        row: dict[str, Any] = {
            "id": getattr(rec, "id", ""),
            "work_id": getattr(rec, "work_id", ""),
            "phase": getattr(rec, "phase", ""),
            "kind": getattr(rec, "kind", ""),
        }
        for name in field_names:
            row[name] = getattr(metrics, name, None)
        rows.append(row)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["phase"] or "(none)"].append(row)
    by_phase: dict[str, dict[str, Any]] = {}
    for ph, group in grouped.items():
        entry: dict[str, Any] = {"n": len(group)}
        for name in field_names:
            nums = [r[name] for r in group if isinstance(r[name], int)]
            if nums:
                entry[f"{name}_sum"] = sum(nums)
                entry[f"{name}_mean"] = sum(nums) / len(nums)
            labels = [r[name] for r in group if isinstance(r[name], str) and r[name]]
            if labels:
                counts: dict[str, int] = {}
                for label in labels:
                    counts[label] = counts.get(label, 0) + 1
                entry[f"{name}_counts"] = counts
        by_phase[ph] = entry

    return {
        "construct": construct,
        "query": CONSTRUCT_QUERIES[construct],
        "source": "record.metrics",
        "rows": rows,
        "by_phase": by_phase,
    }
