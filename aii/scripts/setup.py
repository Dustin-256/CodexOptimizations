#!/usr/bin/env python3
"""Bootstrap or uninstall the local aii scaffold."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.error import URLError
from urllib.request import Request, urlopen

try:
    import termios
    import tty
except ImportError:
    termios = None
    tty = None

try:
    import msvcrt
except ImportError:
    msvcrt = None


BASE_DIR = Path.cwd()
RAW_BASE = "https://raw.githubusercontent.com/Dustin-256/CodexOptimizations/main"
SKILLS = (
    "code-review",
    "deep-interview",
    "fetch-models",
    "planner",
    "plan-executor",
    "plan-modifier",
    "resume-last-task",
)
SCRIPTS = (
    "send_webhook_embed.py",
    "bump_version.py",
    "fetch_models.py",
)
CODEX_SKILLS_DIR = Path.home() / ".codex" / "skills"
ENV_PATH = BASE_DIR / ".env"
ENV_KEY_NOTIFICATION_PROVIDER = "codex_notification_provider"
ENV_KEY_WEBHOOK = "codex_webhook"
ENV_KEY_TELEGRAM_BOT_TOKEN = "codex_telegram_bot_token"
ENV_KEY_TELEGRAM_CHAT_ID = "codex_telegram_chat_id"
ENV_KEY_IGNORE_WEBHOOK_MISSING = "codex_ignore_webhook_missing"
DEFAULT_NOTIFICATION_PROVIDER = "discord"
TELEGRAM_API_BASE = "https://api.telegram.org"
AGENTS_PATH = BASE_DIR / "AGENTS.md"
AGENTS_BAK_PATH = BASE_DIR / "AGENTS.md.bak"
CLAUDE_PATH = BASE_DIR / "CLAUDE.md"
CLAUDE_BAK_PATH = BASE_DIR / "CLAUDE.md.bak"
AFTMAN_PATHS = (
    BASE_DIR / "aftman.toml",
    BASE_DIR / ".aftman.toml",
)
AGENTS_TEMPLATE_PATHS = {
    "generic": "agents/generic.md",
    "roblox": "agents/Roblox.MD",
}
CLAUDE_TEMPLATE_PATH = "agents/claude.md"
ALWAYS_OVERWRITE_FILES = {
    "ProjectInstructions.md",
}
AII_PATH = BASE_DIR / "aii"
CLAUDE_DIR = BASE_DIR / ".claude"
CLAUDE_SETTINGS_PATH = CLAUDE_DIR / "settings.json"
CLAUDE_SKILLS_PATH = CLAUDE_DIR / "skills"
CLAUDE_COMMANDS_PATH = CLAUDE_DIR / "commands"
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

CLAUDE_SETTINGS_CONTENT = """{
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)"
    ]
  }
}
"""

FETCH_MODELS_COMMAND_CONTENT = """---
allowed-tools: Bash(python3 aii/scripts/fetch_models.py)
description: Refresh the shared Codex and Claude Code model cache
---

Refresh `aii/models/cache.yaml` with current tool-specific model information for Codex and Claude Code.

Run:

!`python3 aii/scripts/fetch_models.py`

After it completes, summarize whether the cache updated cleanly and mention any warnings. Do not substitute generic ChatGPT or Claude chat model lists for Codex or Claude Code model data.
"""

STATIC_FILES = {
    "aii/README.md": """# aii

`aii` is the working area for structured AI execution in this repository.

## Why this is useful

It keeps planning and execution artifacts in one predictable place so work can be resumed cleanly across sessions and collaborators, regardless of whether the repository is bootstrapped for Codex or Claude Code.

## What it can do

- provide a home for reusable skill definitions in `skills/`
- provide shared automation scripts in `scripts/`
- provide a tool-specific model cache in `models/`
- preserve requirements in `interviews/`
- track execution plans in `plans/`
- persist resumable task state in `metadata/`

