"""Single structured lesson ledger — the committed system of record (storage v3).

One JSONL record per accepted fact in ``spdd/memory/lessons.jsonl``.
Day-to-day captures land in the gitignored stage
(``.sdlc/staged/lessons.jsonl``); ``accept`` promotes the keepers into the
committed ledger in one batch. SQLite and Guide are pure projections of
these records — never independently written.

Record shape (IDs stay Guide-compatible ``{kind}:{workId}:{area}:{source}``).
``workId`` may be ``(none)`` when the day had no Work ID — unstructured
capture is ``kind + area + body``, not an invented ``FEAT-ADHOC-*``.

    {"id": "pitfall:FEAT-013-x:engine:retro", "kind": "pitfall",
     "work_id": "FEAT-013-x", "area": "engine", "phase": "retro",
     "ts": "2026-08-08T12:00:00Z", "title": "one-line summary",
     "body": "detail", "source": "retro", "keywords": ["sqlite"],
     "commit": "abc1234", "schema": 1}
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .project import Project

# Committed kinds — the pared-down, highest-value set.
LEDGER_KINDS = ("decision", "pitfall", "pattern", "session", "analysis")

SCHEMA = 1

UNSCOPED_WORK_ID = "(none)"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def lesson_id(kind: str, work_id: str, area: str, source: str) -> str:
    work_part = (work_id or "").strip() or UNSCOPED_WORK_ID
    area_part = (area or "").strip() or "(none)"
    src = (source or "").strip() or "capture"
    return f"{kind}:{work_part}:{area_part}:{src}"


@dataclass
class LessonRecord:
    id: str
    kind: str
    work_id: str
    area: str = ""
    phase: str = ""
    ts: str = ""
    title: str = ""
    body: str = ""
    source: str = "capture"
    keywords: list[str] = field(default_factory=list)
    commit: str = ""
    schema: int = SCHEMA

    def __post_init__(self) -> None:
        self.kind = (self.kind or "").strip().lower()
        self.work_id = (self.work_id or "").strip()
        self.area = (self.area or "").strip()
        if not self.ts:
            self.ts = _utc_now()
        if not self.id:
            self.id = lesson_id(self.kind, self.work_id, self.area, self.source)
        if not self.title and self.body:
            self.title = self.body.strip().splitlines()[0][:120]

    def validate(self) -> None:
        if self.kind not in LEDGER_KINDS:
            raise ValueError(f"kind must be one of {'|'.join(LEDGER_KINDS)}")
        if not self.work_id and not self.area:
            raise ValueError("work_id or area is required")
        if not (self.body or self.title):
            raise ValueError("body (or title) is required")

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "work_id": self.work_id,
            "area": self.area,
            "phase": self.phase,
            "ts": self.ts,
            "title": self.title,
            "body": self.body,
            "source": self.source,
            "keywords": list(self.keywords),
            "commit": self.commit,
            "schema": self.schema,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "LessonRecord":
        return cls(
            id=str(data.get("id") or ""),
            kind=str(data.get("kind") or ""),
            work_id=str(data.get("work_id") or ""),
            area=str(data.get("area") or ""),
            phase=str(data.get("phase") or ""),
            ts=str(data.get("ts") or ""),
            title=str(data.get("title") or ""),
            body=str(data.get("body") or ""),
            source=str(data.get("source") or "capture"),
            keywords=[str(k) for k in (data.get("keywords") or [])],
            commit=str(data.get("commit") or ""),
            schema=int(data.get("schema") or SCHEMA),
        )


def _read_jsonl(path: Path) -> list[LessonRecord]:
    if not path.is_file():
        return []
    out: list[LessonRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(LessonRecord.from_json(json.loads(line)))
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
    return out


def _write_jsonl(path: Path, records: Iterable[LessonRecord]) -> None:
    """Atomic rewrite (used by accept/discard, never by hot append)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec.to_json(), ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class LessonsLedger:
    """Read/append the committed ledger + gitignored stage."""

    def __init__(self, project: Project | None = None) -> None:
        self.project = project or Project.resolve()
        self.path = self.project.ledger_path
        self.stage_path = self.project.staged_ledger_path

    # --- write ---

    def stage(self, record: LessonRecord) -> LessonRecord:
        """Capture-time write: gitignored stage only (git stays quiet)."""
        record.validate()
        if not record.commit:
            record.commit = self._git_head()
        self.stage_path.parent.mkdir(parents=True, exist_ok=True)
        with self.stage_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_json(), ensure_ascii=False) + "\n")
        return record

    def append_accepted(self, record: LessonRecord) -> LessonRecord:
        """Direct accept: append to the committed ledger (dedupe by id, last wins)."""
        record.validate()
        if not record.commit:
            record.commit = self._git_head()
        existing = [r for r in _read_jsonl(self.path) if r.id != record.id]
        existing.append(record)
        _write_jsonl(self.path, existing)
        return record

    def accept(
        self,
        *,
        work_id: str = "",
        ids: Iterable[str] | None = None,
        discard_rest: bool = False,
    ) -> dict[str, Any]:
        """Promote staged records into the committed ledger in one batch.

        - ``work_id`` limits promotion to one Work ID (default: all staged).
        - ``ids`` limits promotion to specific record ids.
        - ``discard_rest`` drops non-promoted staged records for the same
          scope instead of leaving them staged.
        """
        staged = _read_jsonl(self.stage_path)
        want_ids = set(ids) if ids else None

        def in_scope(rec: LessonRecord) -> bool:
            if work_id and rec.work_id != work_id:
                return False
            if want_ids is not None and rec.id not in want_ids:
                return False
            return True

        promote = [r for r in staged if in_scope(r)]
        # Dedupe within the batch: last record per id wins.
        by_id: dict[str, LessonRecord] = {}
        for rec in promote:
            by_id[rec.id] = rec
        promote = list(by_id.values())

        accepted = {r.id: r for r in _read_jsonl(self.path)}
        for rec in promote:
            accepted[rec.id] = rec
        if promote:
            _write_jsonl(self.path, accepted.values())

        if discard_rest:
            remaining = [
                r
                for r in staged
                if not (work_id == "" or r.work_id == work_id)
            ]
        else:
            promoted_ids = {r.id for r in promote}
            remaining = [r for r in staged if r.id not in promoted_ids]
        _write_jsonl(self.stage_path, remaining)

        return {
            "accepted": [r.id for r in promote],
            "accepted_count": len(promote),
            "staged_remaining": len(remaining),
            "ledger": self._rel(self.path),
        }

    def discard_staged(self, *, work_id: str = "") -> int:
        staged = _read_jsonl(self.stage_path)
        keep = [r for r in staged if work_id and r.work_id != work_id]
        dropped = len(staged) - len(keep)
        _write_jsonl(self.stage_path, keep)
        return dropped

    # --- read ---

    def records(
        self,
        *,
        work_id: str = "",
        area: str = "",
        kind: str = "",
        keyword: str = "",
        include_staged: bool = True,
    ) -> list[LessonRecord]:
        rows: dict[str, LessonRecord] = {}
        for rec in _read_jsonl(self.path):
            rows[rec.id] = rec
        if include_staged:
            for rec in _read_jsonl(self.stage_path):
                rows[rec.id] = rec
        out: list[LessonRecord] = []
        kw = keyword.strip().lower()
        for rec in rows.values():
            if work_id and rec.work_id != work_id:
                continue
            if area and rec.area != area:
                continue
            if kind and rec.kind != kind:
                continue
            if kw and kw not in [k.lower() for k in rec.keywords]:
                continue
            out.append(rec)
        out.sort(key=lambda r: (r.ts, r.id), reverse=True)
        return out

    def staged_ids(self) -> set[str]:
        return {r.id for r in _read_jsonl(self.stage_path)}

    def get(self, record_id: str) -> LessonRecord | None:
        for rec in self.records():
            if rec.id == record_id:
                return rec
        return None

    def accepted_ids(self) -> set[str]:
        return {r.id for r in _read_jsonl(self.path)}

    def digest(
        self,
        *,
        areas: Iterable[str] = (),
        keywords: Iterable[str] = (),
        work_id: str = "",
        limit: int = 8,
    ) -> dict[str, Any]:
        """Bounded 'Related Past Work' summary for session briefs.

        Counts per kind/area plus top-N one-line titles with ids — never
        full bodies. Matches on area, keyword, or same Work ID.
        """
        area_set = {a.strip() for a in areas if a and a.strip()}
        kw_set = {k.strip().lower() for k in keywords if k and k.strip()}
        matches: list[LessonRecord] = []
        for rec in self.records():
            hit = False
            if work_id and rec.work_id == work_id:
                hit = True
            if rec.area and rec.area in area_set:
                hit = True
            if kw_set and kw_set.intersection(k.lower() for k in rec.keywords):
                hit = True
            if hit:
                matches.append(rec)
        counts: dict[str, int] = {}
        area_counts: dict[str, int] = {}
        for rec in matches:
            counts[rec.kind] = counts.get(rec.kind, 0) + 1
            if rec.area:
                area_counts[rec.area] = area_counts.get(rec.area, 0) + 1
        top = [
            {"id": r.id, "kind": r.kind, "work_id": r.work_id, "title": r.title}
            for r in matches[: max(1, limit)]
        ]
        return {
            "total": len(matches),
            "by_kind": counts,
            "by_area": area_counts,
            "top": top,
        }

    # --- helpers ---

    def _git_head(self) -> str:
        try:
            return subprocess.check_output(
                ["git", "-C", str(self.project.root), "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""

    def _rel(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.project.root.resolve()))
        except ValueError:
            return str(path)
