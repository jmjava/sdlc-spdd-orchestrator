"""Tests for Jira markdown ↔ ADF / wiki conversion and push payload shape."""

from __future__ import annotations

import json
from pathlib import Path

from sdlc_engine.issues import IssueSyncService
from sdlc_engine.jira_format import (
    adf_to_markdown,
    build_github_markdown,
    build_jira_markdown,
    markdown_to_adf,
    markdown_to_wiki,
)
from sdlc_engine.project import Project


SAMPLE_MD = """## Summary

Ship formatted Jira descriptions.

## Description

Support **bold**, `code`, and [links](https://example.com).

## Acceptance criteria

- Given a milestone draft
- When we push to Jira Cloud
- Then the description renders with headings and lists

## Traceability

- Work ID: `FEAT-400-jira-fmt`
- Requirement: `requirements/milestones/FEAT-400-jira-fmt.md`
"""


def test_markdown_to_adf_structure() -> None:
    doc = markdown_to_adf(SAMPLE_MD)
    assert doc["type"] == "doc"
    assert doc["version"] == 1
    types = [n["type"] for n in doc["content"]]
    assert "heading" in types
    assert "bulletList" in types
    assert "paragraph" in types
    # bold mark present
    blob = json.dumps(doc)
    assert "strong" in blob
    assert "code" in blob
    assert "link" in blob


def test_markdown_to_wiki_headings_and_lists() -> None:
    wiki = markdown_to_wiki(SAMPLE_MD)
    assert "h2. Summary" in wiki
    assert "* Given a milestone draft" in wiki
    assert "*Ship formatted" in wiki or "Ship formatted" in wiki


def test_adf_roundtrip_preserves_headings() -> None:
    doc = markdown_to_adf(SAMPLE_MD)
    back = adf_to_markdown(doc)
    assert "## Summary" in back or "# Summary" in back
    assert "Given a milestone draft" in back
    assert "FEAT-400-jira-fmt" in back


def test_build_jira_markdown_sections() -> None:
    md = build_jira_markdown(
        work_id="FEAT-401",
        summary="Title",
        description="Body para",
        acceptance="- Given x When y Then z",
        business_value="Saves time",
        requirement_rel="requirements/milestones/FEAT-401.md",
    )
    assert "## Summary" in md
    assert "## Description" in md
    assert "## Business value" in md
    assert "## Acceptance criteria" in md
    assert "## Traceability" in md
    assert "`FEAT-401`" in md


def test_build_github_markdown_matches_jira_sections() -> None:
    gh = build_github_markdown(
        work_id="FEAT-501",
        summary="Title",
        description="Body",
        acceptance="- [ ] done",
        requirement_rel="requirements/milestones/FEAT-501.md",
    )
    assert "## Description" in gh
    assert "## Acceptance criteria" in gh
    assert "## Traceability" in gh
    assert build_github_markdown(work_id="x") == build_jira_markdown(work_id="x")


def test_github_draft_from_structured_sections(tmp_path: Path) -> None:
    work_id = "FEAT-502-gh-template"
    req = tmp_path / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True)
    req.write_text(
        f"""# Requirement: {work_id}

## Summary

Fallback summary.

## GitHub

- Number: 42
- Title: GH title

### Description

Structured **body**.

### Acceptance criteria

- [ ] AC one
""",
        encoding="utf-8",
    )
    drafts = IssueSyncService(Project(tmp_path)).draft(work_id, system="github")
    assert len(drafts) == 1
    body = drafts[0].body
    assert "## Description" in body
    assert "Structured **body**." in body
    assert "## Acceptance criteria" in body
    assert "FEAT-502-gh-template" in body


def test_empty_metadata_adjacent_bullets_still_ok_in_adf() -> None:
    doc = markdown_to_adf("## Heading\n\n- item one\n- item two\n")
    assert doc["content"][0]["type"] == "heading"
    assert doc["content"][1]["type"] == "bulletList"
    assert len(doc["content"][1]["content"]) == 2


