#!/usr/bin/env python3
"""Refresh the shared Codex and Claude Code model cache."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "aii" / "models" / "cache.yaml"
TIMEOUT_SECONDS = 20

SOURCES = {
    "openai_models": "https://developers.openai.com/api/docs/models",
    "openai_codex": "https://developers.openai.com/api/docs/models/gpt-5.3-codex",
    "openai_codex_previous": "https://developers.openai.com/api/docs/models/gpt-5.2-codex",
    "claude_code_model_config": "https://docs.anthropic.com/en/docs/claude-code/model-config",
    "anthropic_models": "https://docs.anthropic.com/en/docs/about-claude/models/all-models",
}

EXPECTED_MARKERS = {
    "openai_models": ("gpt-5.5", "gpt-5.4", "gpt-5.4-mini"),
    "openai_codex": ("gpt-5.3-codex",),
    "claude_code_model_config": ("opusplan", "sonnet", "opus", "haiku"),
}


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": "codex-optimizations-fetch-models"})
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8", errors="replace")


def collect_warnings(pages: dict[str, str]) -> list[str]:
    warnings: list[str] = []
    for source_name, markers in EXPECTED_MARKERS.items():
        text = pages.get(source_name, "").lower()
        for marker in markers:
            if marker.lower() not in text:
                warnings.append(f"{marker} was not found in {source_name}")
    return warnings


def render_cache(fetched_at: str, warnings: list[str]) -> str:
    warning_lines = "\n".join(f"  - {warning}" for warning in warnings) or "  - none"
    return f"""schema_version: 1
fetched_at: {fetched_at}
stale_after_days: 14
warnings:
{warning_lines}
source_policy:
  - Use Codex-specific/OpenAI coding-agent model information for Codex recommendations.
  - Use Claude Code model configuration and aliases for Claude Code recommendations.
  - Do not substitute generic ChatGPT or Claude chat model lists when tool-specific names or reasoning controls differ.

sources:
  codex:
    - name: OpenAI models catalog
      url: {SOURCES["openai_models"]}
    - name: OpenAI GPT-5.3-Codex model page
      url: {SOURCES["openai_codex"]}
    - name: OpenAI GPT-5.2-Codex model page
      url: {SOURCES["openai_codex_previous"]}
  claude_code:
    - name: Claude Code model configuration
      url: {SOURCES["claude_code_model_config"]}
    - name: Anthropic models overview
      url: {SOURCES["anthropic_models"]}

tools:
  codex:
    display_name: Codex
    current_tool_detection:
      positive_signals:
        - active instructions identify the assistant as Codex
        - Codex model/reasoning controls are present
      fallback_instruction: If the current tool cannot be detected, state the uncertainty and still choose from this cache based on task scope.
    recommendation_policy:
      default_primary:
        model: GPT-5.5
        model_id: gpt-5.5
        reasoning: medium
      default_fallback:
        model: GPT-5.4
        model_id: gpt-5.4
        reasoning: medium
      conservation_fallback:
        model: GPT-5.4-mini
        model_id: gpt-5.4-mini
        reasoning: medium
      notes:
        - Prefer GPT-5.5 medium for simple through moderately complex Codex work.
        - Use GPT-5.4 medium or GPT-5.4-mini medium when conserving tokens.
        - Consider xhigh reasoning only for unusually complex Codex execution when Claude is not preferred.
    models:
      - model: GPT-5.5
        model_id: gpt-5.5
        role: primary_codex_workhorse
        reasoning_efforts: [none, low, medium, high, xhigh]
        tool_specificity: Codex/OpenAI coding-agent recommendation; not a ChatGPT chat-model entry.
      - model: GPT-5.4
        model_id: gpt-5.4
        role: capable_codex_fallback
        reasoning_efforts: [none, low, medium, high, xhigh]
        tool_specificity: Codex/OpenAI coding-agent recommendation; not a ChatGPT chat-model entry.
      - model: GPT-5.4-mini
        model_id: gpt-5.4-mini
        role: cheaper_codex_fallback
        reasoning_efforts: [none, low, medium, high, xhigh]
        tool_specificity: Codex/OpenAI coding-agent recommendation; not a ChatGPT chat-model entry.
      - model: GPT-5.3-Codex
        model_id: gpt-5.3-codex
        role: codex_optimized_agentic_coding
        reasoning_efforts: [low, medium, high, xhigh]
        tool_specificity: Codex-optimized OpenAI model entry.

  claude_code:
    display_name: Claude Code
    current_tool_detection:
      positive_signals:
        - active instructions identify the assistant as Claude Code
        - Claude Code slash commands such as /model or /status are available
      fallback_instruction: If Claude Code identity cannot be detected, state the uncertainty before recommending a Claude Code switch.
    recommendation_policy:
      default_primary:
        model: opus
        expanded_name: Claude Opus 4.1 alias
        thinking: high
      default_fallback:
        model: sonnet
        expanded_name: Claude Sonnet 4 alias
        thinking: medium
      simple_task_fallback:
        model: haiku
        expanded_name: Claude Haiku alias
        thinking: low
      notes:
        - Reserve Claude Code Opus for major refactors, broad architecture changes, high-risk migrations, and work that must be right on the first serious execution pass.
        - Prefer Codex for simple and moderate tasks because the user's Codex token budget is materially larger.
    aliases:
      - alias: opus
        role: most_capable_complex_reasoning
        current_mapping_summary: Most capable Opus model, currently Opus 4.1 per Claude Code docs.
        thinking_levels: [medium, high]
      - alias: sonnet
        role: daily_coding_tasks
        current_mapping_summary: Latest Sonnet model, currently Sonnet 4 per Claude Code docs.
        thinking_levels: [low, medium, high]
      - alias: haiku
        role: simple_fast_tasks
        current_mapping_summary: Fast efficient Haiku model per Claude Code docs.
        thinking_levels: [low, medium]
      - alias: opusplan
        role: hybrid_planning_execution
        current_mapping_summary: Uses opus for plan mode and sonnet for execution.
        thinking_levels: [high]
"""


def main() -> int:
    pages: dict[str, str] = {}
    failed: list[str] = []

    for name, url in SOURCES.items():
        try:
            pages[name] = fetch(url)
        except (OSError, URLError) as exc:
            failed.append(f"{name}: {exc}")

    if not pages:
        print("failed to fetch model sources; cache was not updated")
        for failure in failed:
            print(f"- {failure}")
        return 1

    warnings = collect_warnings(pages)
    warnings.extend(f"fetch failed for {failure}" for failure in failed)

    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT.write_text(render_cache(fetched_at, warnings), encoding="utf-8")

    print(f"updated {DEFAULT_OUTPUT.relative_to(ROOT)}")
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