## Layout
- `skills/`: opt-in skills such as `code-review`, `deep-interview`, `fetch-models`, `planner`, `plan-executor`, `plan-modifier`, and `resume-last-task`
- `scripts/`: reusable helpers such as `send_webhook_embed.py` for standardized Discord embeds
- `models/`: shared Codex and Claude Code model cache used by planner recommendations
- `interviews/`: saved markdown requirement handoff documents
- `plans/`: machine-readable YAML execution plans
- `metadata/`: shared resumable task state for workflows such as `$resume-last-task`

## Skill roles

- `code-review`: reviews code-only changes against repo instructions and coding standards, then proposes or applies fixes.
- `deep-interview`: captures requirements, constraints, assumptions, and ambiguity into a structured interview artifact.
- `fetch-models`: refreshes the shared Codex and Claude Code model cache under `models/cache.yaml`.
- `planner`: turns the interview artifact into an executable YAML plan under `aii/plans/`.
- `plan-executor`: executes or resumes a plan step-by-step while persisting progress and blockers.
- `plan-modifier`: updates an existing plan in place when scope changes or blockers require plan revisions.
- `resume-last-task`: restores the most recent resumable task context from `aii/metadata/` and continues work.

Typical flow: interview -> plan -> execute -> modify (if needed) -> resume later.

Use the `fetch-models` skill in Codex, or `/fetch-models` in Claude Code, to refresh `models/cache.yaml` from current official Codex/OpenAI and Claude Code/Anthropic sources. The model cache is tool-specific and must not be replaced with generic ChatGPT or Claude chat model lists.

## How to use it

1. Bootstrap the repo with `python3 bootstrap.py`.
2. Run a requirements interview and save it in `interviews/`.
3. Generate an execution plan into `plans/`.
4. Execute or modify the plan while persisting progress in `metadata/`.
5. Resume later using the saved state instead of starting over.

TTY runs with no flags open the interactive setup wizard. Use `python3 bootstrap.py --no-interactive --tool=codex` or `python3 bootstrap.py --no-interactive --tool=claude` to install a specific profile directly.
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
    "aii/version.txt": "v7\n",
    "aii/interviews/.gitkeep": "",
    "aii/plans/.gitkeep": "",
    "aii/metadata/.gitkeep": "",
    "aii/models/.gitkeep": "",
    "aii/metadata/state.yaml": """last_task: null

history: []
""",
}


@dataclass(frozen=True)
class ToolProfile:
    name: str
    label: str
    instruction_target: str
    instruction_template: str | None
    project_skill_dir: str | None
    install_local_skills: bool = False
    extra_files: tuple[tuple[str, str], ...] = ()


