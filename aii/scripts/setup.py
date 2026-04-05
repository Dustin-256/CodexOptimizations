#!/usr/bin/env python3
"""Bootstrap or uninstall the local aii scaffold."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


BASE_DIR = Path.cwd()
RAW_BASE = "https://raw.githubusercontent.com/Dustin-256/CodexOptimizations/main"
SKILLS = (
    "deep-interview",
    "planner",
    "plan-executor",
    "plan-modifier",
    "resume-last-task",
)
SCRIPTS = (
    "send_webhook_embed.py",
    "bump_version.py",
)
CODEX_SKILLS_DIR = Path.home() / ".codex" / "skills"
ENV_PATH = BASE_DIR / ".env"
ENV_KEY_WEBHOOK = "codex_webhook"
ENV_KEY_IGNORE_WEBHOOK_MISSING = "codex_ignore_webhook_missing"
AGENTS_PATH = BASE_DIR / "AGENTS.md"
AGENTS_BAK_PATH = BASE_DIR / "AGENTS.md.bak"
AFTMAN_PATHS = (
    BASE_DIR / "aftman.toml",
    BASE_DIR / ".aftman.toml",
)
AGENTS_TEMPLATE_PATHS = {
    "generic": "agents/generic.md",
    "roblox": "agents/Roblox.MD",
}
ALWAYS_OVERWRITE_FILES = {
    "ProjectInstructions.md",
}
AII_PATH = BASE_DIR / "aii"
GITIGNORE_PATH = BASE_DIR / ".gitignore"
GIT_HOOKS_PATH = BASE_DIR / ".git" / "hooks"
PRE_PUSH_HOOK_PATH = GIT_HOOKS_PATH / "pre-push"
HOOK_MARKER_START = "# BEGIN aii pre-push version hook"
HOOK_MARKER_END = "# END aii pre-push version hook"
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

`aii` is the working area for structured AI execution in this repository.

## Why this is useful

It keeps planning and execution artifacts in one predictable place so work can be resumed cleanly across sessions and collaborators.

## What it can do

- provide a home for reusable skill definitions in `skills/`
- provide shared automation scripts in `scripts/`
- preserve requirements in `interviews/`
- track execution plans in `plans/`
- persist resumable task state in `metadata/`

## Layout
- `skills/`: opt-in skills such as `deep-interview`, `planner`, `plan-executor`, `plan-modifier`, and `resume-last-task`
- `scripts/`: reusable helpers such as `send_webhook_embed.py` for standardized Discord embeds
- `interviews/`: saved markdown requirement handoff documents
- `plans/`: machine-readable YAML execution plans
- `metadata/`: shared resumable task state for workflows such as `$resume-last-task`

## Skill roles

- `deep-interview`: captures requirements, constraints, assumptions, and ambiguity into a structured interview artifact.
- `planner`: turns the interview artifact into an executable YAML plan under `aii/plans/`.
- `plan-executor`: executes or resumes a plan step-by-step while persisting progress and blockers.
- `plan-modifier`: updates an existing plan in place when scope changes or blockers require plan revisions.
- `resume-last-task`: restores the most recent resumable task context from `aii/metadata/` and continues work.

Typical flow: interview -> plan -> execute -> modify (if needed) -> resume later.

## How to use it

1. Bootstrap the repo with `python3 bootstrap.py`.
2. Run a requirements interview and save it in `interviews/`.
3. Generate an execution plan into `plans/`.
4. Execute or modify the plan while persisting progress in `metadata/`.
5. Resume later using the saved state instead of starting over.

Use `python bootstrap.py` to recreate the baseline scaffold if needed.
""",
    "ProjectInstructions.md": """# Project Instructions

This file is used for project-specific instructions that AI assistants must follow when working in this repository.
Use it to define constraints, conventions, workflows, architecture rules, and any non-negotiable requirements that are unique to your project.

## Add Your Instructions Here
- Add clear project rules and constraints.
- Add required build, test, and deployment commands.
- Add architecture and coding standards specific to this project.
- Add domain-specific terminology, behavior rules, and guardrails.
""",
    "version.txt": "v1\n",
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
        "--type",
        dest="project_type",
        choices=("auto", "generic", "roblox"),
        default="auto",
        help=(
            "Project template type for AGENTS.md. "
            "auto: infer from aftman.toml and rojo; generic: force generic; roblox: force Roblox."
        ),
    )
    parser.add_argument(
        "--install-pre-push-hook",
        action="store_true",
        help="Install/update the managed git pre-push version bump hook (contributor workflow).",
    )
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
    parser.add_argument(
        "--no-install-skills",
        action="store_true",
        help="Scaffold repo files only; do not symlink skills into ~/.codex/skills.",
    )
    parser.add_argument(
        "--webhook",
        metavar="URL",
        help="Persist Discord webhook URL to .env as codex_webhook for embed webhook reports.",
    )
    parser.add_argument(
        "--always-skip-missing-webhook",
        action="store_true",
        help=(
            "Persist codex_ignore_webhook_missing=true in .env so runs do not halt when "
            "codex_webhook is missing."
        ),
    )
    parser.add_argument(
        "--test-webhook-embed",
        action="store_true",
        help="Send a test embed webhook report and exit.",
    )
    return parser.parse_args()


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "codex-optimizations-bootstrap"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def _strip_comment(line: str) -> str:
    return line.split("#", 1)[0].strip()


