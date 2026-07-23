#!/usr/bin/env python3
"""One-time local contributor setup for this repository.

Releases are automated by .github/workflows/release.yml: a new GitHub Release
is cut on every push to main, and its tag is what bootstrap.py reads. Because of
that, contributors no longer need a local version-bump hook. This script removes
the legacy managed pre-push version hook if an older checkout still installed it.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

HOOK_MARKER_START = "# BEGIN aii pre-push version hook"
HOOK_MARKER_END = "# END aii pre-push version hook"


def resolve_repo_root() -> Path:
    repo_root = Path(__file__).resolve().parent
    if (repo_root / ".git").exists():
        return repo_root

    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            "run this script inside a git repository clone") from exc
    return Path(completed.stdout.strip())


def remove_managed_pre_push_hook(repo_root: Path) -> None:
    pre_push_path = repo_root / ".git" / "hooks" / "pre-push"
    if not pre_push_path.exists():
        print("no managed pre-push hook to remove")
        return
    existing = pre_push_path.read_text(encoding="utf-8")
    managed = HOOK_MARKER_START in existing and HOOK_MARKER_END in existing
    if not managed:
        print("left .git/hooks/pre-push in place (not managed by aii)")
        return
    pre_push_path.unlink()
    print("removed legacy managed .git/hooks/pre-push")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def main() -> int:
    parse_args()
    repo_root = resolve_repo_root()
    remove_managed_pre_push_hook(repo_root)
    print("contributor setup complete: releases are automated on push to main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
