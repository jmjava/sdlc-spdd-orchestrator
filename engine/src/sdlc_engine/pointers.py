"""Lean git pointer ledger (path 1) — append-only JSONL under spdd/memory/."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .project import Project

POINTER_REL = Path("spdd/memory/pointers.jsonl")
STAGING_NAME = "pointers-staging.jsonl"

_SAFE = re.compile(r"[^a-zA-Z0-9._-]+")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug(text: str, max_len: int = 48) -> str:
    s = _SAFE.sub("-", (text or "").strip())[:max_len].strip("-")
    return s or "x"


@dataclass
class PointerRecord:
    id: str
    kind: str
    work_id: str
    intent: str = ""
    subtype: str = ""
    commit_sha: str = ""
    paths: list[str] = field(default_factory=list)
    links: dict[str, Any] = field(default_factory=dict)
    ts: str = ""
    schema: int = 1

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "schema": self.schema,
            "ts": self.ts or _utc_now(),
            "work_id": self.work_id,
            "kind": self.kind,
            "subtype": self.subtype,
            "intent": self.intent,
            "commit_sha": self.commit_sha,
            "paths": list(self.paths),
            "links": dict(self.links),
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "PointerRecord":
        return cls(
            id=str(data.get("id") or ""),
            kind=str(data.get("kind") or ""),
            work_id=str(data.get("work_id") or ""),
            intent=str(data.get("intent") or ""),
            subtype=str(data.get("subtype") or ""),
            commit_sha=str(data.get("commit_sha") or ""),
            paths=list(data.get("paths") or []),
            links=dict(data.get("links") or {}),
            ts=str(data.get("ts") or ""),
            schema=int(data.get("schema") or 1),
        )


class PointerLedger:
    """Read/append committed pointers.jsonl and optional staging file."""

    def __init__(self, project: Project | None = None) -> None:
        self.project = project or Project.resolve()
        self.path = self.project.root / POINTER_REL
        self.staging_path = self.project.sdlc_dir / STAGING_NAME

    def ensure(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.is_file():
            self.path.write_text("", encoding="utf-8")
        self.project.ensure_runtime_dirs()

    def list(
        self,
        *,
        work_id: str = "",
        kind: str = "",
        area: str = "",
        include_staging: bool = False,
    ) -> list[PointerRecord]:
        rows: list[PointerRecord] = []
        for path in self._iter_paths(include_staging=include_staging):
            if not path.is_file():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = PointerRecord.from_json(json.loads(line))
                except json.JSONDecodeError:
                    continue
                if work_id and rec.work_id != work_id:
                    continue
                if kind and rec.kind != kind:
                    continue
                if area:
                    areas = rec.links.get("areas") or []
                    if area not in areas:
                        continue
                rows.append(rec)
        return rows

    def append(self, record: PointerRecord, *, staging: bool = False) -> PointerRecord:
        self.ensure()
        if not record.ts:
            record.ts = _utc_now()
        if not record.id:
            record.id = (
                f"ptr_{record.ts.replace(':', '').replace('-', '')}_"
                f"{_slug(record.work_id)}_{_slug(record.kind)}"
            )
        target = self.staging_path if staging else self.path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_json(), ensure_ascii=False) + "\n")
        return record

    def _iter_paths(self, *, include_staging: bool) -> Iterable[Path]:
        yield self.path
        if include_staging:
            yield self.staging_path
