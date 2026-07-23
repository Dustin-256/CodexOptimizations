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
- Prefer a single strong executor by default; recommend a subagent or multi-agent split when it is clearly worth it (see the Subagent and Multi-Agent Recommendation Rule).
- Do not expand task scope unless it materially affects correctness.

## Subagent and Multi-Agent Recommendation Rule
- Default to a single strong executor. Do not fan out work for its own sake.
- Proactively recommend a subagent or multi-agent split when it is clearly worth it. Treat it as worth it when any of these hold:
  - the task has 2 or more independent lanes with different outputs that can progress without merge or conflict churn
  - broad read-only investigation spans many files where parallel search would materially cut time
  - independent review or verification would benefit from a separate perspective than the implementer
  - a large, well-bounded surface would be slow to execute sequentially and its lanes are cleanly separable
- Do not recommend a split when the lanes are tightly coupled, touch the same files, or need constant coordination; coordination cost usually outweighs the benefit.
- Recommend rather than silently switch: state the proposed lanes, the coordination or merge plan, and why it is worth it, then let the user confirm before starting multi-agent execution.
- This is tool-agnostic. Claude Code can run the split with its subagent capability; other tools can use separate sessions or worktrees per lane. Only add tool-specific mechanics when a lane actually needs them.
- Respect the Phase Lock Protocol: a recommendation is not a phase transition, and entering multi-agent execution still requires the user's explicit go-ahead.

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
