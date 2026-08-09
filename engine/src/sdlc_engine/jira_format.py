"""Jira description formatting: markdown ↔ ADF / wiki markup.

Jira Cloud REST v3 requires Atlassian Document Format (ADF) for `description`.
Plain markdown strings either fail create or render as unformatted blobs — the
main pain point when syncing from `requirements/milestones/ ## Jira`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Structured body from milestone fields
# ---------------------------------------------------------------------------


def build_jira_markdown(
    *,
    work_id: str,
    summary: str = "",
    description: str = "",
    acceptance: str = "",
    business_value: str = "",
    scope_in: str = "",
    scope_out: str = "",
    requirement_rel: str = "",
) -> str:
    """Compose a consistently structured markdown description for Jira."""
    parts: list[str] = []

    def _add(heading: str, body: str) -> None:
        body = (body or "").strip()
        if not body:
            return
        parts.append(f"## {heading}")
        parts.append("")
        parts.append(body)
        parts.append("")

    _add("Summary", summary)
    _add("Description", description)
    _add("Business value", business_value)
    _add("Scope in", scope_in)
    _add("Scope out", scope_out)
    _add("Acceptance criteria", acceptance)

    parts.append("## Traceability")
    parts.append("")
    parts.append(f"- Work ID: `{work_id}`")
    if requirement_rel:
        parts.append(f"- Requirement: `{requirement_rel}`")
    parts.append("")
    return "\n".join(parts).strip() + "\n"


def build_github_markdown(
    *,
    work_id: str,
    summary: str = "",
    description: str = "",
    acceptance: str = "",
    business_value: str = "",
    scope_in: str = "",
    scope_out: str = "",
    requirement_rel: str = "",
) -> str:
    """Compose a GFM issue body from structured requirement fields.

    GitHub Issues render markdown natively — no ADF conversion. Uses the same
    section layout as :func:`build_jira_markdown` so requirement docs can mirror
    ``## Jira`` and ``## GitHub`` subsections.
    """
    return build_jira_markdown(
        work_id=work_id,
        summary=summary,
        description=description,
        acceptance=acceptance,
        business_value=business_value,
        scope_in=scope_in,
        scope_out=scope_out,
        requirement_rel=requirement_rel,
    )


# ---------------------------------------------------------------------------
# Markdown → ADF
# ---------------------------------------------------------------------------


def _text_nodes(text: str) -> list[dict[str, Any]]:
    """Parse a single line of markdown into ADF inline text nodes."""
    if not text:
        return []
    nodes: list[dict[str, Any]] = []
    # Links, bold, italic, code — left-to-right scan
    token = re.compile(
        r"(`([^`]+)`)"
        r"|(\*\*([^*]+)\*\*)"
        r"|(\*([^*]+)\*)"
        r"|(\[([^\]]+)\]\(([^)]+)\))"
        r"|(_([^_]+)_)"
    )
    pos = 0
    for m in token.finditer(text):
        if m.start() > pos:
            nodes.append({"type": "text", "text": text[pos : m.start()]})
        if m.group(2) is not None:  # code
            nodes.append({"type": "text", "text": m.group(2), "marks": [{"type": "code"}]})
        elif m.group(4) is not None:  # **bold**
            nodes.append({"type": "text", "text": m.group(4), "marks": [{"type": "strong"}]})
        elif m.group(6) is not None:  # *italic*
            nodes.append({"type": "text", "text": m.group(6), "marks": [{"type": "em"}]})
        elif m.group(8) is not None:  # [label](url)
            nodes.append(
                {
                    "type": "text",
                    "text": m.group(8),
                    "marks": [{"type": "link", "attrs": {"href": m.group(9)}}],
                }
            )
        elif m.group(11) is not None:  # _italic_
            nodes.append({"type": "text", "text": m.group(11), "marks": [{"type": "em"}]})
        pos = m.end()
    if pos < len(text):
        nodes.append({"type": "text", "text": text[pos:]})
    # ADF disallows empty text nodes
    return [n for n in nodes if n.get("text") != ""]


def _paragraph(text: str) -> dict[str, Any]:
    content = _text_nodes(text.strip())
    if not content:
        # Empty paragraph still valid as hardBreak container — use a space.
        content = [{"type": "text", "text": " "}]
    return {"type": "paragraph", "content": content}


def _heading(level: int, text: str) -> dict[str, Any]:
    level = max(1, min(level, 6))
    content = _text_nodes(text.strip()) or [{"type": "text", "text": text.strip() or " "}]
    return {"type": "heading", "attrs": {"level": level}, "content": content}


def _code_block(text: str, language: str = "") -> dict[str, Any]:
    node: dict[str, Any] = {
        "type": "codeBlock",
        "content": [{"type": "text", "text": text.rstrip("\n") or " "}],
    }
    if language:
        node["attrs"] = {"language": language}
    return node


def _rule() -> dict[str, Any]:
    return {"type": "rule"}


def _list(items: list[tuple[str, str]], ordered: bool = False) -> dict[str, Any]:
    """items: list of (marker, text) where marker is '', 'todo', or 'done'."""
    list_items = []
    for marker, text in items:
        para = _paragraph(text)
        if marker == "todo":
            # Task items use taskList in newer ADF; keep bullet + [ ] prefix for compatibility.
            para = _paragraph(f"[ ] {text}")
        elif marker == "done":
            para = _paragraph(f"[x] {text}")
        list_items.append({"type": "listItem", "content": [para]})
    return {"type": "orderedList" if ordered else "bulletList", "content": list_items}


def markdown_to_adf(markdown: str) -> dict[str, Any]:
    """Convert a constrained markdown subset to Atlassian Document Format."""
    lines = (markdown or "").replace("\r\n", "\n").split("\n")
    content: list[dict[str, Any]] = []
    i = 0
    bullet_re = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")
    check_re = re.compile(r"^\[([ xX])\]\s+(.*)$")

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Fenced code
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            i += 1
            buf: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            content.append(_code_block("\n".join(buf), lang))
            continue

        # Horizontal rule
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            content.append(_rule())
            i += 1
            continue

        # Headings
        hm = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if hm:
            content.append(_heading(len(hm.group(1)), hm.group(2)))
            i += 1
            continue

        # Lists (bullet / ordered / checkbox)
        bm = bullet_re.match(line)
        if bm:
            ordered = bm.group(2)[-1] == "."
            items: list[tuple[str, str]] = []
            while i < len(lines):
                bm2 = bullet_re.match(lines[i])
                if not bm2:
                    break
                is_ord = bm2.group(2)[-1] == "."
                if is_ord != ordered:
                    break
                body = bm2.group(3)
                cm = check_re.match(body)
                if cm:
                    marker = "done" if cm.group(1).lower() == "x" else "todo"
                    items.append((marker, cm.group(2)))
                else:
                    items.append(("", body))
                i += 1
            content.append(_list(items, ordered=ordered))
            continue

        # Paragraph — gather consecutive non-empty, non-special lines
        buf = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i]
            ns = nxt.strip()
            if not ns:
                break
            if (
                ns.startswith("#")
                or ns.startswith("```")
                or bullet_re.match(nxt)
                or re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", ns)
            ):
                break
            buf.append(ns)
            i += 1
        content.append(_paragraph(" ".join(buf)))

    if not content:
        content = [_paragraph(" ")]

    return {"type": "doc", "version": 1, "content": content}


# ---------------------------------------------------------------------------
# Markdown → Jira wiki markup (API v2)
# ---------------------------------------------------------------------------


def markdown_to_wiki(markdown: str) -> str:
    """Convert constrained markdown to Jira wiki markup for REST API v2."""
    lines = (markdown or "").replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    bullet_re = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")
    in_code = False
    code_buf: list[str] = []

    def _inline_wiki(text: str) -> str:
        text = re.sub(r"`([^`]+)`", r"{{\1}}", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"*\1*", text)
        text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"_\1_", text)
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"[\1|\2]", text)
        return text

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                lang = ""  # ignored for wiki
                out.append("{code" + (f":{lang}" if lang else "") + "}")
                out.extend(code_buf)
                out.append("{code}")
                in_code = False
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue
        if not stripped:
            out.append("")
            i += 1
            continue
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            out.append("----")
            i += 1
            continue
        hm = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if hm:
            level = min(len(hm.group(1)), 6)
            out.append(f"h{level}. {_inline_wiki(hm.group(2))}")
            i += 1
            continue
        bm = bullet_re.match(line)
        if bm:
            ordered = bm.group(2)[-1] == "."
            while i < len(lines) and bullet_re.match(lines[i]):
                bm2 = bullet_re.match(lines[i])
                assert bm2
                body = bm2.group(3)
                prefix = "#" if ordered else "*"
                cm = re.match(r"^\[([ xX])\]\s+(.*)$", body)
                if cm:
                    mark = "(x)" if cm.group(1).lower() == "x" else "( )"
                    out.append(f"{prefix} {mark} {_inline_wiki(cm.group(2))}")
                else:
                    out.append(f"{prefix} {_inline_wiki(body)}")
                i += 1
            continue
        out.append(_inline_wiki(stripped))
        i += 1
    return "\n".join(out).strip() + "\n"


# ---------------------------------------------------------------------------
# ADF → wiki markup (optional Server/DC shim)
# Prefer raw ADF for Cloud v3; convert only when description_format=wiki.
# Adapted from an external ADF upload helper — no product-specific keys/hosts.
# ---------------------------------------------------------------------------


def _wiki_apply_marks(text: str, marks: list) -> str:
    """Apply ADF marks to a text string, producing wiki markup."""
    for mark in marks or []:
        mt = mark.get("type", "")
        if mt == "strong":
            inner = text.strip()
            trailing = text[len(text.rstrip()) :]
            leading = text[: len(text) - len(text.lstrip())]
            text = f"{leading}*{inner}*{trailing}"
        elif mt == "em":
            inner = text.strip()
            trailing = text[len(text.rstrip()) :]
            leading = text[: len(text) - len(text.lstrip())]
            text = f"{leading}_{inner}_{trailing}"
        elif mt == "code":
            # Escape { } so wiki does not treat {param} as a macro.
            escaped = text.replace("{", r"\{").replace("}", r"\}")
            text = f"{{{{{escaped}}}}}"
        elif mt == "underline":
            text = f"+{text}+"
        elif mt == "strike":
            text = f"-{text}-"
        elif mt == "link":
            href = (mark.get("attrs") or {}).get("href", "")
            text = f"[{text}|{href}]" if href else text
    return text


def _adf_inline_wiki(node: dict) -> str:
    t = node.get("type", "")
    if t == "hardBreak":
        return "\n"
    if t == "text":
        return _wiki_apply_marks(node.get("text", ""), node.get("marks") or [])
    return "".join(_adf_inline_wiki(c) for c in node.get("content") or [])


def _para_segments_wiki(para_node: dict) -> list[str]:
    """Split a paragraph's inline content on hardBreaks."""
    segments: list[str] = []
    buf: list[str] = []
    for child in para_node.get("content") or []:
        if child.get("type") == "hardBreak":
            segments.append("".join(buf))
            buf = []
        else:
            buf.append(_adf_inline_wiki(child))
    if buf:
        segments.append("".join(buf))
    return [s for s in segments if s.strip()]


