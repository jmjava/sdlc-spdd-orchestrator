"""ADF template library: combos, schema validation, render pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sdlc_engine.adf_templates import (
    AdfTemplateLibrary,
    TemplateError,
    bind_variables,
    validate_against_schema,
)
from sdlc_engine.cli import main
from sdlc_engine.project import Project


def test_stock_combos_validate() -> None:
    lib = AdfTemplateLibrary()
    combos = lib.list_combos()
    ids = {c.id for c in combos}
    assert {"feature", "spike", "bug"} <= ids
    for combo in combos:
        loaded = lib.load_combo(combo.id)
        assert loaded.parts
        for part_id in loaded.parts:
            assert (lib.parts_dir / f"{part_id}.md").is_file()


def test_combo_manifest_schema_rejects_bad() -> None:
    lib = AdfTemplateLibrary()
    schema = lib.combo_schema()
    errors = validate_against_schema({"title": "x"}, schema)
    assert any("id" in e for e in errors)


def test_bind_variables_and_unknown_empty() -> None:
    out = bind_variables("Hi {{name}} / {{missing}}!", {"name": "Ada"})
    assert out == "Hi Ada / !"


def test_render_feature_from_milestone(tmp_path: Path) -> None:
    root = tmp_path
    (root / "requirements" / "milestones").mkdir(parents=True)
    work_id = "FEAT-900-template-demo"
    (root / "requirements" / "milestones" / f"{work_id}.md").write_text(
        """# Requirement

## Summary

Ship ADF templates from planning.

## Motivation

Operators need consistent Jira docs.

## Acceptance Criteria

- Given a Work ID
- When template render runs
- Then ADF validates

## Non-Goals

- Auto-push to Jira

## Jira

- Key: TBD
- Issue type: Story
- Summary: Ship ADF templates from planning
""",
        encoding="utf-8",
    )
    lib = AdfTemplateLibrary()
    result = lib.render(Project.resolve(root), work_id, "feature")
    assert result.adf["type"] == "doc"
    assert result.adf["version"] == 1
    assert result.adf["content"]
    blob = json.dumps(result.adf)
    assert "Ship ADF templates" in blob
    assert work_id in blob
    assert "Traceability" in result.markdown
    assert lib.validate_adf(result.adf) == []


def test_render_writes_output(tmp_path: Path) -> None:
    root = tmp_path
    (root / "requirements" / "milestones").mkdir(parents=True)
    work_id = "BUG-901-template-bug"
    (root / "requirements" / "milestones" / f"{work_id}.md").write_text(
        "## Summary\n\nFix the thing.\n",
        encoding="utf-8",
    )
    out = root / "adf" / f"{work_id}.adf.json"
    lib = AdfTemplateLibrary()
    result = lib.render(
        Project.resolve(root),
        work_id,
        "bug",
        output=out,
    )
    assert out.is_file()
    assert result.output_path == str(out)
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["type"] == "doc"


def test_suggest_combo() -> None:
    lib = AdfTemplateLibrary()
    assert lib.suggest_combo("SPIKE-089-x") == "spike"
    assert lib.suggest_combo("BUG-001-y") == "bug"
    assert lib.suggest_combo("FEAT-001-z") == "feature"


def test_unknown_combo_raises() -> None:
    lib = AdfTemplateLibrary()
    with pytest.raises(TemplateError, match="unknown combo"):
        lib.load_combo("nope-combo")


def test_cli_template_list_and_render(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "requirements" / "milestones").mkdir(parents=True)
    work_id = "SPIKE-902-cli-template"
    (tmp_path / "requirements" / "milestones" / f"{work_id}.md").write_text(
        "## Summary\n\nCLI template smoke.\n",
        encoding="utf-8",
    )
    assert main(["template", "list", "--json"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["ok"] is True
    assert any(c["id"] == "feature" for c in listed["combos"])

    assert main(["template", "validate"]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True

    rc = main(
        [
            "--root",
            str(tmp_path),
            "template",
            "render",
            "--work-id",
            work_id,
            "--combo",
            "spike",
            "--json",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["combo_id"] == "spike"
    assert payload["adf"]["type"] == "doc"
