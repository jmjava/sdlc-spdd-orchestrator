"""One-shot storage v3 migration: legacy agent-context → ledger + export."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import context_model as cm
from .db import LocalIndex
from .lessons_ledger import LEDGER_KINDS, LessonRecord, LessonsLedger, lesson_id
from .persistence import BACKEND_SQLITE, enabled as backend_enabled
from .project import Project
from .registry import RegistryRow, TeamRegistry


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


EXPORT_PATHS = (
    Path("agent-context/memory"),
    Path("agent-context/sessions"),
    Path("agent-context/features"),
    Path("agent-context/work-registry.tsv"),
    Path("spdd/memory/lessons"),
    Path("spdd/memory/context-index.md"),
    Path("spdd/memory/pointers.jsonl"),
    Path("spdd/memory/entries"),
    Path("spdd/memory/sessions"),
    Path("spdd/memory/domain-index.md"),
)

LESSON_BODY_FILES: tuple[tuple[str, Path], ...] = (
    ("decision", Path("agent-context/memory/architecture-decisions.md")),
    ("pitfall", Path("agent-context/memory/known-pitfalls.md")),
    ("pattern", Path("agent-context/memory/reusable-patterns.md")),
    ("decision", Path("spdd/memory/lessons/decisions.md")),
    ("pitfall", Path("spdd/memory/lessons/pitfalls.md")),
    ("pattern", Path("spdd/memory/lessons/patterns.md")),
)


@dataclass
class StorageMigration:
    project: Project

    def detect(self) -> dict[str, Any]:
        home = self.project.home
        root = self.project.root
        marker = self.project.sdlc_dir / "storage-v3-migrated"
        legacy: list[str] = []
        for rel in EXPORT_PATHS:
            p = home / rel if (home / rel).exists() else root / rel
            if p.exists():
                legacy.append(str(rel))
        return {
            "migrated": marker.is_file(),
            "marker": str(marker) if marker.is_file() else "",
            "legacy_present": legacy,
            "ledger_exists": self.project.ledger_path.is_file(),
            "registry_jsonl_exists": self.project.registry_jsonl_path.is_file(),
            "needs_migration": bool(legacy) and not marker.is_file(),
        }

    def run(self, *, dry_run: bool = False) -> dict[str, Any]:
        counts: dict[str, int] = {
            "context_index": 0,
            "lesson_files": 0,
            "session_history": 0,
            "domain_index": 0,
            "prompt_log": 0,
            "registry_tsv": 0,
        }
        exported: list[str] = []
        home = self.project.home
        root = self.project.root
        ledger = LessonsLedger(self.project)
        existing_ids = ledger.accepted_ids() | ledger.staged_ids()

        def _append(record: LessonRecord) -> None:
            if record.id in existing_ids:
                return
            record.validate()
            if not dry_run:
                ledger.append_accepted(record)
            existing_ids.add(record.id)
            return None

        # a) context-index.md
        for rel in (
            Path("agent-context/memory/context-index.md"),
            Path("spdd/memory/context-index.md"),
        ):
            path = home / rel if (home / rel).is_file() else root / rel
            if not path.is_file():
                continue
            try:
                rows = cm.parse_md_table(path.read_text(encoding="utf-8"))
            except OSError:
                continue
            for row in rows:
                kind = (row.get("kind") or "").strip().lower()
                if kind in {"session", "metric"} or not kind:
                    continue
                area = (row.get("area") or "").strip()
                wid = (row.get("work id") or row.get("work_id") or "_memory").strip()
                phase = (row.get("phase") or "").strip()
                ts = (row.get("timestamp") or "").strip()
                source = (row.get("source") or "context-index").strip()
                entry = (row.get("entry") or "").strip()
                if kind in {"decision", "pitfall", "pattern", "analysis"}:
                    rid = lesson_id(kind, wid, area, source)
                    _append(
                        LessonRecord(
                            id=rid,
                            kind=kind,
                            work_id=wid,
                            area=area,
                            phase=phase,
                            ts=ts,
                            title=entry[:120],
                            body=entry,
                            source=source,
                        )
                    )
                    counts["context_index"] += 1

        # b) lesson body files
        for kind, rel in LESSON_BODY_FILES:
            path = home / rel if (home / rel).is_file() else root / rel
            if not path.is_file():
                continue
            try:
                blocks = cm.extract_lesson_blocks(path.read_text(encoding="utf-8"))
            except OSError:
                continue
            for block in blocks:
                wid = (block.get("work_id") or "_memory").strip()
                source = str(rel).replace("\\", "/")
                rid = (block.get("legacy_id") or "").strip() or lesson_id(
                    kind, wid, block.get("area") or "", source
                )
                _append(
                    LessonRecord(
                        id=rid,
                        kind=kind,
                        work_id=wid,
                        area=block.get("area") or "",
                        ts=block.get("ts") or "",
                        title=block.get("title") or "",
                        body=block.get("body") or "",
                        source=source,
                    )
                )
                counts["lesson_files"] += 1

        # c) session-history.md
        for rel in (Path("agent-context/memory/session-history.md"),):
            path = home / rel if (home / rel).is_file() else root / rel
            if not path.is_file():
                continue
            try:
                sessions = cm.extract_session_history(path.read_text(encoding="utf-8"))
            except OSError:
                continue
            for sess in sessions:
                wid = (sess.get("work_id") or "_memory").strip()
                source = "session-history"
                rid = lesson_id("session", wid, "", source + ":" + (sess.get("ts") or ""))
                _append(
                    LessonRecord(
                        id=rid,
                        kind="session",
                        work_id=wid,
                        phase=sess.get("phase") or "",
                        ts=sess.get("ts") or "",
                        title=sess.get("summary") or "",
                        body=sess.get("body") or "",
                        source=source,
                    )
                )
                counts["session_history"] += 1

        # d) domain-index.md — merge keywords into analysis records
        analysis_by_key: dict[tuple[str, str], LessonRecord] = {}
        for rel in (
            Path("agent-context/memory/domain-index.md"),
            Path("spdd/memory/domain-index.md"),
        ):
            path = home / rel if (home / rel).is_file() else root / rel
            if not path.is_file():
                continue
            try:
                rows = cm.parse_md_table(path.read_text(encoding="utf-8"))
            except OSError:
                continue
            for row in rows:
                keyword = (row.get("keyword") or "").strip().lower()
                if not keyword:
                    continue
                area = (row.get("area") or "").strip()
                wid = (row.get("work id") or row.get("work_id") or "_memory").strip()
                key = (wid, area)
                if key not in analysis_by_key:
                    analysis_by_key[key] = LessonRecord(
                        id=lesson_id("analysis", wid, area, "domain-index"),
                        kind="analysis",
                        work_id=wid,
                        area=area,
                        source="domain-index",
                        title=f"Domain keywords for {area or wid}",
                        body="",
                        keywords=[],
                    )
                if keyword not in analysis_by_key[key].keywords:
                    analysis_by_key[key].keywords.append(keyword)
                counts["domain_index"] += 1
        for rec in analysis_by_key.values():
            _append(rec)

        # e) prompt-optimization-log.md
        for rel in (Path("agent-context/memory/prompt-optimization-log.md"),):
            path = home / rel if (home / rel).is_file() else root / rel
            if not path.is_file():
                continue
            try:
                entries = cm.extract_prompt_entries(path.read_text(encoding="utf-8"))
            except OSError:
                continue
            for ent in entries:
                title = ent.get("title") or "prompt"
                rid = lesson_id("decision", "_memory", "", "prompt-log:" + title[:40])
                _append(
                    LessonRecord(
                        id=rid,
                        kind="decision",
                        work_id="_memory",
                        title=title,
                        body=ent.get("body") or "",
                        source="prompt-log",
                    )
                )
                counts["prompt_log"] += 1

        # f) work-registry.tsv → registry.jsonl events
        tsv = self.project.home / "agent-context" / "work-registry.tsv"
        if tsv.is_file() and not self.project.registry_jsonl_path.is_file():
            reg = TeamRegistry(self.project)
            if not dry_run:
                reg.ensure()
            for line in tsv.read_text(encoding="utf-8").splitlines():
                if not line or line.startswith("#") or line.startswith("work_id"):
                    continue
                parts = line.split("\t")
                while len(parts) < 7:
                    parts.append("")
                row = RegistryRow(
                    work_id=parts[0],
                    status=parts[1],
                    phase=parts[2],
                    operation=parts[3],
                    owner=parts[4],
                    updated=parts[5] or _utc_now(),
                    note=parts[6],
                )
                if not dry_run:
                    reg.upsert(row, event="migrate")
                counts["registry_tsv"] += 1

        # Export legacy trees
        stamp = _utc_stamp()
        export_root = self.project.sdlc_dir / "legacy-export" / stamp
        for rel in EXPORT_PATHS:
            src = home / rel if (home / rel).exists() else root / rel
            if not src.exists():
                continue
            dest = export_root / rel
            if dry_run:
                exported.append(str(rel))
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(src), str(dest))
            else:
                shutil.move(str(src), str(dest))
            exported.append(str(rel))

        sqlite_rebuilt = False
        if not dry_run and backend_enabled(self.project, BACKEND_SQLITE):
            try:
                LocalIndex(self.project).rebuild()
                sqlite_rebuilt = True
            except Exception:
                pass

        marker = self.project.sdlc_dir / "storage-v3-migrated"
        if not dry_run:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(stamp + "\n", encoding="utf-8")

        return {
            "ok": True,
            "dry_run": dry_run,
            "stamp": stamp,
            "records_migrated": counts,
            "exported": exported,
            "export_dir": str(export_root) if exported else "",
            "sqlite_rebuilt": sqlite_rebuilt,
            "marker": str(marker),
        }
