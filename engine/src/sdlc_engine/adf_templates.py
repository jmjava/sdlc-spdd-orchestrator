"""ADF template library: combo manifests, part assembly, markdown→ADF render."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .jira_format import adf_to_markdown, markdown_to_adf
from .links import parse_milestone_requirement
from .project import Project

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")

_WORK_TYPE_LABEL = {
    "feature": "Feature",
    "feat": "Feature",
    "spike": "Spike",
    "bug": "Bugfix",
    "bugfix": "Bugfix",
    "chore": "Chore",
    "refactor": "Refactor",
    "doc": "Doc",
    "test": "Test",
}


@dataclass(frozen=True)
class ComboManifest:
    id: str
    title: str
    parts: tuple[str, ...]
    description: str = ""
    work_types: tuple[str, ...] = ()
    path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "work_types": list(self.work_types),
            "parts": list(self.parts),
            "path": self.path,
        }


@dataclass
class RenderResult:
    work_id: str
    combo_id: str
    markdown: str
    adf: dict[str, Any]
    variables: dict[str, str] = field(default_factory=dict)
    output_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": True,
            "work_id": self.work_id,
            "combo_id": self.combo_id,
            "markdown": self.markdown,
            "adf": self.adf,
            "variables": self.variables,
            "output_path": self.output_path,
        }


class TemplateError(ValueError):
    """Invalid combo, missing part, or schema validation failure."""


def orchestrator_templates_root() -> Path:
    """Locate orchestrator repo root that owns ``templates/adf``."""
    here = Path(__file__).resolve()
    # engine/src/sdlc_engine/adf_templates.py → repo root is parents[3]
    candidate = here.parents[3]
    if (candidate / "templates" / "adf").is_dir():
        return candidate
    env = os.environ.get("SDLC_ORCHESTRATOR_ROOT", "").strip()
    if env:
        p = Path(env).expanduser().resolve()
        if (p / "templates" / "adf").is_dir():
            return p
    raise FileNotFoundError(
        "Could not locate templates/adf. Set SDLC_ORCHESTRATOR_ROOT "
        "or run from an editable install of this repo."
    )


def default_library_root() -> Path:
    """Orchestrator ``templates/adf`` stay-set (not consumer project root)."""
    return orchestrator_templates_root() / "templates" / "adf"


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TemplateError(f"invalid JSON in {path}: {exc}") from exc


def _schema_type_ok(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    return True


def validate_against_schema(data: Any, schema: dict[str, Any], *, path: str = "$") -> list[str]:
    """Tiny JSON Schema subset validator (no external dependency)."""
    errors: list[str] = []
    if "const" in schema and data != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {data!r}")
    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _schema_type_ok(data, expected_type):
        errors.append(f"{path}: expected type {expected_type}, got {type(data).__name__}")
        return errors
    if isinstance(data, str):
        min_len = schema.get("minLength")
        if isinstance(min_len, int) and len(data) < min_len:
            errors.append(f"{path}: string shorter than minLength {min_len}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.search(pattern, data):
            errors.append(f"{path}: string does not match pattern {pattern}")
    if isinstance(data, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(data) < min_items:
            errors.append(f"{path}: array shorter than minItems {min_items}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for i, item in enumerate(data):
                errors.extend(validate_against_schema(item, item_schema, path=f"{path}[{i}]"))
    if isinstance(data, dict):
        required = schema.get("required") or []
        for key in required:
            if key not in data:
                errors.append(f"{path}: missing required property {key!r}")
        props = schema.get("properties") or {}
        for key, sub in props.items():
            if key in data and isinstance(sub, dict):
                errors.extend(validate_against_schema(data[key], sub, path=f"{path}.{key}"))
    return errors


def bind_variables(text: str, variables: dict[str, str]) -> str:
    """Replace ``{{name}}`` placeholders; unknown names become empty string."""

    def _repl(match: re.Match[str]) -> str:
        return variables.get(match.group(1), "")

    return _PLACEHOLDER_RE.sub(_repl, text)


def _excerpt(path: Path, *, max_chars: int = 1200) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _section_from_markdown(text: str, heading: str) -> str:
    """Return body under ``## heading`` (first match)."""
    lines = text.splitlines()
    collecting = False
    body: list[str] = []
    target = f"## {heading}".lower()
    for line in lines:
        if line.strip().lower() == target:
            collecting = True
            continue
        if collecting and line.startswith("## "):
            break
        if collecting:
            body.append(line)
    return "\n".join(body).strip()


