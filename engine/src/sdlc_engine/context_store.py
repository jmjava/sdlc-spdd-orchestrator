"""Triple-path context store: lean git + SQLite relational + Guide DICE.

Persist fans out to all three (soft-fail on SQLite/Guide). Retrieve assembles
what is available. Tests prove entry into each mechanism.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .context_model import CONTEXT_KINDS
from .db import LocalIndex
from .persistence import (
    BACKEND_GIT,
    BACKEND_GUIDE,
    BACKEND_SQLITE,
    enabled as backend_enabled,
    load_config as load_persistence_config,
)
from .pointers import PointerLedger, PointerRecord
from .project import Project

LESSON_FILES = {
    "decision": Path("spdd/memory/lessons/decisions.md"),
    "pitfall": Path("spdd/memory/lessons/pitfalls.md"),
    "pattern": Path("spdd/memory/lessons/patterns.md"),
}
CONTEXT_INDEX = Path("spdd/memory/context-index.md")
LEGACY_CONTEXT_INDEX = Path("agent-context/memory/context-index.md")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _lesson_id(kind: str, work_id: str, area: str, source: str) -> str:
    area_part = area or "(none)"
    src = source or "capture"
    return f"{kind}:{work_id}:{area_part}:{src}"


@dataclass
class PersistResult:
    ok: bool
    git: dict[str, Any] = field(default_factory=dict)
    sqlite: dict[str, Any] = field(default_factory=dict)
    guide: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    partial: bool = False
    backends: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "partial": self.partial,
            "backends": list(self.backends),
            "git": self.git,
            "sqlite": self.sqlite,
            "guide": self.guide,
            "errors": list(self.errors),
        }


class ContextStore:
    """Fan-out persist / assemble retrieve across three backends."""

    def __init__(
        self,
        project: Project | None = None,
        *,
        guide_base_url: str | None = None,
        guide_timeout: float = 30.0,
    ) -> None:
        self.project = project or Project.resolve()
        self.index = LocalIndex(self.project)
        self.pointers = PointerLedger(self.project)
        env_url = os.environ.get("GUIDE_BASE_URL", "").strip()
        port = os.environ.get("GUIDE_PORT", "21337").strip() or "21337"
        persist_cfg = load_persistence_config(self.project)
        cfg_url = str(persist_cfg.get("guide_base_url") or "").strip()
        self.guide_base_url = (
            guide_base_url or env_url or cfg_url or f"http://localhost:{port}"
        ).rstrip("/")
        self.guide_timeout = guide_timeout

    def _backends(self) -> list[str]:
        return list(load_persistence_config(self.project).get("backends") or [])

    def _finalize_persist(self, result: PersistResult) -> PersistResult:
        """ok = required git path succeeded; partial = soft-fail secondaries."""
        result.backends = self._backends()
        result.ok = bool(result.git.get("ok"))
        result.partial = bool(result.errors)
        return result

    # --- persist ---

    def persist_lesson(
        self,
        *,
        kind: str,
        work_id: str,
        body: str,
        area: str = "",
        source: str = "capture",
        phase: str = "sync",
        project_guide: bool = True,
    ) -> PersistResult:
        """Write one accepted lesson into git stay-set, SQLite, and Guide."""
        kind_n = (kind or "").strip().lower()
        if kind_n not in LESSON_FILES:
            raise ValueError("kind must be decision|pitfall|pattern")
        wid = (work_id or "").strip()
        if not wid:
            raise ValueError("work_id is required")
        text = (body or "").strip()
        if not text:
            raise ValueError("body is required")

        result = PersistResult(ok=True)
        lid = _lesson_id(kind_n, wid, area, source)
        ts = _utc_now()
        want_sqlite = backend_enabled(self.project, BACKEND_SQLITE)
        want_guide = project_guide and backend_enabled(self.project, BACKEND_GUIDE)

        # Path 1: lean git (always required; git-pointers cannot be disabled)
        try:
            git_meta = self._persist_lesson_git(
                kind=kind_n,
                work_id=wid,
                body=text,
                area=area,
                source=source,
                phase=phase,
                lesson_id=lid,
                ts=ts,
            )
            result.git = {"ok": True, **git_meta}
        except Exception as exc:  # noqa: BLE001 - soft reporting; git is required
            result.ok = False
            result.git = {"ok": False, "error": str(exc)}
            result.errors.append(f"git: {exc}")
            return self._finalize_persist(result)

        # Path 2: SQLite relational
        if want_sqlite:
            try:
                self.index.upsert_lesson(
                    lesson_id=lid,
                    kind=kind_n,
                    work_id=wid,
                    area=area,
                    body=text,
                    source=source,
                    ts=ts,
                )
                self.index.upsert_pointer_row(
                    pointer_id=git_meta["pointer_id"],
                    kind="lesson",
                    work_id=wid,
                    intent=text[:200],
                    payload={"lesson_id": lid, "area": area, "subtype": kind_n},
                    ts=ts,
                )
                graph = self.index.graph_for_work(wid)
                result.sqlite = {
                    "ok": True,
                    "lesson_id": lid,
                    "lessons_for_work": len(graph.get("lessons") or []),
                    "requirements": len(graph.get("requirements") or []),
                    "canvases": len(graph.get("canvases") or []),
                    "areas": len(graph.get("areas") or []),
                    "edges": len(graph.get("edges") or []),
                    "schema": "4",
                }
            except Exception as exc:  # noqa: BLE001
                result.sqlite = {"ok": False, "error": str(exc)}
                result.errors.append(f"sqlite: {exc}")
        else:
            result.sqlite = {"ok": False, "skipped": True}

        # Path 3: Guide DICE projection
        if want_guide:
            try:
                guide_meta = self.project_to_guide()
                result.guide = {"ok": True, **guide_meta}
            except Exception as exc:  # noqa: BLE001
                result.guide = {"ok": False, "error": str(exc)}
                result.errors.append(f"guide: {exc}")
        else:
            result.guide = {"ok": False, "skipped": True}

        return self._finalize_persist(result)

    def persist_context_entry(
        self,
        *,
        kind: str,
        work_id: str,
        body: str,
        area: str = "",
        phase: str = "",
        source: str = "capture",
        project_guide: bool = True,
    ) -> PersistResult:
        """Fan-out a non-lesson agent-context entry (progress/analysis/metric/…)."""
        kind_n = (kind or "").strip().lower()
        if kind_n not in CONTEXT_KINDS:
            raise ValueError(f"kind must be one of {sorted(CONTEXT_KINDS)}")
        if kind_n in LESSON_FILES:
            return self.persist_lesson(
                kind=kind_n,
                work_id=work_id,
                body=body,
                area=area,
                source=source,
                phase=phase or "sync",
                project_guide=project_guide,
            )
        wid = (work_id or "").strip()
        if not wid:
            raise ValueError("work_id is required")
        text = (body or "").strip()
        if not text:
            raise ValueError("body is required")

        result = PersistResult(ok=True)
        ts = _utc_now()
        want_sqlite = backend_enabled(self.project, BACKEND_SQLITE)
        want_guide = project_guide and backend_enabled(self.project, BACKEND_GUIDE)

        # Path 1: lean git (always required; git-pointers cannot be disabled)
        try:
            git_meta = self._persist_entry_git(
                kind=kind_n,
                work_id=wid,
                body=text,
                area=area,
                phase=phase,
                source=source,
                ts=ts,
            )
            result.git = {"ok": True, **git_meta}
        except Exception as exc:  # noqa: BLE001
            result.ok = False
            result.git = {"ok": False, "error": str(exc)}
            result.errors.append(f"git: {exc}")
            return self._finalize_persist(result)

        if want_sqlite:
            try:
                eid = self.index.upsert_context_entry(
                    kind=kind_n,
                    work_id=wid,
                    area=area,
                    phase=phase,
                    path=git_meta.get("path", ""),
                    title=text[:120],
                    body=text,
                    source=source,
                    ts=ts,
                )
                self.index.upsert_pointer_row(
                    pointer_id=git_meta["pointer_id"],
                    kind=kind_n,
                    work_id=wid,
                    intent=text[:200],
                    payload={"entry_id": eid, "area": area},
                    ts=ts,
                )
                graph = self.index.graph_for_work(wid)
                cov = self.index.capability_coverage()
                result.sqlite = {
                    "ok": True,
                    "entry_id": eid,
                    "context_entries": len(graph.get("context_entries") or []),
                    "requirements": len(graph.get("requirements") or []),
                    "canvases": len(graph.get("canvases") or []),
                    "coverage_complete": cov.get("complete"),
                    "schema": "4",
                }
            except Exception as exc:  # noqa: BLE001
                result.sqlite = {"ok": False, "error": str(exc)}
                result.errors.append(f"sqlite: {exc}")
        else:
            result.sqlite = {"ok": False, "skipped": True}

        if want_guide:
            try:
                guide_meta = self.project_to_guide()
                result.guide = {"ok": True, **guide_meta}
            except Exception as exc:  # noqa: BLE001
                result.guide = {"ok": False, "error": str(exc)}
                result.errors.append(f"guide: {exc}")
        else:
            result.guide = {"ok": False, "skipped": True}

        return self._finalize_persist(result)

    def _persist_entry_git(
        self,
        *,
        kind: str,
        work_id: str,
        body: str,
        area: str,
        phase: str,
        source: str,
        ts: str,
    ) -> dict[str, Any]:
        """Lean-git write for non-lesson context entries (+ dual-write index)."""
        # Stay-set ledger only — no agent-context/features mirrors (#86).
        mem_dir = self.project.root / "spdd" / "memory" / "entries"
        mem_dir.mkdir(parents=True, exist_ok=True)
        rel = Path("spdd/memory/entries") / f"{kind}.md"
        path = self.project.root / rel
        if not path.is_file():
            path.write_text(f"# {kind.title()} Entries\n\n", encoding="utf-8")
        block = (
            f"\n## {work_id} — {ts}\n\n"
            f"- Area: {area or '(none)'}\n"
            f"- Phase: {phase or '(none)'}\n"
            f"- Source: {source}\n\n"
            f"{body}\n"
        )
        with path.open("a", encoding="utf-8") as fh:
            fh.write(block)

        index_path = self.project.root / CONTEXT_INDEX
        index_path.parent.mkdir(parents=True, exist_ok=True)
        if not index_path.is_file():
            index_path.write_text(
                "# Context Index\n\n"
                "| Area | Kind | Work ID | Phase | Timestamp | Source | Entry |\n"
                "|------|------|---------|-------|-----------|--------|-------|\n",
                encoding="utf-8",
            )
        entry = body[:120].replace("|", "/")
        row = (
            f"| {area or '(none)'} | {kind} | {work_id} | {phase or ''} | "
            f"{ts} | {source} | {entry} |\n"
        )
        with index_path.open("a", encoding="utf-8") as fh:
            fh.write(row)
        legacy = self.project.root / LEGACY_CONTEXT_INDEX
        legacy.parent.mkdir(parents=True, exist_ok=True)
        if not legacy.is_file():
            legacy.write_text(index_path.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            with legacy.open("a", encoding="utf-8") as fh:
                fh.write(row)

        ptr = self.pointers.append(
            PointerRecord(
                id="",
                kind=kind,
                subtype=kind,
                work_id=work_id,
                intent=body[:200],
                paths=[rel.as_posix(), CONTEXT_INDEX.as_posix()],
                links={"areas": [area] if area else []},
                ts=ts,
            )
        )
        return {
            "path": rel.as_posix(),
            "index_path": CONTEXT_INDEX.as_posix(),
            "pointer_id": ptr.id,
        }

    def _persist_lesson_git(
        self,
        *,
        kind: str,
        work_id: str,
        body: str,
        area: str,
        source: str,
        phase: str,
        lesson_id: str,
        ts: str,
    ) -> dict[str, Any]:
        lesson_rel = LESSON_FILES[kind]
        lesson_path = self.project.root / lesson_rel
        lesson_path.parent.mkdir(parents=True, exist_ok=True)
        if not lesson_path.is_file():
            titles = {
                "decision": "Architecture Decisions",
                "pitfall": "Known Pitfalls",
                "pattern": "Reusable Patterns",
            }
            lesson_path.write_text(f"# {titles[kind]}\n\n", encoding="utf-8")

        anchor = lesson_id.replace(":", "-")
        block = (
            f"\n## {work_id} — {ts}\n\n"
            f"<!-- id: {lesson_id} -->\n"
            f"- Area: {area or '(none)'}\n"
            f"- Source: {source}\n\n"
            f"{body}\n"
        )
        with lesson_path.open("a", encoding="utf-8") as fh:
            fh.write(block)

        index_path = self.project.root / CONTEXT_INDEX
        index_path.parent.mkdir(parents=True, exist_ok=True)
        if not index_path.is_file():
            index_path.write_text(
                "# Context Index\n\n"
                "| Area | Kind | Work ID | Phase | Timestamp | Source | Entry |\n"
                "|------|------|---------|-------|-----------|--------|-------|\n",
                encoding="utf-8",
            )
        area_cell = area or "(none)"
        # Entry is projected into Guide entity name/description — include body marker for retrieval proof.
        entry = f"{body[:120].replace('|', '/')} ({lesson_rel.as_posix()}#{anchor})"
        row = (
            f"| {area_cell} | {kind} | {work_id} | {phase} | {ts} | {source} | {entry} |\n"
        )
        with index_path.open("a", encoding="utf-8") as fh:
            fh.write(row)

        # Dual-write legacy path so current Guide loaders still see lessons.
        legacy = self.project.root / LEGACY_CONTEXT_INDEX
        legacy.parent.mkdir(parents=True, exist_ok=True)
        if not legacy.is_file():
            legacy.write_text(index_path.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            with legacy.open("a", encoding="utf-8") as fh:
                fh.write(row)

        ptr = self.pointers.append(
            PointerRecord(
                id="",
                kind="lesson",
                subtype=kind,
                work_id=work_id,
                intent=body[:200],
                paths=[lesson_rel.as_posix(), CONTEXT_INDEX.as_posix()],
                links={"areas": [area] if area else [], "lesson_id": lesson_id},
                ts=ts,
            )
        )
        return {
            "lesson_id": lesson_id,
            "lesson_path": lesson_rel.as_posix(),
            "index_path": CONTEXT_INDEX.as_posix(),
            "pointer_id": ptr.id,
        }

    def project_to_guide(self) -> dict[str, Any]:
        """POST SPDD projection load against this project root."""
        url = f"{self.guide_base_url}/api/v1/data/spdd-projection/load"
        payload = json.dumps({"rootPath": str(self.project.root.resolve())}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.guide_timeout) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body) if body else {}
                return {
                    "url": url,
                    "status": getattr(resp, "status", 200),
                    "workIds": data.get("workIds"),
                    "decisions": data.get("decisions"),
                    "pitfalls": data.get("pitfalls"),
                    "patterns": data.get("patterns"),
                    "raw": data,
                }
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Guide HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Guide unreachable at {url}: {exc}") from exc

    def guide_work(self, work_id: str) -> dict[str, Any]:
        url = f"{self.guide_base_url}/api/v1/data/spdd-projection/work/{work_id}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=self.guide_timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def retrieve(self, *, work_id: str = "", area: str = "") -> dict[str, Any]:
        out: dict[str, Any] = {
            "work_id": work_id,
            "area": area,
            "git_pointers": [],
            "sqlite_lessons": [],
            "sqlite_graph": None,
            "guide": None,
            "errors": [],
        }
        try:
            out["git_pointers"] = [
                p.to_json()
                for p in self.pointers.list(work_id=work_id, area=area, kind="lesson")
            ]
        except Exception as exc:  # noqa: BLE001
            out["errors"].append(f"git: {exc}")
        try:
            if area:
                out["sqlite_lessons"] = self.index.lessons_for_area(area)
            elif work_id:
                out["sqlite_lessons"] = self.index.lessons_for_work(work_id)
            if work_id:
                out["sqlite_graph"] = self.index.graph_for_work(work_id)
        except Exception as exc:  # noqa: BLE001
            out["errors"].append(f"sqlite: {exc}")
        if work_id:
            try:
                out["guide"] = self.guide_work(work_id)
            except Exception as exc:  # noqa: BLE001
                out["errors"].append(f"guide: {exc}")
        return out
