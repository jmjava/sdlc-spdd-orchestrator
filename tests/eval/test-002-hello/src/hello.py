"""Minimal hello app — TEST-002 frozen gold (copy of live-consumer seed + new AC)."""


def greet(name: str = "world") -> str:
    return f"hello, {name}"


if __name__ == "__main__":
    print(greet())
