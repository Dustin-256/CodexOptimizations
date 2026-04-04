---
name: planner
description: generate an implementation plan from a named interview artifact and save it as a machine-readable yaml checklist under aii/plans. use after deep-interview is complete.
---

# planner

Read a saved interview, turn it into a sequential execution plan, confirm the plan with the user, and save it to:

`aii/plans/<name>.yaml`

This skill is for planning only. Do not implement plan steps.

## Workflow

### 1) Resolve the interview target from context first
Before asking for anything, determine whether the interview target is already clear from:

- the user's most recent message
- the immediately preceding chat context in this conversation
- `aii/metadata/state.yaml` if it points to a resumable or recently completed interview artifact

Prefer the current conversation over stale metadata when they disagree.

If the user is clearly continuing from a just-finished `deep-interview`, reuse that interview name directly instead of asking for it again.

If exactly one interview target is clearly implied, proceed with that target.

If the signals conflict or the target is still ambiguous, ask a short clarifying question for the interview name instead of guessing.

Load:

`aii/interviews/<name>.md`

If it does not exist, stop and ask the user to run `deep-interview` first or provide a valid name.

### 2) Read the interview before planning
Use the interview as the source of truth for:

- objective
- scope
- constraints
- caveats
- success criteria
- non-goals

If the interview verdict is `Not ready for planning`, do not generate a final plan. Explain why and direct the user back to `deep-interview`.

### 3) Draft a resumable plan
Produce a plan with actionable, sequential steps.

Each step should:
- represent a meaningful unit of work
- be specific enough to execute
- be resumable after interruption
- avoid combining unrelated work into a single step
- stay flat at the top level during planning

If a step is too large, split it into multiple top-level steps.

Do not create nested substeps during initial planning. Substeps are reserved for blocker-recovery work that may be added later if execution encounters a real blocker.

Prefer a small number of high-quality steps over a long noisy checklist.

### 4) Present the draft plan for approval
Before saving the plan, show the user:
- the ordered steps
- major assumptions
- any caveats inherited from the interview

Ask whether the plan is acceptable as written.

Do not save the plan until the user approves it.

### 5) Save the approved plan
Write the final plan to:

`aii/plans/<name>.yaml`

If a plan already exists, ask whether to overwrite it. Do not silently replace existing plans.

If the parent directory does not exist, create it.

### 6) Update shared metadata
Update:

`aii/metadata/state.yaml`

Use this structure:

```yaml
last_task:
  skill: planner
  target_type: plan
  target_name: <name>
  target_path: aii/plans/<name>.yaml
  state: in_progress | awaiting_input | completed
  resumable: true
  summary: <short human-readable summary>
  updated_at: <ISO-8601 timestamp>

history: []
```

Write metadata when planning starts, when awaiting user approval, and when the plan file is saved.

When planning starts from a conversation-driven handoff, ensure `target_name` and `target_path` match the interview artifact that was actually selected from chat context or metadata.

## YAML format

Use this structure:

```yaml
name: <name>
source_interview: aii/interviews/<name>.md
status: not_started
current_step_id: null

runtime:
  started_at: null
  last_active_at: null
  completed_at: null
  auto_notify_after_seconds: 300
  notification_sent: false

metadata:
  created_at: <ISO-8601 timestamp>
  last_updated: <ISO-8601 timestamp>
  readiness_verdict: <copied from interview>

steps:
  - id: step-1
    kind: standard
    title: <short title>
    description: <what this step accomplishes>
    status: pending
    notes: []
    verification: []
    runtime:
      started_at: null
      last_active_at: null
      completed_at: null
    blockers: []
    substeps: []
```

## Rules
- Check current chat context first, then recent task metadata, before asking for an interview name.
- Reuse the implied interview automatically when the handoff from `deep-interview` is clear.
- If chat context and metadata disagree, prefer the active conversation and mention the conflict briefly only if it affects confidence.
- Ask for the interview name only when the target remains ambiguous after checking both chat context and metadata.
- Do not implement any steps.
- Do not mark steps complete during plan creation.
- Start all step statuses as `pending`.
- Start plan status as `not_started`.
- Start `current_step_id` as `null`.
- Keep the plan machine-readable first; optimize for reliable future consumption by `plan-runner` or `plan-modifier`.
- Preserve important caveats from the interview in either step descriptions or a short assumptions summary before approval.
- Use `runtime.auto_notify_after_seconds: 300` by default unless the user explicitly wants a different threshold.
- Keep planning flat. If a step needs decomposition, create more top-level steps instead of nested steps.
- Do not create blocker-recovery substeps during initial planning.
- Reserve `substeps` for future execution-time blocker recovery only.
- Reserve `blockers` for execution history only. Initial plans should start with an empty `blockers` list on every step.
- Keep `aii/metadata/state.yaml` updated so a future `$resume-last-task` flow can recover the current planning session cleanly.
