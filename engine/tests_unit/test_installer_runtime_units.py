"""Direct unit coverage for installer runtime/ops helpers (mocked I/O)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from sdlc_engine.installer import guide_compliance as gc
from sdlc_engine.installer import guide_ops as go
from sdlc_engine.installer import guide_runtime as gr
from sdlc_engine.installer import runner as rn
from sdlc_engine.installer import viewer_runtime as vr


def test_relax_codegen_gradle_network_timeout(tmp_path: Path) -> None:
    props = tmp_path / "codegen-gradle" / "gradle" / "wrapper" / "gradle-wrapper.properties"
    props.parent.mkdir(parents=True)
    props.write_text(
        "distributionUrl=https\\://services.gradle.org/distributions/gradle-9.6.1-bin.zip\n"
        "networkTimeout=10000\n",
        encoding="utf-8",
    )
    assert gr.relax_codegen_gradle_network_timeout(tmp_path) is True
    text = props.read_text(encoding="utf-8")
    assert f"networkTimeout={gr.MIN_GRADLE_NETWORK_TIMEOUT_MS}" in text
    assert "networkTimeout=10000" not in text
    assert gr.relax_codegen_gradle_network_timeout(tmp_path) is False
    assert gr.relax_codegen_gradle_network_timeout(tmp_path / "missing") is False


def test_guide_runtime_ensure_clone_and_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "guide"
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> dict[str, Any]:
        calls.append(list(cmd))
        if len(cmd) >= 2 and cmd[0] == "git" and cmd[1] == "clone":
            dest = Path(cmd[-1])
            dest.mkdir(parents=True)
            (dest / ".git").mkdir()
            (dest / "scripts").mkdir()
            (dest / "scripts" / "append-ingest.sh").write_text("x\n")
            (dest / "compose.yaml").write_text("x\n")
            return {"ok": True, "exit_code": 0, "log": "cloned", "command": cmd}
        return {"ok": True, "exit_code": 0, "log": "ok", "command": cmd}

    monkeypatch.setattr(gr, "_run", fake_run)
    cfg = {
        "guide_home": str(home),
        "guide_git_url": "https://github.com/jmjava/orch-guide.git",
        "guide_git_ref": "main",
    }
    cloned = gr.ensure_guide_repo(cfg, pull=False)
    assert cloned["ok"] is True
    assert cloned["action"] == "clone"

    present = gr.ensure_guide_repo(cfg, pull=True)
    assert present["ok"] is True
    assert any("fetch" in " ".join(c) for c in calls)

    # path exists but is not a git clone
    bare = tmp_path / "not-git"
    bare.mkdir()
    bad = gr.ensure_guide_repo(
        {"guide_home": str(bare), "guide_git_url": "https://github.com/jmjava/orch-guide.git"},
        pull=False,
    )
    assert bad["ok"] is False


def test_guide_runtime_start_stop_guide(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "guide"
    (home / "scripts").mkdir(parents=True)
    (home / "scripts" / "append-ingest.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    (home / "compose.yaml").write_text("services: {}\n", encoding="utf-8")

    monkeypatch.setattr(gr, "start_neo4j", lambda cfg: {"ok": True, "log": "up"})
    monkeypatch.setattr(gr, "_tcp_open", lambda *a, **k: False)
    monkeypatch.setattr(gr, "_pid_alive", lambda pid: True)
    monkeypatch.setattr(
        gr.subprocess,
        "Popen",
        lambda *a, **k: MagicMock(pid=5555),
    )
    monkeypatch.setattr(gr, "_run", lambda *a, **k: {"ok": True, "log": "", "exit_code": 0})
    monkeypatch.setattr(gr.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(gr.os, "killpg", lambda *a, **k: None)
    monkeypatch.setattr(gr.os, "kill", lambda *a, **k: None)

    cfg = {
        "guide_home": str(home),
        "host": "127.0.0.1",
        "port": 21337,
        "profile": "sdlc-spdd",
        "neo4j_bolt_port": 7687,
        "neo4j_http_port": 7474,
        "neo4j_https_port": 7473,
    }
    started = gr.start_guide(tmp_path, cfg, ingest=False, ensure_neo4j=True)
    assert started["ok"] is True
    assert started["pid"] == 5555
    assert (tmp_path / ".sdlc" / "guide-runtime.json").is_file()

    again = gr.start_guide(tmp_path, cfg, ingest=False, ensure_neo4j=False)
    assert again["ok"] is False

    stopped = gr.stop_guide(tmp_path, cfg)
    assert stopped["ok"] is True


def test_guide_runtime_neo4j_helpers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "guide"
    home.mkdir()
    (home / "compose.yaml").write_text("x\n")
    monkeypatch.setattr(
        gr,
        "_run",
        lambda *a, **k: {"ok": True, "exit_code": 0, "log": "ok", "command": a[0]},
    )
    monkeypatch.setattr(gr, "_tcp_open", lambda *a, **k: True)
    cfg = {
        "guide_home": str(home),
        "neo4j_bolt_port": 7687,
        "neo4j_http_port": 7474,
        "neo4j_https_port": 7473,
        "profile": "sdlc-spdd",
        "port": 21337,
    }
    assert gr.start_neo4j(cfg)["ok"] is True
    assert gr.stop_neo4j(cfg)["ok"] is True
    probe = gr.probe_neo4j(cfg)
    assert probe["bolt_open"] is True


def test_guide_ops_request_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        def __init__(self, code: int = 200, body: bytes = b'{"ok":true}') -> None:
            self.status = code
            self._body = body

        def __enter__(self) -> "_Resp":
            return self

        def __exit__(self, *a: Any) -> None:
            return None

        def read(self) -> bytes:
            return self._body

    monkeypatch.setattr(go.urllib.request, "urlopen", lambda *a, **k: _Resp())
    assert go.guide_stats("127.0.0.1", 21337)["ok"] is True
    assert go.load_references("127.0.0.1", 21337)["ok"] is True
    assert go.purge_preview("127.0.0.1", 21337, directory="/tmp")["ok"] is True
    assert go.purge_content("127.0.0.1", 21337, directory="/tmp")["ok"] is True
    assert go.reset_git_revision("127.0.0.1", 21337, directory="/tmp")["ok"] is True

    monkeypatch.setattr(
        go.subprocess,
        "run",
        lambda *a, **k: MagicMock(returncode=0, stdout="ok\n", stderr=""),
    )
    wiped = go.purge_all_content_elements_docker()
    assert wiped["ok"] is True


def test_guide_compliance_http(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class _Resp:
        status = 200

        def __enter__(self) -> "_Resp":
            return self

        def __exit__(self, *a: Any) -> None:
            return None

        def read(self) -> bytes:
            return b'{"workIdCount":3}'

    monkeypatch.setattr(gc.urllib.request, "urlopen", lambda *a, **k: _Resp())
    assert gc.projection_stats("127.0.0.1", 21337)["ok"] is True
    loaded = gc.load_spdd_projection("127.0.0.1", 21337)
    assert loaded["ok"] is True

    class _Sse:
        status = 200

        def __enter__(self) -> "_Sse":
            return self

        def __exit__(self, *a: Any) -> None:
            return None

        def read(self, n: int = -1) -> bytes:
            return b":ok\n"

    monkeypatch.setattr(gc.urllib.request, "urlopen", lambda *a, **k: _Sse())
    assert gc.probe_mcp_sse("127.0.0.1", 21337)["reachable"] is True

    # Named entity detection via SpddEntityDictionary.fromClasses
    spdd = tmp_path / "src" / "main" / "kotlin" / "com" / "embabel" / "guide" / "spdd"
    domain = spdd / "domain"
    domain.mkdir(parents=True)
    (domain / "SpddDomain.kt").write_text("class WorkId\n", encoding="utf-8")
    (spdd / "SpddEntityDictionary.kt").write_text(
        "DataDictionary.fromClasses(\"sdlc-spdd\")\n",
        encoding="utf-8",
    )
    assert gc.named_entity_module_present(tmp_path) is True

    guide_home = tmp_path / "guide-home"
    written = gc.ensure_spdd_profile(
        guide_home, orchestrator_root=tmp_path, profile="sdlc-spdd"
    )
    assert written["ok"] is True


def test_summarize_run_log_parses_install_upgrade_verify() -> None:
    install = rn.summarize_run_log(
        action="install",
        log=(
            "[dry-run] would create /tmp/app/sdlc-spdd/ROADMAP.md\n"
            "[dry-run] would copy templates/x -> /tmp/app/sdlc-spdd/x\n"
            "SDLC-SPDD initialization complete for: /tmp/app\n"
            "Created or updated (2):\n"
            "  sdlc-spdd/ROADMAP.md\n"
            "  none\n"
            "Skipped existing (0):\n"
            "  none\n"
            "Recommended next step: run /sdlc-spdd-init then /sdlc-spdd-plan\n"
            "Framework home: /tmp/app/sdlc-spdd (docs at sdlc-spdd/docs/)\n"
            "Next steps:\n"
            "  1. Open the target project.\n"
            "  2. Start or resume context:\n"
            "     /tmp/app/sdlc-spdd/scripts/start-agent-session.sh --phase init\n"
            "  3. Invoke:\n"
            "     /sdlc-spdd-init\n"
        ),
        command=["setup-agent-prompts.sh", "--dry-run"],
        dry_run=True,
        ok=True,
        exit_code=0,
    )
    assert install["would_count"] == 2
    assert install["would"][0].startswith("create ")
    assert install["headline"].startswith("SDLC-SPDD initialization complete")
    assert "/sdlc-spdd-init" in install["next_steps"][0]
    assert any("Open the target" in step for step in install["next_steps"])
    assert any("start-agent-session.sh" in step for step in install["next_steps"])
    assert install["dry_run"] is True

    upgrade = rn.summarize_run_log(
        action="upgrade",
        log=(
            "WARNING: leftover agent-context/\n"
            "SDLC-SPDD framework upgrade complete for: /tmp/app\n"
            "Created (1):\n"
            "  sdlc-spdd/docs/README.md\n"
            "Backups (1):\n"
            "  /tmp/app/.sdlc-spdd-upgrade-backups/20260816T000000Z/x\n"
        ),
        ok=True,
        exit_code=0,
    )
    assert upgrade["created"] == ["sdlc-spdd/docs/README.md"]
    assert upgrade["backups"]
    assert upgrade["warnings"][0].startswith("WARNING")

    verify = rn.summarize_run_log(
        action="verify",
        log=(
            "  ok  Home: sdlc-spdd/\n"
            "  fail Cursor commands: .cursor/commands/sdlc-spdd-init.md\n"
            "Summary: 1/2 checks passed\n"
            "Install verification failed (1 missing or invalid items).\n"
        ),
        ok=False,
        exit_code=1,
    )
    assert verify["check_ok_count"] == 1
    assert verify["check_fail_count"] == 1
    assert "1/2 checks passed" in verify["checks_summary"]
    assert "verification failed" in verify["headline"].lower()


def test_runner_flags_and_engine_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = rn.orchestrator_root()
    assert (root / "scripts").is_dir()
    assert rn._assistant_flags(["all"]) == ["--all"]
    assert "--cursor" in rn._assistant_flags(["cursor", "copilot"])

    monkeypatch.setattr(
        rn.subprocess,
        "run",
        lambda *a, **k: MagicMock(returncode=0, stdout="ok\n", stderr=""),
    )
    result = rn.run_action(
        action="install",
        target=tmp_path,
        assistants=["cursor"],
        dry_run=True,
        force=True,
        with_python_engine=False,
    )
    assert "ok" in result
    assert "--force" in result["command"]

    up = rn.run_action(
        action="upgrade",
        target=tmp_path,
        assistants=["all"],
        dry_run=True,
        no_backup=True,
    )
    assert "--no-backup" in up["command"]

    bad = rn.run_action(action="nope", target=tmp_path)
    assert bad["ok"] is False

    eng = rn._install_python_engine(root, tmp_path, timeout_sec=30)
    assert "Python engine" in eng

    # with_python_engine live path (non-dry) after successful install
    live = rn.run_action(
        action="install",
        target=tmp_path,
        assistants=["cursor"],
        dry_run=False,
        with_python_engine=True,
    )
    assert live["ok"] is True
    assert live.get("engine_log")


def test_viewer_runtime_probe_http_and_kill_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _Resp:
        status = 200

        def __enter__(self) -> "_Resp":
            return self

        def __exit__(self, *a: Any) -> None:
            return None

    monkeypatch.setattr(vr, "_tcp_open", lambda *a, **k: True)
    monkeypatch.setattr(vr.urllib.request, "urlopen", lambda *a, **k: _Resp())
    probe = vr.probe_viewer("127.0.0.1", 5050)
    assert probe["http_ok"] is True

    # Corrupt runtime file
    rt = tmp_path / ".sdlc"
    rt.mkdir()
    (rt / "adf-viewer-runtime.json").write_text("{not-json", encoding="utf-8")
    assert vr._load_runtime(tmp_path) == {}

    # stop with live pid + port holders
    (rt / "adf-viewer-runtime.json").write_text(
        json.dumps({"pid": 1234, "port": 5050, "host": "127.0.0.1"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(vr, "_pid_alive", lambda pid: True)
    monkeypatch.setattr(vr.os, "killpg", lambda *a, **k: (_ for _ in ()).throw(ProcessLookupError()))
    monkeypatch.setattr(vr.os, "kill", lambda *a, **k: None)
    monkeypatch.setattr(vr.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(
        vr,
        "_run",
        lambda *a, **k: {"ok": True, "log": "9999", "exit_code": 0},
    )
    stopped = vr.stop_viewer(tmp_path)
    assert stopped["ok"] is True

    # _run helper + pid alive false path
    monkeypatch.setattr(
        vr.subprocess,
        "run",
        lambda *a, **k: MagicMock(returncode=0, stdout="1\n", stderr=""),
    )
    assert vr._run(["true"])["ok"] is True

    # start OSError
    monkeypatch.setattr(vr, "_tcp_open", lambda *a, **k: False)
    monkeypatch.setattr(vr, "_pid_alive", lambda pid: False)
    monkeypatch.setattr(
        vr.subprocess,
        "Popen",
        lambda *a, **k: (_ for _ in ()).throw(OSError("boom")),
    )
    boom = vr.start_viewer(tmp_path, port=5066)
    assert boom["ok"] is False

    # guide_ops HTTPError with JSON body
    import io
    import urllib.error

    class _HttpErr(urllib.error.HTTPError):
        def __init__(self) -> None:
            super().__init__("http://x", 500, "err", hdrs=None, fp=io.BytesIO(b'{"e":1}'))

    monkeypatch.setattr(go.urllib.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(_HttpErr()))
    assert go.guide_stats("127.0.0.1", 1)["ok"] is False

    # non-JSON success body
    class _Raw:
        status = 200

        def __enter__(self) -> "_Raw":
            return self

        def __exit__(self, *a: Any) -> None:
            return None

        def read(self) -> bytes:
            return b"not-json"

    monkeypatch.setattr(go.urllib.request, "urlopen", lambda *a, **k: _Raw())
    assert go.guide_stats("127.0.0.1", 21337)["data"]["raw"] == "not-json"

    def raise_url(*a: Any, **k: Any) -> Any:
        raise urllib.error.URLError("down")

    monkeypatch.setattr(gc.urllib.request, "urlopen", raise_url)
    assert gc.projection_stats("127.0.0.1", 1)["ok"] is False
    assert gc.probe_mcp_sse("127.0.0.1", 1)["reachable"] is False

    # runner env override + missing engine
    monkeypatch.setenv("SDLC_ORCHESTRATOR_ROOT", str(rn.orchestrator_root()))
    assert rn.orchestrator_root().is_dir()
    missing_eng = rn._install_python_engine(tmp_path, tmp_path, timeout_sec=5)
    assert "skipped" in missing_eng

    # guide start missing script
    missing = gr.start_guide(tmp_path, {"guide_home": str(tmp_path / "missing")}, ensure_neo4j=False)
    assert missing["ok"] is False

    # neo4j missing home
    assert gr.stop_neo4j({"guide_home": str(tmp_path / "nope")})["ok"] is False

    # start_guide when neo4j fails
    home2 = tmp_path / "guide2"
    (home2 / "scripts").mkdir(parents=True)
    (home2 / "scripts" / "append-ingest.sh").write_text("x\n")
    monkeypatch.setattr(gr, "start_neo4j", lambda cfg: {"ok": False, "log": "neo fail"})
    failed_neo = gr.start_guide(
        tmp_path,
        {"guide_home": str(home2), "port": 21338, "profile": "x", "host": "127.0.0.1"},
        ensure_neo4j=True,
    )
    assert failed_neo["ok"] is False

    # stop_guide killpg/kill branches
    (tmp_path / ".sdlc").mkdir(exist_ok=True)
    (tmp_path / ".sdlc" / "guide-runtime.json").write_text(
        json.dumps({"pid": 7777, "port": 21339}), encoding="utf-8"
    )
    state = {"n": 0}

    def alive(pid: int) -> bool:
        state["n"] += 1
        return state["n"] < 3  # alive for TERM, still alive for KILL check

    monkeypatch.setattr(gr, "_pid_alive", alive)
    monkeypatch.setattr(gr.os, "killpg", lambda *a, **k: None)
    monkeypatch.setattr(gr.os, "kill", lambda *a, **k: None)
    monkeypatch.setattr(gr.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(gr, "_run", lambda *a, **k: {"ok": True, "log": "8888", "exit_code": 0})
    assert gr.stop_guide(tmp_path, {"port": 21339})["ok"] is True

    # HTTPError on viewer probe
    class _HttpProbe(urllib.error.HTTPError):
        def __init__(self) -> None:
            super().__init__("http://x", 403, "no", hdrs=None, fp=io.BytesIO(b""))

    monkeypatch.setattr(vr, "_tcp_open", lambda *a, **k: True)
    monkeypatch.setattr(
        vr.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(_HttpProbe()),
    )
    assert vr.probe_viewer("127.0.0.1", 5050)["http_ok"] is True

    # rollback empty / missing / skip non-dirs
    from sdlc_engine.installer.rollback import restore_backup, list_backups, backups_root

    assert list_backups(tmp_path / "empty-target") == []
    assert restore_backup(tmp_path, "missing-id")["ok"] is False
    empty_b = tmp_path / ".sdlc-spdd-upgrade-backups" / "empty"
    empty_b.mkdir(parents=True)
    assert restore_backup(tmp_path, "empty")["ok"] is False
    br = backups_root(tmp_path)
    (br / "not-a-dir").write_text("x\n", encoding="utf-8")
    assert isinstance(list_backups(tmp_path), list)

    # guide_ops URLError generic
    monkeypatch.setattr(
        go.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(urllib.error.URLError("x")),
    )
    assert go.load_references("127.0.0.1", 9)["ok"] is False

    # Popen OSError on start_guide
    monkeypatch.setattr(gr, "start_neo4j", lambda cfg: {"ok": True, "log": "up"})
    monkeypatch.setattr(gr, "_pid_alive", lambda pid: False)
    monkeypatch.setattr(
        gr.subprocess,
        "Popen",
        lambda *a, **k: (_ for _ in ()).throw(OSError("nope")),
    )
    popen_fail = gr.start_guide(
        tmp_path,
        {"guide_home": str(home2), "port": 21340, "profile": "x", "host": "127.0.0.1"},
        ensure_neo4j=False,
    )
    assert popen_fail["ok"] is False


def test_viewer_edit_url_encodes_path(tmp_path: Path) -> None:
    dest = tmp_path / "adf" / "FEAT-1.adf.json"
    dest.parent.mkdir()
    dest.write_text("{}", encoding="utf-8")
    url = vr.viewer_edit_url("127.0.0.1", 5050, dest)
    assert url.startswith("http://127.0.0.1:5050/edit?path=")
    assert "FEAT-1.adf.json" in url
