# CodexOptimizations

Utilities and scaffolding for adding reusable Codex workflows to a repository.

## Why this is useful

Most teams lose time repeating the same planning and execution setup for AI-assisted work. This repo gives you a reusable baseline so every project starts with:
- a consistent `AGENTS.md` operating model
- reusable Codex skills for requirement capture, planning, execution, and resuming work
- a stable folder structure for interview artifacts, machine-readable plans, and task metadata

Result: faster setup, less process drift, and easier handoff between sessions.

## What it can do

`bootstrap.py` can:
- scaffold an `aii/` workspace (`skills/`, `interviews/`, `plans/`, `metadata/`)
- fetch and install canonical `AGENTS.md` and skill definitions from this repo
- back up an existing `AGENTS.md` to `AGENTS.md.bak` before replacing it
- symlink skills into `~/.codex/skills` so Codex can use them directly
- manage `.gitignore` entries for generated `aii` artifacts
- uninstall the scaffold and restore previous agent config

## What it installs

Running the bootstrap creates or updates:
- `AGENTS.md` (fetched from this repo's `main` branch)
- `aii/README.md`
- `aii/interviews/.gitkeep`
- `aii/plans/.gitkeep`
- `aii/metadata/.gitkeep`
- `aii/metadata/state.yaml`
- `aii/skills/*/SKILL.md` for:
  - `deep-interview`
  - `planner`
  - `plan-executor`
  - `plan-modifier`
  - `resume-last-task`

It also updates `.gitignore` to keep generated workflow artifacts untracked.

## Skill roles

Installed skills are designed to work as a pipeline:
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
  - `~/.codex/skills` (unless `--no-install-skills` is used)

## Usage

From the repository root:

```bash
python3 bootstrap.py
```

Typical workflow:
1. Run `python3 bootstrap.py` in a target repository.
2. Start using the installed skills (for example: requirements interview -> plan generation -> plan execution).
3. Keep `aii/interviews/`, `aii/plans/`, and `aii/metadata/` as the project memory for ongoing work.

### Options

- `--force`:
  overwrite existing scaffold files and replace existing skill links
- `--no-install-skills`:
  scaffold repository files only; skip `~/.codex/skills` symlinks
- `--uninstall`:
  remove scaffolded content and restore `AGENTS.md` from `AGENTS.md.bak` when available
- `--webhook URL`:
  save `codex_webhook=URL` to `.env` for long-task completion reports (and bootstrap run reports)

Examples:

```bash
# Fresh install
python3 bootstrap.py

# Reinstall and overwrite existing scaffold files
python3 bootstrap.py --force

# Scaffold repo only (no ~/.codex/skills symlinks)
python3 bootstrap.py --no-install-skills

# Remove scaffold and restore AGENTS backup
python3 bootstrap.py --uninstall

# Save webhook to .env and report run status
python3 bootstrap.py --webhook https://discord.com/api/webhooks/...
```

## Uninstall behavior

`--uninstall` does the following:
- removes symlinked skills for this scaffold from `~/.codex/skills`
- removes `aii/`
- restores `AGENTS.md` from `AGENTS.md.bak` (or removes `AGENTS.md` if no backup exists)
- removes the bootstrap-managed block from `.gitignore`

## Repository layout

```text
.
├── bootstrap.py
├── AGENTS.md
├── todo.md
└── aii/
    ├── README.md
    ├── interviews/
    ├── plans/
    ├── metadata/
    └── skills/
```

## Notes

- The bootstrap script fetches canonical `AGENTS.md` and skill definitions from this repository's `main` branch.
- Existing `AGENTS.md` is backed up to `AGENTS.md.bak` before install.
- If a target skill path in `~/.codex/skills` already exists and is not the expected symlink, `--force` is required.
- Keep `.env` gitignored so `codex_webhook` remains local.