def _aftman_has_rojo(path: Path) -> bool:
    in_tools_block = False
    section_header = re.compile(r"^\[(.+)\]$")
    for line in path.read_text(encoding="utf-8").splitlines():
        cleaned = _strip_comment(line)
        if not cleaned:
            continue
        header_match = section_header.match(cleaned)
        if header_match:
            in_tools_block = header_match.group(1).strip() == "tools"
            continue
        if in_tools_block and re.match(r"^rojo\s*=", cleaned):
            return True
    return False


def detect_project_type(requested_type: str) -> str:
    if requested_type in {"generic", "roblox"}:
        return requested_type

    for aftman_path in AFTMAN_PATHS:
        if aftman_path.exists() and _aftman_has_rojo(aftman_path):
            return "roblox"
    return "generic"


def read_local_relative(relative_path: str) -> str | None:
    candidates = (
        BASE_DIR / relative_path,
        Path(__file__).resolve().parents[2] / relative_path,
    )
    for local_path in candidates:
        if local_path.exists():
            return local_path.read_text(encoding="utf-8")
    return None


def truncate_discord_message(message: str, limit: int = 2000) -> str:
    if len(message) <= limit:
        return message
    return message[: limit - 3] + "..."


def _build_webhook_embed(action: str, status: str, details: str) -> dict[str, object]:
    color_by_status = {
        "succeeded": 0x2ECC71,
        "failed": 0xE74C3C,
        "progress": 0x3498DB,
    }
    emoji_by_status = {
        "succeeded": "✅",
        "failed": "❌",
        "progress": "🔄",
    }
    normalized = status if status in color_by_status else "succeeded"
    return {
        "title": f"{emoji_by_status[normalized]} bootstrap.py {action} {normalized}",
        "description": "Bootstrap execution report",
        "color": color_by_status[normalized],
        "fields": [
            {"name": "Repository", "value": str(BASE_DIR), "inline": False},
            {"name": "Details", "value": truncate_discord_message(details, 1000), "inline": False},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def send_webhook_report(
    webhook_url: str | None, *, action: str, status: str, details: str
) -> None:
    if not webhook_url:
        return

    payload = json.dumps(
        {
            "embeds": [_build_webhook_embed(action=action, status=status, details=details)],
            "allowed_mentions": {"parse": []},
        }
    ).encode("utf-8")
    request = Request(
        webhook_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "codex-optimizations-bootstrap",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30):
            pass
    except URLError as exc:
        print(f"warning: failed to send webhook report: {exc}")


def load_codex_webhook(env_path: Path = ENV_PATH) -> str | None:
    return load_env_value(ENV_KEY_WEBHOOK, env_path=env_path)


def load_codex_ignore_webhook_missing(env_path: Path = ENV_PATH) -> bool:
    value = load_env_value(ENV_KEY_IGNORE_WEBHOOK_MISSING, env_path=env_path)
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_env_value(key: str, env_path: Path = ENV_PATH) -> str | None:
    if not env_path.exists():
        return None
    key_prefix = f"{key}="
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :].lstrip()
        if not stripped.startswith(key_prefix):
            continue
        value = stripped.split("=", 1)[1].strip()
        return value.strip("\"'")
    return None


def save_codex_webhook(webhook_url: str, env_path: Path = ENV_PATH) -> None:
    save_env_value(ENV_KEY_WEBHOOK, webhook_url, env_path=env_path)
    print("updated .env with codex_webhook for embed webhook reports")


def save_codex_ignore_webhook_missing(
    should_ignore: bool, env_path: Path = ENV_PATH
) -> None:
    save_env_value(
        ENV_KEY_IGNORE_WEBHOOK_MISSING,
        "true" if should_ignore else "false",
        env_path=env_path,
    )
    print(
        "updated .env with codex_ignore_webhook_missing="
        + ("true" if should_ignore else "false")
    )


def save_env_value(key: str, value: str, env_path: Path = ENV_PATH) -> None:
    new_entry = f"{key}={value}"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []

    replaced = False
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        comparison = stripped
        if comparison.startswith("export "):
            comparison = comparison[len("export ") :].lstrip()
        if comparison.startswith(f"{key}="):
            if not replaced:
                new_lines.append(new_entry)
                replaced = True
            continue
        new_lines.append(line)

    if not replaced:
        new_lines.append(new_entry)

    env_path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")


def load_agents_template(project_type: str) -> str:
    relative_path = AGENTS_TEMPLATE_PATHS[project_type]
    local_content = read_local_relative(relative_path)
    if local_content is not None:
        return local_content
    return fetch_text(f"{RAW_BASE}/{relative_path}")


def build_remote_files(project_type: str) -> dict[str, str]:
    files: dict[str, str] = {
        "AGENTS.md": load_agents_template(project_type),
    }
    for skill in SKILLS:
        relative_path = f"aii/skills/{skill}/SKILL.md"
        files[relative_path] = fetch_text(f"{RAW_BASE}/aii/skills/{skill}/SKILL.md")
    for script in SCRIPTS:
        relative_path = f"aii/scripts/{script}"
        local_content = read_local_relative(relative_path)
        if local_content is not None:
            files[relative_path] = local_content
            continue
        files[relative_path] = fetch_text(f"{RAW_BASE}/aii/scripts/{script}")
    return files


def write_file(relative_path: str, content: str, force: bool) -> None:
    path = BASE_DIR / relative_path
    if path.exists() and not force and relative_path not in ALWAYS_OVERWRITE_FILES:
        raise FileExistsError(
            f"{relative_path} already exists. Re-run with --force to overwrite."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path}")


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
            'if [[ -n "$(git status --porcelain -- version.txt)" ]]; then',
            '  echo "pre-push: version.txt has uncommitted changes; commit or discard them before push." >&2',
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
            "  if git diff-tree --no-commit-id --name-only -r $range -- version.txt | grep -qx 'version.txt'; then",
            "    needs_bump=0",
            "    break",
            "  fi",
            "done",
            "",
            "if [[ \"$saw_ref\" -eq 0 ]]; then",
            "  if git diff-tree --no-commit-id --name-only -r HEAD -- version.txt | grep -qx 'version.txt'; then",
            "    needs_bump=0",
            "  fi",
            "fi",
            "",
            "if [[ \"$needs_bump\" -eq 0 ]]; then",
            "  exit 0",
            "fi",
            "",
            "python3 aii/scripts/bump_version.py",
            "git add version.txt",
            'echo "pre-push: bumped and staged version.txt. Commit it, then push again." >&2',
            "exit 1",
            HOOK_MARKER_END,
            "",
        )
    )


