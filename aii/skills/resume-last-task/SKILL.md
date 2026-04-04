---
name: resume-last-task
description: read shared aii metadata, summarize the last resumable task in plain language, ask for confirmation, then hand off to the relevant skill after re-reading the underlying artifact.
---

# resume-last-task

Read shared task metadata, explain what was in progress in plain language, ask whether the user wants to continue, and then hand off to the relevant skill if confirmed.

This skill is for resuming work, not for directly editing plans or interviews itself.

## Workflow

### 1) Read shared metadata first
Load:

`aii/metadata/state.yaml`

If it does not exist, say there is no saved task to resume and stop.

Use `last_task` as the source of truth.

### 2) Validate resumability
If any of these are true, do not offer automatic resume:
- `last_task` is missing
- `last_task.resumable` is false
- `last_task.state` is `completed`
- `last_task.target_path` is missing
- the target file no longer exists

In those cases, explain the situation plainly and stop.

### 3) Re-read the underlying artifact before summarizing
Before offering resume, re-read the current target file referenced by:

`last_task.target_path`

Do not rely only on cached metadata. The target file may have changed since the last session.

### 4) Summarize in plain language
Explain all of the following with short, minimal-technical language:
- the current skill
- what we were doing
- the immediate next step
- what remains after that

Keep the summary concise and non-technical by default.

If the target is a plan, derive the summary from the actual plan state:
- immediate next step = the next actionable top-level step or blocker-recovery substep
- remaining work = a high-level summary of the remaining pending or blocked top-level steps

If the target is an interview:
- summarize what still needs clarification

If the target is a plan draft in `planner`:
- summarize whether the plan is awaiting approval or still needs drafting

If the target is a plan under `plan-modifier`:
- summarize what kind of plan change is in progress

### 5) Ask for confirmation
Ask whether the user wants to resume now.

Use plain wording similar to:

- `Last task: continue plan-executor on "worker-system-audit".`
- `Next: finish the recovery work for the blocked payout step.`
- `After that: retry that step, then continue the remaining steps for the worker audit.`
- `Do you want to resume this now?`

### 6) Hand off after confirmation
If the user confirms:
- re-read the target artifact again immediately before continuing
- hand off to the relevant skill named in `last_task.skill`
- continue using the stored target name/path

During handoff, the receiving skill should still consider the active conversation. If the user has clearly redirected to a different interview or plan in the current chat, do not blindly follow stale metadata.

Supported handoffs:
- `deep-interview`
- `planner`
- `plan-executor`
- `plan-modifier`

If the stored skill is unsupported or inconsistent with the target artifact, explain the problem and stop instead of guessing.

## Shared metadata expectations

Expected metadata shape:

```yaml
last_task:
  skill: deep-interview | planner | plan-executor | plan-modifier
  target_type: interview | plan
  target_name: <name>
  target_path: aii/interviews/<name>.md | aii/plans/<name>.yaml
  state: in_progress | blocked | awaiting_input | completed
  resumable: true | false
  summary: <short human-readable summary>
  updated_at: <ISO-8601 timestamp>

history: []
```

## Rules
- Always read `aii/metadata/state.yaml` first.
- Always re-read the underlying target file before summarizing.
- Keep the explanation short and low-jargon by default.
- For plans, summarize the remaining top-level work at a high level rather than dumping raw YAML details.
- Do not resume automatically without confirmation.
- After confirmation, re-read the artifact one more time before handing off.
- Treat metadata as the resume source of truth for offering the resume, but let the active conversation override it if the user explicitly redirects before handoff.
