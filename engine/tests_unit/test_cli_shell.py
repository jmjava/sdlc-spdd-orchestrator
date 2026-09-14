from pathlib import Path

import pytest

from sdlc_engine.cli import main


def _write_helper(path: Path, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "#!/bin/sh\n"
        f'printf "{label}|%s|%s\\n" "$PWD" "$*"\n',
        encoding="utf-8",
    )
    path.chmod(0o755)


@pytest.mark.parametrize(
    ("relative_dir", "script_arg"),
    [
        ("scripts", "bridge-helper"),
        ("sdlc-spdd/scripts", "bridge-helper.sh"),
    ],
)
def test_shell_bridge_runs_source_and_installed_helpers(
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
    relative_dir: str,
    script_arg: str,
) -> None:
    helper = tmp_path / relative_dir / "bridge-helper.sh"
    _write_helper(helper, relative_dir)

    assert main(["--root", str(tmp_path), "shell", script_arg, "alpha", "beta"]) == 0

    output = capfd.readouterr().out.strip()
    assert output == f"{relative_dir}|{tmp_path}|alpha beta"


def test_shell_bridge_prefers_orchestrator_scripts(
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
) -> None:
    _write_helper(tmp_path / "scripts" / "same-name.sh", "source")
    _write_helper(tmp_path / "sdlc-spdd" / "scripts" / "same-name.sh", "installed")

    assert main(["--root", str(tmp_path), "shell", "same-name"]) == 0

    assert capfd.readouterr().out.startswith("source|")


def test_shell_bridge_reports_missing_script(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--root", str(tmp_path), "shell", "not-installed"]) == 1
    assert (
        capsys.readouterr().err.strip()
        == "shell bridge: script not found: not-installed"
    )
