"""Stable module/console entrypoint; implementation lives in app/."""

# Direct file execution puts this package directory on sys.path instead of
# src/. Supply the package context that Python normally sets for `python -m`.
if not __package__:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "cityflo_ai_engineer_assignment"

from .app.cli import main as run_cli
from .app.server import create_server

mcp = create_server()


def main() -> None:
    run_cli(mcp)


if __name__ == "__main__":
    main()
