"""Archive completed/cancelled Work ID artifacts."""

from __future__ import annotations

import shutil
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

    def _move(self, src: Path, dest: Path, dry_run: bool) -> bool:
        if not src.exists():
            return False
        if dry_run:
            print(f"[dry-run] would move {self.project.rel(src)} -> {self.project.rel(dest)}")
            return True
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            print(f"archive: destination already exists, skipping {self.project.rel(dest)}")
            return False
        shutil.move(str(src), str(dest))
        print(f"Moved {self.project.rel(src)} -> {self.project.rel(dest)}")
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

        home = self.project.home
        moved = False
        for src, dest in [
            (
                self.project.canvas_path(work_id),
                self.project.spdd_dir / "canvas" / "archive" / f"{work_id}.md",
            ),
            (
                self.project.analysis_path(work_id),
                self.project.spdd_dir / "analysis" / "archive" / f"{work_id}-analysis.md",
            ),
            (
                self.project.review_path(work_id),
                self.project.spdd_dir / "reviews" / "archive" / f"{work_id}-review.md",
            ),
            (
                self.project.sync_path(work_id),
                self.project.spdd_dir / "sync" / "archive" / f"{work_id}-sync.md",
            ),
        ]:
            moved |= self._move(src, dest, dry_run)

        session_dirs = [self.project.hot_session_dir(), home / "agent-context" / "sessions"]
        if home != self.project.root:
            session_dirs.append(self.project.root / "agent-context" / "sessions")
        seen_sessions: set[Path] = set()
        for sessions in session_dirs:
            if not sessions.is_dir() or sessions in seen_sessions:
                continue
            seen_sessions.add(sessions)
            for sess in sessions.iterdir():
                if not sess.is_file() or sess.name == "current-session.md":
                    continue
                if work_id in sess.name:
                    moved |= self._move(sess, sessions / "archive" / sess.name, dry_run)

        state_src = self.project.workflows_dir / f"{work_id}.state"
        moved |= self._move(
            state_src,
            self.project.workflows_dir / "archive" / f"{work_id}.state",
            dry_run,
        )

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
        if not moved:
            print(f"archive: {work_id} marked archived (no movable artifacts found; milestone left in place)")
        else:
            print(f"Archived {work_id} ({kind}). Commit moved paths + spdd/memory/registry.jsonl.")
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