def test_jira_push_sends_adf_on_cloud(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "bot@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")
    monkeypatch.setenv("JIRA_PROJECT", "ORCH")
    work_id = "FEAT-402-adf-push"
    req = tmp_path / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True)
    req.write_text(
        f"""# Requirement: {work_id}

## Summary

ADF push demo.

## Jira

- Key: TBD
- Summary: ADF push demo
- Issue type: Story
- Labels: sdlc

### Description

Need **formatted** descriptions in Jira Cloud.

### Acceptance criteria (Given/When/Then)

- Given a draft
- When pushed
- Then ADF is used
""",
        encoding="utf-8",
    )
    (tmp_path / "spdd" / "canvas").mkdir(parents=True)
    (tmp_path / "spdd" / "canvas" / f"{work_id}.md").write_text(
        f"# REASONS Canvas: {work_id}\n\n## Metadata\n\n- Work ID: {work_id}\n"
        "- Source System:\n- Source Issue:\n\n## Final Status\n\n- Status: Draft\n",
        encoding="utf-8",
    )

    seen: dict = {}

    class _Resp:
        def read(self) -> bytes:
            return json.dumps({"key": "ORCH-88"}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

    def fake_urlopen(req, timeout=30):  # noqa: ANN001
        seen["url"] = req.full_url
        payload = json.loads(req.data.decode())
        seen["payload"] = payload
        return _Resp()

    out = IssueSyncService(Project(tmp_path), urlopen=fake_urlopen).push(
        work_id, "jira", apply=True
    )
    assert "ORCH-88" in out
    assert "/rest/api/3/issue" in seen["url"]
    desc = seen["payload"]["fields"]["description"]
    assert isinstance(desc, dict)
    assert desc["type"] == "doc"
    assert desc["version"] == 1
    assert any(n.get("type") == "heading" for n in desc["content"])


def test_jira_push_wiki_when_forced(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://jira.corp.example")
    monkeypatch.setenv("JIRA_EMAIL", "bot@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")
    monkeypatch.setenv("JIRA_PROJECT", "ORCH")
    monkeypatch.setenv("JIRA_API_VERSION", "2")
    monkeypatch.setenv("JIRA_DESCRIPTION_FORMAT", "wiki")
    work_id = "FEAT-403-wiki"
    req = tmp_path / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True)
    req.write_text(
        f"""# Requirement: {work_id}

## Summary

Wiki demo.

## Jira

- Key: TBD
- Summary: Wiki demo

### Description

Plain server install.
""",
        encoding="utf-8",
    )
    (tmp_path / "spdd" / "canvas").mkdir(parents=True)
    (tmp_path / "spdd" / "canvas" / f"{work_id}.md").write_text(
        f"# C\n\n## Metadata\n\n- Work ID: {work_id}\n- Source Issue:\n\n## Final Status\n\n- Status: Draft\n",
        encoding="utf-8",
    )
    seen: dict = {}

    class _Resp:
        def read(self) -> bytes:
            return json.dumps({"key": "ORCH-11"}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

    def fake_urlopen(req, timeout=30):  # noqa: ANN001
        seen["url"] = req.full_url
        seen["desc"] = json.loads(req.data.decode())["fields"]["description"]
        return _Resp()

    IssueSyncService(Project(tmp_path), urlopen=fake_urlopen).push(work_id, "jira", apply=True)
    assert "/rest/api/2/issue" in seen["url"]
    assert isinstance(seen["desc"], str)
    assert "h2." in seen["desc"] or "Wiki demo" in seen["desc"] or "Plain server" in seen["desc"]


def test_jira_pull_adf_description_to_milestone(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "bot@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")
    work_id = "FEAT-404-pull-adf"
    req = tmp_path / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True)
    req.write_text(
        f"""# Requirement: {work_id}

## Summary

Pull me.

## Jira

- Key: ORCH-12
- Summary: old

### Description

old desc
""",
        encoding="utf-8",
    )

    adf = markdown_to_adf("## From Jira\n\nPulled **ADF** body.\n")

    class _Resp:
        def read(self) -> bytes:
            return json.dumps(
                {
                    "key": "ORCH-12",
                    "fields": {
                        "summary": "Pulled title",
                        "status": {"name": "To Do"},
                        "labels": [],
                        "description": adf,
                    },
                }
            ).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

    def fake_urlopen(req, timeout=30):  # noqa: ANN001
        assert "/rest/api/3/issue/ORCH-12" in req.full_url
        return _Resp()

    report = IssueSyncService(Project(tmp_path), urlopen=fake_urlopen).pull(
        work_id, "jira", apply=True
    )
    assert "Pulled title" in report
    text = req.read_text(encoding="utf-8")
    assert "Summary: Pulled title" in text
    assert "From Jira" in text or "Pulled" in text
    assert "ADF" in text


def test_adf_to_wiki_headings_and_marks() -> None:
    from sdlc_engine.jira_format import adf_to_wiki

    adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Summary"}],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "bold", "marks": [{"type": "strong"}]},
                    {"type": "text", "text": " and "},
                    {"type": "text", "text": "code", "marks": [{"type": "code"}]},
                ],
            },
        ],
    }
    wiki = adf_to_wiki(adf)
    assert "h2. Summary" in wiki
    assert "*bold*" in wiki
    assert "{{code}}" in wiki


