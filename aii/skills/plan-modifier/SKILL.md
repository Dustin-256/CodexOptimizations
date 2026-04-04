---
name: plan-modifier
description: modify an existing plan in place, preserve completed execution history, add or revise blocker-recovery substeps, and record an audit trail of plan changes.
---

# plan-modifier

Read an existing plan, discuss or apply requested changes, update the plan in place, and preserve a modification history.

This skill is for editing existing plans only. It should not create new plans from scratch and it should not execute plan steps.

## Workflow

### 1) Select the plan
Ask for the plan name first.

Load:

`aii/plans/<name>.yaml`

If the plan does not exist, stop and ask the user to provide a valid name or create one through `planner`.

### 2) Update shared metadata
Update:

`aii/metadata/state.yaml`

Use this structure:

```yaml
last_task:
  skill: plan-modifier
  target_type: plan
  target_name: <name>
  target_path: aii/plans/<name>.yaml
  state: in_progress | awaiting_input | completed
  resumable: true
  summary: <short human-readable summary>
  updated_at: <ISO-8601 timestamp>

history: []
```

Write metadata when modification starts, when user input is needed for non-obvious edits, and when the updated plan is saved.

### 3) Read the current plan before proposing changes
Use the existing plan as the source of truth for:
- current step ordering
- step status
- existing blocker history
- existing blocker-recovery substeps
- runtime metadata
- past modifications

Do not assume the user's request matches the current plan state until you have read it.

### 4) Distinguish obvious edits from design-shaping edits
Obvious edits may be applied autonomously.

Examples of obvious edits:
- renaming a step
- rewriting a step description without changing execution semantics
- adding or revising a note
- adjusting `runtime.auto_notify_after_seconds`
- making a directly requested, unambiguous wording cleanup

Design-shaping edits require discussion before saving.

Examples of design-shaping edits:
- reordering steps
- deleting steps
- splitting or merging steps
- changing plan scope
- changing execution semantics
- proactively adding blocker-recovery substeps to a step that is not currently blocked
- modifying blocked execution strategy in a way that introduces real tradeoffs

### 5) Preserve completed execution history
Treat completed steps as immutable execution history.

Do not:
- edit completed steps structurally
- delete completed steps
- reorder completed steps
- split or merge completed steps

If the user wants to change already-completed work:
- add a new corrective or follow-up step
- or recommend creating a new plan if the requested change effectively refactors already-finished logic at a broader level

### 6) Handle blocker-recovery substeps carefully
You may add or revise blocker-recovery substeps.

If the target step is already `blocked`:
- you may add or revise blocker-recovery substeps normally

If the target step is not currently `blocked`:
- warn the user that this is proactive fallback authoring
- ask for confirmation before saving

Use wording equivalent to:
"This step is not currently blocked. Adding blocker-recovery substeps now means we are pre-authoring fallback work. Do you still want to do that?"

### 7) Modification history
Every time you save the plan, append a modification record at the top level:

```yaml
modifications:
  - at: <ISO-8601 timestamp>
    type: <modification type>
    summary: <short human-readable summary>
    reason: <why this change was made>
```

Recommended `type` values:
- `rename_step`
- `update_step`
- `add_step`
- `delete_step`
- `reorder_steps`
- `split_step`
- `merge_steps`
- `add_blocker_recovery`
- `update_blocker_recovery`
- `remove_blocker_recovery`
- `update_runtime_metadata`

Do not rewrite old modification history entries. Append new ones.

### 8) Save behavior
Save changes in place only:

`aii/plans/<name>.yaml`

Do not create versioned copies such as `.v2`.

For obvious edits:
- apply directly
- append a modification record
- save the plan

For design-shaping edits:
- discuss the proposed change with the user
- explain important consequences or tradeoffs
- wait for approval
- then append a modification record and save

## Expected plan format

The plan is expected to support:

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

modifications: []

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
    blockers: []
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
- Ask for the plan name first.
- Always read the current plan before changing it.
- Edit plans in place only.
- Obvious edits may be applied autonomously.
- Non-obvious edits should be conversational and approved before saving.
- Never structurally modify completed steps.
- Use new corrective steps or a new plan when already-completed work needs to change.
- Proactive blocker-recovery substeps require a warning and explicit confirmation if the target step is not blocked.
- Append a modification history record every time the plan is saved.
- Keep `aii/metadata/state.yaml` updated so a future `$resume-last-task` flow can recover the current modification session cleanly.