TOOL_PROFILES = {
    "codex": ToolProfile(
        name="codex",
        label="Codex",
        instruction_target="AGENTS.md",
        instruction_template=None,
        project_skill_dir=None,
        install_local_skills=True,
    ),
    "claude": ToolProfile(
        name="claude",
        label="Claude Code",
        instruction_target="CLAUDE.md",
        instruction_template=CLAUDE_TEMPLATE_PATH,
        project_skill_dir=".claude/skills",
        extra_files=(
            (".claude/settings.json", CLAUDE_SETTINGS_CONTENT),
            (".claude/commands/fetch-models.md", FETCH_MODELS_COMMAND_CONTENT),
        ),
    ),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tool",
        choices=tuple(TOOL_PROFILES),
        default="codex",
        help="Tool profile to install. Defaults to codex.",
    )
    parser.add_argument(
        "--type",
        dest="project_type",
        choices=("auto", "generic", "roblox"),
        default="auto",
        help=(
            "Project template type for instruction files. "
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
        help="Remove the aii scaffold and restore backed up instruction files if present.",
    )
    parser.add_argument(
        "--no-install-skills",
        action="store_true",
        help="Skip Codex skill symlinks into ~/.codex/skills. Ignored for Claude installs.",
    )
    parser.add_argument(
        "--webhook",
        metavar="URL",
        help="Persist Discord webhook URL to .env as codex_webhook.",
    )
    parser.add_argument(
        "--notification-provider",
        choices=("discord", "telegram"),
        help="Persist notification provider to .env as codex_notification_provider.",
    )
    parser.add_argument(
        "--telegram-bot-token",
        help="Persist Telegram bot token to .env as codex_telegram_bot_token.",
    )
    parser.add_argument(
        "--telegram-chat-id",
        help="Persist Telegram chat id to .env as codex_telegram_chat_id.",
    )
    parser.add_argument(
        "--always-skip-missing-webhook",
        action="store_true",
        help=(
            "Persist codex_ignore_webhook_missing=true in .env so runs do not halt when "
            "notification config is missing."
        ),
    )
    parser.add_argument(
        "--test-webhook-embed",
        action="store_true",
        help="Send a test notification report and exit.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run the full interactive setup wizard.",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable the interactive setup wizard even when running in a TTY.",
    )
    return parser.parse_args(argv)


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


def load_text(relative_path: str) -> str:
    local_content = read_local_relative(relative_path)
    if local_content is not None:
        return local_content
    return fetch_text(f"{RAW_BASE}/{relative_path}")


def truncate_discord_message(message: str, limit: int = 2000) -> str:
    if len(message) <= limit:
        return message
    return message[: limit - 3] + "..."


def truncate_telegram_message(message: str) -> str:
    if len(message) <= 4096:
        return message
    return message[:4093] + "..."


def _build_webhook_embed(action: str, status: str, details: str) -> dict[str, object]:
    color_by_status = {
        "succeeded": 0x2ECC71,
        "failed": 0xE74C3C,
        "progress": 0x3498DB,
    }
    emoji_by_status = {
        "succeeded": "OK",
        "failed": "FAIL",
        "progress": "RUN",
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


def _build_telegram_message(action: str, status: str, details: str) -> str:
    normalized = status if status in {"succeeded", "failed", "progress"} else "succeeded"
    text = "\n".join(
        (
            f"bootstrap.py {action} {normalized}",
            "Bootstrap execution report",
            f"Repository: {BASE_DIR}",
            f"Details: {details}",
        )
    )
    return truncate_telegram_message(text)


def send_discord_webhook_report(
    webhook_url: str, *, action: str, status: str, details: str
) -> None:
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

    with urlopen(request, timeout=30):
        pass


def send_telegram_report(
    bot_token: str, chat_id: str, *, action: str, status: str, details: str
) -> None:
    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": _build_telegram_message(
                action=action,
                status=status,
                details=details,
            ),
        }
    ).encode("utf-8")
    request = Request(
        f"{TELEGRAM_API_BASE}/bot{bot_token}/sendMessage",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "codex-optimizations-bootstrap",
        },
        method="POST",
    )

    with urlopen(request, timeout=30):
        pass


def send_webhook_report(
    *,
    provider: str,
    webhook_url: str | None,
    telegram_bot_token: str | None,
    telegram_chat_id: str | None,
    action: str,
    status: str,
    details: str,
) -> None:
    try:
        if provider == "discord" and webhook_url:
            send_discord_webhook_report(
                webhook_url,
                action=action,
                status=status,
                details=details,
            )
        elif provider == "telegram" and telegram_bot_token and telegram_chat_id:
            send_telegram_report(
                telegram_bot_token,
                telegram_chat_id,
                action=action,
                status=status,
                details=details,
            )
    except URLError as exc:
        print(f"warning: failed to send {provider} notification: {exc}")


def load_codex_webhook(env_path: Path = ENV_PATH) -> str | None:
    return load_env_value(ENV_KEY_WEBHOOK, env_path=env_path)


def load_codex_notification_provider(env_path: Path = ENV_PATH) -> str:
    value = load_env_value(ENV_KEY_NOTIFICATION_PROVIDER, env_path=env_path)
    if not value:
        return DEFAULT_NOTIFICATION_PROVIDER
    normalized = value.strip().lower()
    if normalized not in {"discord", "telegram"}:
        raise ValueError(
            f"invalid {ENV_KEY_NOTIFICATION_PROVIDER}={value!r}; "
            "expected 'discord' or 'telegram'"
        )
    return normalized


def load_codex_telegram_bot_token(env_path: Path = ENV_PATH) -> str | None:
    return load_env_value(ENV_KEY_TELEGRAM_BOT_TOKEN, env_path=env_path)


