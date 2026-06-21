"""Run the CLI without relying on an installed console-script launcher."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
