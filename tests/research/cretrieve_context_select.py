"""Shared C-RETRIEVE context-select fixture (TEST-003 T04).

Four records: two Work IDs, three areas, three kinds. Retrieve must return
the matching subset and exclude sibling records. This is selectivity, not
RQ4 usefulness.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sdlc_engine.context_store import ContextStore
from sdlc_engine.lessons_ledger import lesson_id as make_lesson_id

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "cretrieve_context_select.json"

KIND_LIST = {
    "pitfall": "pitfalls",
    "decision": "decisions",
    "pattern": "patterns",
}


def load_records() -> list[dict[str, str]]:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return list(data["records"])


def record_id(row: dict[str, str]) -> str:
    return make_lesson_id(row["kind"], row["work_id"], row["area"], row["source"])


def ids_matching(
    records: list[dict[str, str]],
    *,
    work_id: str = "",
    area: str = "",
    kind: str = "",
) -> set[str]:
    out: set[str] = set()
    for row in records:
        if work_id and row["work_id"] != work_id:
            continue
        if area and row["area"] != area:
            continue
        if kind and row["kind"] != kind:
            continue
        out.add(record_id(row))
    return out


def seed_canvases(root: Path, records: list[dict[str, str]]) -> None:
    works = sorted({row["work_id"] for row in records})
    req = root / "requirements" / "milestones"
    req.mkdir(parents=True, exist_ok=True)
    canvas = root / "spdd" / "canvas"
    canvas.mkdir(parents=True, exist_ok=True)
    (root / "spdd" / "memory").mkdir(parents=True, exist_ok=True)
    for wid in works:
        (req / f"{wid}.md").write_text(
            f"# Requirement {wid}\n\nContext-select proof.\n", encoding="utf-8"
        )
        (canvas / f"{wid}.md").write_text(
            f"""# REASONS Canvas: {wid}

## Metadata

- Work ID: {wid}
- Work Type: Feature
- Status: In Progress
""",
            encoding="utf-8",
        )


def persist_records(
    store: ContextStore,
    records: list[dict[str, str]],
    *,
    project_guide: bool = False,
) -> dict[str, str]:
    """Accept every row. Project to Guide once at the end when requested."""
    keys: dict[str, str] = {}
    for row in records:
        result = store.persist_lesson(
            kind=row["kind"],
            work_id=row["work_id"],
            area=row["area"],
            body=row["body"],
            source=row["source"],
            accept=True,
            project_guide=False,
        )
        assert result.git.get("ok") is True, result.as_dict()
        lid = str(result.git.get("id") or "")
        assert lid == record_id(row), (lid, record_id(row))
        keys[row["key"]] = lid
    if project_guide:
        out = store.project_to_guide()
        assert out.get("status") == 200, out
    return keys


def retrieved_ids(store: ContextStore, **kwargs: Any) -> set[str]:
    hits = store.retrieve(include_staged=False, limit=50, **kwargs)
    return {str(row.get("id") or "") for row in (hits.get("ledger") or [])}


def subgraph_kind_ids(data: dict[str, Any], kind: str) -> set[str]:
    key = KIND_LIST[kind]
    ids: set[str] = set()
    for item in data.get(key) or []:
        if isinstance(item, str) and item.strip():
            ids.add(item.strip())
            continue
        if isinstance(item, dict):
            eid = item.get("id") or item.get("entityId") or item.get("recordId") or ""
            if eid:
                ids.add(str(eid))
    return ids
