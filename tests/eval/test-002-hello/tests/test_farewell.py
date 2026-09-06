"""Gold observable: farewell() must exist and return goodbye, {name}."""

from src.hello import farewell


def test_farewell() -> None:
    assert farewell("ada") == "goodbye, ada"
