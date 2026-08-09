"""Issue tracker selection — re-exports from :mod:`integration_config`."""

from __future__ import annotations

from .integration_config import (
    ALL_TRACKERS,
    CONFIG_REL,
    DEFAULT_TRACKER,
    TRACKER_GITHUB,
    TRACKER_JIRA,
    TRACKER_NONE,
    config_path,
    effective_tracker,
    load_config,
    normalize_tracker,
    save_config as save_tracker_only,
    status_dict as tracker_status_dict,
)

__all__ = [
    "ALL_TRACKERS",
    "CONFIG_REL",
    "DEFAULT_TRACKER",
    "TRACKER_GITHUB",
    "TRACKER_JIRA",
    "TRACKER_NONE",
    "config_path",
    "effective_tracker",
    "load_config",
    "normalize_tracker",
    "save_tracker_only",
    "tracker_status_dict",
]


def save_config(project, *, tracker: str, notes: str = "") -> dict:  # noqa: ANN001
    """Legacy save API (tracker + notes only)."""
    from .integration_config import save_config as _save

    return _save(project, {"tracker": tracker, "notes": notes})


def status_dict(project) -> dict:  # noqa: ANN001
    """Legacy status API (tracker fields only)."""
    full = tracker_status_dict(project)
    return {
        "tracker": full.get("tracker"),
        "effective_tracker": full.get("effective_tracker"),
        "notes": full.get("notes"),
        "config_path": full.get("config_path"),
        "config_exists": full.get("config_exists"),
        "env_override": full.get("env_tracker_override", ""),
        "source": "env" if full.get("env_tracker_override") else "file",
    }
