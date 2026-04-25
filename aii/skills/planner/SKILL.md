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

### 4) Build a model recommendation
Before presenting the draft plan for approval, build a concise model recommendation from the interview and draft plan scope.

First load the model cache:

`aii/models/cache.yaml`

The cache must be specific to Codex and Claude Code. Do not substitute generic ChatGPT or Claude chat model lists when Codex or Claude Code model names, aliases, or reasoning/thinking controls may differ.

If the cache is missing or stale:
- say that model cache data is missing or stale
- recommend running the Codex `fetch-models` skill or the Claude Code `/fetch-models` project command, depending on the active tool
- use conservative tier-based guidance without claiming the named models are latest

If the cache is present and fresh enough, use it as the source of truth for available tool-specific model names, aliases, and reasoning/thinking options.

Recommendation rules:
- Recommend the best assistant/tool for the task, not merely the current tool.
- Prefer Codex for simple, moderate, iterative, and clearly scoped implementation work because the user's Codex token budget is materially larger.
- For most Codex work, recommend `GPT-5.5` with `medium` reasoning as the primary option.
- For cheaper Codex fallback, recommend `GPT-5.4` with `medium` reasoning, or `GPT-5.4-mini` with `medium` reasoning when stronger conservation is needed.
- Reserve Claude Code for major refactors, broad multi-file architectural changes, unusually high-risk migrations, or work that must be correct on the first serious execution attempt.
- For high-risk Claude Code work, recommend the Claude Code `opus` alias with `high` thinking as the primary option.
- For cheaper Claude Code fallback, recommend the Claude Code `sonnet` alias with `medium` thinking.
- Consider Claude Code `opusplan` only when the planning phase itself needs Opus-level architecture reasoning and execution can reasonably continue on Sonnet.

Every recommendation must include:
- current tool when it can be inferred, or `unknown`
- whether to stay on the current tool or switch tools
- primary tool, model or alias, and reasoning/thinking level
- cheaper fallback tool, model or alias, and reasoning/thinking level
- a brief rationale tied to the actual plan scope
- cache path and fetched timestamp when available
- display-ready text that can be saved and replayed later

Do not claim to know the current configured reasoning level if the runtime does not expose it. Recommend the target reasoning/thinking level instead.

Approval prompt recommendation format:

```markdown
Model recommendation:
- Primary: <tool>, <exact model or alias>, <reasoning/thinking level>. <one-sentence rationale>
- Fallback: <tool>, <exact model or alias>, <reasoning/thinking level>. <one-sentence rationale>
- Switch: <stay on current tool | switch to Codex | switch to Claude Code>. <one-sentence why>
```

Examples:
- For a normal scoped implementation in Codex: `Primary: Codex, GPT-5.5, medium reasoning. Fallback: Codex, GPT-5.4, medium reasoning.`
- For a normal scoped implementation while currently in Claude Code: recommend switching to `Codex, GPT-5.5, medium reasoning` unless the task risk justifies Claude.
- For a major high-risk refactor: `Primary: Claude Code, opus, high thinking. Fallback: Claude Code, sonnet, medium thinking` or a Codex high/xhigh fallback if Claude budget is tight.
- For a complex architecture planning pass that can execute cheaper afterward: consider `Claude Code, opusplan, high thinking`.

### 5) Present the draft plan for approval
Before saving the plan, show the user:
- the ordered steps
- major assumptions
- any caveats inherited from the interview
- the model recommendation, including primary and cheaper fallback

Ask whether the plan is acceptable as written.

Do not save the plan until the user approves it.

### 6) Save the approved plan
Write the final plan to:

`aii/plans/<name>.yaml`

If a plan already exists, ask whether to overwrite it. Do not silently replace existing plans.

If the parent directory does not exist, create it.

### 7) Update shared metadata
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
  model_recommendation:
    cache_path: aii/models/cache.yaml
    cache_fetched_at: <ISO-8601 timestamp | null>
    current_tool: Codex | Claude Code | unknown
    switch_recommendation: stay_on_current_tool | switch_to_codex | switch_to_claude_code | unknown
    primary:
      tool: Codex | Claude Code
      model: <exact model name or Claude Code alias>
      reasoning: <Codex reasoning level, when tool is Codex>
      thinking: <Claude Code thinking level, when tool is Claude Code>
      rationale: <why this is the best fit>
    fallback:
      tool: Codex | Claude Code
      model: <exact model name or Claude Code alias>
      reasoning: <Codex reasoning level, when tool is Codex>
      thinking: <Claude Code thinking level, when tool is Claude Code>
      rationale: <why this is the cheaper fallback>
    display_text: <exact recommendation text to replay during resume/execution>

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
- Read `aii/models/cache.yaml` before naming specific model recommendations.
- If `aii/models/cache.yaml` is missing or stale, recommend the Codex `fetch-models` skill or the Claude Code `/fetch-models` project command and avoid claiming stale model names are current.
- Model recommendations must be specific to Codex and Claude Code, not generic ChatGPT or Claude chat models.
- Always save `metadata.model_recommendation.display_text` so resume paths can replay the exact same recommendation without recalculating it.
- Use `runtime.auto_notify_after_seconds: 300` by default unless the user explicitly wants a different threshold.
- Keep planning flat. If a step needs decomposition, create more top-level steps instead of nested steps.
- Do not create blocker-recovery substeps during initial planning.
- Reserve `substeps` for future execution-time blocker recovery only.
- Reserve `blockers` for execution history only. Initial plans should start with an empty `blockers` list on every step.
- Keep `aii/metadata/state.yaml` updated so a future `$resume-last-task` flow can recover the current planning session cleanly.