def load_codex_telegram_chat_id(env_path: Path = ENV_PATH) -> str | None:
    return load_env_value(ENV_KEY_TELEGRAM_CHAT_ID, env_path=env_path)


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
    print("updated .env with codex_webhook")


def save_codex_notification_provider(
    provider: str, env_path: Path = ENV_PATH
) -> None:
    save_env_value(ENV_KEY_NOTIFICATION_PROVIDER, provider, env_path=env_path)
    print(f"updated .env with codex_notification_provider={provider}")


def save_codex_telegram_bot_token(
    bot_token: str, env_path: Path = ENV_PATH
) -> None:
    save_env_value(ENV_KEY_TELEGRAM_BOT_TOKEN, bot_token, env_path=env_path)
    print("updated .env with codex_telegram_bot_token")


def save_codex_telegram_chat_id(chat_id: str, env_path: Path = ENV_PATH) -> None:
    save_env_value(ENV_KEY_TELEGRAM_CHAT_ID, chat_id, env_path=env_path)
    print("updated .env with codex_telegram_chat_id")


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


def load_instruction_template(profile: ToolProfile, project_type: str) -> str:
    if profile.name == "codex":
        return load_text(AGENTS_TEMPLATE_PATHS[project_type])
    if not profile.instruction_template:
        raise RuntimeError(f"tool profile {profile.name} is missing an instruction template")
    return load_text(profile.instruction_template)


def managed_agents_templates() -> tuple[str, ...]:
    return tuple(load_text(path) for path in AGENTS_TEMPLATE_PATHS.values())


def managed_claude_template() -> str:
    return load_text(CLAUDE_TEMPLATE_PATH)


def build_scaffold_files(project_type: str, tool_name: str) -> dict[str, str]:
    profile = TOOL_PROFILES[tool_name]
    files: dict[str, str] = dict(STATIC_FILES)
    files[profile.instruction_target] = load_instruction_template(profile, project_type)

    skill_contents: dict[str, str] = {}
    for skill in SKILLS:
        relative_path = f"aii/skills/{skill}/SKILL.md"
        content = load_text(relative_path)
        files[relative_path] = content
        skill_contents[skill] = content

    for script in SCRIPTS:
        relative_path = f"aii/scripts/{script}"
        files[relative_path] = load_text(relative_path)

    for relative_path, content in profile.extra_files:
        files[relative_path] = content

    if profile.project_skill_dir:
        for skill, content in skill_contents.items():
            files[f"{profile.project_skill_dir}/{skill}/SKILL.md"] = content

    return files


def write_file(relative_path: str, content: str, force: bool) -> None:
    path = BASE_DIR / relative_path
    if relative_path == "aii/version.txt":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path}")
        return
    if path.exists() and not force and relative_path not in ALWAYS_OVERWRITE_FILES:
        existing_content = path.read_text(encoding="utf-8")
        if existing_content == content:
            print(f"kept {path} (already up to date)")
            return
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
            if AGENTS_PATH.read_text(encoding="utf-8") in managed_agents_templates():
                AGENTS_PATH.unlink()
                print("removed AGENTS.md")
            else:
                print("left AGENTS.md in place because no managed backup exists")
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


def backup_claude() -> None:
    if not CLAUDE_PATH.exists():
        return
    CLAUDE_BAK_PATH.write_text(CLAUDE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"wrote {CLAUDE_BAK_PATH}")


