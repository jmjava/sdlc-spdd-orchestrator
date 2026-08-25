"""Context store (storage v3): one ledger write, derived projections.

Persist writes the lesson ledger only (stage by default; accepted on
``accept``). SQLite (opt-in cache) and Guide (primary query/working store)
are pure projections of the ledger, re-derived by rebuild/reproject —
parity by construction, verified by :meth:`ContextStore.parity`.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .db import SCHEMA_VERSION, LocalIndex
from .lessons_ledger import LEDGER_KINDS, LessonRecord, LessonsLedger
from .persistence import (
    BACKEND_GUIDE,
    BACKEND_SQLITE,
    enabled as backend_enabled,
    load_config as load_persistence_config,
)
from .project import Project


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
    """Ledger-first persist; assemble retrieve from ledger + projections."""

    def __init__(
        self,
        project: Project | None = None,
        *,
        guide_base_url: str | None = None,
        guide_timeout: float = 30.0,
    ) -> None:
        self.project = project or Project.resolve()
        self.ledger = LessonsLedger(self.project)
        self.index = LocalIndex(self.project)
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

    # --- persist ---

    def persist_lesson(
        self,
        *,
        kind: str,
        work_id: str,
        body: str,
        title: str = "",
        area: str = "",
        source: str = "capture",
        phase: str = "",
        keywords: list[str] | None = None,
        accept: bool = False,
        project_guide: bool = True,
    ) -> PersistResult:
        """Write one lesson record. Staged by default; ``accept=True`` lands
        it in the committed ledger immediately (retro/sync accept points)."""
        record = LessonRecord(
            id="",
            kind=kind,
            work_id=work_id,
            area=area,
            phase=phase,
            title=title,
            body=(body or "").strip(),
            source=source,
            keywords=list(keywords or []),
        )
        result = PersistResult(ok=True)
        want_sqlite = backend_enabled(self.project, BACKEND_SQLITE)
        want_guide = project_guide and backend_enabled(self.project, BACKEND_GUIDE)

        # Path 1: the ledger (required; stage keeps git quiet until accept).
        try:
            if accept:
                self.ledger.append_accepted(record)
            else:
                self.ledger.stage(record)
            result.git = {
                "ok": True,
                "id": record.id,
                "staged": not accept,
                "path": self._rel(
                    self.ledger.path if accept else self.ledger.stage_path
                ),
            }
        except Exception as exc:  # noqa: BLE001 - ledger is the required path
            result.ok = False
            result.git = {"ok": False, "error": str(exc)}
            result.errors.append(f"git: {exc}")
            return self._finalize(result)

        # Projections (soft-fail): staged records are queryable immediately.
        if want_sqlite:
            try:
                self.index.upsert_lesson_record(record, staged=not accept)
                result.sqlite = {"ok": True, "id": record.id, "schema": SCHEMA_VERSION}
            except Exception as exc:  # noqa: BLE001
                result.sqlite = {"ok": False, "error": str(exc)}
                result.errors.append(f"sqlite: {exc}")
        else:
            result.sqlite = {"ok": False, "skipped": True}

        if want_guide:
            try:
                result.guide = {"ok": True, **self.project_to_guide()}
            except Exception as exc:  # noqa: BLE001
                result.guide = {"ok": False, "error": str(exc)}
                result.errors.append(f"guide: {exc}")
        else:
            result.guide = {"ok": False, "skipped": True}

        return self._finalize(result)

    def accept(
        self,
        *,
        work_id: str = "",
        ids: list[str] | None = None,
        discard_rest: bool = False,
        project_guide: bool = True,
    ) -> dict[str, Any]:
        """Promote staged records to the committed ledger, then reproject."""
        out = self.ledger.accept(
            work_id=work_id, ids=ids, discard_rest=discard_rest
        )
        if backend_enabled(self.project, BACKEND_SQLITE):
            try:
                self.index.rebuild()
                out["sqlite"] = {"ok": True, "rebuilt": True}
            except Exception as exc:  # noqa: BLE001
                out["sqlite"] = {"ok": False, "error": str(exc)}
        if project_guide and backend_enabled(self.project, BACKEND_GUIDE):
            try:
                out["guide"] = {"ok": True, **self.project_to_guide()}
            except Exception as exc:  # noqa: BLE001
                out["guide"] = {"ok": False, "error": str(exc)}
        return out

    def _finalize(self, result: PersistResult) -> PersistResult:
        result.backends = self._backends()
        result.ok = bool(result.git.get("ok"))
        result.partial = bool(result.errors)
        return result

    def _rel(self, path: Path) -> str:
        return self.project.rel(path)

    # --- Guide ---

    def project_to_guide(self) -> dict[str, Any]:
        """POST SPDD projection load against this project's home folder."""
        url = f"{self.guide_base_url}/api/v1/data/spdd-projection/load"
        payload = json.dumps(
            {"rootPath": str(self.project.home.resolve())}
        ).encode("utf-8")
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

    def guide_stats(self) -> dict[str, Any]:
        url = f"{self.guide_base_url}/api/v1/data/spdd-projection/stats"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=self.guide_timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def guide_lesson_ids(self) -> set[str]:
        """All lesson entity ids known to Guide (for parity diff)."""
        ids: set[str] = set()
        for label in ("Decision", "Pitfall", "Pattern", "Session", "Analysis"):
            url = (
                f"{self.guide_base_url}/api/v1/data/spdd-projection/"
                f"by-label?label={label}&limit=10000"
            )
            req = urllib.request.Request(url, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=self.guide_timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except (urllib.error.URLError, json.JSONDecodeError):
                raise
            for item in data.get("items") or data.get("entities") or []:
                eid = item.get("id") or item.get("entityId") or ""
                if eid:
                    ids.add(str(eid))
        return ids

    # --- retrieve ---

    def retrieve(
        self,
        *,
        work_id: str = "",
        area: str = "",
        kind: str = "",
        keyword: str = "",
        include_staged: bool = True,
        limit: int = 50,
    ) -> dict[str, Any]:
        want_sqlite = backend_enabled(self.project, BACKEND_SQLITE)
        want_guide = backend_enabled(self.project, BACKEND_GUIDE)
        out: dict[str, Any] = {
            "work_id": work_id,
            "area": area,
            "kind": kind,
            "backends": self._backends(),
            "ledger": [],
            "sqlite_graph": None,
            "guide": None,
            "errors": [],
        }
        try:
            staged = self.ledger.staged_ids()
            records = self.ledger.records(
                work_id=work_id,
                area=area,
                kind=kind,
                keyword=keyword,
                include_staged=include_staged,
            )[: max(1, limit)]
            out["ledger"] = [
                {**r.to_json(), "staged": r.id in staged} for r in records
            ]
        except Exception as exc:  # noqa: BLE001
            out["errors"].append(f"ledger: {exc}")
        if want_sqlite and work_id:
            try:
                out["sqlite_graph"] = self.index.graph_for_work(work_id)
            except Exception as exc:  # noqa: BLE001
                out["errors"].append(f"sqlite: {exc}")
        elif work_id:
            out["sqlite_graph"] = {"skipped": True}
        if work_id and want_guide:
            try:
                out["guide"] = self.guide_work(work_id)
            except Exception as exc:  # noqa: BLE001
                out["errors"].append(f"guide: {exc}")
        elif work_id:
            out["guide"] = {"ok": False, "skipped": True}
        return out

    def show(self, record_id: str) -> dict[str, Any] | None:
        """One full record by id — for on-demand body loading."""
        rec = self.ledger.get(record_id)
        if rec is None:
            return None
        data = rec.to_json()
        data["staged"] = record_id in self.ledger.staged_ids()
        return data

    # --- parity ---

    def parity(self, *, repair: bool = False) -> dict[str, Any]:
        """Diff accepted ledger record ids against SQLite and Guide.

        Scope: accepted records only (staged/hot data is runtime state).
        ``repair`` re-derives the projections (db rebuild + Guide reproject).
        """
        ledger_ids = self.ledger.accepted_ids()
        out: dict[str, Any] = {
            "ledger": {"count": len(ledger_ids), "path": self._rel(self.ledger.path)},
            "backends": self._backends(),
            "ok": True,
            "repaired": False,
        }

        if backend_enabled(self.project, BACKEND_SQLITE):
            try:
                sqlite_ids = self.index.accepted_lesson_ids()
                missing = sorted(ledger_ids - sqlite_ids)
                extra = sorted(sqlite_ids - ledger_ids)
                out["sqlite"] = {
                    "enabled": True,
                    "count": len(sqlite_ids),
                    "missing": missing,
                    "extra": extra,
                    "ok": not missing and not extra,
                }
                if missing or extra:
                    out["ok"] = False
            except Exception as exc:  # noqa: BLE001
                out["sqlite"] = {"enabled": True, "ok": False, "error": str(exc)}
                out["ok"] = False
        else:
            out["sqlite"] = {"enabled": False}

        if backend_enabled(self.project, BACKEND_GUIDE):
            try:
                guide_ids = self.guide_lesson_ids()
                missing = sorted(ledger_ids - guide_ids)
                out["guide"] = {
                    "enabled": True,
                    "count": len(guide_ids),
                    "missing": missing,
                    "ok": not missing,
                }
                if missing:
                    out["ok"] = False
            except Exception as exc:  # noqa: BLE001
                out["guide"] = {
                    "enabled": True,
                    "ok": True,
                    "skipped": True,
                    "unreachable": True,
                    "error": str(exc),
                }
                # Guide is optional; unreachable is not committed-ledger drift.
        else:
            out["guide"] = {"enabled": False}

        if repair and not out["ok"]:
            repaired: dict[str, Any] = {}
            if backend_enabled(self.project, BACKEND_SQLITE):
                try:
                    self.index.rebuild()
                    repaired["sqlite"] = "rebuilt"
                except Exception as exc:  # noqa: BLE001
                    repaired["sqlite"] = f"error: {exc}"
            if backend_enabled(self.project, BACKEND_GUIDE):
                try:
                    self.project_to_guide()
                    repaired["guide"] = "reprojected"
                except Exception as exc:  # noqa: BLE001
                    repaired["guide"] = f"error: {exc}"
            out["repaired"] = True
            out["repair_actions"] = repaired
        return out

    # --- session-start digest ---

    def digest(
        self,
        *,
        work_id: str = "",
        areas: list[str] | None = None,
        keywords: list[str] | None = None,
        limit: int = 8,
    ) -> dict[str, Any]:
        return self.ledger.digest(
            areas=areas or [],
            keywords=keywords or [],
            work_id=work_id,
            limit=limit,
        )


__all__ = ["ContextStore", "PersistResult", "LEDGER_KINDS"]
