#!/usr/bin/env python3
"""Install or remove the managed contributor version pre-push hook."""

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
        raise RuntimeError("run this script inside a git repository clone") from exc
    return Path(completed.stdout.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing non-managed pre-push hook.",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove managed pre-push hook if present.",
    )
    return parser.parse_args()


def build_pre_push_hook_script() -> str:
    return "\n".join(
        (
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            HOOK_MARKER_START,
            'repo_root="$(git rev-parse --show-toplevel)"',
            'cd "$repo_root"',
            "",
            'if [[ "${AII_SKIP_VERSION_BUMP:-}" == "1" ]]; then',
            "  exit 0",
            "fi",
            "",
            'if [[ ! -f "aii/scripts/bump_version.py" ]]; then',
            '  echo "pre-push: missing aii/scripts/bump_version.py; run bootstrap first." >&2',
            "  exit 1",
            "fi",
            "",
            'if [[ -n "$(git status --porcelain -- aii/version.txt)" ]]; then',
            '  echo "pre-push: aii/version.txt has uncommitted changes; commit or discard them before push." >&2',
            "  exit 1",
            "fi",
            "",
            "needs_bump=1",
            "saw_ref=0",
            "",
            "while read -r local_ref local_sha remote_ref remote_sha; do",
            "  saw_ref=1",
            "  if [[ \"$local_sha\" == \"0000000000000000000000000000000000000000\" ]]; then",
            "    continue",
            "  fi",
            "",
            "  if [[ \"$remote_sha\" == \"0000000000000000000000000000000000000000\" ]]; then",
            "    range=\"$local_sha\"",
            "  else",
            "    range=\"$remote_sha..$local_sha\"",
            "  fi",
            "",
            "  if git diff-tree --no-commit-id --name-only -r $range -- aii/version.txt | grep -qx 'aii/version.txt'; then",
            "    needs_bump=0",
            "    break",
            "  fi",
            "done",
            "",
            "if [[ \"$saw_ref\" -eq 0 ]]; then",
            "  if git diff-tree --no-commit-id --name-only -r HEAD -- aii/version.txt | grep -qx 'aii/version.txt'; then",
            "    needs_bump=0",
            "  fi",
            "fi",
            "",
            "if [[ \"$needs_bump\" -eq 0 ]]; then",
            "  exit 0",
            "fi",
            "",
            "python3 aii/scripts/bump_version.py",
            "git add aii/version.txt",
            'echo "pre-push: bumped and staged aii/version.txt. Commit it, then push again." >&2',
            "exit 1",
            HOOK_MARKER_END,
            "",
        )
    )


def install_pre_push_hook(repo_root: Path, force: bool) -> None:
    hooks_path = repo_root / ".git" / "hooks"
    pre_push_path = hooks_path / "pre-push"
    if not hooks_path.exists():
        raise RuntimeError(".git/hooks not found; run inside a git repository clone")

    new_script = build_pre_push_hook_script()
    if pre_push_path.exists():
        existing = pre_push_path.read_text(encoding="utf-8")
        managed = HOOK_MARKER_START in existing and HOOK_MARKER_END in existing
        if not managed and not force:
            raise RuntimeError(
                "existing .git/hooks/pre-push is not managed by this repo; rerun with --force to overwrite"
            )

    pre_push_path.write_text(new_script, encoding="utf-8")
    pre_push_path.chmod(pre_push_path.stat().st_mode | 0o111)
    print("installed managed .git/hooks/pre-push")


def uninstall_pre_push_hook(repo_root: Path) -> None:
    pre_push_path = repo_root / ".git" / "hooks" / "pre-push"
    if not pre_push_path.exists():
        print("managed pre-push hook not found")
        return
    existing = pre_push_path.read_text(encoding="utf-8")
    managed = HOOK_MARKER_START in existing and HOOK_MARKER_END in existing
    if not managed:
        raise RuntimeError("existing .git/hooks/pre-push is not managed by this repo; refusing to remove")
    pre_push_path.unlink()
    print("removed managed .git/hooks/pre-push")


def main(argv: list[str] | None = None) -> int:
    _ = argv
    args = parse_args()
    repo_root = resolve_repo_root()
    if args.uninstall:
        uninstall_pre_push_hook(repo_root)
        return 0
    install_pre_push_hook(repo_root, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
