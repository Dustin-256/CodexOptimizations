#!/usr/bin/env python3
"""Increment aii/version.txt numeric tag (vN -> vN+1)."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


VERSION_PATH = Path.cwd() / "aii" / "version.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--set",
        metavar="VERSION",
        help="Set exact version tag (for example: v17 or 17).",
    )
    return parser.parse_args()


def parse_version(text: str) -> int:
    match = re.fullmatch(r"v?(\d+)", text.strip())
    if not match:
        raise ValueError(f"invalid version format: {text!r}; expected vN or N")
    return int(match.group(1))


def main() -> None:
    args = parse_args()

    current = VERSION_PATH.read_text(encoding="utf-8").strip() if VERSION_PATH.exists() else "v0"

    if args.set:
        next_value = parse_version(args.set)
    else:
        next_value = parse_version(current) + 1

    new_tag = f"v{next_value}"
    VERSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    VERSION_PATH.write_text(new_tag + "\n", encoding="utf-8")
    print(f"updated {VERSION_PATH} -> {new_tag}")


if __name__ == "__main__":
    main()