def restore_claude_backup() -> None:
    if not CLAUDE_BAK_PATH.exists():
        if CLAUDE_PATH.exists():
            if CLAUDE_PATH.read_text(encoding="utf-8") == managed_claude_template():
                CLAUDE_PATH.unlink()
                print("removed CLAUDE.md")
            else:
                print("left CLAUDE.md in place because no managed backup exists")
        return
    CLAUDE_PATH.write_text(CLAUDE_BAK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    CLAUDE_BAK_PATH.unlink()
    print("restored CLAUDE.md from CLAUDE.md.bak")
    print("removed CLAUDE.md.bak")


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


def uninstall_claude_files() -> None:
    restore_claude_backup()

    if CLAUDE_SETTINGS_PATH.exists():
        if CLAUDE_SETTINGS_PATH.read_text(encoding="utf-8") == CLAUDE_SETTINGS_CONTENT:
            CLAUDE_SETTINGS_PATH.unlink()
            print("removed .claude/settings.json")
        else:
            print("left .claude/settings.json in place because it is not the managed template")

    fetch_models_command = CLAUDE_COMMANDS_PATH / "fetch-models.md"
    if fetch_models_command.exists():
        if fetch_models_command.read_text(encoding="utf-8") == FETCH_MODELS_COMMAND_CONTENT:
            fetch_models_command.unlink()
            print("removed .claude/commands/fetch-models.md")
        else:
            print("left .claude/commands/fetch-models.md in place because it is not the managed template")

    for skill in SKILLS:
        skill_dir = CLAUDE_SKILLS_PATH / skill
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
            print(f"removed {skill_dir}")

    if CLAUDE_SKILLS_PATH.exists() and not any(CLAUDE_SKILLS_PATH.iterdir()):
        CLAUDE_SKILLS_PATH.rmdir()
        print("removed .claude/skills")

    if CLAUDE_COMMANDS_PATH.exists() and not any(CLAUDE_COMMANDS_PATH.iterdir()):
        CLAUDE_COMMANDS_PATH.rmdir()
        print("removed .claude/commands")

    if CLAUDE_DIR.exists() and not any(CLAUDE_DIR.iterdir()):
        CLAUDE_DIR.rmdir()
        print("removed .claude")


def install(
    *,
    force: bool,
    install_skills: bool,
    project_type: str,
    tool_name: str,
    install_pre_push_hook_enabled: bool,
) -> None:
    profile = TOOL_PROFILES[tool_name]
    files = build_scaffold_files(project_type, tool_name)

    if profile.name == "codex":
        backup_agents()
    if profile.name == "claude":
        backup_claude()

    for relative_path, content in files.items():
        write_file(relative_path, content, force=force)

    update_gitignore_for_install()
    if install_pre_push_hook_enabled:
        install_pre_push_hook(force=force)
    if install_skills and profile.install_local_skills:
        install_codex_skills(force=force)


def uninstall() -> None:
    uninstall_codex_skills()
    uninstall_claude_files()
    uninstall_pre_push_hook()
    if AII_PATH.exists():
        shutil.rmtree(AII_PATH)
        print("removed aii/")
    restore_agents_backup()
    update_gitignore_for_uninstall()


def prompt_for_notification_if_missing(
    provider: str,
    webhook_url: str | None,
    telegram_bot_token: str | None,
    telegram_chat_id: str | None,
    ignore_missing_webhook: bool,
) -> tuple[str | None, str | None, str | None]:
    provider_configured = (
        bool(webhook_url)
        if provider == "discord"
        else bool(telegram_bot_token and telegram_chat_id)
    )
    if provider_configured or ignore_missing_webhook:
        return webhook_url, telegram_bot_token, telegram_chat_id

    if not sys.stdin.isatty():
        print(
            f"warning: {provider} notification config is missing; "
            "continuing without notification reports. "
            "Use --always-skip-missing-webhook to suppress this warning."
        )
        return webhook_url, telegram_bot_token, telegram_chat_id

    print(f"{provider} notification config is missing.")
    answer = input("Would you like to enter it now? [y/N]: ").strip().lower()
    if answer not in {"y", "yes"}:
        print("continuing without notification reports")
        return webhook_url, telegram_bot_token, telegram_chat_id

    if provider == "discord":
        entered = input("Paste Discord webhook URL: ").strip()
        if not entered:
            print("no webhook URL provided; continuing without notification reports")
            return webhook_url, telegram_bot_token, telegram_chat_id

        save_codex_webhook(entered)
        return entered, telegram_bot_token, telegram_chat_id

    entered_token = input("Paste Telegram bot token: ").strip()
    entered_chat_id = input("Paste Telegram chat id: ").strip()
    if not entered_token or not entered_chat_id:
        print("telegram config incomplete; continuing without notification reports")
        return webhook_url, telegram_bot_token, telegram_chat_id

    save_codex_telegram_bot_token(entered_token)
    save_codex_telegram_chat_id(entered_chat_id)
    return webhook_url, entered_token, entered_chat_id


def supports_interactive_io() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def read_key() -> str:
    if msvcrt is not None:
        first = msvcrt.getwch()
        if first in {"\x00", "\xe0"}:
            second = msvcrt.getwch()
            return {
                "H": "up",
                "P": "down",
                "K": "left",
                "M": "right",
            }.get(second, "unknown")
        if first in {"\r", "\n"}:
            return "enter"
        if first == "\x03":
            raise KeyboardInterrupt
        if first == "\x1b":
            return "escape"
        return first.lower()

    if termios is None or tty is None:
        raise RuntimeError("interactive mode requires a supported TTY")

    fd = sys.stdin.fileno()
    original = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        first = sys.stdin.read(1)
        if first == "\x03":
            raise KeyboardInterrupt
        if first == "\x1b":
            second = sys.stdin.read(1)
            if second == "[":
                third = sys.stdin.read(1)
                return {
                    "A": "up",
                    "B": "down",
                    "C": "right",
                    "D": "left",
                }.get(third, "escape")
            return "escape"
        if first in {"\r", "\n"}:
            return "enter"
        return first.lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original)