def _is_gwt_list_item(list_item_node: dict) -> bool:
    """True when a listItem paragraph uses hardBreaks (Given/When/Then pattern)."""
    for child in list_item_node.get("content") or []:
        if child.get("type") == "paragraph":
            if any(c.get("type") == "hardBreak" for c in child.get("content") or []):
                return True
    return False


def _adf_list_item_wiki(node: dict, marker: str, depth: int = 1) -> str:
    prefix = marker * depth
    lines: list[str] = []
    for child in node.get("content") or []:
        ct = child.get("type", "")
        if ct == "paragraph":
            text = "".join(_adf_inline_wiki(c) for c in child.get("content") or [])
            lines.append(f"{prefix} {text}")
        elif ct in ("bulletList", "orderedList"):
            sub_marker = "*" if ct == "bulletList" else "#"
            for sub_item in child.get("content") or []:
                lines.append(_adf_list_item_wiki(sub_item, sub_marker, depth + 1))
    return "\n".join(lines)


def _adf_bullet_list_to_wiki(node: dict, marker: str = "*") -> str:
    """
    Convert bulletList/orderedList to wiki.

    List items with hardBreaks (GWT) become numbered scenarios with sub-bullets:
      * *Scenario 1*
      ** *Given* ...
      ** *When* ...
      ** *Then* ...
    """
    items = node.get("content") or []
    scenario_num = 0
    lines: list[str] = []
    for item in items:
        if _is_gwt_list_item(item):
            scenario_num += 1
            lines.append(f"{marker} *Scenario {scenario_num}*")
            for child in item.get("content") or []:
                if child.get("type") == "paragraph":
                    for seg in _para_segments_wiki(child):
                        lines.append(f"{marker * 2} {seg}")
        else:
            lines.append(_adf_list_item_wiki(item, marker))
    return "\n".join(lines)


