"""Jira link + sync APIs on the ops console."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("flask")

from sdlc_engine.installer.app import create_app
from sdlc_engine.project import Project
from sdlc_engine.registry import TeamRegistry


def _seed(root: Path, work_id: str) -> None:
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(
        f"""---
work_id: "{work_id}"
jira_key: ""
---

# Requirement: {work_id}

## Summary

Demo work.

## Jira

- Key: TBD
- Summary: Demo summary
- Issue type: Story

### Description
Local description

## GitHub

- Number: TBD
""",
        encoding="utf-8",
    )
    canvas = root / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"""# REASONS Canvas: {work_id} - Demo

## Metadata

- Work ID: {work_id}
- Source System:
- Source Issue:
- Source URL:
""",
        encoding="utf-8",
    )
    (root / "spdd" / "memory").mkdir(parents=True, exist_ok=True)
    reg = root / "spdd" / "memory" / "registry.jsonl"
    if not reg.is_file():
        reg.write_text("", encoding="utf-8")
    TeamRegistry(Project.resolve(root)).claim(work_id)


def test_api_jira_link_dry_run_and_apply(tmp_path: Path) -> None:
    work_id = "FEAT-001-order-status-api"
    _seed(tmp_path, work_id)
    app = create_app(tmp_path)
    client = app.test_client()

    dry = client.post(
        "/api/jira/link",
        json={
            "target": str(tmp_path),
            "work_id": work_id,
            "jira_key": "PROJ-123",
            "summary": "Order status",
            "dry_run": True,
        },
    )
    assert dry.status_code == 200
    body = dry.get_json()
    assert body["ok"] is True
    assert body["dry_run"] is True
    assert any("would set" in a for a in body["actions"])

    req_text = (tmp_path / "requirements" / "milestones" / f"{work_id}.md").read_text()
    assert "PROJ-123" not in req_text

    apply = client.post(
        "/api/jira/link",
        json={
            "target": str(tmp_path),
            "work_id": work_id,
            "jira_key": "PROJ-123",
            "summary": "Order status",
            "apply": True,
        },
    )
    assert apply.status_code == 200
    applied = apply.get_json()
    assert applied["linked"] is True

    req_text = (tmp_path / "requirements" / "milestones" / f"{work_id}.md").read_text()
    assert "Key: PROJ-123" in req_text
    assert 'jira_key: "PROJ-123"' in req_text
    canvas = (tmp_path / "spdd" / "canvas" / f"{work_id}.md").read_text()
    assert "Source Issue: PROJ-123" in canvas

    status = client.post(
        "/api/jira/status",
        json={"target": str(tmp_path), "work_id": work_id},
    )
    assert status.status_code == 200
    st = status.get_json()
    assert st["jira_key"] == "PROJ-123"
    assert st["linked"] is True


def test_api_jira_sync_requires_linked_key(tmp_path: Path) -> None:
    work_id = "FEAT-002-demo"
    _seed(tmp_path, work_id)
    app = create_app(tmp_path)
    client = app.test_client()
    res = client.post(
        "/api/jira/sync",
        json={"target": str(tmp_path), "work_id": work_id, "direction": "pull"},
    )
    assert res.status_code == 400
    assert "no Jira Key linked" in res.get_json()["error"]
