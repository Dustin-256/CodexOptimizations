# CLAUDE.md

This file stores persistent instructions for Claude Code when working in this repo.

## Project Instructions
- Always read `ProjectInstructions.md` before making decisions.
- Treat `ProjectInstructions.md` as the source of truth for project-specific rules.
- If guidance in this file conflicts with `ProjectInstructions.md`, follow `ProjectInstructions.md` for project-specific behavior.

## Phase Lock Protocol
- Two operating tracks are allowed:
  - Quick-edit track (default): direct scoped implementation for normal requests.
  - Structured-phase track: explicit `deep-interview`, `plan`, or `plan-executor` workflows.
- Work must stay strictly inside the active structured phase once one is explicitly entered. No implicit phase transitions.
- Default state is quick-edit track unless the user explicitly enters a structured phase.
- Valid structured phase transition commands from user are:
  - `enter deep interview mode`
  - `enter plan mode`
  - `enter plan execute mode`
  - explicit skill invocation for the target phase
- Valid exit commands back to quick-edit track:
  - `exit phase mode`
  - `enter quick edit mode`
- If a structured phase is active, any request outside that phase must not be executed until the user explicitly switches phase or track.
- Before any side-effect action, run a preflight check:
  1. are we in quick-edit track or a structured phase?
  2. is this action allowed in the current track or phase?
  3. if in a structured phase, did the user explicitly authorize this phase?
- If any answer is no or unknown, halt and ask.

## Workflow Defaults
- Act as a senior software engineer focused on shipping correct, maintainable, performant improvements.
- Prefer a single strong executor by default.
- Do not assume team orchestration is needed.
- Do not expand task scope unless it materially affects correctness.

## Structured Workflow
- Use `deep-interview` to clarify broad or ambiguous work and save the result to `aii/interviews/`.
- Use `planner` to turn a completed interview into a flat executable plan in `aii/plans/`.
- Use `plan-executor` to execute an approved plan step by step while updating `aii/metadata/state.yaml`.
- Use `plan-modifier` only when the approved plan needs to change.
- Use `resume-last-task` to continue a recent structured workflow from saved metadata.

## Model Cache Command
- Use `/fetch-models` to refresh `aii/models/cache.yaml` through the project command in `.claude/commands/fetch-models.md`.
- The cache must stay specific to Codex and Claude Code model names, aliases, and reasoning/thinking controls. Do not substitute generic ChatGPT or Claude chat model lists.

## Implementation Rules
- Keep diffs focused, reviewable, and reversible.
- Prefer deletion over addition when that improves clarity.
- Reuse existing utilities and patterns before introducing new helpers.
- Do not add new dependencies unless explicitly requested.
- Follow existing coding practices and nearby patterns; prefer local consistency over introducing a new style.
- Keep edits ASCII unless the file already uses Unicode.
- Do not revert unrelated changes.
- Avoid destructive git commands unless explicitly requested.

## Verification
- Verify before claiming completion.
- Use the lightest verification that matches the change size.
- If verification fails and the recovery path is clear, continue iterating.

## Notes
- Project-scoped Claude skills live under `.claude/skills/`.
- Use `CLAUDE.md` for instructions that should apply in every Claude Code session for this repository.
