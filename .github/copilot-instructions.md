# Bird Project Collaboration Rules

Apply these rules for work in this repository.

## Status Workflow
- Use these states only: `todo`, `in work`, `done`, `validated`.
- Add a date to each state update using `YYYY-MM-DD`, optionally `HH:MM` when useful.
- Never mark an item as `validated` without explicit user confirmation.

## Delivery Format
- Prefer concise delivery notes.
- When relevant, include: summary, status with date, changed files, tests run, blockers.

## Execution Rules
- Implement directly unless the action is destructive, ambiguous, or unusually long.
- Stay within the requested scope except for direct regressions caused by the change.
- Update documentation when useful, but do not mark roadmap or checklist items as validated without user approval.

## Tests
- Run fast, relevant local tests automatically when practical.
- Ask before running long or expensive test suites.

## Git Safety
- Do not commit unless explicitly asked.
- Do not revert user changes unless explicitly asked.
- Do not use destructive git actions unless explicitly asked.

## Communication
- Ask questions only when there is a real decision blocker.
- Default to concise, concrete answers.