def clear_screen() -> None:
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()


def terminal_width(*, fallback: int = 80) -> int:
    return max(40, shutil.get_terminal_size((fallback, 24)).columns)


def wrap_lines(text: str, width: int) -> list[str]:
    return textwrap.wrap(
        text,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [""]


def prompt_select(title: str, options: list[tuple[str, str]], *, default_index: int = 0) -> str:
    if not supports_interactive_io():
        raise RuntimeError("interactive prompts require a TTY")

    index = max(0, min(default_index, len(options) - 1))
    width = terminal_width()
    rule = "-" * min(width, 72)
    while True:
        clear_screen()
        for line in wrap_lines(title, width):
            print(line)
        print("Use arrow keys and Enter.")
        print()
        print(rule)
        for option_index, (_, label) in enumerate(options):
            marker = ">" if option_index == index else " "
            available_width = max(1, width - 2)
            wrapped_label = wrap_lines(label, available_width)
            print(f"{marker} {wrapped_label[0]}")
            for continuation in wrapped_label[1:]:
                print(f"  {continuation}")
        print(rule)

        key = read_key()
        if key in {"up", "k"}:
            index = (index - 1) % len(options)
            continue
        if key in {"down", "j"}:
            index = (index + 1) % len(options)
            continue
        if key == "enter":
            return options[index][0]
        if key == "escape":
            raise KeyboardInterrupt


def prompt_confirm(prompt: str, *, default: bool = True) -> bool:
    options = [("yes", "Yes"), ("no", "No")]
    selection = prompt_select(prompt, options, default_index=0 if default else 1)
    return selection == "yes"


def prompt_input(prompt: str, *, default: str | None = None) -> str:
    if supports_interactive_io():
        clear_screen()
    print(prompt)
    if default:
        print(f"Press Enter to keep: {default}")
    value = input("> ").strip()
    if value:
        return value
    return default or ""


def build_interactive_config(
    existing_provider: str,
    existing_webhook: str | None,
    existing_telegram_bot_token: str | None,
    existing_telegram_chat_id: str | None,
) -> argparse.Namespace:
    action = prompt_select(
        "Select a setup action",
        [
            ("install", "Install or update scaffold"),
            ("uninstall", "Uninstall scaffold"),
            ("test-webhook", "Send notification test"),
        ],
    )

    tool_name = "codex"
    project_type = "auto"
    force = False
    install_pre_push_hook = False
    no_install_skills = False
    webhook = None
    notification_provider = existing_provider
    telegram_bot_token = None
    telegram_chat_id = None
    always_skip_missing_webhook = False

    if action == "install":
        tool_name = prompt_select(
            "Choose the tool profile",
            [(name, profile.label) for name, profile in TOOL_PROFILES.items()],
        )
        project_type = prompt_select(
            "Choose the project template type",
            [
                ("auto", "Auto-detect"),
                ("generic", "Generic"),
                ("roblox", "Roblox"),
            ],
        )
        force = prompt_confirm("Overwrite existing managed files if needed?", default=False)
        install_pre_push_hook = prompt_confirm(
            "Install the managed pre-push hook?", default=False
        )
        if TOOL_PROFILES[tool_name].install_local_skills:
            no_install_skills = not prompt_confirm(
                "Install Codex skill symlinks into ~/.codex/skills?", default=True
            )

    webhook_mode = prompt_select(
        "Notification configuration",
        [
            ("keep", "Keep current notification settings"),
            ("discord", "Use Discord webhook"),
            ("telegram", "Use Telegram bot"),
            ("skip", "Always skip missing notification prompts"),
        ],
    )
    if webhook_mode == "discord":
        notification_provider = "discord"
        webhook = prompt_input("Enter Discord webhook URL", default=existing_webhook)
    elif webhook_mode == "telegram":
        notification_provider = "telegram"
        telegram_bot_token = prompt_input(
            "Enter Telegram bot token",
            default=existing_telegram_bot_token,
        )
        telegram_chat_id = prompt_input(
            "Enter Telegram chat id",
            default=existing_telegram_chat_id,
        )
    elif webhook_mode == "skip":
        always_skip_missing_webhook = True

    summary_lines = [
        f"Action: {action}",
        f"Tool: {tool_name}",
        f"Project type: {project_type}",
    ]
    if action == "install":
        summary_lines.append(f"Force overwrite: {'yes' if force else 'no'}")
        summary_lines.append(
            f"Install pre-push hook: {'yes' if install_pre_push_hook else 'no'}"
        )
        if TOOL_PROFILES[tool_name].install_local_skills:
            summary_lines.append(
                f"Install Codex symlinks: {'no' if no_install_skills else 'yes'}"
            )
    summary_lines.append(
        "Notification mode: "
        + (
            f"use {notification_provider}"
            if webhook_mode in {"discord", "telegram"}
            else "always skip missing prompts"
            if webhook_mode == "skip"
            else "leave current settings"
        )
    )

    if supports_interactive_io():
        clear_screen()
    print("Configuration summary")
    print()
    for line in summary_lines:
        print(f"- {line}")
    print()
    if not prompt_confirm("Proceed with this configuration?", default=True):
        raise KeyboardInterrupt

    return SimpleNamespace(
        tool=tool_name,
        project_type=project_type,
        install_pre_push_hook=install_pre_push_hook,
        force=force,
        uninstall=action == "uninstall",
        no_install_skills=no_install_skills,
        notification_provider=notification_provider,
        webhook=webhook,
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id,
        always_skip_missing_webhook=always_skip_missing_webhook,
        test_webhook_embed=action == "test-webhook",
        interactive=True,
        no_interactive=False,
    )


def should_run_interactive(args: argparse.Namespace, raw_args: list[str]) -> bool:
    if args.no_interactive:
        return False
    if args.interactive:
        return True
    return supports_interactive_io() and not raw_args


def resolve_interactive_notification(
    provider: str,
    webhook_url: str | None,
    telegram_bot_token: str | None,
    telegram_chat_id: str | None,
    ignore_missing_webhook: bool,
) -> tuple[str | None, str | None, str | None, bool]:
    provider_configured = (
        bool(webhook_url)
        if provider == "discord"
        else bool(telegram_bot_token and telegram_chat_id)
    )
    if provider_configured or ignore_missing_webhook:
        return webhook_url, telegram_bot_token, telegram_chat_id, ignore_missing_webhook

    choice = prompt_select(
        f"No {provider} notification config is set",
        [
            ("continue", "Continue without notification reports for this run"),
            ("set", "Set notification config now"),
            ("skip", "Always skip missing notification prompts"),
        ],
    )
    if choice == "set":
        if provider == "discord":
            entered = prompt_input("Enter Discord webhook URL")
            if entered:
                save_codex_webhook(entered)
                return entered, telegram_bot_token, telegram_chat_id, ignore_missing_webhook
            return webhook_url, telegram_bot_token, telegram_chat_id, ignore_missing_webhook

        entered_token = prompt_input("Enter Telegram bot token")
        entered_chat_id = prompt_input("Enter Telegram chat id")
        if entered_token and entered_chat_id:
            save_codex_telegram_bot_token(entered_token)
            save_codex_telegram_chat_id(entered_chat_id)
            return webhook_url, entered_token, entered_chat_id, ignore_missing_webhook
        return webhook_url, telegram_bot_token, telegram_chat_id, ignore_missing_webhook
    if choice == "skip":
        save_codex_ignore_webhook_missing(True)
        return webhook_url, telegram_bot_token, telegram_chat_id, True
    print("continuing without notification reports")
    return webhook_url, telegram_bot_token, telegram_chat_id, ignore_missing_webhook


def main(argv: list[str] | None = None) -> None:
    raw_args = sys.argv[1:] if argv is None else list(argv)
    args = parse_args(raw_args)
    if should_run_interactive(args, raw_args):
        try:
            args = build_interactive_config(
                load_codex_notification_provider(),
                load_codex_webhook(),
                load_codex_telegram_bot_token(),
                load_codex_telegram_chat_id(),
            )
        except KeyboardInterrupt:
            print("\nsetup cancelled")
            return

    resolved_project_type = detect_project_type(args.project_type)
    if args.notification_provider:
        save_codex_notification_provider(args.notification_provider)
    if args.webhook:
        save_codex_webhook(args.webhook)
    if args.telegram_bot_token:
        save_codex_telegram_bot_token(args.telegram_bot_token)
    if args.telegram_chat_id:
        save_codex_telegram_chat_id(args.telegram_chat_id)
    if args.always_skip_missing_webhook:
        save_codex_ignore_webhook_missing(True)

    provider = args.notification_provider or load_codex_notification_provider()
    webhook_url = args.webhook or load_codex_webhook()
    telegram_bot_token = args.telegram_bot_token or load_codex_telegram_bot_token()
    telegram_chat_id = args.telegram_chat_id or load_codex_telegram_chat_id()
    ignore_missing_webhook = load_codex_ignore_webhook_missing()
    if getattr(args, "interactive", False):
        (
            webhook_url,
            telegram_bot_token,
            telegram_chat_id,
            ignore_missing_webhook,
        ) = resolve_interactive_notification(
            provider,
            webhook_url,
            telegram_bot_token,
            telegram_chat_id,
            ignore_missing_webhook,
        )
    else:
        (
            webhook_url,
            telegram_bot_token,
            telegram_chat_id,
        ) = prompt_for_notification_if_missing(
            provider,
            webhook_url,
            telegram_bot_token,
            telegram_chat_id,
            ignore_missing_webhook,
        )

    if args.test_webhook_embed:
        provider_configured = (
            bool(webhook_url)
            if provider == "discord"
            else bool(telegram_bot_token and telegram_chat_id)
        )
        if not provider_configured:
            print("notification config missing; no test message sent")
            return
        send_webhook_report(
            provider=provider,
            webhook_url=webhook_url,
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            action="test",
            status="progress",
            details="notification delivery test from bootstrap.py",
        )
        print(f"sent {provider} notification test")
        return

    action = "uninstall" if args.uninstall else "install"
    try:
        send_webhook_report(
            provider=provider,
            webhook_url=webhook_url,
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            action=action,
            status="progress",
            details="starting scaffold operation",
        )
        if args.uninstall:
            uninstall()
        else:
            print(f"using tool profile: {args.tool}")
            print(f"using project type: {resolved_project_type}")
            install(
                force=args.force,
                install_skills=not args.no_install_skills,
                project_type=resolved_project_type,
                tool_name=args.tool,
                install_pre_push_hook_enabled=args.install_pre_push_hook,
            )
        send_webhook_report(
            provider=provider,
            webhook_url=webhook_url,
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            action=action,
            status="progress",
            details="scaffold operation reached finalization stage",
        )
        send_webhook_report(
            provider=provider,
            webhook_url=webhook_url,
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            action=action,
            status="succeeded",
            details="scaffold operation completed successfully",
        )
    except Exception as exc:
        send_webhook_report(
            provider=provider,
            webhook_url=webhook_url,
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            action=action,
            status="failed",
            details=f"{type(exc).__name__}: {exc}",
        )
        raise


if __name__ == "__main__":
    main()
