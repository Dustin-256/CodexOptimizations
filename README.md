# CodexOptimizations

Utilities and scaffolding for adding reusable Codex and Claude Code workflows to a repository.

## One-Line Install (Users)

Run one command to download `bootstrap.py`, execute it once, then delete it.

### Windows (PowerShell)

```powershell
$tmp = Join-Path $env:TEMP "codex-bootstrap.py"; Invoke-WebRequest "https://raw.githubusercontent.com/Dustin-256/CodexOptimizations/main/bootstrap.py" -OutFile $tmp; try { py -3 $tmp } finally { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
```

### Windows (PowerShell, `--force`)

```powershell
$tmp = Join-Path $env:TEMP "codex-bootstrap.py"; Invoke-WebRequest "https://raw.githubusercontent.com/Dustin-256/CodexOptimizations/main/bootstrap.py" -OutFile $tmp; try { py -3 $tmp --force } finally { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
```

### Linux

```bash
tmp="$(mktemp)"; curl -fsSL "https://raw.githubusercontent.com/Dustin-256/CodexOptimizations/main/bootstrap.py" -o "$tmp" && python3 "$tmp"; rc=$?; rm -f "$tmp"; exit $rc
```

### Linux (`--force`)

```bash
tmp="$(mktemp)"; curl -fsSL "https://raw.githubusercontent.com/Dustin-256/CodexOptimizations/main/bootstrap.py" -o "$tmp" && python3 "$tmp" --force; rc=$?; rm -f "$tmp"; exit $rc
```

### macOS

```bash
tmp="$(mktemp)"; curl -fsSL "https://raw.githubusercontent.com/Dustin-256/CodexOptimizations/main/bootstrap.py" -o "$tmp" && python3 "$tmp"; rc=$?; rm -f "$tmp"; exit $rc
```

### macOS (`--force`)

```bash
tmp="$(mktemp)"; curl -fsSL "https://raw.githubusercontent.com/Dustin-256/CodexOptimizations/main/bootstrap.py" -o "$tmp" && python3 "$tmp" --force; rc=$?; rm -f "$tmp"; exit $rc
```

## Why this is useful

Most teams lose time repeating the same planning and execution setup for AI-assisted work. This repo gives you a reusable baseline so every project starts with:
- a consistent structured workflow for interviews, planning, execution, and resume
- a Codex-default setup that can also target Claude Code with `--tool=claude`
- a stable folder structure for interview artifacts, machine-readable plans, and task metadata

Result: faster setup, less process drift, and easier handoff between sessions.

## What it can do

`bootstrap.py` can:
- scaffold an `aii/` workspace (`skills/`, `scripts/`, `models/`, `interviews/`, `plans/`, `metadata/`)
- fetch and install canonical instruction files and workflow assets from this repo
- install a Codex profile or a Claude Code profile from the same setup engine
- launch a full interactive arrow-key setup wizard when run in a TTY with no flags
- fetch and install canonical utility scripts (including webhook embed sender) from this repo
- maintain a shared `aii/models/cache.yaml` for Codex and Claude Code model recommendations
- refresh that model cache with `/fetch-models`
- back up an existing `AGENTS.md` to `AGENTS.md.bak` before replacing it
- back up an existing `CLAUDE.md` to `CLAUDE.md.bak` before replacing it
- symlink skills into `~/.codex/skills` so Codex can use them directly
- manage `.gitignore` entries for generated `aii` artifacts
- uninstall the scaffold and restore previous agent config

## What it installs

Running the bootstrap always creates or updates:
- `aii/README.md`
- `aii/scripts/send_webhook_embed.py`
- `aii/scripts/fetch_models.py`
- `aii/models/.gitkeep`
- `aii/interviews/.gitkeep`
- `aii/plans/.gitkeep`
- `aii/metadata/.gitkeep`
- `aii/metadata/state.yaml`
- `aii/skills/*/SKILL.md` for:
  - `code-review`
  - `deep-interview`
  - `planner`
  - `plan-executor`
  - `plan-modifier`
  - `resume-last-task`

Tool-specific outputs:
- Codex default:
  - `AGENTS.md`
  - `~/.codex/skills/<skill>` symlinks, unless `--no-install-skills` is used
- Claude Code:
  - `CLAUDE.md`
  - `.claude/settings.json`
  - `.claude/commands/fetch-models.md`
  - `.claude/skills/*/SKILL.md`

It also updates `.gitignore` to keep generated workflow artifacts untracked.

The installed `aii/scripts/send_webhook_embed.py` script provides a shared, embed-first webhook notification path for progress, blocked, success, failure, and test events.

The installed `aii/scripts/fetch_models.py` script refreshes `aii/models/cache.yaml` from current official Codex/OpenAI and Claude Code/Anthropic sources. The cache is intentionally tool-specific; it should not be replaced with generic ChatGPT or Claude chat model lists.

## Skill roles

