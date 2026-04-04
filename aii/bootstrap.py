#!/usr/bin/env python3
"""Bootstrap or uninstall the local aii scaffold."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
RAW_BASE = "https://raw.githubusercontent.com/Dustin-256/CodexOptimizations/main"
SKILLS = (
    "deep-interview",
    "planner",
    "plan-executor",
    "plan-modifier",
    "resume-last-task",
)
AGENTS_PATH = ROOT / "AGENTS.md"
AGENTS_BAK_PATH = ROOT / "AGENTS.md.bak"
AII_PATH = ROOT / "aii"
GITIGNORE_PATH = ROOT / ".gitignore"
BACKUP_HEADER = (
    "THIS FILE IS TO NOT BE USED, IT IS SIMPLY A BACKUP OF AGENTS.MD "
    "ALWAYS REFER TO AGENTS.MD and ignore this."
)
GITIGNORE_BLOCK_START = "# BEGIN aii bootstrap"
GITIGNORE_BLOCK_END = "# END aii bootstrap"
GITIGNORE_BLOCK = "\n".join(
    (
        GITIGNORE_BLOCK_START,
        "aii/interviews/*",
        "!aii/interviews/.gitkeep",
        "",
        "aii/plans/*",
        "!aii/plans/.gitkeep",
        "",
        "aii/metadata/*",
        "!aii/metadata/.gitkeep",
        GITIGNORE_BLOCK_END,
    )
)

STATIC_FILES = {
    "aii/README.md": """# aii

`aii` stores reusable AI workflow artifacts for this repo.

## Layout
- `skills/`: opt-in skills such as `deep-interview`, `planner`, `plan-executor`, `plan-modifier`, and `resume-last-task`
- `interviews/`: saved markdown requirement handoff documents
- `plans/`: machine-readable YAML execution plans
- `metadata/`: shared resumable task state for workflows such as `$resume-last-task`

Use `python aii/bootstrap.py` to recreate the baseline scaffold if needed.
""",
    "aii/interviews/.gitkeep": "",
    "aii/plans/.gitkeep": "",
    "aii/metadata/.gitkeep": "",
    "aii/metadata/state.yaml": """last_task: null

history: []
""",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing scaffold files during install.",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove the aii scaffold and restore AGENTS.md from AGENTS.md.bak if present.",
    )
    return parser.parse_args()


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "codex-optimizations-bootstrap"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def build_remote_files() -> dict[str, str]:
    files: dict[str, str] = {
        "AGENTS.md": fetch_text(f"{RAW_BASE}/AGENTS.md"),
    }
    for skill in SKILLS:
        relative_path = f"aii/skills/{skill}/SKILL.md"
        files[relative_path] = fetch_text(f"{RAW_BASE}/aii/skills/{skill}/SKILL.md")
    return files


def write_file(relative_path: str, content: str, force: bool) -> None:
    path = ROOT / relative_path
    if path.exists() and not force:
        raise FileExistsError(
            f"{relative_path} already exists. Re-run with --force to overwrite."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"wrote {relative_path}")


def backup_agents() -> None:
    if not AGENTS_PATH.exists():
        return
    backup_content = f"{BACKUP_HEADER}\n\n{AGENTS_PATH.read_text(encoding='utf-8')}"
    AGENTS_BAK_PATH.write_text(backup_content, encoding="utf-8")
    print(f"wrote {AGENTS_BAK_PATH.relative_to(ROOT)}")


def restore_agents_backup() -> None:
    if not AGENTS_BAK_PATH.exists():
        if AGENTS_PATH.exists():
            AGENTS_PATH.unlink()
            print("removed AGENTS.md")
        return
    backup_content = AGENTS_BAK_PATH.read_text(encoding="utf-8")
    if backup_content.startswith(BACKUP_HEADER):
        restored = backup_content[len(BACKUP_HEADER) :].lstrip("\n")
    else:
        restored = backup_content
    AGENTS_PATH.write_text(restored, encoding="utf-8")
    AGENTS_BAK_PATH.unlink()
    print("restored AGENTS.md from AGENTS.md.bak")
    print("removed AGENTS.md.bak")


def update_gitignore_for_install() -> None:
    existing = GITIGNORE_PATH.read_text(encoding="utf-8") if GITIGNORE_PATH.exists() else ""
    if GITIGNORE_BLOCK_START in existing and GITIGNORE_BLOCK_END in existing:
        return
    new_content = existing.rstrip()
    if new_content:
        new_content += "\n\n"
    new_content += GITIGNORE_BLOCK + "\n"
    GITIGNORE_PATH.write_text(new_content, encoding="utf-8")
    print("updated .gitignore")


def update_gitignore_for_uninstall() -> None:
    if not GITIGNORE_PATH.exists():
        return
    content = GITIGNORE_PATH.read_text(encoding="utf-8")
    start = content.find(GITIGNORE_BLOCK_START)
    end = content.find(GITIGNORE_BLOCK_END)
    if start == -1 or end == -1:
        return
    end += len(GITIGNORE_BLOCK_END)
    new_content = (content[:start] + content[end:]).strip()
    if new_content:
        new_content += "\n"
        GITIGNORE_PATH.write_text(new_content, encoding="utf-8")
        print("updated .gitignore")
    else:
        GITIGNORE_PATH.unlink()
        print("removed .gitignore")


def install(force: bool) -> None:
    files = {**STATIC_FILES, **build_remote_files()}
    backup_agents()
    for relative_path, content in files.items():
        write_file(relative_path, content, force=force)
    update_gitignore_for_install()


def uninstall() -> None:
    if AII_PATH.exists():
        shutil.rmtree(AII_PATH)
        print("removed aii/")
    restore_agents_backup()
    update_gitignore_for_uninstall()


def main() -> None:
    args = parse_args()
    if args.uninstall:
        uninstall()
        return
    install(force=args.force)


if __name__ == "__main__":
    main()
