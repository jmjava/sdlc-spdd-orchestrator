"""Seed a disposable ops-console playground tree (no consumer install)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from ..io_util import save_json_dict
from ..timeutil import utc_now
from .runner import orchestrator_root

PLAYGROUND_DIRNAME = "console-playground"
MARKER_NAME = "playground.json"

WORKS: tuple[tuple[str, str, str], ...] = (
    ("FEAT-930-console-playground", "feature", "Add a playground seed so the Vue console can be clicked without a consumer install."),
    ("SPIKE-931-console-playground", "spike", "Spike whether a disposable tree is enough to exercise every console tab."),
    ("BUG-932-console-playground", "bug", "Fix empty Dashboard when the target has no pointer or canvas."),
)


def default_playground_dir(orch: Path | str | None = None) -> Path:
    root = Path(orch) if orch is not None else orchestrator_root()
    return root / ".sdlc" / PLAYGROUND_DIRNAME


def is_playground(target: Path | str) -> bool:
    return (Path(target).expanduser().resolve() / ".sdlc" / MARKER_NAME).is_file()


def materialize_playground(
    dest: Path | str | None = None,
    *,
    refresh: bool = True,
    orch: Path | str | None = None,
) -> Path:
    """Write a self-contained SPDD tree and return its path.

    Default dest is ``<orchestrator>/.sdlc/console-playground`` (gitignored).
    ``refresh=True`` replaces the tree so clicks that write files stay disposable.
    """
    root = Path(dest) if dest is not None else default_playground_dir(orch)
    root = root.expanduser().resolve()
    if refresh and root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    ts = utc_now()
    sdlc = root / ".sdlc"
    memory = root / "spdd" / "memory"
    canvas_dir = root / "spdd" / "canvas"
    analysis_dir = root / "spdd" / "analysis"
    reviews_dir = root / "spdd" / "reviews"
    milestones = root / "requirements" / "milestones"
    adf_dir = root / "adf"
    sessions = sdlc / "sessions"
    staged = sdlc / "staged"
    backup = root / ".sdlc-spdd-upgrade-backups" / "20260815T120000Z"
    for path in (
        sdlc,
        memory,
        canvas_dir,
        analysis_dir,
        reviews_dir,
        milestones,
        adf_dir,
        sessions,
        staged,
        backup,
    ):
        path.mkdir(parents=True, exist_ok=True)

    active = WORKS[0][0]
    (sdlc / "pointer").write_text(active + "\n", encoding="utf-8")
    save_json_dict(
        sdlc / MARKER_NAME,
        {"playground": True, "created_at": ts, "works": [w[0] for w in WORKS]},
    )
    save_json_dict(
        sdlc / "persistence-config.json",
        {
            "backends": ["git-pointers", "sqlite"],
            "guide_url": "",
            "notes": "Playground: git + sqlite only (no live Guide).",
        },
    )
    save_json_dict(
        sdlc / "integrations-config.json",
        {
            "tracker": "github",
            "jira": {
                "base_url": "https://example.atlassian.net",
                "email": "playground@example.com",
                "project": "PLAY",
            },
            "github": {"repo": "example/console-playground"},
        },
    )
    save_json_dict(
        sdlc / "guide-config.json",
        {
            "guide_home": "",
            "guide_git_url": "https://github.com/jmjava/orch-guide.git",
            "guide_git_ref": "sdlc-spdd-projection-v2",
            "host": "127.0.0.1",
            "port": 21337,
            "notes": "Playground stub — Guide stays DOWN unless you point at a real clone.",
        },
    )

    lessons: list[dict[str, Any]] = []
    registry: list[dict[str, Any]] = []
    for work_id, kind, summary in WORKS:
        _write_requirement(milestones / f"{work_id}.md", work_id, kind, summary)
        _write_canvas(canvas_dir / f"{work_id}.md", work_id, kind, summary)
        (analysis_dir / f"{work_id}-analysis.md").write_text(
            f"# Analysis: {work_id}\n\nPlayground analysis for {summary}\n",
            encoding="utf-8",
        )
        lessons.append(
            {
                "id": f"pitfall:{work_id}:console:playground",
                "kind": "pitfall",
                "work_id": work_id,
                "area": "console",
                "phase": "retro",
                "ts": ts,
                "title": f"Playground pitfall for {work_id}",
                "body": summary,
                "source": "playground",
                "keywords": ["playground", kind],
                "commit": "",
                "schema": 1,
            }
        )
        registry.append(
            {
                "event": "claim",
                "work_id": work_id,
                "status": "In Progress",
                "phase": "code" if work_id == active else "plan",
                "operation": "T02" if work_id == active else "T01",
                "owner": "playground",
                "note": "seeded for Vue console playground",
                "ts": ts,
            }
        )
        _write_adf(adf_dir / f"{work_id}.adf.json", work_id, summary)

    (reviews_dir / f"{active}-review.md").write_text(
        f"# Review: {active}\n\nPlayground review stub (T01 done, T02 open).\n",
        encoding="utf-8",
    )
    _write_jsonl(memory / "lessons.jsonl", lessons)
    _write_jsonl(memory / "registry.jsonl", registry)
    _write_jsonl(
        staged / "lessons.jsonl",
        [
            {
                "id": f"session:{active}:console:capture",
                "kind": "session",
                "work_id": active,
                "area": "console",
                "phase": "code",
                "ts": ts,
                "title": "Staged playground capture",
                "body": "This row is staged only — Persistence parity should show drift until accept.",
                "source": "playground",
                "keywords": ["playground", "staged"],
                "commit": "",
                "schema": 1,
            }
        ],
    )
    sessions.joinpath("current-session.md").write_text(
        f"# Current session\n\n- Work ID: {active}\n- Phase: code\n- Playground: yes\n",
        encoding="utf-8",
    )
    (backup / "README.md").write_text(
        "Fake upgrade backup for the Rollback tab. Dry-run restore is safe.\n",
        encoding="utf-8",
    )
    (root / "PLAYGROUND.md").write_text(
        "# Vue ops console playground\n\n"
        "Disposable SPDD tree. Regenerated by `sdlc.sh console --playground`.\n"
        "Do not install this into a real app. Guide/Jira/GitHub stay mocked or DOWN.\n",
        encoding="utf-8",
    )
    return root


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_requirement(path: Path, work_id: str, kind: str, summary: str) -> None:
    issue_type = {"feature": "Story", "spike": "Spike", "bug": "Bug"}.get(kind, "Task")
    path.write_text(
        f"""---
