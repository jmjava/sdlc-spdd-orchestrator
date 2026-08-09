"""Unit tests for adf_to_html."""

from __future__ import annotations

from pathlib import Path

import pytest

from sdlc_engine.viewer.adf_html import adf_to_html
from sdlc_engine.viewer.store import AdfStore


def test_empty_doc() -> None:
    html = adf_to_html({"type": "doc", "version": 1, "content": []})
    assert "<p" in html


def test_top_level_block_indexes() -> None:
    doc = {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "heading", "attrs": {"level": 1}, "content": [{"type": "text", "text": "A"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "B"}]},
        ],
    }
    html = adf_to_html(doc)
    assert 'data-block-index="0"' in html
    assert 'data-block-index="1"' in html


def test_headings_marks_escape() -> None:
    doc = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": "Title <script>"}],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "bold", "marks": [{"type": "strong"}]},
                    {"type": "text", "text": " "},
                    {"type": "text", "text": "em", "marks": [{"type": "em"}]},
                    {"type": "text", "text": " "},
                    {"type": "text", "text": "code", "marks": [{"type": "code"}]},
                    {"type": "text", "text": " "},
                    {
                        "type": "text",
                        "text": "link",
                        "marks": [{"type": "link", "attrs": {"href": "https://example.com"}}],
                    },
                    {"type": "text", "text": " "},
                    {"type": "text", "text": "strike", "marks": [{"type": "strike"}]},
                    {"type": "text", "text": " "},
                    {"type": "text", "text": "under", "marks": [{"type": "underline"}]},
                ],
            },
        ],
    }
    html = adf_to_html(doc)
    assert "Title &lt;script&gt;" in html and "<h1" in html
    assert "<strong>bold</strong>" in html
    assert "<em>em</em>" in html
    assert "<code>code</code>" in html
    assert 'href="https://example.com"' in html
    assert "<s>strike</s>" in html
    assert "<u>under</u>" in html


def test_panel_code_blockquote_rule() -> None:
    doc = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "panel",
                "attrs": {"panelType": "warning"},
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Careful"}]}],
            },
            {
                "type": "codeBlock",
                "attrs": {"language": "python"},
                "content": [{"type": "text", "text": "print(1)"}],
            },
            {
                "type": "blockquote",
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": "q"}]}],
            },
            {"type": "rule"},
        ],
    }
    html = adf_to_html(doc)
    assert 'data-panel-type="warning"' in html
    assert "Careful" in html
    assert 'data-language="python"' in html
    assert "print(1)" in html
    assert "<blockquote" in html
    assert "<hr" in html


def test_gwt_scenarios() -> None:
    doc = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {"type": "text", "text": "Given a file", "marks": [{"type": "strong"}]},
                                    {"type": "hardBreak"},
                                    {"type": "text", "text": "When loaded", "marks": [{"type": "strong"}]},
                                    {"type": "hardBreak"},
                                    {"type": "text", "text": "Then shown", "marks": [{"type": "strong"}]},
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }
    html = adf_to_html(doc)
    assert "gwt-block" in html
    assert "gwt-scenario" in html
    assert "Given a file" in html
    assert "<ul>" not in html


def test_table_and_image() -> None:
    doc = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "table",
                "content": [
                    {
                        "type": "tableRow",
                        "content": [
                            {
                                "type": "tableHeader",
                                "content": [
                                    {"type": "paragraph", "content": [{"type": "text", "text": "H"}]}
                                ],
                            },
                            {
                                "type": "tableCell",
                                "content": [
                                    {"type": "paragraph", "content": [{"type": "text", "text": "C"}]}
                                ],
                            },
                        ],
                    }
                ],
            },
            {
                "type": "mediaSingle",
                "attrs": {"layout": "center"},
                "content": [
                    {
                        "type": "media",
                        "attrs": {
                            "type": "external",
                            "url": "https://example.com/a.png",
                            "alt": "a",
                        },
                    }
                ],
            },
        ],
    }
    html = adf_to_html(doc)
    assert "<table" in html
    assert "<th>" in html
    assert "<td>" in html
    assert 'src="https://example.com/a.png"' in html


def test_unknown_node_warns() -> None:
    warnings: list[str] = []
    doc = {
        "type": "doc",
        "version": 1,
        "content": [{"type": "futureNode", "content": []}],
    }
    adf_to_html(doc, collect_warnings=warnings)
    assert any("futureNode" in w for w in warnings)


def test_nested_lists() -> None:
    doc = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {"type": "paragraph", "content": [{"type": "text", "text": "outer"}]},
                            {
                                "type": "bulletList",
                                "content": [
                                    {
                                        "type": "listItem",
                                        "content": [
                                            {
                                                "type": "paragraph",
                                                "content": [{"type": "text", "text": "inner"}],
                                            }
                                        ],
                                    }
                                ],
                            },
                        ],
                    }
                ],
            }
        ],
    }
    html = adf_to_html(doc)
    assert "outer" in html and "inner" in html
    assert html.count("<ul") == 2


def test_rich_fixture_renders() -> None:
    root = Path(__file__).resolve().parents[2]
    doc = AdfStore(root).load("ORCH-rich.adf.json")
    html = adf_to_html(doc)
    assert "gwt-scenario" in html
    assert "adf-table" in html
    assert "media-single" in html
    assert "panel-info" in html


def test_root_must_be_doc() -> None:
    with pytest.raises(ValueError):
        adf_to_html({"type": "paragraph"})
