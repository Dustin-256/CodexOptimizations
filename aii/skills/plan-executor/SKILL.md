---
name: plan-executor
description: execute or resume an existing plan from aii/plans, persist progress and blocker history, handle blocker-resolution discussions, and continue until the plan is complete or waiting on user input.
---

# plan-executor

Read an existing plan, execute it step by step, persist state changes as work progresses, and resume cleanly after interruptions.

This skill is for execution. It should not create new plans and it should not silently modify plan structure beyond execution-time state updates and approved blocker-recovery substeps.

## Workflow

### 1) Resolve the plan target from context first
Before asking for anything, determine whether the plan target is already clear from:

- the user's most recent message
- the immediately preceding chat context in this conversation
- `aii/metadata/state.yaml` if it points to a resumable or recently active plan artifact

Prefer the current conversation over stale metadata when they disagree.

If the user is clearly continuing from a just-finished `planner` handoff or a recent paused execution session, reuse that plan name directly instead of asking for it again.

If exactly one plan target is clearly implied, proceed with that target.

If the signals conflict or the target is still ambiguous, ask a short clarifying question for the plan name instead of guessing.

Load:

`aii/plans/<name>.yaml`

Also load the source interview referenced by the plan.

If the plan does not exist, stop and ask the user to run `planner` first or provide a valid name.

### 2) Update shared metadata immediately
Update:

`aii/metadata/state.yaml`

Use this structure:

```yaml
last_task:
  skill: plan-executor
  target_type: plan
  target_name: <name>
  target_path: aii/plans/<name>.yaml
  state: in_progress | blocked | awaiting_input | completed
  resumable: true
  summary: <short human-readable summary>
  updated_at: <ISO-8601 timestamp>

history: []
```

Write metadata:
- when execution starts
- when execution pauses for user input
- when a blocker is recorded
- when the plan completes

When execution starts from a conversation-driven handoff, ensure `target_name` and `target_path` match the plan artifact that was actually selected from chat context or metadata.

### 3) Resume from persisted plan state
Read the plan as the source of truth.

Use:
- `status`
- `current_step_id`
- each step's `status`
- blocker history
- blocker-recovery `substeps`
- runtime timestamps

If the plan is already `completed`, report that clearly and stop.

If the current step is `blocked` and recovery substeps already exist, continue automatically with those recovery substeps.

If the current step is `blocked` and no recovery substeps exist, enter blocker-resolution mode.

Otherwise, continue from the next executable step.

### 4) Persist state before doing work
Before executing a step:
- set the plan `status` to `in_progress` if needed
- set `current_step_id`
- set the step status to `in_progress`
- set `runtime.started_at` if empty
- update `runtime.last_active_at`

Write this state before doing the execution work so resume can detect that execution had already begun if the session is interrupted.

### 5) Execute sequentially
Execute top-level steps in order.

For blocked steps with approved recovery substeps:
- execute the recovery substeps in order
- if they all complete without blockage, retry the parent step automatically

Do not skip steps silently.
Do not reorder steps unless the user explicitly changes the plan through `plan-modifier`.

### 6) Verification before completion
Do not mark a step `completed` unless it has been verified at a level appropriate to the change.

Record concise verification notes in the step's `verification` list.

When a step completes:
- set the step status to `completed`
- update the step runtime timestamps
- add concise execution notes if useful
- update the plan `current_step_id`

### 7) Blocker-resolution mode
If execution cannot continue safely, mark the step as `blocked`.

When blocking a step:
- keep existing blocker history
- append a new blocker record rather than overwriting older blockers
- include a clear blocker reason
- include notes explaining what went wrong
- set blocker `created_at`
- leave `resolved_at` as `null`

After recording the blocker:
- propose several fix options
- for each option, explain why it may work and what its tradeoffs are
- let the user choose one or propose their own fix

