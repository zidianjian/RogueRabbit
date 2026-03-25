from rogue_rabbit import CURRENT_PHASE, __version__


def build_banner() -> str:
    return f"RogueRabbit {__version__} {CURRENT_PHASE}"


def main() -> None:
    print(build_banner())


if __name__ == "__main__":
    main()
