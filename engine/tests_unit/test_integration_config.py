"""Tests for .sdlc/integrations-config.json credential resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from sdlc_engine.integration_config import (
    integration_env,
    load_config,
    resolve_integrations,
    save_config,
    status_dict,
)
from sdlc_engine.issues import IssueSyncService
from sdlc_engine.project import Project


def test_save_and_resolve_jira_from_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "JIRA_BASE_URL",
        "JIRA_EMAIL",
        "JIRA_API_TOKEN",
        "JIRA_PROJECT",
        "GH_TOKEN",
        "SDLC_GITHUB_REPO",
    ):
        monkeypatch.delenv(key, raising=False)
    project = Project(tmp_path)
    save_config(
        project,
        {
            "tracker": "jira",
            "jira": {
                "base_url": "https://example.atlassian.net",
                "email": "bot@example.com",
                "api_token": "secret-token",
                "project": "ORCH",
            },
            "github": {"token": "gh-secret", "repo": "acme/app"},
        },
    )
    resolved = resolve_integrations(project)
    assert resolved.tracker == "jira"
    assert resolved.jira_configured is True
    assert resolved.github_configured is True
    st = status_dict(project)
    assert st["jira"]["configured"] is True
    assert st["github"]["configured"] is True
    assert "secret" not in str(st)


def test_env_overrides_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JIRA_API_TOKEN", "env-token")
    project = Project(tmp_path)
    save_config(
        project,
        {"tracker": "github", "jira": {"api_token": "file-token"}},
    )
    resolved = resolve_integrations(project)
    assert resolved.jira_api_token == "env-token"


def test_integration_env_overlays_for_push(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JIRA_BASE_URL", raising=False)
    monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
    monkeypatch.delenv("JIRA_EMAIL", raising=False)
    project = Project(tmp_path)
    save_config(
        project,
        {
            "tracker": "jira",
            "jira": {
                "base_url": "https://cfg.atlassian.net",
                "email": "cfg@example.com",
                "api_token": "cfg-token",
            },
        },
    )
    svc = IssueSyncService(project)
    with integration_env(project):
        assert svc._jira_base_url() == "https://cfg.atlassian.net"
        assert svc._jira_auth_mode() in {"basic", "bearer"}
    assert not svc._jira_base_url()


def test_v3_home_writes_under_sdlc_spdd_runtime(tmp_path: Path) -> None:
    (tmp_path / "sdlc-spdd").mkdir()
    project = Project(tmp_path)
    save_config(project, {"tracker": "github", "github": {"repo": "acme/app"}})
    cfg = tmp_path / "sdlc-spdd" / ".sdlc" / "integrations-config.json"
    assert cfg.is_file()
    assert not (tmp_path / ".sdlc" / "integrations-config.json").exists()
