#!/usr/bin/env python3
"""Fetch/update cached aii setup script from the latest GitHub Release, then execute it."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


BASE_DIR = Path.cwd()
OWNER_REPO = "Dustin-256/CodexOptimizations"
RAW_BASE = f"https://raw.githubusercontent.com/{OWNER_REPO}"
RELEASES_API_URL = f"https://api.github.com/repos/{OWNER_REPO}/releases/latest"
DEFAULT_REF = "main"
REMOTE_SETUP_PATH = "aii/scripts/setup.py"
CACHE_SETUP_PATH = BASE_DIR / REMOTE_SETUP_PATH
# Local cache stamp: records which release tag the cached setup script came from.
CACHE_VERSION_PATH = BASE_DIR / "aii" / "version.txt"
USER_AGENT = "codex-optimizations-bootstrap-launcher"


def fetch_via_curl(url: str, *, accept: str | None = None) -> str | None:
    header_args = ("-H", f"Accept: {accept}") if accept else ()
    commands = (
        ("curl", "-fsSL", *header_args, url),
        ("curl.exe", "-fsSL", *header_args, url),
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


def fetch_text(url: str, *, accept: str | None = None) -> str:
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except URLError as exc:
        # Some Python distributions (notably certain MSYS2 installs on Windows)
        # do not have a complete CA trust chain configured.
        fallback = fetch_via_curl(url, accept=accept)
        if fallback is not None:
            return fallback
        raise exc


def read_local_version() -> str | None:
    if not CACHE_VERSION_PATH.exists():
        return None
    return CACHE_VERSION_PATH.read_text(encoding="utf-8").strip() or None


def fetch_latest_release_tag() -> str | None:
    """Return the tag_name of the latest GitHub Release, or None if unavailable."""
    try:
        raw = fetch_text(RELEASES_API_URL, accept="application/vnd.github+json")
    except URLError:
        return None
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    tag = data.get("tag_name")
    if isinstance(tag, str) and tag.strip():
        return tag.strip()
    return None


def write_cached_setup(setup_source: str, version_tag: str | None) -> None:
    CACHE_SETUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_SETUP_PATH.write_text(setup_source, encoding="utf-8")
    if version_tag:
        CACHE_VERSION_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_VERSION_PATH.write_text(version_tag.strip() + "\n", encoding="utf-8")


def fetch_setup_source(ref: str) -> str:
    """Fetch setup.py at the given git ref, falling back to the default branch."""
    setup_url = f"{RAW_BASE}/{ref}/{REMOTE_SETUP_PATH}"
    try:
        return fetch_text(setup_url)
    except URLError:
        if ref == DEFAULT_REF:
            raise
        # The release tag may not be servable yet; fall back to the default branch.
        return fetch_text(f"{RAW_BASE}/{DEFAULT_REF}/{REMOTE_SETUP_PATH}")


def ensure_cached_setup() -> None:
    local_version = read_local_version()
    remote_version = fetch_latest_release_tag()

    # Cache is valid only when the cached engine exists and matches the latest
    # release tag. If the release API is unreachable, keep whatever is cached.
    should_update = (not CACHE_SETUP_PATH.exists()) or (
        remote_version is not None and remote_version != local_version
    )

    if should_update:
        ref = remote_version or DEFAULT_REF
        setup_source = fetch_setup_source(ref)
        write_cached_setup(setup_source, remote_version)
        print(f"updated cached setup script ({remote_version or DEFAULT_REF})")
        return

    if CACHE_SETUP_PATH.exists():
        print(f"using cached setup script ({local_version or 'unknown-version'})")
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
