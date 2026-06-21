"""Compatibility entry point; prefer ``python -m tree_age.cli`` or ``tree-age``."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from tree_age.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
