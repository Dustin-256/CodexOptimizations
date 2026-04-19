---
name: code-review
description: review code-only changes against repository instructions and local style standards, recommend fixes, and optionally patch files after permission. supports whole project, src, subfolder, path, and single-file scopes.
---

# code-review

Review code only. Do not review or modify policy documents, plans, or other non-code files.

When reviewing code, use the repo's instruction sources as the standard:
- `AGENTS.md`
- `ProjectInstructions.md` if it exists in this repository

## Scope

This skill must support these review targets:
- whole project
- `src`
- subfolder
- path
- single file

## Target Selection

When invoked without an explicit target:
1. Check whether `git` is available and whether there are uncommitted changes.
2. If there are uncommitted changes, recommend reviewing those changed files first.
3. If there are no local changes and a `src` directory exists, recommend `src`.
4. Otherwise, recommend the whole project.

Always show the full choice list to the user:
- whole project
- `src`
- subfolder
- path
- single file

Do not start scanning until the user chooses a target or approves the recommended scan.

## Review Behavior

Focus on code quality, consistency, and maintainability.

Look for:
- violations of repo instructions
- small one-off helper functions that should be inlined instead of extracted
- unnecessary configuration variables or constants that were not requested
- over-abstraction that hurts readability
- naming or structure problems
- obvious performance or clarity regressions

Use judgment. Larger or genuinely reusable abstractions are acceptable.

## User-Invoked Mode

When the skill is invoked by the user:
- report the violations you find
- explain why they matter
- propose concrete fixes
- wait for the user's approval before patching files

After approval:
- patch the requested files directly
- keep the edits aligned with the user's instructions
- re-run the review on the patched files if needed to confirm the violations are resolved

## Plan-Executor Mode

When the skill is invoked automatically from `plan-executor`:
- review only the files changed by the current `plan-executor` run
- do not expand the review to unrelated files
- patch violations automatically within those changed files
- re-run the review until the changed files are clean or no safe fix remains

## Output Format

Keep the report concise and actionable:
- list findings in severity order
- include file paths for each finding
- include the suggested fix for each finding
- say clearly when no issues are found

Do not review policy documents as review targets. If they are mentioned as instruction sources, use them only as standards for code review.
