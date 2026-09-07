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
from .guide_client import GuideClient
from .lessons_ledger import LEDGER_KINDS, LessonRecord, LessonsLedger
from .metrics import ProcessMetrics
from .persistence import (
    BACKEND_GUIDE,
    BACKEND_SQLITE,
    enabled as backend_enabled,
    load_config as load_persistence_config,
)
from .project import Project

_SUBGRAPH_LESSON_KEYS = (
    "pitfalls",
    "decisions",
    "patterns",
    "sessions",
    "analyses",
)

# orch-guide tag sdlc-spdd-projection-v2 projects these kinds from context-index.md.
_GUIDE_INGEST_KINDS = ("decision", "pitfall", "pattern")

_GUIDE_INDEX_HEADER = (
    "# Context Index\n"
    "\n"
    "> Derived from `spdd/memory/lessons.jsonl` for Guide v2 ingest. Do not hand-edit.\n"
    "\n"
    "| Area | Kind | Work ID | Phase | Timestamp | Source | Entry |\n"
    "|------|------|---------|-------|-----------|--------|-------|\n"
)


def lesson_ids_from_subgraph(data: dict[str, Any]) -> set[str]:
    """Collect lesson record ids from a ``spdd_workSubgraph`` payload."""
    ids: set[str] = set()
    for key in _SUBGRAPH_LESSON_KEYS:
        for item in data.get(key) or []:
            if isinstance(item, str) and item.strip():
                ids.add(item.strip())
                continue
            if not isinstance(item, dict):
                continue
            eid = item.get("id") or item.get("entityId") or item.get("recordId") or ""
            if eid:
                ids.add(str(eid))
    return ids


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
        metrics: ProcessMetrics | dict[str, Any] | None = None,
        readiness: str | None = None,
        review_result: str | None = None,
        rework: int | None = None,
        context_files: int | None = None,
        validate_cycles: int | None = None,
        review_cycles: int | None = None,
    ) -> PersistResult:
        """Write one lesson record. Staged by default; ``accept=True`` lands
        it in the committed ledger immediately (retro/sync accept points)."""
        if metrics is None:
            metrics = ProcessMetrics.from_capture(
                readiness=readiness,
                review_result=review_result,
                rework=rework,
                context_files=context_files,
                validate_cycles=validate_cycles,
                review_cycles=review_cycles,
                strict=True,
            )
        elif isinstance(metrics, dict):
            metrics = ProcessMetrics.from_json(metrics)
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
            metrics=metrics,
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

    def _guide_client(self) -> GuideClient:
        return GuideClient(self.guide_base_url, timeout=self.guide_timeout)

    def write_guide_ingest_index(self) -> Path:
        """Rebuild Guide v2's ingest table from the accepted ledger.

        ``sdlc-spdd-projection-v2`` projects canvases plus
        ``spdd/memory/context-index.md`` — it does **not** read
        ``lessons.jsonl``. The table is a derived projection so persist→load
        stores the same record ids the ledger uses
        (``{kind}:{workId}:{area}:{source}``). Hand-writing this file in a
        test is not a C-RETRIEVE pass.
        """
        path = self.project.home / "spdd" / "memory" / "context-index.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [_GUIDE_INDEX_HEADER]
        for rec in self.ledger.records(include_staged=False):
            if rec.kind not in _GUIDE_INGEST_KINDS:
                continue
            area = (rec.area or "").strip() or "(none)"
            wid = (rec.work_id or "").strip() or "(none)"
            # Guide splits on `|` and drops empty cells; keep seven columns.
            phase = (rec.phase or "").strip() or "-"
            ts = (rec.ts or "").strip() or "-"
            source = (rec.source or "").strip() or "capture"
            entry = (rec.title or rec.body or rec.kind).strip().splitlines()[0]
            entry = entry.replace("|", "/").replace("\n", " ")[:300]
            lines.append(
                f"| {area} | {rec.kind} | {wid} | {phase} | {ts} | {source} | {entry} |\n"
            )
        path.write_text("".join(lines), encoding="utf-8")
        return path

    def project_to_guide(self) -> dict[str, Any]:
        """POST SPDD projection load against this project's home folder."""
        index_path = self.write_guide_ingest_index()
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
                    "ingestIndex": self._rel(index_path),
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
        """Lesson record ids in the Guide/Neo4j projection.

        Reads ``spdd_workSubgraph`` for each accepted ledger Work ID — the
        retrieve API in ``docs/dice-projection-runbook.md``. Global
        ``by-label`` is capped (max 100) and is not the C-RETRIEVE instrument.
        """
        client = self._guide_client()
        work_ids = sorted(
            {
                rec.work_id
                for rec in self.ledger.records(include_staged=False)
                if (rec.work_id or "").strip()
            }
        )
        ids: set[str] = set()
        for wid in work_ids:
            sg = client.work_subgraph(wid)
            if not sg.get("ok"):
                status = sg.get("status")
                if status == 404:
                    continue
                raise RuntimeError(
                    f"Guide work_subgraph {wid}: status={status} "
                    f"error={sg.get('error')}"
                )
            ids |= lesson_ids_from_subgraph(sg.get("data") or {})
        return ids

    # --- retrieve ---

    def retrieve(
        self,
        *,
        work_id: str = "",
        area: str = "",
        kind: str = "",
        keyword: str = "",
        query: str = "",
        rank: str = "",
        include_staged: bool = True,
        limit: int = 50,
    ) -> dict[str, Any]:
        from .retrieve import (
            ALG_KEYWORD_LIST,
            ALG_TITLE_BODY,
            ALG_UNFILTERED_TS,
            keyword_list_filter,
            rank_title_body,
        )

        want_sqlite = backend_enabled(self.project, BACKEND_SQLITE)
        want_guide = backend_enabled(self.project, BACKEND_GUIDE)
        algorithm = (rank or "").strip().lower()
        query = (query or "").strip()
        keyword = (keyword or "").strip()
        if not algorithm:
            if query:
                algorithm = ALG_TITLE_BODY
            elif keyword:
                algorithm = ALG_KEYWORD_LIST
            else:
                algorithm = ALG_UNFILTERED_TS
        out: dict[str, Any] = {
            "work_id": work_id,
            "area": area,
            "kind": kind,
            "algorithm": algorithm,
            "query": query,
            "keyword": keyword,
            "backends": self._backends(),
            "ledger": [],
            "sqlite_graph": None,
            "guide": None,
            "errors": [],
        }
        try:
            staged = self.ledger.staged_ids()
            candidates = self.ledger.records(
                work_id=work_id,
                area=area,
                kind=kind,
                keyword="" if algorithm == ALG_TITLE_BODY else keyword,
                include_staged=include_staged,
            )
            if algorithm == ALG_TITLE_BODY:
                ranked = rank_title_body(candidates, query)[: max(1, limit)]
                out["ledger"] = [
                    {**r.to_json(), "score": score, "staged": r.id in staged}
                    for score, r in ranked
                ]
            else:
                if algorithm == ALG_KEYWORD_LIST:
                    candidates = keyword_list_filter(candidates, keyword)
                records = candidates[: max(1, limit)]
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

    def metrics_query(
        self,
        *,
        construct: str = "",
        work_id: str = "",
        phase: str = "",
        include_staged: bool = True,
    ) -> dict[str, Any]:
        return self.ledger.metrics_query(
            construct=construct,
            work_id=work_id,
            phase=phase,
            include_staged=include_staged,
        )

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
            client = self._guide_client()
            if not client.health_ok():
                out["guide"] = {
                    "enabled": True,
                    "ok": True,
                    "skipped": True,
                    "unreachable": True,
                }
            else:
                try:
                    guide_ids = self.guide_lesson_ids()
                    missing = sorted(ledger_ids - guide_ids)
                    out["guide"] = {
                        "enabled": True,
                        "count": len(guide_ids),
                        "missing": missing,
                        "ok": not missing,
                        "via": "work_subgraph",
                    }
                    if missing:
                        out["ok"] = False
                except Exception as exc:  # noqa: BLE001
                    out["guide"] = {
                        "enabled": True,
                        "ok": False,
                        "error": str(exc),
                    }
                    out["ok"] = False
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


__all__ = [
    "ContextStore",
    "PersistResult",
    "LEDGER_KINDS",
    "lesson_ids_from_subgraph",
]