class AdfTemplateLibrary:
    """Load combo manifests + parts from ``templates/adf``."""

    def __init__(self, library_root: Path | str | None = None) -> None:
        self.root = Path(library_root or default_library_root()).expanduser().resolve()
        self.parts_dir = self.root / "parts"
        self.combos_dir = self.root / "combos"
        self.schemas_dir = self.root / "schemas"

    def combo_schema(self) -> dict[str, Any]:
        path = self.schemas_dir / "combo-manifest.schema.json"
        if not path.is_file():
            raise TemplateError(f"missing combo schema: {path}")
        data = _load_json(path)
        if not isinstance(data, dict):
            raise TemplateError("combo schema must be an object")
        return data

    def adf_schema(self) -> dict[str, Any]:
        path = self.schemas_dir / "adf-doc.schema.json"
        if not path.is_file():
            raise TemplateError(f"missing ADF schema: {path}")
        data = _load_json(path)
        if not isinstance(data, dict):
            raise TemplateError("ADF schema must be an object")
        return data

    def load_combo(self, combo_id: str) -> ComboManifest:
        cid = (combo_id or "").strip()
        if not cid:
            raise TemplateError("combo id is required")
        path = self.combos_dir / f"{cid}.json"
        if not path.is_file():
            raise TemplateError(f"unknown combo: {cid}")
        raw = _load_json(path)
        if not isinstance(raw, dict):
            raise TemplateError(f"combo {cid} must be a JSON object")
        errors = validate_against_schema(raw, self.combo_schema())
        if errors:
            raise TemplateError(f"combo {cid} failed schema: {'; '.join(errors)}")
        parts = tuple(str(p) for p in (raw.get("parts") or []))
        for part_id in parts:
            part_path = self.parts_dir / f"{part_id}.md"
            if not part_path.is_file():
                raise TemplateError(f"combo {cid} references missing part: {part_id}")
        return ComboManifest(
            id=str(raw["id"]),
            title=str(raw["title"]),
            description=str(raw.get("description") or ""),
            work_types=tuple(str(x) for x in (raw.get("work_types") or [])),
            parts=parts,
            path=str(path),
        )

    def list_combos(self) -> list[ComboManifest]:
        if not self.combos_dir.is_dir():
            return []
        combos: list[ComboManifest] = []
        for path in sorted(self.combos_dir.glob("*.json")):
            combos.append(self.load_combo(path.stem))
        return combos

    def load_part(self, part_id: str) -> str:
        path = self.parts_dir / f"{part_id}.md"
        if not path.is_file():
            raise TemplateError(f"missing part: {part_id}")
        return path.read_text(encoding="utf-8")

    def collect_variables(
        self,
        project: Project,
        work_id: str,
        *,
        overrides: dict[str, str] | None = None,
        work_type: str = "",
    ) -> dict[str, str]:
        wid = (work_id or "").strip()
        if not wid:
            raise TemplateError("work_id is required")
        req_path = project.milestone_path(wid)
        parsed = parse_milestone_requirement(req_path) if req_path.is_file() else {}
        req_text = req_path.read_text(encoding="utf-8") if req_path.is_file() else ""
        analysis_path = project.analysis_path(wid)
        canvas_path = project.canvas_path(wid)
        progress_path = project.progress_log_path(wid)
        progress_excerpt = ""
        if progress_path.is_file():
            progress_excerpt = Project.ledger_section_for_work(
                progress_path.read_text(encoding="utf-8"), wid
            )
            if len(progress_excerpt) > 1200:
                progress_excerpt = progress_excerpt[:1199].rstrip() + "…"

        inferred_type = work_type.strip().lower()
        if not inferred_type:
            prefix = wid.split("-", 1)[0].lower()
            inferred_type = {
                "feat": "feature",
                "bug": "bug",
                "spike": "spike",
                "chore": "chore",
                "ref": "refactor",
                "doc": "doc",
                "test": "test",
            }.get(prefix, "feature")

        summary = (
            (parsed.get("jira_summary") or parsed.get("summary") or "").strip()
            or _section_from_markdown(req_text, "Summary")
            or wid
        )
        description = (
            (parsed.get("jira_description") or "").strip()
            or _section_from_markdown(req_text, "Motivation")
            or _section_from_markdown(req_text, "Description")
            or summary
        )
        acceptance = (
            (parsed.get("jira_acceptance") or "").strip()
            or _section_from_markdown(req_text, "Acceptance Criteria")
            or _section_from_markdown(req_text, "Acceptance criteria")
            or "(none captured yet)"
        )
        scope_out = (
            (parsed.get("jira_scope_out") or "").strip()
            or _section_from_markdown(req_text, "Non-Goals")
            or _section_from_markdown(req_text, "Non-goals")
            or "(none)"
        )
        business_value = (
            (parsed.get("jira_business_value") or "").strip()
            or _section_from_markdown(req_text, "Business value")
            or "(see requirement)"
        )
        scope_in = (
            (parsed.get("jira_scope_in") or "").strip()
            or _section_from_markdown(req_text, "Scope in")
            or "(see acceptance criteria)"
        )

        variables: dict[str, str] = {
            "work_id": wid,
            "work_type": inferred_type,
            "work_type_label": _WORK_TYPE_LABEL.get(inferred_type, inferred_type.title()),
            "summary": " ".join(summary.split()),
            "description": description.strip() or summary,
            "acceptance": acceptance.strip() or "(none)",
            "business_value": business_value.strip() or "(none)",
            "scope_in": scope_in.strip() or "(none)",
            "scope_out": scope_out.strip() or "(none)",
            "requirement_rel": (
                f"requirements/milestones/{wid}.md" if req_path.is_file() else "(missing)"
            ),
            "analysis_rel": (
                f"spdd/analysis/{wid}-analysis.md" if analysis_path.is_file() else "(missing)"
            ),
            "canvas_rel": (
                str(canvas_path.relative_to(project.root))
                if canvas_path.is_file()
                else "(missing)"
            ),
            "analysis_excerpt": _excerpt(analysis_path),
            "canvas_excerpt": _excerpt(canvas_path),
            "progress_excerpt": progress_excerpt or "(none)",
            "title": " ".join(summary.split())[:255] or wid,
        }
        if overrides:
            for key, value in overrides.items():
                if key:
                    variables[str(key)] = str(value)
        return variables

    def assemble_markdown(self, combo: ComboManifest, variables: dict[str, str]) -> str:
        chunks: list[str] = []
        for part_id in combo.parts:
            raw = self.load_part(part_id)
            chunks.append(bind_variables(raw, variables).strip())
        return "\n\n".join(c for c in chunks if c).strip() + "\n"

    def validate_adf(self, doc: dict[str, Any]) -> list[str]:
        return validate_against_schema(doc, self.adf_schema())

    def render(
        self,
        project: Project,
        work_id: str,
        combo_id: str,
        *,
        overrides: dict[str, str] | None = None,
        work_type: str = "",
        output: Path | str | None = None,
    ) -> RenderResult:
        combo = self.load_combo(combo_id)
        variables = self.collect_variables(
            project, work_id, overrides=overrides, work_type=work_type or ""
        )
        markdown = self.assemble_markdown(combo, variables)
        adf = markdown_to_adf(markdown)
        errors = self.validate_adf(adf)
        if errors:
            raise TemplateError(f"rendered ADF failed schema: {'; '.join(errors)}")
        # Round-trip sanity: markdown preview stays non-empty
        preview = adf_to_markdown(adf).strip()
        if not preview:
            raise TemplateError("rendered ADF produced empty markdown preview")

        out_path = ""
        if output is not None:
            dest = Path(output)
            if not dest.is_absolute():
                dest = project.root / dest
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(adf, indent=2) + "\n", encoding="utf-8")
            out_path = str(dest)

        return RenderResult(
            work_id=work_id,
            combo_id=combo.id,
            markdown=markdown,
            adf=adf,
            variables=variables,
            output_path=out_path,
        )

    def suggest_combo(self, work_id: str, work_type: str = "") -> str:
        inferred = (work_type or "").strip().lower()
        if not inferred:
            prefix = (work_id or "").split("-", 1)[0].lower()
            inferred = {
                "feat": "feature",
                "bug": "bug",
                "spike": "spike",
            }.get(prefix, "feature")
        for combo in self.list_combos():
            if inferred in {t.lower() for t in combo.work_types} or combo.id == inferred:
                return combo.id
        return "feature"
