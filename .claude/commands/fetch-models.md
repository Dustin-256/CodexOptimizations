---
allowed-tools: Bash(python3 aii/scripts/fetch_models.py)
description: Refresh the shared Codex and Claude Code model cache
---

Refresh `aii/models/cache.yaml` with current tool-specific model information for Codex and Claude Code.

Run:

!`python3 aii/scripts/fetch_models.py`

After it completes, summarize whether the cache updated cleanly and mention any warnings. Do not substitute generic ChatGPT or Claude chat model lists for Codex or Claude Code model data.
