---
name: fetch-models
description: refresh the shared Codex and Claude Code model cache under aii/models/cache.yaml from current official tool-specific model sources.
---

# fetch-models

Refresh the shared model cache:

`aii/models/cache.yaml`

This skill is for Codex model-cache refreshes. Claude Code may also expose the same workflow as the `/fetch-models` project slash command.

## Workflow

1. Run from the repository root:

```bash
python3 aii/scripts/fetch_models.py
```

2. Read the command output.

3. Report whether the cache updated successfully.

4. If warnings are printed, summarize them plainly.

## Rules

- Use only Codex-specific/OpenAI coding-agent sources and Claude Code/Anthropic sources encoded in `aii/scripts/fetch_models.py`.
- Do not substitute generic ChatGPT or Claude chat model lists for Codex or Claude Code model data.
- Do not edit recommendations manually unless the fetch script reports warnings that require a conservative fallback.
- Do not expose secrets or environment values.
