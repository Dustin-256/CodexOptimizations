# aii

`aii` is the working area for structured AI execution in this repository.

## Why this is useful

It keeps planning and execution artifacts in one predictable place so work can be resumed cleanly across sessions and collaborators.

## What it can do

- provide a home for reusable skill definitions in `skills/`
- preserve requirements in `interviews/`
- track execution plans in `plans/`
- persist resumable task state in `metadata/`

## Layout
- `skills/`: opt-in skills such as `deep-interview`, `planner`, `plan-executor`, `plan-modifier`, and `resume-last-task`
- `interviews/`: saved markdown requirement handoff documents
- `plans/`: machine-readable YAML execution plans
- `metadata/`: shared resumable task state for workflows such as `$resume-last-task`

## Skill roles

- `deep-interview`: captures requirements, constraints, assumptions, and ambiguity into a structured interview artifact.
- `planner`: turns the interview artifact into an executable YAML plan under `aii/plans/`.
- `plan-executor`: executes or resumes a plan step-by-step while persisting progress and blockers.
- `plan-modifier`: updates an existing plan in place when scope changes or blockers require plan revisions.
- `resume-last-task`: restores the most recent resumable task context from `aii/metadata/` and continues work.

Typical flow: interview -> plan -> execute -> modify (if needed) -> resume later.

## How to use it

1. Bootstrap the repo with `python3 bootstrap.py`.
2. Run a requirements interview and save it in `interviews/`.
3. Generate an execution plan into `plans/`.
4. Execute or modify the plan while persisting progress in `metadata/`.
5. Resume later using the saved state instead of starting over.

Use `python bootstrap.py` to recreate the baseline scaffold if needed.
