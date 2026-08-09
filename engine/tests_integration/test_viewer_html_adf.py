"""Unit tests for html_to_adf and HTML↔ADF round-trip."""

from __future__ import annotations

import json
from pathlib import Path

from sdlc_engine.viewer.adf_html import adf_to_html
from sdlc_engine.viewer.html_adf import html_to_adf
from sdlc_engine.viewer.store import AdfStore


def test_empty_html() -> None:
    doc = html_to_adf("")
    assert doc["type"] == "doc"
    assert doc["version"] == 1


def test_paragraph_marks() -> None:
    doc = html_to_adf(
        "<p><strong>b</strong> <em>i</em> <code>c</code> "
        '<a href="https://example.com">l</a> <s>s</s> <u>u</u></p>'
    )
    texts = []
    for n in doc["content"][0]["content"]:
        if n.get("type") == "text":
            texts.append((n["text"], [m["type"] for m in n.get("marks") or []]))
    assert ("b", ["strong"]) in texts
    assert ("i", ["em"]) in texts
    assert ("c", ["code"]) in texts
    assert any(t[0] == "l" and "link" in t[1] for t in texts)


def test_heading_list_code_panel() -> None:
    html = """
    <h2>Title</h2>
    <ul><li><p>one</p></li><li><p>two</p></li></ul>
    <pre class="code-block" data-language="bash"><code>echo hi</code></pre>
    <div class="panel panel-info" data-panel-type="info"><p>note</p></div>
    <hr>
    <blockquote><p>q</p></blockquote>
    """
    doc = html_to_adf(html)
    types = [n["type"] for n in doc["content"]]
    assert "heading" in types
    assert "bulletList" in types
    assert "codeBlock" in types
    assert "panel" in types
    assert "rule" in types
    assert "blockquote" in types


def test_gwt_roundtrip() -> None:
    html = """
    <div class="gwt-block">
      <div class="gwt-scenario">
        <div class="gwt-line"><strong>Given </strong>x</div>
        <div class="gwt-line"><strong>When </strong>y</div>
        <div class="gwt-line"><strong>Then </strong>z</div>
      </div>
    </div>
    """
    doc = html_to_adf(html)
    assert doc["content"][0]["type"] == "bulletList"
    para = doc["content"][0]["content"][0]["content"][0]
    assert para["type"] == "paragraph"
    hardbreaks = sum(1 for n in para["content"] if n.get("type") == "hardBreak")
    assert hardbreaks == 2
    again = adf_to_html(doc)
    assert "Given" in again and "gwt-scenario" in again


def test_scenario_chrome_stripped_from_adf() -> None:
    html = """
    <div class="gwt-block">
      <div class="gwt-scenario">
        <div class="gwt-chrome" contenteditable="false">
          <button class="gwt-handle" type="button">⋮⋮</button>
          <button class="gwt-delete" type="button">×</button>
        </div>
        <div class="gwt-line"><strong>Given </strong>a</div>
        <div class="gwt-line"><strong>When </strong>b</div>
        <div class="gwt-line"><strong>Then </strong>c</div>
      </div>
    </div>
    """
    doc = html_to_adf(html)
    blob = json.dumps(doc)
    assert "gwt-chrome" not in blob
    assert "Given" in blob
    assert doc["content"][0]["type"] == "bulletList"


def test_multiple_scenarios_one_bullet_list() -> None:
    """Matches real Jira AC: one bulletList, each listItem = one Scenario pill."""
    html = """
    <h2>Acceptance Criteria</h2>
    <div class="gwt-block">
      <div class="gwt-scenario">
        <div class="gwt-line"><strong>Given </strong>a</div>
        <div class="gwt-line"><strong>When </strong>b</div>
        <div class="gwt-line"><strong>Then </strong>c</div>
      </div>
      <div class="gwt-scenario">
        <div class="gwt-line"><strong>Given </strong>d</div>
        <div class="gwt-line"><strong>When </strong>e</div>
        <div class="gwt-line"><strong>Then </strong>f</div>
      </div>
    </div>
    """
    doc = html_to_adf(html)
    lists = [n for n in doc["content"] if n.get("type") == "bulletList"]
    assert len(lists) == 1
    assert len(lists[0]["content"]) == 2
    again = adf_to_html(doc)
    assert again.count("gwt-scenario") == 2
    assert "Acceptance Criteria" in again


def test_table_and_image() -> None:
    html = """
    <table class="adf-table"><tbody>
      <tr><th><p>A</p></th><td><p>B</p></td></tr>
    </tbody></table>
    <figure class="media-single" data-layout="center">
      <img src="https://example.com/x.png" alt="x" />
    </figure>
    """
    doc = html_to_adf(html)
    types = [n["type"] for n in doc["content"]]
    assert "table" in types
    assert "mediaSingle" in types
    media = doc["content"][types.index("mediaSingle")]["content"][0]
    assert media["attrs"]["url"] == "https://example.com/x.png"


def test_html_adf_html_stable_for_rich_fixture() -> None:
    root = Path(__file__).resolve().parents[2]
    doc = AdfStore(root).load("ORCH-rich.adf.json")
    html1 = adf_to_html(doc)
    back = html_to_adf(html1)
    html2 = adf_to_html(back)
    # Supported subset should be stable enough for key markers
    for marker in ("ORCH Demo Ticket", "gwt-scenario", "adf-table", "media-single", "panel-info"):
        assert marker in html1
        assert marker in html2


def test_reject_empty_text_nodes_stripped() -> None:
    doc = html_to_adf("<p>hi</p>")
    for n in doc["content"][0].get("content") or []:
        if n.get("type") == "text":
            assert n["text"] != ""
