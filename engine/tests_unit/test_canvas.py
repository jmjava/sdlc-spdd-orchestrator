from pathlib import Path

from sdlc_engine.canvas import final_kind, next_operation


def test_final_kind_variants(tmp_path: Path) -> None:
    p = tmp_path / "c.md"
    p.write_text("## Final Status\n\n- Status: Complete (T01–T03)\n", encoding="utf-8")
    assert final_kind(p) == "complete"
    p.write_text("## Final Status\n\n- Status: Cancelled\n", encoding="utf-8")
    assert final_kind(p) == "cancelled"
    p.write_text("## Final Status\n\n- Status: Canceled — cut\n", encoding="utf-8")
    assert final_kind(p) == "cancelled"
    p.write_text("## Final Status\n\n- Status: In Progress\n", encoding="utf-8")
    assert final_kind(p) == "other"


def test_next_operation(tmp_path: Path) -> None:
    p = tmp_path / "ops.md"
    p.write_text(
        """# x
## Operations
### T01 - Done thing
- Status: Complete
### T02 - Next thing
- Status: Not Started
""",
        encoding="utf-8",
    )
    op, title = next_operation(p)
    assert op == "T02"
    assert "Next thing" in title