def _panel_to_wiki_section(content: list) -> str:
    """Render an ADF panel as bold-label lines (avoids table pipe escaping)."""
    lines: list[str] = []
    for child in content:
        if child.get("type") != "paragraph":
            lines.append(adf_to_wiki(child))
            continue
        inline_nodes = child.get("content") or []
        if (
            inline_nodes
            and inline_nodes[0].get("type") == "text"
            and any(m.get("type") == "strong" for m in inline_nodes[0].get("marks") or [])
        ):
            label = inline_nodes[0].get("text", "").rstrip(": ").strip()
            value = "".join(_adf_inline_wiki(c) for c in inline_nodes[1:]).strip()
            lines.append(f"*{label}:* {value}")
        else:
            lines.append("".join(_adf_inline_wiki(c) for c in inline_nodes))
    return "\n".join(lines)


def adf_to_wiki(node: Any) -> str:
    """Convert an ADF document/node tree to Atlassian wiki markup (Server/DC v2).

    This is an **optional shim**. Jira Cloud v3 should receive raw ADF via
    ``description_format=adf`` (default). Only call this when the operator
    explicitly chooses wiki output.
    """
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return str(node)

    t = node.get("type", "")
    content = node.get("content") or []

    if t == "doc":
        parts = [adf_to_wiki(c) for c in content]
        return "\n\n".join(p for p in parts if p.strip()) + ("\n" if parts else "")

    if t == "heading":
        level = int((node.get("attrs") or {}).get("level") or 1)
        level = max(1, min(level, 6))
        text = "".join(_adf_inline_wiki(c) for c in content)
        return f"h{level}. {text}"

    if t == "paragraph":
        return "".join(_adf_inline_wiki(c) for c in content)

    if t == "bulletList":
        return _adf_bullet_list_to_wiki(node, "*")

    if t == "orderedList":
        return _adf_bullet_list_to_wiki(node, "#")

    if t == "codeBlock":
        lang = (node.get("attrs") or {}).get("language") or ""
        text = "".join(c.get("text", "") for c in content)
        tag = f"code:{lang}" if lang else "code"
        return f"{{{tag}}}\n{text}\n{{code}}"

    if t == "panel":
        return _panel_to_wiki_section(content)

    if t == "blockquote":
        return "bq. " + "".join(adf_to_wiki(c) for c in content)

    if t == "rule":
        return "----"

    nested = [adf_to_wiki(c) for c in content]
    return "\n\n".join(p for p in nested if p.strip())


