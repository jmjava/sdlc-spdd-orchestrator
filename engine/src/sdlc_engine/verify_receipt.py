"""Kasana I1 machine artifact: command + exit + pass/fail on a lesson.

Prompt-only Validation text is not a receipt. ``sdlc.sh capture`` (code)
and ``sdlc.sh complete`` refuse unless this object is present.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

VERIFY_RESULTS = ("pass", "fail")

# Ledger schema bump when a record carries a verify receipt.
SCHEMA_WITH_VERIFY = 3


class VerifyReceiptError(ValueError):
    """Missing or invalid I1 verify receipt."""


@dataclass
class VerifyReceipt:
    command: str = ""
    exit: int | None = None
    result: str = ""

    def present(self) -> bool:
        return bool(self.command.strip()) and self.exit is not None and bool(
            (self.result or "").strip()
        )

    def validate(self) -> None:
        command = (self.command or "").strip()
        if not command:
            raise VerifyReceiptError(
                "verify receipt required: command, exit, and pass/fail result"
            )
        if self.exit is None:
            raise VerifyReceiptError(
                "verify receipt required: command, exit, and pass/fail result"
            )
        try:
            exit_code = int(self.exit)
        except (TypeError, ValueError) as exc:
            raise VerifyReceiptError("verify.exit must be an integer") from exc
        result = (self.result or "").strip().lower()
        if result not in VERIFY_RESULTS:
            raise VerifyReceiptError(
                f"verify.result must be one of {'|'.join(VERIFY_RESULTS)}"
            )
        self.command = command
        self.exit = exit_code
        self.result = result

    def require_pass(self) -> None:
        self.validate()
        if self.result != "pass":
            raise VerifyReceiptError(
                "complete requires verify.result=pass (do not mark T## complete on fail)"
            )

    def to_json(self) -> dict[str, Any]:
        if not self.present():
            return {}
        return {
            "command": self.command,
            "exit": int(self.exit) if self.exit is not None else None,
            "result": self.result,
        }

    @classmethod
    def from_json(cls, data: Any) -> "VerifyReceipt":
        if not data or not isinstance(data, dict):
            return cls()
        command = str(data.get("command") or "").strip()
        raw_exit = data.get("exit")
        result = str(data.get("result") or "").strip().lower()
        exit_code: int | None
        if raw_exit in (None, ""):
            exit_code = None
        else:
            try:
                exit_code = int(raw_exit)
            except (TypeError, ValueError):
                exit_code = None
        if result and result not in VERIFY_RESULTS:
            result = ""
        return cls(command=command, exit=exit_code, result=result)

    @classmethod
    def from_capture(
        cls,
        *,
        command: str | None = None,
        exit: Any = None,
        result: str | None = None,
        required: bool = False,
        require_pass: bool = False,
    ) -> "VerifyReceipt":
        receipt = cls(
            command=(command or "").strip(),
            exit=None if exit in (None, "") else exit,
            result=(result or "").strip().lower(),
        )
        if required or receipt.present() or require_pass:
            if require_pass:
                receipt.require_pass()
            else:
                receipt.validate()
        return receipt
