# Interview: tool-agnostic-setup-cli

## Objective
Decide whether the repo should expose a tool-agnostic setup flow that defaults to Codex, while allowing explicit selection of Claude and future tools.

## Current State
The repo is currently Codex-oriented. `bootstrap.py` downloads and runs `aii/scripts/setup.py`, and that setup script installs Codex-specific skills, `AGENTS.md`, and Codex local state.
`bootstrap.py` should remain a thin wrapper.

## Desired Outcome
A single setup entrypoint that can keep Codex as the default but accept something like `--tool=claude` to generate tool-specific setup behavior now and for future tools later.
The workflow should stay the same across tools where possible.
Claude should get its own config files and install path details so the setup is fully Claude-compatible while preserving the same overall workflow.
The entire setup flow should be keyboard-navigable with arrow keys and Enter when run interactively.

## Constraints
- Codex must remain the default behavior unless explicitly overridden.
- The existing workflow should not break for current users.
- The design should stay simple enough to extend to more tools later.
- Tool-specific behavior may affect installed instructions, skill layout, and local integration points.
- The setup should support a data-driven registry instead of a hardcoded one-off switch.
- Claude support should make use of Claude-specific config and integration points rather than a lowest-common-denominator fallback.
- The interactive CLI should support full-flow navigation, not just an initial menu.

## Assumptions
- `aii/scripts/setup.py` is the right place for the CLI behavior, with `bootstrap.py` staying as a thin launcher.
- The user wants a practical selector, not a one-off Claude-only branch.
- Future tool support should be additive rather than requiring a rewrite.
- Keeping the same high-level workflow for Claude is acceptable if the implementation stays tool-aware.
- "100% Claude compatibility" means the setup should install the right Claude-specific files and conventions available in this repo, not just rename Codex artifacts.

## Open Questions
None.

## Success Criteria
- Running setup with no tool flag produces the current Codex-oriented scaffold.
- Running setup with `--tool=claude` produces Claude-specific setup behavior.
- Adding another tool later requires small, local changes.
- The current Codex flow still works without extra steps.
- The workflow shape remains consistent across tools unless a tool cannot support a specific step.
- Claude-specific config files and install behavior are generated automatically when `--tool=claude` is selected.
- The repo keeps a shared workflow while remaining fully tool-aware.
- Interactive runs let the user move through the setup flow with arrow keys and select options without typing every choice.

## Non-Goals
- Designing every future tool integration in detail.
- Reworking unrelated repository workflows.
- Changing the high-level interview/plan/execute workflow unless a tool requires a small compatibility tweak.
- Removing the Codex default.

## Interview Metrics
- Ambiguity: 2/10
- Scope Clarity: 9/10
- Dependency Clarity: 8/10
- Implementation Readiness: 8/10
- Risk Level: 3/10
- Requirements Confidence: 9/10

## Readiness Verdict
Ready for planning

## Remaining Gaps
- None.
