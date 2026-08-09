import subprocess
from pathlib import Path

from sdlc_engine.cli import main
from sdlc_engine.commit_message import CommitMessageError, CommitMessageService
from sdlc_engine.project import Project


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _init_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("# demo\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")
    # create a main branch alias for merge-base resolution when default is master
    cur = subprocess.check_output(
        ["git", "-C", str(root), "branch", "--show-current"], text=True
    ).strip()
    if cur != "main":
        _git(root, "branch", "-M", "main")
    return root


def test_collect_prefers_staged(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    (root / "a.txt").write_text("staged\n", encoding="utf-8")
    _git(root, "add", "a.txt")
    (root / "b.txt").write_text("unstaged-only\n", encoding="utf-8")
    snap = CommitMessageService(Project(root)).collect()
    assert snap.source == "staged"
    assert "a.txt" in snap.files
    assert "b.txt" not in snap.files
    assert "+staged" in snap.diff_text


def test_collect_falls_back_to_unstaged(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    (root / "README.md").write_text("# demo\nchanged\n", encoding="utf-8")
    snap = CommitMessageService(Project(root)).collect()
    assert snap.source == "unstaged"
    assert "README.md" in snap.files


def test_collect_ahead_of_base(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _git(root, "checkout", "-b", "feature")
    (root / "feat.txt").write_text("x\n", encoding="utf-8")
    _git(root, "add", "feat.txt")
    _git(root, "commit", "-m", "add feat")
    snap = CommitMessageService(Project(root)).collect(base="main")
    assert snap.source == "ahead-of-base"
    assert snap.base_ref == "main"
    assert "feat.txt" in snap.files
    assert any("add feat" in c for c in snap.ahead_commits)


def test_collect_empty_fails(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    try:
        CommitMessageService(Project(root)).collect(base="main")
        assert False, "expected CommitMessageError"
    except CommitMessageError as exc:
        assert "nothing to commit" in str(exc)


def test_cli_commit_message_text_and_json(tmp_path: Path, capsys) -> None:
    root = _init_repo(tmp_path)
    (root / "c.txt").write_text("cli\n", encoding="utf-8")
    _git(root, "add", "c.txt")
    assert main(["--root", str(root), "commit-message", "--hint", "ship it", "--work-id", "FEAT-008"]) == 0
    out = capsys.readouterr().out
    assert "source: staged" in out
    assert "work_id: FEAT-008" in out
    assert "hint: ship it" in out
    assert "c.txt" in out
    assert main(["--root", str(root), "commit-message", "--json"]) == 0
    jout = capsys.readouterr().out
    assert '"source": "staged"' in jout