def load_adf_document(data: Any) -> dict[str, Any]:
    """Validate a parsed ADF object (version=1, type=doc)."""
    if not isinstance(data, dict):
        raise ValueError("ADF must be a JSON object")
    if data.get("version") != 1 or data.get("type") != "doc":
        raise ValueError(
            "ADF root must be {\"type\": \"doc\", \"version\": 1, ...}; "
            f"got type={data.get('type')!r} version={data.get('version')!r}"
        )
    if "content" not in data:
        raise ValueError("ADF doc requires a content array")
    return data


def load_adf_file(path: Path) -> dict[str, Any]:
    """Load and validate ADF JSON from a file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{path}': {exc}") from exc
    return load_adf_document(data)


# ---------------------------------------------------------------------------
# ADF → markdown (for pull)
# ---------------------------------------------------------------------------


def adf_to_markdown(doc: Any) -> str:
    """Best-effort ADF → markdown for writing back into milestone requirements."""
    if doc is None:
        return ""
    if isinstance(doc, str):
        return doc
    if not isinstance(doc, dict):
        return str(doc)
    content = doc.get("content") or []
    parts: list[str] = []

    def inline(nodes: list[dict] | None) -> str:
        if not nodes:
            return ""
        chunks: list[str] = []
        for n in nodes:
            t = n.get("type")
            if t == "text":
                text = n.get("text", "")
                marks = {m.get("type") for m in (n.get("marks") or [])}
                href = None
                for m in n.get("marks") or []:
                    if m.get("type") == "link":
                        href = (m.get("attrs") or {}).get("href")
                if "code" in marks:
                    text = f"`{text}`"
                if "strong" in marks:
                    text = f"**{text}**"
                if "em" in marks:
                    text = f"*{text}*"
                if href:
                    text = f"[{text}]({href})"
                chunks.append(text)
            elif t == "hardBreak":
                chunks.append("\n")
            elif t == "emoji":
                chunks.append((n.get("attrs") or {}).get("shortName", ""))
            elif "content" in n:
                chunks.append(inline(n.get("content")))
        return "".join(chunks)

    def walk(nodes: list[dict]) -> None:
        for n in nodes:
            t = n.get("type")
            if t == "paragraph":
                parts.append(inline(n.get("content")))
                parts.append("")
            elif t == "heading":
                level = int((n.get("attrs") or {}).get("level") or 1)
                parts.append("#" * level + " " + inline(n.get("content")))
                parts.append("")
            elif t == "bulletList":
                for item in n.get("content") or []:
                    text = inline((item.get("content") or [{}])[0].get("content"))
                    # flatten nested paragraphs lightly
                    if not text and item.get("content"):
                        text = " ".join(
                            inline(p.get("content"))
                            for p in item["content"]
                            if p.get("type") == "paragraph"
                        )
                    parts.append(f"- {text}".rstrip())
                parts.append("")
            elif t == "orderedList":
                for idx, item in enumerate(n.get("content") or [], 1):
                    text = ""
                    if item.get("content"):
                        text = " ".join(
                            inline(p.get("content"))
                            for p in item["content"]
                            if p.get("type") == "paragraph"
                        )
                    parts.append(f"{idx}. {text}".rstrip())
                parts.append("")
            elif t == "codeBlock":
                lang = (n.get("attrs") or {}).get("language") or ""
                parts.append(f"```{lang}".rstrip())
                parts.append(inline(n.get("content")))
                parts.append("```")
                parts.append("")
            elif t == "rule":
                parts.append("---")
                parts.append("")
            elif t == "blockquote":
                walk(n.get("content") or [])
            elif "content" in n:
                walk(n["content"])

    walk(content)
    # collapse excess blanks
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(parts)).strip()
    return text + ("\n" if text else "")