def test_adf_to_wiki_gwt_scenarios() -> None:
    from sdlc_engine.jira_format import adf_to_wiki

    adf = {
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
                                    {
                                        "type": "text",
                                        "text": "Given a requirement",
                                        "marks": [{"type": "strong"}],
                                    },
                                    {"type": "hardBreak"},
                                    {
                                        "type": "text",
                                        "text": "When push runs",
                                        "marks": [{"type": "strong"}],
                                    },
                                    {"type": "hardBreak"},
                                    {
                                        "type": "text",
                                        "text": "Then ADF is sent",
                                        "marks": [{"type": "strong"}],
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }
    wiki = adf_to_wiki(adf)
    assert "*Scenario 1*" in wiki
    assert "**" in wiki
    assert "Given a requirement" in wiki


def test_jira_push_updates_existing_key_with_raw_adf(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "bot@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")
    monkeypatch.setenv("JIRA_PROJECT", "ORCH")
    monkeypatch.delenv("JIRA_DESCRIPTION_FALLBACK", raising=False)
    work_id = "FEAT-405-update-adf"
    req = tmp_path / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True)
    req.write_text(
        f"""# Requirement: {work_id}

## Summary

Update me.

## Jira

- Key: ORCH-99
- Summary: Update me

### Description

New body with **ADF**.
""",
        encoding="utf-8",
    )
    seen: dict = {}

    class _Resp:
        def read(self) -> bytes:
            return b""

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

    def fake_urlopen(req, timeout=30):  # noqa: ANN001
        seen["method"] = req.get_method()
        seen["url"] = req.full_url
        seen["payload"] = json.loads(req.data.decode())
        seen["auth"] = req.get_header("Authorization")
        return _Resp()

    out = IssueSyncService(Project(tmp_path), urlopen=fake_urlopen).push(
        work_id, "jira", apply=True
    )
    assert "Updated" in out
    assert seen["method"] == "PUT"
    assert "/rest/api/3/issue/ORCH-99" in seen["url"]
    desc = seen["payload"]["fields"]["description"]
    assert isinstance(desc, dict)
    assert desc["type"] == "doc"
    assert seen["auth"].startswith("Basic ")


def _sample_adf(text: str = "Hello ADF") -> dict:
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }


def test_download_adf_dry_run_and_apply(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "bot@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")
    remote = _sample_adf("Remote hand edit")
    local_path = tmp_path / "adf" / "ORCH-88.adf.json"
    local_path.parent.mkdir(parents=True)
    local_path.write_text(json.dumps(_sample_adf("Local version"), indent=2), encoding="utf-8")

    class _Resp:
        def read(self) -> bytes:
            return json.dumps(
                {"fields": {"summary": "S", "description": remote}}
            ).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

    def fake_urlopen(req, timeout=30):  # noqa: ANN001
        assert req.get_method() == "GET"
        assert "ORCH-88" in req.full_url
        return _Resp()

    svc = IssueSyncService(Project(tmp_path), urlopen=fake_urlopen)
    dry = svc.download_adf("ORCH-88", apply=False)
    assert "[dry-run]" in dry
    assert "differ" in dry
    assert local_path.read_text(encoding="utf-8").find("Local version") > 0

    out = svc.download_adf("ORCH-88", apply=True)
    assert "Wrote" in out
    written = json.loads(local_path.read_text(encoding="utf-8"))
    assert written["content"][0]["content"][0]["text"] == "Remote hand edit"


