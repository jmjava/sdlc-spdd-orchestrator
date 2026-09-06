"""Unstructured-chat condition (n=1, operator-as-agent). Extra shout() is C-DRIFT."""


def greet(name: str = "world") -> str:
    return f"hello, {name}"


def farewell(name: str) -> str:
    return f"goodbye, {name}"


def shout(name: str) -> str:
    """Not on the gold canvas — unmapped extra behavior."""
    return f"HELLO, {name.upper()}!"


if __name__ == "__main__":
    print(greet())
    print(farewell("ada"))
    print(shout("ada"))