def install_pre_push_hook(force: bool) -> None:
    if not GIT_HOOKS_PATH.exists():
        print("skipped pre-push hook install: .git/hooks not found")
        return

    new_script = build_pre_push_hook_script()
    if PRE_PUSH_HOOK_PATH.exists():
        existing = PRE_PUSH_HOOK_PATH.read_text(encoding="utf-8")
        managed = HOOK_MARKER_START in existing and HOOK_MARKER_END in existing
        if not managed and not force:
            print(
                "left existing .git/hooks/pre-push in place "
                "(not managed by aii; re-run with --force to overwrite)"
            )
            return

    PRE_PUSH_HOOK_PATH.write_text(new_script, encoding="utf-8")
    current_mode = PRE_PUSH_HOOK_PATH.stat().st_mode
    PRE_PUSH_HOOK_PATH.chmod(current_mode | 0o111)
    print("installed managed .git/hooks/pre-push")


def uninstall_pre_push_hook() -> None:
    if not PRE_PUSH_HOOK_PATH.exists():
        return
    existing = PRE_PUSH_HOOK_PATH.read_text(encoding="utf-8")
    managed = HOOK_MARKER_START in existing and HOOK_MARKER_END in existing
    if not managed:
        print("left .git/hooks/pre-push in place (not managed by aii)")
        return
    PRE_PUSH_HOOK_PATH.unlink()
    print("removed managed .git/hooks/pre-push")