Installed skills are designed to work as a pipeline:
- `code-review`: reviews code-only changes against repo instructions and coding standards, then proposes or applies fixes.
- `deep-interview`: captures requirements, constraints, assumptions, and ambiguity into a structured interview artifact.
- `planner`: turns the interview artifact into an executable YAML plan under `aii/plans/`.
- `plan-executor`: executes or resumes a plan step-by-step while persisting progress and blockers.
- `plan-modifier`: updates an existing plan in place when scope changes or blockers require plan revisions.
- `resume-last-task`: restores the most recent resumable task context from `aii/metadata/` and continues work.

Use them independently when needed, but the normal flow is interview -> plan -> execute -> modify (if needed) -> resume later.

## Requirements

- Python 3.9+
- Network access to GitHub raw content (`raw.githubusercontent.com`)
- Filesystem permission to write:
  - the current repository
  - `~/.codex/skills` for Codex installs unless `--no-install-skills` is used

## Usage

From the repository root:

```bash
python3 bootstrap.py
```

TTY runs with no flags open the interactive setup wizard by default. Use `--no-interactive` to force the old non-interactive behavior.

### Contributor Init (Repo Clone)

For contributors working on this repository itself, run:

```bash
python3 init_repo.py
```

This does one-time local contributor setup:
- installs the managed `pre-push` version hook
- does not run bootstrap or scaffold files

Typical workflow:
1. Run `python3 bootstrap.py` in a target repository.
2. Start using the installed skills (for example: requirements interview -> plan generation -> plan execution).
3. Keep `aii/interviews/`, `aii/plans/`, and `aii/metadata/` as the project memory for ongoing work.
4. Run `/fetch-models` when model recommendations need the latest Codex and Claude Code model cache.

### Options

- `--tool codex|claude`:
  choose the tool profile to install; defaults to `codex`
- `--force`:
  overwrite existing scaffold files and replace existing skill links
- `--no-install-skills`:
  skip `~/.codex/skills` symlinks for Codex installs
- `--uninstall`:
  remove scaffolded content and restore `AGENTS.md` or `CLAUDE.md` from backups when available
- `--webhook URL`:
  save `codex_webhook=URL` to `.env` for embed-based webhook reports (including bootstrap run reports)
- `--always-skip-missing-webhook`:
  save `codex_ignore_webhook_missing=true` to `.env` so runs do not halt when `codex_webhook` is missing
- `--test-webhook-embed`:
  send a test embed using current webhook settings, then exit
- `--interactive`:
  force the full interactive arrow-key wizard
- `--no-interactive`:
  disable the wizard even in a TTY

Examples:

```bash
# Interactive install with prompts
python3 bootstrap.py

# Non-interactive Codex install
python3 bootstrap.py --no-interactive

# Non-interactive Claude install
python3 bootstrap.py --no-interactive --tool=claude

# Reinstall and overwrite existing scaffold files
python3 bootstrap.py --tool=claude --force

# Codex scaffold without ~/.codex/skills symlinks
python3 bootstrap.py --tool=codex --no-install-skills

# Remove scaffold and restore backups
python3 bootstrap.py --uninstall

# Save webhook to .env and report run status using embeds
python3 bootstrap.py --webhook https://discord.com/api/webhooks/...

# Persist skip behavior when webhook is intentionally not configured
python3 bootstrap.py --always-skip-missing-webhook

# Send a test embed and exit
python3 bootstrap.py --test-webhook-embed
```

### Shared Embed Script

Use the installed helper for non-bootstrap notifications:

```bash
python3 aii/scripts/send_webhook_embed.py \
  --event progress \
  --summary "Executing plan step" \
  --plan-name worker-system-audit \
  --step-id step-2 \
  --step-title "Validate remote throttling" \
  --runtime "6m 12s"
```

### Model Cache Refresh

Use `/fetch-models` to refresh `aii/models/cache.yaml`.

For Codex, the project instructions treat `/fetch-models` as a request to run:

```bash
python3 aii/scripts/fetch_models.py
```

For Claude Code installs, the bootstrap writes `.claude/commands/fetch-models.md`, which exposes `/fetch-models` as a project slash command.

## Uninstall behavior

`--uninstall` does the following:
- removes symlinked skills for this scaffold from `~/.codex/skills`
- removes managed Claude project files such as `.claude/settings.json` and `.claude/skills/*`
- removes `aii/`
- restores `AGENTS.md` or `CLAUDE.md` from backups when available
- removes the bootstrap-managed block from `.gitignore`

## Repository layout

```text
.
├── bootstrap.py
├── AGENTS.md / CLAUDE.md
├── .claude/
├── todo.md
└── aii/
    ├── README.md
    ├── models/
    ├── scripts/
    │   ├── fetch_models.py
    │   └── send_webhook_embed.py
    ├── interviews/
    ├── plans/
    ├── metadata/
    └── skills/
```

## Notes

- The bootstrap script fetches the cached setup engine from this repository's `main` branch unless the local cached version is already current.
- Existing `AGENTS.md` and `CLAUDE.md` are backed up before install when present.
- If a target skill path in `~/.codex/skills` already exists and is not the expected symlink, `--force` is required.
- Claude installs use project-scoped Claude skills under `.claude/skills/`.
- Keep `.env` gitignored so `codex_webhook` and `codex_ignore_webhook_missing` remain local.