work_id: "{work_id}"
jira_key: ""
github_number: ""
---

# Requirement: {work_id}

## Summary

{summary}

## Jira

- Key: TBD
- Summary: {summary}
- Issue type: {issue_type}

### Description

Playground requirement. Link/sync dry-run only.

## GitHub

- Number: TBD
""",
        encoding="utf-8",
    )


def _write_canvas(path: Path, work_id: str, kind: str, summary: str) -> None:
    path.write_text(
        f"""# REASONS Canvas: {work_id} - Playground

## Metadata

- Work ID: {work_id}
- Work Type: {kind}
- Status: Ready For Coding
- Owner: playground

## R - Requirements

### User Goal

{summary}

### Acceptance Criteria

- [x] Seed a disposable console target
- [ ] Click every Vue tab against this tree

## O - Operations

### T01 - Seed playground tree

- Status: Complete
- Description: Write requirements, canvas, ledger, ADF
- Files: examples / .sdlc/console-playground
- Tests: unit
- Validation: materialize_playground tests pass

### T02 - Exercise Vue tabs

- Status: Not Started
- Description: Open Dashboard, Persistence, Templates, Issues, ADF
- Files: console-ui
- Tests: Playwright optional
- Validation: tabs load without a consumer install

## N - Norms

- One operation per coding session

## S - Safeguards

- Do not push to Jira/GitHub from this tree
- Do not point Guide ingest at a real corpus unless you intend to

## Architecture Notes

- Readiness: Ready For Coding
""",
        encoding="utf-8",
    )


def _write_adf(path: Path, work_id: str, summary: str) -> None:
    save_json_dict(
        path,
        {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": work_id}],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": summary}],
                },
            ],
        },
    )
