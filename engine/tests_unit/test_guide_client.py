"""Unit tests for GuideClient (HTTP parity with spdd_* MCP tools)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from sdlc_engine.guide_client import GuideClient, SPDD_MCP_TOOLS


def test_spdd_mcp_tools_list() -> None:
    assert "spdd_workSubgraph" in SPDD_MCP_TOOLS
    assert "spdd_getLesson" in SPDD_MCP_TOOLS


def test_call_mcp_work_subgraph() -> None:
    client = GuideClient("http://guide.test")
    body = json.dumps({"found": True, "pitfalls": []}).encode()

    class Resp:
        status = 200

        def read(self):
            return body

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    with patch("sdlc_engine.guide_client.urllib.request.urlopen", return_value=Resp()):
        out = client.call_mcp_tool("spdd_workSubgraph", {"workId": "FEAT-001-x"})
    assert out["ok"] is True
    assert out["tool"] == "spdd_workSubgraph"
    assert out["data"]["found"] is True


def test_call_mcp_get_lesson() -> None:
    client = GuideClient("http://guide.test")
    marker = "ROUNDTRIP-MARKER-42"
    body = json.dumps({"id": "pitfall:W:engine:test", "body": marker}).encode()

    class Resp:
        status = 200

        def read(self):
            return body

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    with patch("sdlc_engine.guide_client.urllib.request.urlopen", return_value=Resp()):
        out = client.call_mcp_tool("spdd_getLesson", {"id": "pitfall:W:engine:test"})
    assert out["ok"] is True
    assert marker in out["data"]["body"]


def test_call_mcp_unknown_tool() -> None:
    client = GuideClient("http://guide.test")
    out = client.call_mcp_tool("spdd_nope", {})
    assert out["ok"] is False
    assert "unknown tool" in out["error"]


def test_project_load_posts_root_path() -> None:
    client = GuideClient("http://guide.test")
    captured: dict = {}

    def fake_urlopen(req, timeout=30):
        captured["url"] = req.full_url
        captured["data"] = req.data
        resp = MagicMock()
        resp.status = 200
        resp.read.return_value = b'{"workIds":1}'
        resp.__enter__ = lambda s: resp
        resp.__exit__ = lambda s, *a: False
        return resp

    with patch("sdlc_engine.guide_client.urllib.request.urlopen", side_effect=fake_urlopen):
        out = client.project_load("/tmp/project")
    assert out["ok"] is True
    assert "spdd-projection/load" in captured["url"]
    assert b"/tmp/project" in captured["data"]