def backup_agents() -> None:
    if not AGENTS_PATH.exists():
        return
    backup_content = f"{BACKUP_HEADER}\n\n{AGENTS_PATH.read_text(encoding='utf-8')}"
    AGENTS_BAK_PATH.write_text(backup_content, encoding="utf-8")
    print(f"wrote {AGENTS_BAK_PATH}")


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


def install_codex_skills(force: bool) -> None:
    CODEX_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    for skill in SKILLS:
        source = AII_PATH / "skills" / skill
        target = CODEX_SKILLS_DIR / skill
        if target.exists() or target.is_symlink():
            if target.is_symlink() and target.resolve() == source.resolve():
                continue
            if not force:
                raise FileExistsError(
                    f"{target} already exists. Re-run with --force to overwrite."
                )
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
        target.symlink_to(source, target_is_directory=True)
        print(f"linked {target} -> {source}")


def uninstall_codex_skills() -> None:
    for skill in SKILLS:
        target = CODEX_SKILLS_DIR / skill
        if not target.exists() and not target.is_symlink():
            continue
        if target.is_symlink():
            target.unlink()
            print(f"removed {target}")
            continue
        print(f"left {target} in place because it is not a symlink")


def install(
    force: bool,
    install_skills: bool,
    project_type: str,
    install_pre_push_hook_enabled: bool,
) -> None:
    files = {**STATIC_FILES, **build_remote_files(project_type)}
    backup_agents()
    for relative_path, content in files.items():
        write_file(relative_path, content, force=force)
    update_gitignore_for_install()
    if install_pre_push_hook_enabled:
        install_pre_push_hook(force=force)
    if install_skills:
        install_codex_skills(force=force)


def uninstall() -> None:
    uninstall_codex_skills()
    uninstall_pre_push_hook()
    if AII_PATH.exists():
        shutil.rmtree(AII_PATH)
        print("removed aii/")
    restore_agents_backup()
    update_gitignore_for_uninstall()


def main() -> None:
    args = parse_args()
    resolved_project_type = detect_project_type(args.project_type)
    if args.webhook:
        save_codex_webhook(args.webhook)
    if args.always_skip_missing_webhook:
        save_codex_ignore_webhook_missing(True)

    webhook_url = args.webhook or load_codex_webhook()
    ignore_missing_webhook = load_codex_ignore_webhook_missing()
    if not webhook_url and not ignore_missing_webhook:
        raise RuntimeError(
            "codex_webhook is missing. Set it in .env or run with "
            "--webhook URL. To always skip this gate, run with "
            "--always-skip-missing-webhook once."
        )

    if args.test_webhook_embed:
        if not webhook_url:
            print("webhook missing; no test embed sent")
            return
        send_webhook_report(
            webhook_url,
            action="test",
            status="progress",
            details="embed delivery test from bootstrap.py",
        )
        print("sent webhook embed test")
        return

    action = "uninstall" if args.uninstall else "install"
    try:
        send_webhook_report(
            webhook_url,
            action=action,
            status="progress",
            details="starting scaffold operation",
        )
        if args.uninstall:
            uninstall()
        else:
            print(f"using project type: {resolved_project_type}")
            install(
                force=args.force,
                install_skills=not args.no_install_skills,
                project_type=resolved_project_type,
                install_pre_push_hook_enabled=args.install_pre_push_hook,
            )
        send_webhook_report(
            webhook_url,
            action=action,
            status="progress",
            details="scaffold operation reached finalization stage",
        )
        send_webhook_report(
            webhook_url,
            action=action,
            status="succeeded",
            details="scaffold operation completed successfully",
        )
    except Exception as exc:
        send_webhook_report(
            webhook_url,
            action=action,
            status="failed",
            details=f"{type(exc).__name__}: {exc}",
        )
        raise


if __name__ == "__main__":
    main()
