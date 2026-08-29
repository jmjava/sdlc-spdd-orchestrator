"""Rebuild / ingest helpers for the local SQLite index."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from . import canvas as canvas_mod
from .db_schema import (
    NODE_AREA,
    NODE_CANVAS,
    NODE_LESSON,
    NODE_REQUIREMENT,
    NODE_SESSION,
    NODE_WORK,
    REL_ABOUT,
    REL_AREA,
    REL_CANVAS,
    REL_FOR_WORK,
    REL_REASONS,
    REL_RECORDED_FOR,
    REL_REQUIREMENT,
    RebuildStats,
)
from .lessons_ledger import LessonRecord, LessonsLedger
from .links import collect_links, note_token, parse_canvas_metadata, parse_milestone_requirement
from .registry import TeamRegistry
from .timeutil import utc_from_timestamp
from .timeutil import utc_now as _utc_now


class IndexRebuildMixin:
    """Full-index rebuild and ledger/session ingest."""

    def rebuild(self) -> RebuildStats:
        stats = RebuildStats(path=str(self.db_path), rebuilt_at=_utc_now(), source_commit=self._git_head())
        with self.connect() as conn:
            self._init_schema(conn)
            registry = TeamRegistry(self.project)
            rows = {r.work_id: r for r in registry.rows()}
            work_ids = registry.discover_work_ids()
            fts = self._meta(conn, "fts") == "fts5"

            for wid in work_ids:
                reg = rows.get(wid)
                links = collect_links(self.project, wid, reg)
                meta: dict[str, str] = {}
                if links.canvas and links.canvas.is_file():
                    meta = parse_canvas_metadata(links.canvas)
                req_parsed: dict[str, str] = {}
                if links.milestone_req and links.milestone_req.is_file():
                    req_parsed = parse_milestone_requirement(links.milestone_req)
                final = ""
                if links.canvas and links.canvas.is_file():
                    kind = canvas_mod.final_kind(links.canvas)
                    final = kind or ""
                    # Prefer explicit Final Status text when present
                    text = links.canvas.read_text(encoding="utf-8")
                    m = re.search(
                        r"## Final Status.*?^\s*-\s*Status:\s*(.+)$",
                        text,
                        re.IGNORECASE | re.MULTILINE | re.DOTALL,
                    )
                    if m:
                        final = m.group(1).strip()

                title = meta.get("title") or req_parsed.get("jira_summary") or wid
                jira = links.jira_key or (note_token(reg.note, "jira") if reg else "")
                gh = links.github_number or ""
                if reg and not gh:
                    tok = note_token(reg.note, "github")
                    gh = tok.lstrip("#") if tok else ""

                canvas_rel = self._rel(links.canvas) if links.canvas and links.canvas.is_file() else ""
                req_rel = (
                    self._rel(links.milestone_req)
                    if links.milestone_req and links.milestone_req.is_file()
                    else ""
                )

                conn.execute(
                    """
                    INSERT INTO work_items(
                      work_id, title, work_type, canvas_status, final_status, milestone,
                      source_system, source_issue, source_url,
                      canvas_path, requirement_path,
                      registry_status, registry_owner, registry_phase, registry_note,
                      jira_key, github_number,
                      has_canvas, has_requirement, updated
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        wid,
                        title,
                        meta.get("work_type") or "",
                        meta.get("status") or "",
                        final,
                        meta.get("milestone") or "",
                        meta.get("source_system") or links.canvas_source_system or "",
                        meta.get("source_issue") or links.canvas_source_issue or "",
                        meta.get("source_url") or links.canvas_source_url or "",
                        canvas_rel,
                        req_rel,
                        reg.status if reg else "available",
                        reg.owner if reg else "",
                        reg.phase if reg else "",
                        reg.note if reg else "",
                        jira,
                        gh,
                        1 if canvas_rel else 0,
                        1 if req_rel else 0,
                        reg.updated if reg else stats.rebuilt_at,
                    ),
                )
                stats.work_items += 1

                # First-class stay-set nodes + linkage edges (requirement ↔ REASONS).
                req_id = ""
                canvas_id = ""
                if req_rel:
                    req_id = f"{wid}:requirement"
                    conn.execute(
                        "INSERT INTO requirements(id, work_id, path, title, summary, jira_key, updated) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (
                            req_id,
                            wid,
                            req_rel,
                            title,
                            req_parsed.get("summary") or req_parsed.get("jira_summary") or "",
                            jira,
                            reg.updated if reg else stats.rebuilt_at,
                        ),
                    )
                    stats.requirements += 1
                    self._insert_edge(
                        conn,
                        NODE_WORK,
                        wid,
                        REL_REQUIREMENT,
                        NODE_REQUIREMENT,
                        req_id,
                    )
                    stats.edges += 1
                if canvas_rel:
                    canvas_id = f"{wid}:canvas"
                    conn.execute(
                        "INSERT INTO canvases("
                        "id, work_id, path, title, status, readiness, final_status, updated) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (
                            canvas_id,
                            wid,
                            canvas_rel,
                            title,
                            meta.get("status") or "",
                            meta.get("readiness") or "",
                            final,
                            reg.updated if reg else stats.rebuilt_at,
                        ),
                    )
                    stats.canvases += 1
                    self._insert_edge(
                        conn, NODE_WORK, wid, REL_CANVAS, NODE_CANVAS, canvas_id
                    )
                    stats.edges += 1
                if req_id and canvas_id:
                    self._insert_edge(
                        conn,
                        NODE_REQUIREMENT,
                        req_id,
                        REL_REASONS,
                        NODE_CANVAS,
                        canvas_id,
                    )
                    stats.edges += 1

                body_bits = [title, meta.get("status") or "", jira, gh, reg.note if reg else ""]
                if links.milestone_req and links.milestone_req.is_file():
                    body_bits.append(req_parsed.get("summary") or "")
                    body_bits.append(req_parsed.get("jira_description") or "")

                for kind, path in self._artifact_paths(wid, links):
                    if not path.is_file():
                        continue
                    mtime = ""
                    try:
                        mtime = utc_from_timestamp(path.stat().st_mtime)
                    except OSError:
                        pass
                    conn.execute(
                        "INSERT OR REPLACE INTO artifacts(work_id, kind, path, title, mtime) "
                        "VALUES (?,?,?,?,?)",
                        (wid, kind, self._rel(path), title if kind == "canvas" else "", mtime),
                    )
                    stats.artifacts += 1

                if fts:
                    conn.execute(
                        "INSERT INTO work_search(work_id, title, work_type, canvas_status, "
                        "jira_key, github_number, registry_note, body) VALUES (?,?,?,?,?,?,?,?)",
                        (
                            wid,
                            title,
                            meta.get("work_type") or "",
                            meta.get("status") or "",
                            jira,
                            gh,
                            reg.note if reg else "",
                            "\n".join(x for x in body_bits if x),
                        ),
                    )

            # Local sessions (machine-private)
            local_root = self.project.sdlc_dir / "local-sessions"
            if local_root.is_dir():
                for meta_path in sorted(local_root.glob("*/session.json")):
                    try:
                        data = json.loads(meta_path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        continue
                    sid = data.get("id") or meta_path.parent.name
                    conn.execute(
                        "INSERT OR REPLACE INTO local_sessions("
                        "session_id, title, status, intent, owner, promoted_to, updated, path) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (
                            sid,
                            data.get("title") or "",
                            data.get("status") or "",
                            data.get("intent") or "",
                            data.get("owner") or "",
                            data.get("promoted_to") or "",
                            data.get("updated") or "",
                            self._rel(meta_path.parent),
                        ),
                    )
                    stats.local_sessions += 1

            # Ledger + governance + hot sessions (storage v3).
            self._ingest_full_context(conn, stats)

            conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES ('rebuilt_at', ?)",
                (stats.rebuilt_at,),
            )
            conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES ('source_commit', ?)",
                (stats.source_commit,),
            )
            conn.commit()
        return stats

    def _artifact_paths(self, wid: str, links) -> list[tuple[str, Path]]:
        out: list[tuple[str, Path]] = []
        if links.canvas:
            out.append(("canvas", links.canvas))
        if links.milestone_req:
            out.append(("requirement", links.milestone_req))
        analysis = self.project.analysis_path(wid)
        if analysis.is_file():
            out.append(("analysis", analysis))
        review = self.project.review_path(wid)
        if review.is_file():
            out.append(("review", review))
        sync = self.project.sync_path(wid)
        if sync.is_file():
            out.append(("sync", sync))
        return out

    def _ensure_area_row(self, conn: sqlite3.Connection, area: str) -> str:
        name = (area or "").strip()
        if not name:
            return ""
        conn.execute(
            "INSERT INTO areas(id, name, description) VALUES (?,?,?) "
            "ON CONFLICT(id) DO NOTHING",
            (name, name, ""),
        )
        return name

    def _upsert_entry_row(
        self,
        conn: sqlite3.Connection,
        *,
        kind: str,
        work_id: str = "",
        area: str = "",
        phase: str = "",
        path: str = "",
        title: str = "",
        body: str = "",
        source: str = "",
        ts: str = "",
        entry_id: str = "",
    ) -> str:
        from .context_model import NODE_ENTRY as CM_ENTRY
        from .context_model import stable_id

        kind_n = (kind or "").strip().lower()
        wid = (work_id or "").strip()
        if wid:
            conn.execute(
                "INSERT OR IGNORE INTO work_items(work_id, title, updated) VALUES (?,?,?)",
                (wid, wid, _utc_now()),
            )
        eid = entry_id or stable_id(kind_n, wid, area, path, title, source, ts)
        when = ts or _utc_now()
        conn.execute(
            "INSERT INTO context_entries("
            "id, kind, work_id, area, phase, path, title, body, source, ts) "
            "VALUES (?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "kind=excluded.kind, work_id=excluded.work_id, area=excluded.area, "
            "phase=excluded.phase, path=excluded.path, title=excluded.title, "
            "body=excluded.body, source=excluded.source, ts=excluded.ts",
            (
                eid,
                kind_n,
                wid,
                area or "",
                phase or "",
                path or "",
                title or "",
                body or "",
                source or "",
                when,
            ),
        )
        if wid:
            self._insert_edge(conn, CM_ENTRY, eid, REL_FOR_WORK, NODE_WORK, wid)
            req_id = f"{wid}:requirement"
            canvas_id = f"{wid}:canvas"
            if conn.execute(
                "SELECT 1 FROM requirements WHERE id = ?", (req_id,)
            ).fetchone():
                self._insert_edge(
                    conn, CM_ENTRY, eid, REL_ABOUT, NODE_REQUIREMENT, req_id
                )
            if conn.execute(
                "SELECT 1 FROM canvases WHERE id = ?", (canvas_id,)
            ).fetchone():
                self._insert_edge(conn, CM_ENTRY, eid, REL_ABOUT, NODE_CANVAS, canvas_id)
        if area:
            area_id = self._ensure_area_row(conn, area)
            self._insert_edge(conn, CM_ENTRY, eid, REL_ABOUT, NODE_AREA, area_id)
            if wid:
                self._insert_edge(conn, NODE_WORK, wid, REL_AREA, NODE_AREA, area_id)
                conn.execute(
                    "INSERT OR IGNORE INTO work_areas(work_id, area) VALUES (?,?)",
                    (wid, area_id),
                )
                if conn.execute(
                    "SELECT 1 FROM requirements WHERE id = ?", (f"{wid}:requirement",)
                ).fetchone():
                    self._insert_edge(
                        conn,
                        NODE_REQUIREMENT,
                        f"{wid}:requirement",
                        REL_AREA,
                        NODE_AREA,
                        area_id,
                    )
                if conn.execute(
                    "SELECT 1 FROM canvases WHERE id = ?", (f"{wid}:canvas",)
                ).fetchone():
                    self._insert_edge(
                        conn,
                        NODE_CANVAS,
                        f"{wid}:canvas",
                        REL_AREA,
                        NODE_AREA,
                        area_id,
                    )
        return eid

    def _ingest_lesson_row(
        self,
        conn: sqlite3.Connection,
        record: LessonRecord,
        *,
        staged: bool,
        stats: RebuildStats,
    ) -> None:
        """Insert one ledger record into lessons + edges + keyword nodes."""
        from . import context_model as cm

        wid = (record.work_id or "").strip() or "(none)"
        conn.execute(
            "INSERT OR IGNORE INTO work_items(work_id, title, updated) VALUES (?,?,?)",
            (wid, record.work_id or "unstructured (no Work ID)", _utc_now()),
        )
        kw_json = json.dumps(list(record.keywords or []), ensure_ascii=False)
        conn.execute(
            "INSERT INTO lessons("
            "id, kind, work_id, area, title, body, source, phase, keywords, ts, staged) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "kind=excluded.kind, work_id=excluded.work_id, area=excluded.area, "
            "title=excluded.title, body=excluded.body, source=excluded.source, "
            "phase=excluded.phase, keywords=excluded.keywords, ts=excluded.ts, "
            "staged=excluded.staged",
            (
                record.id,
                record.kind,
                wid,
                record.area or "",
                record.title or "",
                record.body or "",
                record.source or "",
                record.phase or "",
                kw_json,
                record.ts or _utc_now(),
                1 if staged else 0,
            ),
        )
        if staged:
            stats.staged_lessons += 1
        else:
            stats.lessons += 1
        self._insert_edge(conn, NODE_LESSON, record.id, REL_RECORDED_FOR, NODE_WORK, wid)
        req_id = f"{wid}:requirement"
        canvas_id = f"{wid}:canvas"
        if conn.execute("SELECT 1 FROM requirements WHERE id = ?", (req_id,)).fetchone():
            self._insert_edge(conn, NODE_LESSON, record.id, REL_ABOUT, NODE_REQUIREMENT, req_id)
            stats.edges += 1
        if conn.execute("SELECT 1 FROM canvases WHERE id = ?", (canvas_id,)).fetchone():
            self._insert_edge(conn, NODE_LESSON, record.id, REL_ABOUT, NODE_CANVAS, canvas_id)
            stats.edges += 1
        if record.area:
            area_id = self._ensure_area_row(conn, record.area)
            self._insert_edge(conn, NODE_LESSON, record.id, REL_ABOUT, NODE_AREA, area_id)
            self._insert_edge(conn, NODE_WORK, wid, REL_AREA, NODE_AREA, area_id)
            conn.execute(
                "INSERT OR IGNORE INTO work_areas(work_id, area) VALUES (?,?)",
                (wid, area_id),
            )
            stats.edges += 2
        for kw in record.keywords or []:
            keyword = (kw or "").strip().lower()
            if not keyword:
                continue
            kid = cm.stable_id("keyword", keyword)
            conn.execute(
                "INSERT INTO domain_keywords(id, keyword) VALUES (?,?) "
                "ON CONFLICT(id) DO UPDATE SET keyword=excluded.keyword",
                (kid, keyword),
            )
            stats.domain_keywords += 1
            if record.area:
                self._insert_edge(conn, cm.NODE_KEYWORD, kid, REL_ABOUT, NODE_AREA, record.area)
            self._insert_edge(conn, cm.NODE_KEYWORD, kid, REL_ABOUT, NODE_LESSON, record.id)
            stats.edges += 1

    def _ingest_full_context(
        self, conn: sqlite3.Connection, stats: RebuildStats
    ) -> None:
        """Ingest governance docs, lessons ledger, and hot sessions (storage v3)."""
        from . import context_model as cm

        home = self.project.home

        # 1) Stay-set governance artifacts
        for rel_dir, kind, pattern in cm.GOVERNANCE_GLOBS:
            d = home / rel_dir
            if not d.is_dir():
                continue
            for path in sorted(d.glob(pattern)):
                if not path.is_file():
                    continue
                wid = cm.work_id_from_name(path.name)
                body = ""
                try:
                    body = path.read_text(encoding="utf-8")[:4000]
                except OSError:
                    pass
                self._upsert_entry_row(
                    conn,
                    kind=kind,
                    work_id=wid,
                    path=self._rel(path),
                    title=path.stem,
                    body=body,
                    source="stay-set",
                )
                stats.context_entries += 1
                stats.edges += 1

        # 2) Lessons ledger (accepted + staged)
        ledger = LessonsLedger(self.project)
        staged_ids = ledger.staged_ids()
        for rec in ledger.records(include_staged=True):
            self._ingest_lesson_row(conn, rec, staged=(rec.id in staged_ids), stats=stats)

        # 3) Hot session briefs (.sdlc/sessions/*.md)
        sdir = self.project.hot_session_dir()
        if sdir.is_dir():
            for path in sorted(sdir.glob("*.md")):
                wid = cm.work_id_from_name(path.name)
                body = ""
                try:
                    body = path.read_text(encoding="utf-8")[:4000]
                except OSError:
                    pass
                sid = path.stem
                conn.execute(
                    "INSERT INTO context_sessions(id, work_id, phase, path, summary, ts) "
                    "VALUES (?,?,?,?,?,?) "
                    "ON CONFLICT(id) DO UPDATE SET "
                    "work_id=excluded.work_id, path=excluded.path, summary=excluded.summary",
                    (sid, wid, "", self._rel(path), body[:500], _utc_now()),
                )
                if wid:
                    self._insert_edge(conn, NODE_SESSION, sid, REL_FOR_WORK, NODE_WORK, wid)
                self._upsert_entry_row(
                    conn,
                    kind="session",
                    work_id=wid,
                    path=self._rel(path),
                    title=sid,
                    body=body,
                    source="hot-session",
                    entry_id=f"session:{sid}",
                )
                stats.context_entries += 1

