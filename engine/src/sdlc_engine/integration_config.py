"""Per-project issue tracker + Jira/GitHub credentials (gitignored runtime).

Config file: ``.sdlc/integrations-config.json`` (falls back to legacy
``.sdlc/issue-tracker-config.json`` for tracker-only fields).

Environment variables always win over file values when set.
Secrets are never returned from :func:`status_dict` — only ``*_set`` booleans.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from .io_util import load_json_dict
from .project import Project

CONFIG_REL = Path(".sdlc") / "integrations-config.json"
LEGACY_TRACKER_REL = Path(".sdlc") / "issue-tracker-config.json"

TRACKER_JIRA = "jira"
TRACKER_GITHUB = "github"
TRACKER_NONE = "none"

ALL_TRACKERS: tuple[str, ...] = (TRACKER_JIRA, TRACKER_GITHUB, TRACKER_NONE)
DEFAULT_TRACKER = TRACKER_GITHUB

_TRACKER_ALIASES = {
    "jira": TRACKER_JIRA,
    "atlassian": TRACKER_JIRA,
    "github": TRACKER_GITHUB,
    "gh": TRACKER_GITHUB,
    "none": TRACKER_NONE,
    "off": TRACKER_NONE,
    "disabled": TRACKER_NONE,
}

_JIRA_ENV_MAP = {
    "base_url": ("JIRA_BASE_URL", "JIRA_URL"),
    "email": ("JIRA_EMAIL",),
    "api_token": ("JIRA_API_TOKEN",),
    "project": ("JIRA_PROJECT",),
    "api_version": ("JIRA_API_VERSION",),
    "auth_mode": ("JIRA_AUTH_MODE",),
}

_GITHUB_ENV_MAP = {
    "token": ("GH_TOKEN", "GITHUB_TOKEN"),
    "repo": ("SDLC_GITHUB_REPO", "GH_REPO"),
}


def normalize_tracker(raw: str) -> str:
    name = str(raw or "").strip().lower().replace("_", "-")
    return _TRACKER_ALIASES.get(name, name)


def config_path(project: Project) -> Path:
    return project.sdlc_dir / CONFIG_REL.name


def _read_json(path: Path) -> dict[str, Any]:
    return load_json_dict(path)


def _first_env(keys: tuple[str, ...]) -> str:
    for key in keys:
        val = os.environ.get(key, "").strip()
        if val:
            return val
    return ""


def _section(cfg: dict[str, Any], name: str) -> dict[str, str]:
    raw = cfg.get(name)
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v).strip() if v is not None else "" for k, v in raw.items()}


@dataclass(frozen=True)
class ResolvedIntegrations:
    tracker: str
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project: str = ""
    jira_api_version: str = ""
    jira_auth_mode: str = ""
    github_token: str = ""
    github_repo: str = ""

    @property
    def jira_configured(self) -> bool:
        if not self.jira_base_url or not self.jira_api_token:
            return False
        mode = (self.jira_auth_mode or "basic").lower()
        if mode == "bearer":
            return True
        return bool(self.jira_email)

    @property
    def github_configured(self) -> bool:
        return bool(self.github_token)


def load_config(project: Project) -> dict[str, Any]:
    path = config_path(project)
    data = _read_json(path)
    if not data:
        legacy = _read_json(project.sdlc_dir / LEGACY_TRACKER_REL.name)
        if legacy:
            data = {
                "tracker": legacy.get("tracker", DEFAULT_TRACKER),
                "notes": legacy.get("notes", ""),
                "jira": {},
                "github": {},
            }
    tracker = normalize_tracker(str(data.get("tracker") or DEFAULT_TRACKER))
    if tracker not in ALL_TRACKERS:
        tracker = DEFAULT_TRACKER
    return {
        "tracker": tracker,
        "notes": str(data.get("notes") or ""),
        "jira": _section(data, "jira"),
        "github": _section(data, "github"),
    }


def save_config(project: Project, payload: dict[str, Any]) -> dict[str, Any]:
    existing = load_config(project)
    tracker = normalize_tracker(str(payload.get("tracker") or existing["tracker"]))
    if tracker not in ALL_TRACKERS:
        raise ValueError(f"tracker must be one of: {', '.join(ALL_TRACKERS)}")

    jira = dict(existing.get("jira") or {})
    gh = dict(existing.get("github") or {})
    incoming_jira = payload.get("jira")
    if isinstance(incoming_jira, dict):
        for key in ("base_url", "email", "project", "api_version", "auth_mode"):
            if key in incoming_jira:
                jira[key] = str(incoming_jira.get(key) or "").strip()
        token = str(incoming_jira.get("api_token") or "").strip()
        if token:
            jira["api_token"] = token
    incoming_gh = payload.get("github")
    if isinstance(incoming_gh, dict):
        if "repo" in incoming_gh:
            gh["repo"] = str(incoming_gh.get("repo") or "").strip()
        token = str(incoming_gh.get("token") or "").strip()
        if token:
            gh["token"] = token

    out = {
        "tracker": tracker,
        "notes": str(payload.get("notes") if "notes" in payload else existing.get("notes") or ""),
        "jira": jira,
        "github": gh,
    }
    path = config_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out


def effective_tracker(project: Project, cfg: dict[str, Any] | None = None) -> str:
    env = normalize_tracker(os.environ.get("SDLC_ISSUE_TRACKER", ""))
    if env in ALL_TRACKERS:
        return env
    if cfg is None:
        cfg = load_config(project)
    saved = normalize_tracker(str(cfg.get("tracker") or ""))
    if saved in ALL_TRACKERS:
        return saved
    return DEFAULT_TRACKER


def resolve_integrations(project: Project) -> ResolvedIntegrations:
    cfg = load_config(project)
    jira = cfg.get("jira") or {}
    gh = cfg.get("github") or {}
    return ResolvedIntegrations(
        tracker=effective_tracker(project, cfg),
        jira_base_url=_first_env(_JIRA_ENV_MAP["base_url"]) or str(jira.get("base_url") or ""),
        jira_email=_first_env(_JIRA_ENV_MAP["email"]) or str(jira.get("email") or ""),
        jira_api_token=_first_env(_JIRA_ENV_MAP["api_token"]) or str(jira.get("api_token") or ""),
        jira_project=_first_env(_JIRA_ENV_MAP["project"]) or str(jira.get("project") or ""),
        jira_api_version=_first_env(_JIRA_ENV_MAP["api_version"]) or str(jira.get("api_version") or ""),
        jira_auth_mode=_first_env(_JIRA_ENV_MAP["auth_mode"]) or str(jira.get("auth_mode") or ""),
        github_token=_first_env(_GITHUB_ENV_MAP["token"]) or str(gh.get("token") or ""),
        github_repo=_first_env(_GITHUB_ENV_MAP["repo"]) or str(gh.get("repo") or ""),
    )


def _overlay_env(resolved: ResolvedIntegrations) -> dict[str, str]:
    overlays: dict[str, str] = {}
    if resolved.jira_base_url and not _first_env(_JIRA_ENV_MAP["base_url"]):
        overlays["JIRA_BASE_URL"] = resolved.jira_base_url
    if resolved.jira_email and not _first_env(_JIRA_ENV_MAP["email"]):
        overlays["JIRA_EMAIL"] = resolved.jira_email
    if resolved.jira_api_token and not _first_env(_JIRA_ENV_MAP["api_token"]):
        overlays["JIRA_API_TOKEN"] = resolved.jira_api_token
    if resolved.jira_project and not _first_env(_JIRA_ENV_MAP["project"]):
        overlays["JIRA_PROJECT"] = resolved.jira_project
    if resolved.jira_api_version and not _first_env(_JIRA_ENV_MAP["api_version"]):
        overlays["JIRA_API_VERSION"] = resolved.jira_api_version
    if resolved.jira_auth_mode and not _first_env(_JIRA_ENV_MAP["auth_mode"]):
        overlays["JIRA_AUTH_MODE"] = resolved.jira_auth_mode
    if resolved.github_token and not _first_env(_GITHUB_ENV_MAP["token"]):
        overlays["GH_TOKEN"] = resolved.github_token
    if resolved.github_repo and not _first_env(_GITHUB_ENV_MAP["repo"]):
        overlays["SDLC_GITHUB_REPO"] = resolved.github_repo
    return overlays


@contextmanager
def integration_env(project: Project) -> Iterator[ResolvedIntegrations]:
    """Temporarily overlay file-based credentials onto ``os.environ``."""
    resolved = resolve_integrations(project)
    overlays = _overlay_env(resolved)
    saved: dict[str, str | None] = {}
    for key, value in overlays.items():
        saved[key] = os.environ.get(key)
        os.environ[key] = value
    try:
        yield resolved
    finally:
        for key, old in saved.items():
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old


def status_dict(project: Project) -> dict[str, Any]:
    cfg = load_config(project)
    resolved = resolve_integrations(project)
    path = config_path(project)
    return {
        "tracker": cfg.get("tracker", DEFAULT_TRACKER),
        "effective_tracker": resolved.tracker,
        "notes": cfg.get("notes", ""),
        "config_path": str(CONFIG_REL),
        "config_exists": path.is_file(),
        "env_tracker_override": normalize_tracker(os.environ.get("SDLC_ISSUE_TRACKER", ""))
        if os.environ.get("SDLC_ISSUE_TRACKER")
        else "",
        "jira": {
            "base_url": resolved.jira_base_url if not _first_env(_JIRA_ENV_MAP["base_url"]) else "",
            "email": resolved.jira_email if not _first_env(_JIRA_ENV_MAP["email"]) else "",
            "project": resolved.jira_project if not _first_env(_JIRA_ENV_MAP["project"]) else "",
            "api_version": resolved.jira_api_version if not _first_env(_JIRA_ENV_MAP["api_version"]) else "",
            "auth_mode": resolved.jira_auth_mode or "basic",
            "base_url_set": bool(resolved.jira_base_url),
            "email_set": bool(resolved.jira_email),
            "token_set": bool(resolved.jira_api_token),
            "project_set": bool(resolved.jira_project),
            "configured": resolved.jira_configured,
            "source": "env"
            if _first_env(_JIRA_ENV_MAP["api_token"])
            else ("file" if (cfg.get("jira") or {}).get("api_token") else "unset"),
        },
        "github": {
            "repo": resolved.github_repo if not _first_env(_GITHUB_ENV_MAP["repo"]) else "",
            "repo_set": bool(resolved.github_repo),
            "token_set": bool(resolved.github_token),
            "configured": resolved.github_configured,
            "source": "env"
            if _first_env(_GITHUB_ENV_MAP["token"])
            else ("file" if (cfg.get("github") or {}).get("token") else "unset"),
        },
    }
