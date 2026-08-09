"""Route agent questions to Guide ``spdd_*`` tools (MCP / HTTP parity)."""

from __future__ import annotations

import json
from typing import Any

from .guide_client import GuideClient, SPDD_MCP_TOOLS


def resolve_guide_query(
    *,
    work_id: str = "",
    area: str = "",
    lesson_id: str = "",
    label: str = "",
    question: str = "",
    stats: bool = False,
    tool: str = "",
    tool_args: dict[str, Any] | None = None,
    limit: int = 20,
) -> tuple[str, dict[str, Any]]:
    """Return (tool_name, arguments) for GuideClient.call_mcp_tool."""
    if tool:
        name = tool.strip()
        if name.startswith("spdd_"):
            return name, dict(tool_args or {})
        if name in {"workSubgraph", "work_subgraph"}:
            return "spdd_workSubgraph", dict(tool_args or {})
        return name if name in SPDD_MCP_TOOLS else f"spdd_{name}", dict(tool_args or {})

    if stats:
        return "spdd_projectionStats", {}

    if lesson_id:
        return "spdd_getLesson", {"id": lesson_id.strip()}

    if label:
        return "spdd_findByLabel", {"label": label.strip(), "limit": limit}

    q = (question or "").strip().lower()
    if q in {"stats", "projection stats", "freshness"}:
        return "spdd_projectionStats", {}

    if work_id and area:
        return "spdd_workSubgraph", {"workId": work_id.strip()}

    if area and not work_id:
        return "spdd_areaLessons", {"area": area.strip(), "limit": limit}

    if work_id:
        return "spdd_workSubgraph", {"workId": work_id.strip()}

    if "area" in q or "lessons for" in q or "cross-run" in q:
        # Best-effort: last token as area hint when no explicit --area
        tokens = [t for t in question.split() if t.strip()]
        if tokens:
            return "spdd_areaLessons", {"area": tokens[-1].strip("/"), "limit": limit}

    if work_id or "work" in q or "subgraph" in q:
        return "spdd_workSubgraph", {"workId": work_id.strip()}

    raise ValueError(
        "guide-query needs --work-id, --area, --lesson-id, --label, --stats, "
        "--tool, or a --question with enough context"
    )


def run_guide_query(client: GuideClient, **kwargs: Any) -> dict[str, Any]:
    tool_name, args = resolve_guide_query(**kwargs)
    result = client.call_mcp_tool(tool_name, args)
    result["resolved_tool"] = tool_name
    result["arguments"] = args
    return result


def format_guide_answer(payload: dict[str, Any]) -> str:
    """Human-readable summary for Cursor/Copilot chat (stdout)."""
    if not payload.get("ok"):
        return json.dumps(payload, indent=2)
    data = payload.get("data") or {}
    tool = payload.get("resolved_tool") or payload.get("tool") or ""
    lines = [f"Guide ({tool})", f"HTTP: {payload.get('http', '')}"]
    if tool == "spdd_projectionStats":
        for key in (
            "workIdCount",
            "pitfallCount",
            "decisionCount",
            "patternCount",
            "canvasCount",
        ):
            if key in data:
                lines.append(f"  {key}: {data[key]}")
    elif tool == "spdd_getLesson":
        body = data.get("body") or data.get("description") or ""
        lines.append(f"  id: {data.get('id', '')}")
        if body:
            lines.append(f"  body: {body[:2000]}")
    elif tool == "spdd_workSubgraph":
        pitfalls = data.get("pitfalls") or []
        decisions = data.get("decisions") or []
        lines.append(f"  work found: {data.get('found', True)}")
        lines.append(f"  pitfalls: {len(pitfalls)}, decisions: {len(decisions)}")
        for p in pitfalls[:5]:
            desc = (p.get("description") or p.get("id") or "")[:200]
            lines.append(f"    - {desc}")
    elif tool == "spdd_areaLessons":
        lines.append(f"  area found: {data.get('found', True)}")
        for kind in ("pitfalls", "decisions", "patterns"):
            items = data.get(kind) or []
            lines.append(f"  {kind}: {len(items)}")
    else:
        lines.append(json.dumps(data, indent=2)[:4000])
    lines.append("")
    lines.append("Full JSON on stderr when using --json; native MCP: connect IDE to /sse")
    return "\n".join(lines)
