"""I1 verify receipt is a machine artifact on LessonRecord, not title/body."""

from __future__ import annotations

import pytest

from sdlc_engine.lessons_ledger import LessonRecord
from sdlc_engine.verify_receipt import (
    SCHEMA_WITH_VERIFY,
    VerifyReceipt,
    VerifyReceiptError,
)


def test_title_body_only_has_no_verify_object() -> None:
    rec = LessonRecord(
        id="",
        kind="session",
        work_id="FEAT-001",
        title="T01 complete",
        body="Validation: pytest looked fine",
        source="capture",
        phase="code",
    )
    payload = rec.to_json()
    assert "verify" not in payload
    assert rec.verify.present() is False
    assert payload["schema"] == 1


def test_receipt_round_trips_command_exit_result() -> None:
    rec = LessonRecord(
        id="",
        kind="session",
        work_id="FEAT-001",
        body="T01 complete",
        source="capture",
        phase="code",
        verify=VerifyReceipt(command="pytest tests/test_foo.py", exit=0, result="pass"),
    )
    payload = rec.to_json()
    assert payload["verify"] == {
        "command": "pytest tests/test_foo.py",
        "exit": 0,
        "result": "pass",
    }
    assert payload["schema"] == SCHEMA_WITH_VERIFY
    restored = LessonRecord.from_json(payload)
    assert restored.verify.command == "pytest tests/test_foo.py"
    assert restored.verify.exit == 0
    assert restored.verify.result == "pass"


def test_from_capture_refuses_missing_receipt() -> None:
    with pytest.raises(VerifyReceiptError, match="verify receipt required"):
        VerifyReceipt.from_capture(required=True)


def test_complete_requires_pass() -> None:
    with pytest.raises(VerifyReceiptError, match="verify.result=pass"):
        VerifyReceipt.from_capture(
            command="pytest",
            exit=1,
            result="fail",
            require_pass=True,
        )