def test_download_adf_identical_and_missing_local(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "bot@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")
    remote = _sample_adf("Same")

    class _Resp:
        def read(self) -> bytes:
            return json.dumps({"fields": {"description": remote}}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

    svc = IssueSyncService(Project(tmp_path), urlopen=lambda req, timeout=30: _Resp())
    missing = svc.download_adf("ORCH-1", apply=False)
    assert "remote-only" in missing

    path = tmp_path / "adf" / "ORCH-1.adf.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(remote, indent=2) + "\n", encoding="utf-8")
    same = svc.download_adf("ORCH-1", apply=False)
    assert "identical" in same


def test_download_adf_rejects_non_adf_description(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "bot@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")

    class _Resp:
        def read(self) -> bytes:
            return json.dumps(
                {"fields": {"description": "wiki *markup* string"}}
            ).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

    svc = IssueSyncService(Project(tmp_path), urlopen=lambda req, timeout=30: _Resp())
    try:
        svc.download_adf("ORCH-2", apply=False)
        raise AssertionError("expected RuntimeError")
    except RuntimeError as exc:
        assert "not ADF" in str(exc)


def test_download_adf_invalid_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "bot@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")
    svc = IssueSyncService(Project(tmp_path))
    try:
        svc.download_adf("not-a-key", apply=False)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "invalid Jira issue key" in str(exc)


def test_upload_adf_raw_vs_wiki_shim(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "bot@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")
    adf_path = tmp_path / "sample.adf.json"
    adf_path.write_text(
        json.dumps(
            {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Hello ADF"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    seen: dict = {}

    class _Resp:
        def read(self) -> bytes:
            return b""

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

    def fake_urlopen(req, timeout=30):  # noqa: ANN001
        seen["url"] = req.full_url
        seen["desc"] = json.loads(req.data.decode())["fields"]["description"]
        return _Resp()

    svc = IssueSyncService(Project(tmp_path), urlopen=fake_urlopen)
    dry = svc.upload_adf("ORCH-77", adf_path, apply=False, description_format="adf")
    assert "[dry-run]" in dry
    assert "raw ADF" in dry.lower() or "description_format: adf" in dry

    out = svc.upload_adf("ORCH-77", adf_path, apply=True, description_format="adf")
    assert "Updated" in out
    assert isinstance(seen["desc"], dict)
    assert seen["desc"]["type"] == "doc"

    out_wiki = svc.upload_adf("ORCH-77", adf_path, apply=True, description_format="wiki")
    assert "description=wiki" in out_wiki
    assert isinstance(seen["desc"], str)
    assert "Hello ADF" in seen["desc"]


def test_no_silent_adf_to_wiki_fallback_by_default(tmp_path: Path, monkeypatch) -> None:
    import urllib.error

    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "bot@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")
    monkeypatch.setenv("JIRA_PROJECT", "ORCH")
    monkeypatch.delenv("JIRA_DESCRIPTION_FALLBACK", raising=False)
    work_id = "FEAT-406-no-fallback"
    req = tmp_path / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True)
    req.write_text(
        f"""# Requirement: {work_id}

## Jira

- Key: TBD
- Summary: No fallback

### Description

Body
""",
        encoding="utf-8",
    )

    def fake_urlopen(req, timeout=30):  # noqa: ANN001
        raise urllib.error.HTTPError(
            req.full_url, 400, "Bad Request", hdrs=None, fp=__import__("io").BytesIO(b"bad adf")
        )

    try:
        IssueSyncService(Project(tmp_path), urlopen=fake_urlopen).push(
            work_id, "jira", apply=True
        )
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "400" in str(exc)
        assert "Fallback" not in str(exc)
