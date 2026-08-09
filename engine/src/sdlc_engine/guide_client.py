"""Guide DICE client — HTTP parity with ``spdd_*`` MCP tools.

Cursor and Copilot connect to Guide at ``/sse`` for native MCP. Agents and
CI use this module (or ``sdlc-engine context guide-query``) for the same
payloads via REST when MCP is not wired in the IDE session.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

SPDD_MCP_TOOLS = (
    "spdd_workSubgraph",
    "spdd_projectionStats",
    "spdd_areaLessons",
    "spdd_findByLabel",
    "spdd_getLesson",
)

_TOOL_HTTP: dict[str, str] = {
    "spdd_workSubgraph": "GET /api/v1/data/spdd-projection/work/{workId}",
    "spdd_projectionStats": "GET /api/v1/data/spdd-projection/stats",
    "spdd_areaLessons": "GET /api/v1/data/spdd-projection/area?name={area}",
    "spdd_findByLabel": "GET /api/v1/data/spdd-projection/by-label?label={label}",
    "spdd_getLesson": "GET /api/v1/data/spdd-projection/lesson/{id}",
}


def resolve_guide_base_url(
    *,
    explicit: str | None = None,
    project_url: str | None = None,
) -> str:
    env = os.environ.get("GUIDE_BASE_URL", "").strip()
    port = os.environ.get("GUIDE_PORT", "21337").strip() or "21337"
    return (explicit or env or project_url or f"http://127.0.0.1:{port}").rstrip("/")


class GuideClient:
    """REST client mirroring Embabel ``spdd_*`` MCP tools."""

    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._prefix = f"{self.base_url}/api/v1/data/spdd-projection"

    def health_ok(self) -> bool:
        url = f"{self.base_url}/actuator/health"
        try:
            with urllib.request.urlopen(url, timeout=min(self.timeout, 5.0)) as resp:
                return int(getattr(resp, "status", 200)) == 200
        except (urllib.error.URLError, OSError, TimeoutError):
            return False

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._prefix}{path}"
        data = None
        headers: dict[str, str] = {}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                parsed = json.loads(raw) if raw else {}
                return {
                    "ok": True,
                    "status": getattr(resp, "status", 200),
                    "data": parsed,
                    "http": f"{method} {path}",
                }
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            try:
                err_body = json.loads(detail) if detail else {}
            except json.JSONDecodeError:
                err_body = {"error": detail or exc.reason}
            return {
                "ok": False,
                "status": exc.code,
                "error": err_body.get("error") or detail or exc.reason,
                "http": f"{method} {path}",
            }
        except urllib.error.URLError as exc:
            return {"ok": False, "error": str(exc), "http": f"{method} {path}"}

    def project_load(self, root_path: str) -> dict[str, Any]:
        return self._request("POST", "/load", body={"rootPath": root_path})

    def projection_stats(self) -> dict[str, Any]:
        return self._request("GET", "/stats")

    def work_subgraph(self, work_id: str) -> dict[str, Any]:
        wid = urllib.parse.quote(work_id.strip(), safe="")
        return self._request("GET", f"/work/{wid}")

    def area_lessons(self, area: str, *, limit: int | None = None) -> dict[str, Any]:
        q = urllib.parse.urlencode({"name": area.strip(), **({"limit": limit} if limit else {})})
        return self._request("GET", f"/area?{q}")

    def find_by_label(self, label: str, *, limit: int = 20) -> dict[str, Any]:
        q = urllib.parse.urlencode({"label": label.strip(), "limit": int(limit)})
        return self._request("GET", f"/by-label?{q}")

    def get_lesson(self, lesson_id: str) -> dict[str, Any]:
        lid = urllib.parse.quote(lesson_id.strip(), safe="")
        return self._request("GET", f"/lesson/{lid}")

    def call_mcp_tool(self, tool: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Invoke an ``spdd_*`` tool by name (HTTP parity with Guide MCP)."""
        name = (tool or "").strip()
        args = dict(arguments or {})
        if name not in SPDD_MCP_TOOLS:
            return {
                "ok": False,
                "error": f"unknown tool {name!r}; expected one of {SPDD_MCP_TOOLS}",
                "http_equivalent": _TOOL_HTTP,
            }
        if name == "spdd_workSubgraph":
            work_id = str(args.get("workId") or args.get("work_id") or "").strip()
            if not work_id:
                return {"ok": False, "error": "workId required", "tool": name}
            out = self.work_subgraph(work_id)
        elif name == "spdd_projectionStats":
            out = self.projection_stats()
        elif name == "spdd_areaLessons":
            area = str(args.get("area") or "").strip()
            if not area:
                return {"ok": False, "error": "area required", "tool": name}
            out = self.area_lessons(area, limit=args.get("limit"))
        elif name == "spdd_findByLabel":
            label = str(args.get("label") or "").strip()
            if not label:
                return {"ok": False, "error": "label required", "tool": name}
            out = self.find_by_label(label, limit=int(args.get("limit") or 20))
        elif name == "spdd_getLesson":
            lesson_id = str(args.get("id") or args.get("lesson_id") or "").strip()
            if not lesson_id:
                return {"ok": False, "error": "id required", "tool": name}
            out = self.get_lesson(lesson_id)
        else:
            return {"ok": False, "error": f"unhandled tool {name}"}
        out["tool"] = name
        out["mcp_sse"] = f"{self.base_url}/sse"
        out["http_equivalent"] = _TOOL_HTTP.get(name, "")
        return out
