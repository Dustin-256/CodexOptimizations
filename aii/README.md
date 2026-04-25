# aii

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

Use the Codex `fetch-models` skill or Claude Code `/fetch-models` to refresh `models/cache.yaml` from current official Codex/OpenAI and Claude Code/Anthropic sources. The model cache is tool-specific and must not be replaced with generic ChatGPT or Claude chat model lists.

## How to use it

1. Bootstrap the repo with `python3 bootstrap.py`.
2. Run a requirements interview and save it in `interviews/`.
3. Generate an execution plan into `plans/`.
4. Execute or modify the plan while persisting progress in `metadata/`.
5. Resume later using the saved state instead of starting over.

TTY runs with no flags open the interactive setup wizard. Use `python3 bootstrap.py --no-interactive --tool=codex` or `python3 bootstrap.py --no-interactive --tool=claude` to install a specific profile directly.