If the user proposes their own fix and there are meaningful downsides:
- state those tradeoffs explicitly
- ask whether the user wants to accept them
- if needed, discuss ways to minimize the tradeoffs before proceeding

Once a fix is agreed:
- convert that recovery work into blocker-recovery substeps under the blocked step
- execute those substeps
- if they complete successfully, retry the parent step automatically

If a recovery substep blocks, record that blocker and stop there.

### 8) Long-task notification behavior
Use plan metadata and runtime timestamps to determine whether notification should be sent.

Default auto-notify threshold:

`runtime.auto_notify_after_seconds: 300`

This value may be overridden in the plan metadata.

Do not run a ticking timer. Instead, compute elapsed time from timestamps whenever state changes or a notification decision is needed.

If the plan was initially judged long-running, ask once at the start whether the user wants webhook notifications.

Even if the plan was not initially judged long-running, if computed runtime exceeds the auto-notify threshold, send notification automatically when possible.

Webhook source:
- check `.env` for `codex_webhook=...`
- if no webhook is configured and notification is needed, ask the user for the URL

Send webhook notifications for:
- plan completion
- blockers that pause execution and require user input

Default blocker webhook content:
- plan name
- blocked step id and title
- short blocker reason
- current runtime in human-readable form
- note that user input is needed

Default completion webhook content:
- plan name
- total runtime in human-readable form
- note that execution completed

Do not include secrets or excessive logs in webhook messages.

### 9) Completion
When all top-level steps are completed:
- set plan `status` to `completed`
- clear `current_step_id`
- set plan `runtime.completed_at`
- update plan metadata timestamps
- update shared metadata to `completed`
- send completion webhook if notification applies

## Plan format expectations

The plan is expected to follow this structure:

```yaml
name: <name>
source_interview: aii/interviews/<name>.md
status: not_started | in_progress | blocked | completed
current_step_id: null | step-<n>

runtime:
  started_at: null | <ISO-8601 timestamp>
  last_active_at: null | <ISO-8601 timestamp>
  completed_at: null | <ISO-8601 timestamp>
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
    status: pending | in_progress | blocked | completed
    notes: []
    verification: []
    runtime:
      started_at: null | <ISO-8601 timestamp>
      last_active_at: null | <ISO-8601 timestamp>
      completed_at: null | <ISO-8601 timestamp>
    blockers:
      - id: blocker-1
        status: active | resolved
        reason: <short explanation>
        notes: []
        created_at: <ISO-8601 timestamp>
        resolved_at: null | <ISO-8601 timestamp>
    substeps:
      - id: step-1.1
        kind: blocker_recovery
        title: <short title>
        description: <what this recovery substep does>
        status: pending | in_progress | blocked | completed
        notes: []
        verification: []
        runtime:
          started_at: null | <ISO-8601 timestamp>
          last_active_at: null | <ISO-8601 timestamp>
          completed_at: null | <ISO-8601 timestamp>
        blockers: []
```

## Rules
- Check current chat context first, then recent task metadata, before asking for a plan name.
- Reuse the implied plan automatically when the handoff from `planner`, `resume-last-task`, or an obvious follow-up execution request is clear.
- If chat context and metadata disagree, prefer the active conversation and mention the conflict briefly only if it affects confidence.
- Ask for the plan name only when the target remains ambiguous after checking both chat context and metadata.
- Always read the current plan before changing it.
- Persist `in_progress` state before doing execution work.
- Persist completion or blocker results immediately after execution changes state.
- Preserve blocker history. Never delete old blocker records.
- When a blocker is resolved, keep the blocker record and mark it `resolved` with `resolved_at`.
- Use flat top-level execution for normal work.
- Reserve `substeps` for blocker-recovery only.
- Continue recovery substeps automatically on resume if they already exist.
- Use human-readable time strings when reporting runtime to the user or to webhooks.
- Keep `aii/metadata/state.yaml` updated so a future `$resume-last-task` flow can recover the current execution state cleanly.
