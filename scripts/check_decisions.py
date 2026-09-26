"""Fail when the decision records in docs/decisions/ disagree with each other.

Usage: python scripts/check_decisions.py [FOLDER]
"""

import sys
from pathlib import Path

from tracemem.decisions import check_folder


def main() -> int:
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "docs" / "decisions"
    errors = check_folder(folder)
    for message in errors:
        print(f"error: {message}")
    if errors:
        return 1
    print(f"decision records OK ({folder})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
