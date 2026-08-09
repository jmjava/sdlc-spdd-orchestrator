"""Guide operator HTTP helpers: stats, incremental ingest, Neo4j purge, git reset."""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from sdlc_engine.project import HOME_DIR_NAME


def _guide_base(host: str, port: int) -> str:
    return f"http://{host}:{int(port)}"


def _request_json(
    method: str,
    url: str,
    *,
    body: dict[str, Any] | None = None,
    timeout: float = 120.0,
) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                parsed: Any = json.loads(raw) if raw.strip() else {}
            except json.JSONDecodeError:
                parsed = {"raw": raw}
            return {
                "ok": 200 <= int(resp.status) < 300,
                "status": int(resp.status),
                "data": parsed,
                "url": url,
            }
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(err_body) if err_body.strip() else {"error": err_body}
        except json.JSONDecodeError:
            parsed = {"error": err_body}
        return {
            "ok": False,
            "status": int(exc.code),
            "data": parsed,
            "error": err_body,
            "url": url,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "status": None, "error": str(exc), "url": url, "data": {}}


def guide_stats(host: str, port: int, *, timeout: float = 15.0) -> dict[str, Any]:
    """GET /api/v1/data/stats — RAG ContentElement counts."""
    return _request_json("GET", f"{_guide_base(host, port)}/api/v1/data/stats", timeout=timeout)


def load_references(host: str, port: int, *, timeout: float = 1800.0) -> dict[str, Any]:
    """POST /api/v1/data/load-references — incremental / append ingest while Guide is up.

    Default timeout is 30 minutes: directory + embedding passes routinely exceed 10 minutes.
    """
    return _request_json(
        "POST",
        f"{_guide_base(host, port)}/api/v1/data/load-references",
        body={},
        timeout=timeout,
    )


def purge_preview(
    host: str,
    port: int,
    *,
    directory: str | None = None,
    uri_prefix: str | None = None,
    sample_limit: int = 15,
    timeout: float = 60.0,
) -> dict[str, Any]:
    body: dict[str, Any] = {"sampleLimit": sample_limit}
    if directory:
        body["directory"] = directory
    if uri_prefix:
        body["uriPrefix"] = uri_prefix
    return _request_json(
        "POST",
        f"{_guide_base(host, port)}/api/v1/data/content-elements/purge-preview",
        body=body,
        timeout=timeout,
    )


def purge_content(
    host: str,
    port: int,
    *,
    directory: str | None = None,
    uri_prefix: str | None = None,
    confirm: bool = False,
    timeout: float = 120.0,
) -> dict[str, Any]:
    body: dict[str, Any] = {"confirm": bool(confirm)}
    if directory:
        body["directory"] = directory
    if uri_prefix:
        body["uriPrefix"] = uri_prefix
    return _request_json(
        "POST",
        f"{_guide_base(host, port)}/api/v1/data/content-elements/purge",
        body=body,
        timeout=timeout,
    )


def reset_git_revision(
    host: str,
    port: int,
    *,
    directory: str,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Force next ingest of ``directory`` to re-scan the full tree (git incremental)."""
    return _request_json(
        "POST",
        f"{_guide_base(host, port)}/api/v1/data/git-ingestion/revision/reset",
        body={"directory": directory},
        timeout=timeout,
    )


def purge_all_content_elements_docker(
    *,
    username: str = "neo4j",
    password: str = "brahmsian",
    container: str = "embabel-neo4j",
    timeout: int = 120,
) -> dict[str, Any]:
    """Nuclear option: DETACH DELETE all ContentElement nodes via cypher-shell in compose Neo4j."""
    cypher = "MATCH (c:ContentElement) DETACH DELETE c RETURN count(*) AS deleted"
    cmd = [
        "docker",
        "exec",
        container,
        "cypher-shell",
        "-u",
        username,
        "-p",
        password,
        cypher,
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    log = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "command": cmd[:-1] + ["<cypher>"],
        "log": log.strip(),
        "warning": "Deletes ALL ContentElement RAG chunks in the local embabel-neo4j store.",
    }


def default_operator_directories(orchestrator_root: Path | str) -> list[str]:
    root = Path(orchestrator_root).expanduser().resolve()
    home = root / HOME_DIR_NAME if (root / HOME_DIR_NAME).is_dir() else root
    return [
        str(home / "spdd" / "canvas"),
        str(home / "spdd" / "analysis"),
        str(home / "spdd" / "memory"),
    ]
