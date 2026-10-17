"""Result object returned by CLI command ``run()`` handlers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CommandResult:
    """Handler return type. ``cli.main`` is the only printer."""

    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""

    @classmethod
    def ok(cls, text: str = "", *, end: str = "\n") -> CommandResult:
        return cls(0, stdout=f"{text}{end}" if text or end else "")

    @classmethod
    def raw(cls, text: str, *, code: int = 0) -> CommandResult:
        """Write ``text`` exactly (for former ``print(..., end="")``)."""
        return cls(code, stdout=text)

    @classmethod
    def error(cls, text: str, *, code: int = 1, end: str = "\n") -> CommandResult:
        return cls(code, stderr=f"{text}{end}" if text or end else "")

    def emit(self) -> int:
        import sys

        if self.stdout:
            sys.stdout.write(self.stdout)
        if self.stderr:
            sys.stderr.write(self.stderr)
        return int(self.exit_code)
