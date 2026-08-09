import json
from pathlib import Path

from sdlc_engine.cli import main


def test_cli_claim_next_archive(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "cli-user")
    work_id = "FEAT-030-cli"
    canvas = tmp_path / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True)
    canvas.write_text(
        f"# {work_id}\n\n## Final Status\n\n- Status: Complete\n",
        encoding="utf-8",
    )
    assert main(["--root", str(tmp_path), "claim", work_id]) == 0
    assert main(["--root", str(tmp_path), "next"]) == 0
    assert main(["--root", str(tmp_path), "archive", work_id]) == 0
    assert (tmp_path / "spdd" / "canvas" / "archive" / f"{work_id}.md").is_file()
    assert main(["--root", str(tmp_path), "version"]) == 0


def test_cli_version_flag() -> None:
    assert main(["--version"]) == 0


def test_cli_work_init_from_adf(tmp_path: Path, capsys) -> None:
    adf = tmp_path / "adf" / "ORCH-12.adf.json"
    adf.parent.mkdir(parents=True)
    adf.write_text(
        json.dumps(
            {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "heading",
                        "attrs": {"level": 1},
                        "content": [{"type": "text", "text": "CLI init"}],
                    },
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "from cli"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    dry = main(
        [
            "--root",
            str(tmp_path),
            "work",
            "init-from-adf",
            "--path",
            str(adf),
            "--work-id",
            "FEAT-013-cli-adf-init",
            "--no-claim",
            "--dry-run",
        ]
    )
    assert dry == 0
    out = capsys.readouterr().out
    assert "FEAT-013-cli-adf-init" in out
    assert "[dry-run]" in out
    assert not (tmp_path / "spdd" / "canvas" / "FEAT-013-cli-adf-init.md").exists()

    rc = main(
        [
            "--root",
            str(tmp_path),
            "work",
            "init-from-adf",
            "--path",
            str(adf),
            "--work-id",
            "FEAT-013-cli-adf-init",
            "--title",
            "CLI title",
            "--no-claim",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Created FEAT-013-cli-adf-init" in out
    assert "/sdlc-spdd-analysis @" in out
    canvas = tmp_path / "spdd" / "canvas" / "FEAT-013-cli-adf-init.md"
    assert canvas.is_file()
    text = canvas.read_text(encoding="utf-8")
    assert "CLI title" in text
    assert "from cli" in text

    again = main(
        [
            "--root",
            str(tmp_path),
            "work",
            "init-from-adf",
            "--path",
            str(adf),
            "--work-id",
            "FEAT-013-cli-adf-init",
            "--no-claim",
        ]
    )
    assert again == 1
    err = capsys.readouterr().err
    assert "already exists" in err


def test_cli_work_init_from_adf_missing_path(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "--root",
            str(tmp_path),
            "work",
            "init-from-adf",
            "--path",
            str(tmp_path / "gone.adf.json"),
            "--no-claim",
        ]
    )
    assert rc == 1
    assert "not found" in capsys.readouterr().err.lower()


def test_cli_work_init_from_adf_claims_by_default(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("SDLC_USER", "cli-claim")
    adf = tmp_path / "ORCH-21.adf.json"
    adf.write_text(
        json.dumps(
            {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "heading",
                        "attrs": {"level": 1},
                        "content": [{"type": "text", "text": "Claim via CLI"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rc = main(
        [
            "--root",
            str(tmp_path),
            "work",
            "init-from-adf",
            "--path",
            str(adf),
            "--work-id",
            "FEAT-013-cli-claim-default",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Created FEAT-013-cli-claim-default" in out
    reg_path = tmp_path / "spdd" / "memory" / "registry.jsonl"
    assert reg_path.is_file()
    assert "cli-claim" in reg_path.read_text(encoding="utf-8")
    assert (tmp_path / ".sdlc" / "pointer").read_text(encoding="utf-8").strip() == (
        "FEAT-013-cli-claim-default"
    )


def test_cli_work_init_from_adf_invalid_json(tmp_path: Path, capsys) -> None:
    adf = tmp_path / "broken.adf.json"
    adf.write_text("{broken", encoding="utf-8")
    rc = main(
        [
            "--root",
            str(tmp_path),
            "work",
            "init-from-adf",
            "--path",
            str(adf),
            "--no-claim",
        ]
    )
    assert rc == 1
    assert capsys.readouterr().err.strip()


def test_cli_work_init_from_adf_claim_conflict(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("SDLC_USER", "bob")
    wid = "FEAT-013-cli-conflict"
    (tmp_path / "spdd" / "memory").mkdir(parents=True, exist_ok=True)
    reg_jsonl = tmp_path / "spdd" / "memory" / "registry.jsonl"
    reg_jsonl.write_text(
        json.dumps(
            {
                "event": "claim",
                "work_id": wid,
                "status": "active",
                "phase": "analysis",
                "owner": "alice",
                "note": "seed",
                "ts": "2026-01-01T00:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    adf = tmp_path / "x.adf.json"
    adf.write_text(
        json.dumps({"type": "doc", "version": 1, "content": []}),
        encoding="utf-8",
    )
    rc = main(
        [
            "--root",
            str(tmp_path),
            "work",
            "init-from-adf",
            "--path",
            str(adf),
            "--work-id",
            wid,
        ]
    )
    assert rc == 1
    assert "alice" in capsys.readouterr().err
    assert not (tmp_path / "spdd" / "canvas" / f"{wid}.md").exists()
