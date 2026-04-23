---
name: deep-interview
description: gather structured requirements for a task and save them as a markdown interview artifact under aii/interviews. use when a request is broad, underspecified, high-impact, ambiguous, or when the user wants requirements clarified before planning or implementation. suggest an interview name when missing, run an iterative ambiguity-reduction interview, score readiness metrics, and produce a readiness verdict for whether the task is ready for planning.
---

# deep-interview

Run a structured requirements interview and save the result to:

`aii/interviews/<name>.md`

This skill is for clarification only. Do not implement code, modify plans, or execute tasks.

## Workflow

### 1) Resolve interview name with suggestion-first behavior
If the user did not provide an interview name, generate a reasonable default name suggestion from the request context.

Ask for confirmation using natural language like:

`You didn't specify a name. Is "<suggested-name>" okay?`

Do not send a separate name-only turn when you already have other clarification questions to ask. Include the name confirmation in the same response paragraph/block as the rest of your current interview questions.

If the user explicitly provides a different name (for example: `use "<name>"`), use that user-provided name.

If the user ignores the name prompt but answers other interview questions, continue the interview and keep using the generated suggested name as the active default.

Use the resolved name for the artifact path:

`aii/interviews/<name>.md`

If the name would be unsafe as a filename, normalize it conservatively while preserving intent.

### 2) Run an iterative deep interview
Your job is to reduce ambiguity until the task is clear enough for planning.

Gather and refine these sections:

- Objective
- Current State
- Desired Outcome
- Constraints
- Assumptions
- Open Questions
- Success Criteria
- Non-Goals

Do not dump a huge questionnaire all at once. Ask in small batches, usually 1 to 3 questions at a time.

Prefer to resolve obvious questions from provided context or code before asking the user.

Keep interviewing until one of these is true:
- the task is clearly ready for planning
- the remaining uncertainty is explicitly recorded as caveats
- the task is not ready for planning and the missing pieces are clearly identified

### 3) Behave like an ambiguity-reduction loop
Take heavy inspiration from the useful part of OMX deep interview behavior:

- identify ambiguity
- ask targeted follow-up questions
- refine the model of the task
- repeat until readiness can be judged

Do not ask repetitive questions.
Do not ask questions whose answers are already grounded in available context.
Do not start planning or implementing.

### 4) Score readiness metrics
When the interview is sufficiently developed, score these metrics from 1 to 10:

- Ambiguity
- Scope Clarity
- Dependency Clarity
- Implementation Readiness
- Risk Level
- Requirements Confidence

Interpretation:
- Higher Ambiguity = worse
- Higher Risk Level = worse
- Higher values for the other metrics = better

These scores should reflect the clarified state at the end of the interview, not the initial request.

### 4.5) Show per-response interview analytics
Every conversational response during deep interview should begin with a compact analytics header.

Use this header on each reply, not just in the final saved artifact.

The header should include:
- Ambiguity
- Scope Clarity
- Dependency Clarity
- Implementation Readiness
- Risk Level
- Requirements Confidence
- Readiness as a 0 to 100 value shown with a 20-slot bar

Use a 20-slot readiness bar where each slot represents 5 percent.

Example:

```markdown
Interview Metrics
- Ambiguity: 3/10
- Scope Clarity: 8/10
- Dependency Clarity: 7/10
- Implementation Readiness: 6/10
- Risk Level: 4/10
- Requirements Confidence: 7/10
- Readiness: 70% [##############------]
```

After the header, continue with the actual interview response.

Keep the header compact and consistent across turns.

### 5) Produce a readiness verdict
After scoring, include exactly one of these verdicts:

- Ready for planning
- Ready for planning with caveats
- Not ready for planning

Use both heuristic judgment and consistent threshold-like reasoning.

Suggested decision logic:
- **Ready for planning**
  - Ambiguity is low
  - Scope Clarity is high
  - Dependency Clarity is at least moderate
  - Implementation Readiness is high
  - Requirements Confidence is high
  - Remaining gaps are minor and explicitly listed

- **Ready for planning with caveats**
  - Core objective is clear
  - Planning can proceed
  - Some dependencies, assumptions, or open questions remain
  - Caveats are explicitly listed

- **Not ready for planning**
  - Ambiguity remains high
  - Or key constraints/dependencies are unknown
  - Or implementation readiness/confidence is too low
  - Missing information would likely lead to a poor or unstable plan

Do not overfit to rigid math. Use judgment, but keep it consistent.

If the verdict is `Ready for planning with caveats`, include a `Caveats` section immediately after the verdict. Use a short numbered list that turns the remaining gaps into direct follow-up questions. Derive those questions from both the recorded gaps and the interview context. If a proposed direction has a tradeoff, call out the tradeoff, mention a concise high-level alternative, and ask the user to confirm they understand the risk and want to proceed or switch to the alternative. Omit the `Caveats` section entirely when the verdict is `Ready for planning` or `Not ready for planning`.

### 6) Save the interview artifact
Write the final artifact to:

`aii/interviews/<name>.md`

If the parent directory does not exist, create it.

If the user immediately asks to continue into planning in the same conversation, treat this saved interview as the default handoff target unless the user names a different interview.

### 7) Update shared metadata
Update:

`aii/metadata/state.yaml`

Use this structure:

```yaml
last_task:
  skill: deep-interview
  target_type: interview
  target_name: <name>
  target_path: aii/interviews/<name>.md
  state: in_progress | awaiting_input | completed
  resumable: true
  summary: <short human-readable summary>
  updated_at: <ISO-8601 timestamp>

history: []
```

Write metadata when the interview starts, when awaiting user input, and when the interview artifact is completed.

When the interview is completed with a verdict of `Ready for planning` or `Ready for planning with caveats`, the saved metadata should make the next `planner` handoff easy to infer, but the active chat still takes precedence if the user redirects.

## Output format

Use this exact structure:

```markdown
# Interview: <name>

## Objective
...

## Current State
...

## Desired Outcome
...

## Constraints
...

## Assumptions
...

## Open Questions
...

## Success Criteria
...

## Non-Goals
...

## Interview Metrics
- Ambiguity: X/10
- Scope Clarity: X/10
- Dependency Clarity: X/10
- Implementation Readiness: X/10
- Risk Level: X/10
- Requirements Confidence: X/10

## Readiness Verdict
Ready for planning | Ready for planning with caveats | Not ready for planning

## Caveats
Only include this section when the verdict is `Ready for planning with caveats`.
1. ...
2. ...

## Remaining Gaps
- ...
- ...
```

## Rules
- If interview name is missing, suggest one and include that confirmation alongside other current interview questions instead of sending a standalone name-only prompt.
- If the user explicitly provides a different name, adopt it.
- If the user ignores the name prompt while answering other questions, keep the generated suggested name.
- Do not implement anything.
- Do not generate a plan.
- Do not modify existing plan files.
- Do not overwrite an existing interview file silently; if one already exists, ask whether to overwrite it or create a new interview name.
- Keep the interview human-readable and concise.
- Prefer concrete statements over vague summaries.
- Record unresolved uncertainty explicitly instead of pretending clarity exists.
- The goal is a strong planning handoff artifact, not exhaustive documentation.
- Keep `aii/metadata/state.yaml` updated so a future `$resume-last-task` flow can recover the current interview cleanly.
- After completing an interview, expect `planner` to continue from this artifact without re-asking for the name when the same chat clearly requests the next step.
