"""Run install / upgrade / verify scripts against a target project."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

_LIST_CAP = 40
_SECTION_HEADERS = (
    ("Created or updated", "created"),
    ("Created (", "created"),
    ("Skipped existing", "skipped"),
    ("Updated framework files", "updated"),
    ("Unchanged framework files", "unchanged"),
    ("Preserved existing project content", "preserved"),
    ("Consolidated", "consolidated"),
    ("Backups", "backups"),
)
_HEADLINE_HINTS = (
    "initialization complete",
    "upgrade complete",
    "setup complete",
    "verification passed",
    "verification failed",
)
_DRY_WOULD = re.compile(r"^\[dry-run\] would (.+)$")
_VERIFY_OK = re.compile(r"^ok\s+(.+)$")
_VERIFY_FAIL = re.compile(r"^fail\s+(.+)$")
_NUMBERED = re.compile(r"^\d+\.\s+")


def summarize_run_log(
    *,
    action: str,
    log: str,
    command: list[str] | None = None,
    dry_run: bool = False,
    ok: bool = False,
    exit_code: int = 0,
) -> dict[str, Any]:
    """Parse install/upgrade/verify script output into console-friendly lists."""
    command = command or []
    buckets: dict[str, list[str]] = {
        "would": [],
        "created": [],
        "skipped": [],
        "updated": [],
        "unchanged": [],
        "preserved": [],
        "consolidated": [],
        "backups": [],
        "checks_ok": [],
        "checks_fail": [],
        "warnings": [],
        "next_steps": [],
    }
    headline = ""
    home = ""
    checks_summary = ""
    section: str | None = None

    def _section_header(stripped: str) -> str | None:
        for prefix, key in _SECTION_HEADERS:
            if stripped.startswith(prefix):
                return key
        return None

    for raw in (log or "").splitlines():
        stripped = raw.strip()
        if not stripped:
            if section and section != "next_steps":
                section = None
            continue

        dry = _DRY_WOULD.match(stripped)
        if dry:
            buckets["would"].append(dry.group(1))
            section = None
            continue

        if stripped.startswith("WARNING"):
            buckets["warnings"].append(stripped)
            section = None
            continue

        if stripped == "Next steps:":
            section = "next_steps"
            continue

        header = _section_header(stripped)
        if header:
            section = header
            continue

        if section == "next_steps":
            if _NUMBERED.match(stripped):
                buckets["next_steps"].append(stripped)
            elif buckets["next_steps"] and (raw.startswith("     ") or stripped.startswith("/")):
                buckets["next_steps"][-1] = f"{buckets['next_steps'][-1]} {stripped}"
            elif stripped.startswith("For "):
                section = None
            continue

        if section and raw.startswith("  ") and stripped != "none":
            buckets[section].append(stripped)
            continue
        if section and not raw.startswith(" "):
            section = None

        if stripped.startswith("Framework home:"):
            home = stripped.split(":", 1)[1].strip()
        if stripped.startswith("Recommended next step:"):
            buckets["next_steps"].append(stripped.split(":", 1)[1].strip())
        if stripped.startswith("Summary:") and "checks passed" in stripped:
            checks_summary = stripped
        if any(hint in stripped.lower() for hint in _HEADLINE_HINTS):
            headline = stripped

        verify_ok = _VERIFY_OK.match(stripped)
        if verify_ok and raw.lstrip().startswith("ok"):
            buckets["checks_ok"].append(verify_ok.group(1))
            continue
        verify_fail = _VERIFY_FAIL.match(stripped)
        if verify_fail and raw.lstrip().startswith("fail"):
            buckets["checks_fail"].append(verify_fail.group(1))

    would_count = len(buckets["would"])
    return {
        "action": action,
        "ok": ok,
        "exit_code": exit_code,
        "dry_run": dry_run,
        "headline": headline,
        "framework_home": home,
        "command": " ".join(str(part) for part in command),
        "would": buckets["would"][:_LIST_CAP],
        "created": buckets["created"][:_LIST_CAP],
        "skipped": buckets["skipped"][:_LIST_CAP],
        "updated": buckets["updated"][:_LIST_CAP],
        "backups": buckets["backups"][:_LIST_CAP],
        "checks_ok": buckets["checks_ok"][:_LIST_CAP],
        "checks_fail": buckets["checks_fail"][:_LIST_CAP],
        "warnings": buckets["warnings"][:20],
        "next_steps": buckets["next_steps"][:12],
        "checks_summary": checks_summary,
        "would_count": would_count,
        "created_count": len(buckets["created"]),
        "check_ok_count": len(buckets["checks_ok"]),
        "check_fail_count": len(buckets["checks_fail"]),
    }


def _run_payload(
    *,
    action: str,
    ok: bool,
    exit_code: int,
    command: list[str],
    log: str,
    dry_run: bool = False,
    engine_log: str = "",
) -> dict[str, Any]:
    text = (log or "").strip()
    return {
        "ok": ok,
        "action": action,
        "exit_code": exit_code,
        "command": command,
        "log": text,
        "engine_log": (engine_log or "").strip(),
        "dry_run": dry_run,
        "summary": summarize_run_log(
            action=action,
            log=text,
            command=command,
            dry_run=dry_run,
            ok=ok,
            exit_code=exit_code,
        ),
    }


def orchestrator_root() -> Path:
    """Locate the SDLC-SPDD orchestrator repo (engine → repo root)."""
    # engine/src/sdlc_engine/installer/runner.py → repo root is parents[4]
    here = Path(__file__).resolve()
    candidate = here.parents[4]
    if (candidate / "scripts" / "setup-agent-prompts.sh").is_file():
        return candidate
    env = os.environ.get("SDLC_ORCHESTRATOR_ROOT", "").strip()
    if env:
        p = Path(env).expanduser().resolve()
        if (p / "scripts" / "setup-agent-prompts.sh").is_file():
            return p
    raise FileNotFoundError(
        "Could not locate orchestrator scripts/. Set SDLC_ORCHESTRATOR_ROOT "
        "or run from an editable install of this repo."
    )


def _assistant_flags(assistants: list[str]) -> list[str]:
    flags: list[str] = []
    normalized = {a.strip().lower() for a in assistants if a and str(a).strip()}
    if "all" in normalized:
        return ["--all"]
    for name in ("cursor", "copilot", "claude"):
        if name in normalized:
            flags.append(f"--{name}")
    return flags


def run_action(
    *,
    action: str,
    target: Path | str,
    assistants: list[str] | None = None,
    dry_run: bool = False,
    force: bool = False,
    no_backup: bool = False,
    with_python_engine: bool = False,
    timeout_sec: int = 300,
) -> dict[str, Any]:
    """Execute install, upgrade, or verify. Returns log + exit code."""
    root = orchestrator_root()
    target_path = Path(target).expanduser().resolve()
    assistants = assistants or ["cursor", "copilot"]
    flags = _assistant_flags(assistants)

    if action == "install":
        script = root / "scripts" / "setup-agent-prompts.sh"
        cmd = [str(script), "--target", str(target_path), *flags]
        if force:
            cmd.append("--force")
        if dry_run:
            cmd.append("--dry-run")
    elif action == "upgrade":
        script = root / "scripts" / "upgrade-project.sh"
        cmd = [str(script), "--target", str(target_path), *flags]
        if dry_run:
            cmd.append("--dry-run")
        if no_backup:
            cmd.append("--no-backup")
    elif action == "verify":
        script = root / "scripts" / "verify-project-install.sh"
        cmd = [str(script), "--target", str(target_path)]
        selected = {a.strip().lower() for a in assistants if a and str(a).strip()}
        want_all = "all" in selected
        for name in ("cursor", "copilot", "claude"):
            if want_all or name in selected:
                cmd.append(f"--require-{name}")
    else:
        return _run_payload(
            action=action,
            ok=False,
            exit_code=2,
            command=[],
            log=f"Unknown action: {action}",
        )

    if not script.is_file():
        return _run_payload(
            action=action,
            ok=False,
            exit_code=2,
            command=cmd,
            log=f"Script not found: {script}",
        )

    proc = subprocess.run(
        cmd,
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        check=False,
    )
    log = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    engine_log = ""
    if with_python_engine and action in {"install", "upgrade"} and proc.returncode == 0 and not dry_run:
        engine_log = _install_python_engine(root, target_path, timeout_sec=timeout_sec)
        log = (log + "\n" + engine_log).strip()

    return _run_payload(
        action=action,
        ok=proc.returncode == 0,
        exit_code=proc.returncode,
        command=cmd,
        log=log,
        dry_run=dry_run,
        engine_log=engine_log,
    )


def _install_python_engine(root: Path, target: Path, *, timeout_sec: int) -> str:
    """Best-effort editable install of the engine into the active Python env."""
    engine_dir = root / "engine"
    if not (engine_dir / "pyproject.toml").is_file():
        return "Python engine: skipped (engine/pyproject.toml missing)"
    cmd = [
        "python3",
        "-m",
        "pip",
        "install",
        "-e",
        str(engine_dir),
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(target),
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        check=False,
    )
    out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    status = "ok" if proc.returncode == 0 else f"failed (exit {proc.returncode})"
    return f"Python engine install ({status}):\n{out.strip()}"
