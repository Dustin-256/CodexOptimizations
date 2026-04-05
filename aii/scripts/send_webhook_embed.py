#!/usr/bin/env python3
"""Send standardized Discord webhook embeds for workflow progress."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ENV_PATH = Path.cwd() / ".env"
ENV_KEY_WEBHOOK = "codex_webhook"
ENV_KEY_IGNORE_WEBHOOK_MISSING = "codex_ignore_webhook_missing"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--event",
        choices=("progress", "success", "failed", "blocked", "test"),
        required=True,
        help="Embed event type.",
    )
    parser.add_argument("--title", help="Optional embed title override.")
    parser.add_argument("--summary", required=True, help="Short summary line.")
    parser.add_argument("--plan-name", help="Plan name.")
    parser.add_argument("--step-id", help="Step id.")
    parser.add_argument("--step-title", help="Step title.")
    parser.add_argument("--runtime", help="Human-readable runtime.")
    parser.add_argument("--details", help="Extra details.")
    parser.add_argument(
        "--field",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Extra embed field (repeatable).",
    )
    parser.add_argument("--webhook", metavar="URL", help="Webhook override.")
    parser.add_argument(
        "--allow-missing-webhook",
        action="store_true",
        help="Do not fail when webhook is missing.",
    )
    parser.add_argument(
        "--always-skip-missing-webhook",
        action="store_true",
        help="Persist codex_ignore_webhook_missing=true in .env.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print payload JSON instead of sending.",
    )
    return parser.parse_args()


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


def load_codex_webhook(env_path: Path = ENV_PATH) -> str | None:
    return load_env_value(ENV_KEY_WEBHOOK, env_path=env_path)


def load_codex_ignore_webhook_missing(env_path: Path = ENV_PATH) -> bool:
    value = load_env_value(ENV_KEY_IGNORE_WEBHOOK_MISSING, env_path=env_path)
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_fields(raw_fields: list[str]) -> list[dict[str, object]]:
    fields: list[dict[str, object]] = []
    for item in raw_fields:
        if "=" not in item:
            raise ValueError(f"invalid --field value: {item!r}; expected KEY=VALUE")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError("field key cannot be empty")
        fields.append({"name": key, "value": value or "-", "inline": False})
    return fields


def build_payload(args: argparse.Namespace) -> dict[str, object]:
    title_by_event = {
        "progress": "🔄 Execution Progress",
        "success": "✅ Execution Success",
        "failed": "❌ Execution Failed",
        "blocked": "⛔ Execution Blocked",
        "test": "🧪 Webhook Test",
    }
    color_by_event = {
        "progress": 0x3498DB,
        "success": 0x2ECC71,
        "failed": 0xE74C3C,
        "blocked": 0xF1C40F,
        "test": 0x9B59B6,
    }

    fields: list[dict[str, object]] = []
    if args.plan_name:
        fields.append({"name": "Plan", "value": args.plan_name, "inline": True})
    if args.step_id:
        fields.append({"name": "Step ID", "value": args.step_id, "inline": True})
    if args.step_title:
        fields.append({"name": "Step", "value": args.step_title, "inline": False})
    if args.runtime:
        fields.append({"name": "Runtime", "value": args.runtime, "inline": True})
    if args.details:
        fields.append({"name": "Details", "value": args.details, "inline": False})
    fields.extend(parse_fields(args.field))

    embed = {
        "title": args.title or title_by_event[args.event],
        "description": args.summary,
        "color": color_by_event[args.event],
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return {"embeds": [embed], "allowed_mentions": {"parse": []}}


def send_payload(webhook_url: str, payload: dict[str, object]) -> None:
    request = Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "codex-optimizations-webhook-embed",
        },
        method="POST",
    )
    with urlopen(request, timeout=30):
        pass


def main() -> None:
    args = parse_args()
    payload = build_payload(args)
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return

    if args.always_skip_missing_webhook:
        save_env_value(ENV_KEY_IGNORE_WEBHOOK_MISSING, "true")
        print("updated .env with codex_ignore_webhook_missing=true")

    webhook_url = args.webhook or load_codex_webhook()
    ignore_missing = load_codex_ignore_webhook_missing()
    if not webhook_url:
        if args.allow_missing_webhook or ignore_missing:
            print("webhook missing; skipping send")
            return
        raise RuntimeError(
            "codex_webhook is missing. Set it in .env, pass --webhook URL, "
            "or set codex_ignore_webhook_missing=true."
        )

    try:
        send_payload(webhook_url, payload)
    except URLError as exc:
        raise RuntimeError(f"failed to send webhook embed: {exc}") from exc
    print("sent webhook embed")


if __name__ == "__main__":
    main()
