"""Archive completed/cancelled Work ID artifacts.

Storage v3 contract: archive *removes* the Work ID's contract artifacts from the
working tree (canvas, analysis, review, sync, hot session briefs, workflow
state) and appends an ``archived`` event to ``spdd/memory/registry.jsonl``.
Git history is the audit trail; there are no ``spdd/*/archive/`` folders.
Requirements and the lessons ledger are never touched.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import canvas as canvas_mod
from .project import Project
from .registry import RegistryRow, TeamRegistry
from .timeutil import utc_now as _utc_now
from .workflow import WorkflowEngine


@dataclass
class ArchiveService:
    project: Project | None = None
    registry: TeamRegistry | None = None
    workflow: WorkflowEngine | None = None

    def __post_init__(self) -> None:
        self.project = self.project or Project.resolve()
        self.workflow = self.workflow or WorkflowEngine(self.project)
        self.registry = self.registry or TeamRegistry(self.project, self.workflow)

    def _remove(self, path: Path, dry_run: bool) -> bool:
        if not path.exists():
            return False
        if dry_run:
            print(f"[dry-run] would remove {self.project.rel(path)}")
            return True
        path.unlink()
        print(f"Removed {self.project.rel(path)}")
        return True

    def archive_work(self, work_id: str, *, dry_run: bool = False, force: bool = False) -> None:
        if not work_id:
            raise ValueError("archive: Work ID required")
        canvas_path = self.project.canvas_path(work_id)
        kind = canvas_mod.final_kind(canvas_path) if canvas_path.is_file() else "other"
        if not force and kind not in {"complete", "cancelled"}:
            raise ValueError(
                f"archive: {work_id} is not Complete or Cancelled (Final Status kind={kind}). Use --force to archive anyway."
            )

        pointer = self.workflow.pointer.get()
        if pointer == work_id:
            if dry_run:
                print(f"[dry-run] would clear pointer for {work_id}")
            else:
                self.workflow.pointer.reset()
                print(f"Cleared local pointer (was {work_id})")

        removed = False
        for src in (
            self.project.canvas_path(work_id),
            self.project.analysis_path(work_id),
            self.project.review_path(work_id),
            self.project.sync_path(work_id),
        ):
            removed |= self._remove(src, dry_run)

        sessions = self.project.hot_session_dir()
        if sessions.is_dir():
            for sess in sorted(sessions.iterdir()):
                if not sess.is_file() or sess.name == "current-session.md":
                    continue
                if work_id in sess.name:
                    removed |= self._remove(sess, dry_run)

        removed |= self._remove(self.project.workflows_dir / f"{work_id}.state", dry_run)

        if dry_run:
            print(f"[dry-run] would mark {work_id} archived in registry.jsonl")
            return

        note = f"archived:{kind if kind != 'other' else 'forced'}"
        self.registry.upsert(
            RegistryRow(
                work_id=work_id,
                status="archived",
                phase="archive",
                owner=self.registry._owner(),
                updated=_utc_now(),
                note=note,
            )
        )
        if not removed:
            print(f"archive: {work_id} marked archived (no artifacts found; requirement left in place)")
        else:
            print(f"Archived {work_id} ({kind}). Commit the removals + spdd/memory/registry.jsonl.")
        print(f"Left in place: requirements/milestones/{work_id}.md (if present).")
        print("Left in place: spdd/memory/lessons.jsonl (archive never truncates the lessons ledger).")

    def archive_eligible(self, *, dry_run: bool = False) -> int:
        count = 0
        existing = {r.work_id: r for r in self.registry.rows()}
        for work_id in self.registry.discover_work_ids():
            if existing.get(work_id) and existing[work_id].status == "archived":
                continue
            if not canvas_mod.is_archivable(self.project.canvas_path(work_id)):
                continue
            self.archive_work(work_id, dry_run=dry_run, force=False)
            count += 1
        print(f"archive: processed {count} eligible Work ID(s)")
        return count
