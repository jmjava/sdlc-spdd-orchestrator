"""Parse and write Work ID links across milestones, canvas, and registry."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .project import Project

_JIRA_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")
_GH_NUM_RE = re.compile(r"^#?(?P<n>\d+)$")


@dataclass
class WorkLinks:
    work_id: str
    milestone_req: Path | None = None
    planning_milestone: Path | None = None
    canvas: Path | None = None
    jira_key: str = ""
    jira_summary: str = ""
    jira_draft: bool = False
    github_number: str = ""
    github_url: str = ""
    github_title: str = ""
    canvas_source_issue: str = ""
    canvas_source_url: str = ""
    canvas_source_system: str = ""
    canvas_status: str = ""
    registry_status: str = ""
    registry_note: str = ""
    registry_jira: str = ""
    registry_github: str = ""
    issues: list[str] = field(default_factory=list)

    @property
    def has_real_jira(self) -> bool:
        return bool(self.jira_key) and _JIRA_KEY_RE.match(self.jira_key) is not None

    @property
    def has_github(self) -> bool:
        return bool(self.github_number)


def _section_body(text: str, heading: str) -> str:
    lines = text.splitlines()
    collecting = False
    body: list[str] = []
    for line in lines:
        if line.startswith(f"## {heading}"):
            collecting = True
            continue
        if collecting and line.startswith("## "):
            break
        if collecting:
            body.append(line)
    return "\n".join(body)


def _bullet_value(section: str, label: str) -> str:
    # Use [ \t]* (not \s*) after the colon so an empty value does not swallow the
    # next markdown bullet via a newline match.
    pattern = re.compile(
        rf"^[ \t]*(?:-[ \t]+)?{re.escape(label)}:[ \t]*(.*)$",
        re.IGNORECASE | re.MULTILINE,
    )
    m = pattern.search(section)
    return m.group(1).strip() if m else ""


def _normalize_jira_key(raw: str) -> tuple[str, bool]:
    key = raw.strip()
    if not key or key.upper() in {"TBD", "TODO", "NONE", "N/A"}:
        return "", True
    if _JIRA_KEY_RE.match(key):
        return key, False
    return key, True


def _normalize_github(raw: str) -> str:
    raw = raw.strip()
    if not raw or raw.upper() in {"TBD", "TODO", "NONE"}:
        return ""
    m = _GH_NUM_RE.match(raw)
    if m:
        return m.group("n")
    m = re.search(r"/issues/(\d+)", raw)
    if m:
        return m.group(1)
    return ""


def parse_milestone_requirement(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    jira = _section_body(text, "Jira")
    github = _section_body(text, "GitHub")
    jira_key, draft = _normalize_jira_key(_bullet_value(jira, "Key"))
    gh_num = _normalize_github(_bullet_value(github, "Number") or _bullet_value(github, "Issue"))
    return {
        "jira_key": jira_key,
        "jira_draft": "1" if draft or (not jira_key and jira.strip()) else "0",
        "jira_summary": _bullet_value(jira, "Summary"),
        "jira_type": _bullet_value(jira, "Issue type") or _bullet_value(jira, "Type"),
        "jira_labels": _bullet_value(jira, "Labels"),
        "jira_components": _bullet_value(jira, "Components"),
        "jira_description": _subsection(jira, "Description"),
        "jira_acceptance": _subsection(jira, "Acceptance criteria (Given/When/Then)")
        or _subsection(jira, "Acceptance criteria"),
        "jira_business_value": _subsection(jira, "Business value"),
        "jira_scope_in": _subsection(jira, "Scope in"),
        "jira_scope_out": _subsection(jira, "Scope out"),
        "github_number": gh_num,
        "github_title": _bullet_value(github, "Title"),
        "github_url": _bullet_value(github, "URL"),
        "github_labels": _bullet_value(github, "Labels"),
        "github_body": _subsection(github, "Body"),
        "github_description": _subsection(github, "Description"),
        "github_acceptance": _subsection(github, "Acceptance criteria (Given/When/Then)")
        or _subsection(github, "Acceptance criteria"),
        "github_business_value": _subsection(github, "Business value"),
        "github_scope_in": _subsection(github, "Scope in"),
        "github_scope_out": _subsection(github, "Scope out"),
        "summary": _section_body(text, "Summary").strip(),
    }


def _subsection(section: str, heading: str) -> str:
    lines = section.splitlines()
    collecting = False
    body: list[str] = []
    for line in lines:
        if line.startswith(f"### {heading}"):
            collecting = True
            continue
        if collecting and line.startswith("### "):
            break
        if collecting:
            body.append(line)
    return "\n".join(body).strip()


def set_milestone_subsection(path: Path, section: str, heading: str, body: str) -> bool:
    """Replace or create `### heading` body under `## section`. Returns True if changed."""
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    section_header = f"## {section}"
    sub_header = f"### {heading}"
    start = None
    end = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == section_header:
            start = i
            continue
        if start is not None and i > start and line.startswith("## "):
            end = i
            break
    if start is None:
        addition = ["", section_header, "", sub_header, "", body.rstrip(), ""]
        path.write_text(text.rstrip() + "\n" + "\n".join(addition), encoding="utf-8")
        return True
    sub_start = None
    sub_end = end
    for i in range(start + 1, end):
        if lines[i].strip() == sub_header:
            sub_start = i
            continue
        if sub_start is not None and i > sub_start and lines[i].startswith("### "):
            sub_end = i
            break
    new_block = [sub_header, ""] + (body.rstrip().splitlines() or [""]) + [""]
    if sub_start is None:
        # insert before end of section
        insert_at = end
        while insert_at > start + 1 and lines[insert_at - 1].strip() == "":
            insert_at -= 1
        lines[insert_at:insert_at] = new_block
    else:
        lines[sub_start:sub_end] = new_block
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def parse_canvas_metadata(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    meta = _section_body(text, "Metadata")
    return {
        "status": _bullet_value(meta, "Status"),
        "source_system": _bullet_value(meta, "Source System"),
        "source_issue": _bullet_value(meta, "Source Issue"),
        "source_url": _bullet_value(meta, "Source URL"),
        "related_pr": _bullet_value(meta, "Related PR"),
        "milestone": _bullet_value(meta, "Milestone"),
        "roadmap": _bullet_value(meta, "Roadmap"),
        "work_id": _bullet_value(meta, "Work ID"),
        "work_type": _bullet_value(meta, "Work Type"),
        "title": _canvas_title(text),
    }


def _canvas_title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# REASONS Canvas:"):
            parts = line.split(" - ", 1)
            return parts[1].strip() if len(parts) == 2 else line.removeprefix("# REASONS Canvas:").strip()
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def note_token(note: str, prefix: str) -> str:
    for tok in note.split():
        if tok.startswith(f"{prefix}:"):
            return tok.split(":", 1)[1]
    return ""


def upsert_note_token(note: str, prefix: str, value: str) -> str:
    tokens = [t for t in note.split() if not t.startswith(f"{prefix}:")]
    if value:
        tokens.insert(0, f"{prefix}:{value}")
    return " ".join(tokens).strip()


def find_planning_milestone(project: Project, work_id: str) -> Path | None:
    for path in sorted(project.root.glob("milestone-*.md")):
        try:
            if work_id in path.read_text(encoding="utf-8"):
                return path
        except OSError:
            continue
    return None


def collect_links(project: Project, work_id: str, registry_row=None) -> WorkLinks:
    req = project.milestone_path(work_id)
    canvas = project.canvas_path(work_id)
    links = WorkLinks(
        work_id=work_id,
        milestone_req=req if req.is_file() else None,
        planning_milestone=find_planning_milestone(project, work_id),
        canvas=canvas if canvas.is_file() else None,
    )
    if links.milestone_req:
        parsed = parse_milestone_requirement(links.milestone_req)
        links.jira_key = parsed.get("jira_key", "")
        links.jira_summary = parsed.get("jira_summary", "")
        links.jira_draft = parsed.get("jira_draft") == "1" or not links.has_real_jira
        links.github_number = parsed.get("github_number", "")
        links.github_url = parsed.get("github_url", "")
        links.github_title = parsed.get("github_title", "")
        if links.milestone_req.is_file() and "## Jira" in links.milestone_req.read_text(encoding="utf-8"):
            if not links.has_real_jira:
                links.jira_draft = True
    if links.canvas:
        meta = parse_canvas_metadata(links.canvas)
        links.canvas_status = meta.get("status", "")
        links.canvas_source_issue = meta.get("source_issue", "")
        links.canvas_source_url = meta.get("source_url", "")
        links.canvas_source_system = meta.get("source_system", "")
    if registry_row is not None:
        links.registry_status = registry_row.status
        links.registry_note = registry_row.note
        links.registry_jira = note_token(registry_row.note, "jira")
        links.registry_github = note_token(registry_row.note, "github")
    return links


def set_milestone_bullet(path: Path, section: str, label: str, value: str) -> bool:
    """Set `- Label: value` under ## section; create section/bullet if missing. Returns True if changed."""
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    section_header = f"## {section}"
    start = None
    end = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == section_header:
            start = i
            continue
        if start is not None and i > start and line.startswith("## "):
            end = i
            break
    bullet_re = re.compile(rf"^(\s*(?:-\s+)?){re.escape(label)}:\s*(.*)$", re.IGNORECASE)
    if start is None:
        # append section
        addition = ["", section_header, "", f"- {label}: {value}", ""]
        path.write_text(text.rstrip() + "\n" + "\n".join(addition), encoding="utf-8")
        return True
    for i in range(start + 1, end):
        m = bullet_re.match(lines[i])
        if m:
            new_line = f"{m.group(1)}{label}: {value}"
            if lines[i] == new_line:
                return False
            lines[i] = new_line
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return True
    # insert bullet after header
    insert_at = start + 1
    while insert_at < end and lines[insert_at].strip() == "":
        insert_at += 1
    lines.insert(insert_at, f"- {label}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def set_canvas_metadata_bullet(path: Path, label: str, value: str) -> bool:
    return set_milestone_bullet(path, "Metadata", label, value)


def ensure_github_section(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    if re.search(r"^## GitHub\s*$", text, re.MULTILINE):
        return False
    block = (
        "\n## GitHub\n\n"
        "Create the issue in GitHub UI, then set **Number** (and matching "
        "``github_number`` frontmatter when used) and commit.\n\n"
        "- Number: TBD\n"
        "- Title: \n"
        "- Labels: \n"
        "- URL: \n"
        "\n"
        "### Description\n"
        "\n"
        "### Acceptance criteria\n"
        "\n"
        "- [ ] …\n"
    )
    path.write_text(text.rstrip() + "\n" + block, encoding="utf-8")
    return True


def set_milestone_frontmatter_field(path: Path, field: str, value: str) -> bool:
    """Set a YAML frontmatter field when `---` block is present. Returns True if changed."""
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False
    fm = text[3:end]
    rest = text[end + 4 :]
    pattern = re.compile(rf"^{re.escape(field)}:\s*.*$", re.MULTILINE)
    quoted = json_escape_yaml(value)
    new_line = f"{field}: {quoted}"
    if pattern.search(fm):
        new_fm = pattern.sub(new_line, fm, count=1)
        changed = new_fm != fm
    else:
        new_fm = fm.rstrip() + "\n" + new_line + "\n"
        changed = True
    if not changed:
        return False
    path.write_text("---" + new_fm + "---" + rest, encoding="utf-8")
    return True


def json_escape_yaml(value: str) -> str:
    """Quote a scalar for YAML frontmatter."""
    v = (value or "").replace("\\", "\\\\").replace('"', '\\"')
    return f'"{v}"'


def ensure_jira_section(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    if re.search(r"^## Jira\s*$", text, re.MULTILINE):
        return False
    block = (
        "\n## Jira\n\n"
        "Draft for issue creation — paste into Jira UI, MCP, or approved API.\n"
        "After create, set **Key** and commit.\n\n"
        "- Key: TBD\n"
        "- Issue type: Story\n"
        "- Summary: \n"
        "- Labels: \n"
    )
    path.write_text(text.rstrip() + "\n" + block, encoding="utf-8")
    return True
