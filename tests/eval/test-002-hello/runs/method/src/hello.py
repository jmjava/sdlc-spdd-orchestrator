"""Full SDLC-SPDD condition (n=1): only the frozen T01 farewell()."""


def greet(name: str = "world") -> str:
    return f"hello, {name}"


def farewell(name: str) -> str:
    return f"goodbye, {name}"


if __name__ == "__main__":
    print(greet())
    print(farewell("ada"))
