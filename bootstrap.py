#!/usr/bin/env python3
"""Fetch/update cached aii setup script, then execute it."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


BASE_DIR = Path.cwd()
RAW_BASE = "https://raw.githubusercontent.com/Dustin-256/CodexOptimizations/main"
REMOTE_SETUP_PATH = "aii/scripts/setup.py"
REMOTE_VERSION_PATHS = ("aii/version.txt",)
CACHE_SETUP_PATH = BASE_DIR / REMOTE_SETUP_PATH
CACHE_VERSION_PATH = BASE_DIR / "aii" / "version.txt"


def fetch_text_via_curl(url: str) -> str | None:
    commands = (
        ("curl", "-fsSL", url),
        ("curl.exe", "-fsSL", url),
    )
    for command in commands:
        try:
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            continue
        return completed.stdout
    return None


def fetch_text(url: str) -> str:
    request = Request(
        url, headers={"User-Agent": "codex-optimizations-bootstrap-launcher"})
    try:
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except URLError as exc:
        # Some Python distributions (notably certain MSYS2 installs on Windows)
        # do not have a complete CA trust chain configured.
        fallback = fetch_text_via_curl(url)
        if fallback is not None:
            return fallback
        raise exc


def read_local_version() -> str | None:
    if not CACHE_VERSION_PATH.exists():
        return None
    return CACHE_VERSION_PATH.read_text(encoding="utf-8").strip() or None


def fetch_remote_version() -> str | None:
    for relative_path in REMOTE_VERSION_PATHS:
        try:
            value = fetch_text(f"{RAW_BASE}/{relative_path}").strip()
        except URLError:
            continue
        if value:
            return value
    return None


def parse_version_tag(tag: str | None) -> int:
    if not tag:
        return -1
    cleaned = tag.strip()
    if cleaned.startswith("v"):
        cleaned = cleaned[1:]
    if not cleaned.isdigit():
        return -1
    return int(cleaned)


def write_cached_setup(setup_source: str, version_tag: str | None) -> None:
    CACHE_SETUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_SETUP_PATH.write_text(setup_source, encoding="utf-8")
    if version_tag:
        CACHE_VERSION_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_VERSION_PATH.write_text(
            version_tag.strip() + "\n", encoding="utf-8")


def ensure_cached_setup() -> None:
    local_version = read_local_version()
    remote_version = fetch_remote_version()

    should_update = False
    if not CACHE_SETUP_PATH.exists():
        should_update = True
    elif remote_version is not None:
        should_update = parse_version_tag(
            remote_version) > parse_version_tag(local_version)

    if should_update:
        setup_source = fetch_text(f"{RAW_BASE}/{REMOTE_SETUP_PATH}")
        write_cached_setup(setup_source, remote_version)
        shown_version = remote_version or "unknown-version"
        print(f"updated cached setup script ({shown_version})")
        return

    if CACHE_SETUP_PATH.exists():
        shown_version = local_version or "unknown-version"
        print(f"using cached setup script ({shown_version})")
        return

    raise RuntimeError(
        "could not find cached setup script and failed to download latest setup script"
    )


def run_cached_setup(argv: list[str]) -> int:
    command = [sys.executable, str(CACHE_SETUP_PATH), *argv]
    completed = subprocess.run(command, cwd=BASE_DIR)
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    forwarded_args = sys.argv[1:] if argv is None else argv
    try:
        ensure_cached_setup()
    except URLError as exc:
        raise RuntimeError(f"failed to fetch setup script: {exc}") from exc
    return run_cached_setup(forwarded_args)


if __name__ == "__main__":
    raise SystemExit(main())
