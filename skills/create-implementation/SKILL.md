---
name: create-implementation
description: Implement a feature or task following the specification and plan, producing working, tested code.
argument-hint: "[task or specification]"
---

# Create Implementation

Implements a feature or task following its specification, plan, and task decomposition.
Produces working code that passes tests and meets all acceptance criteria.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- A task description, specification, or plan provided in context or as `$1`
- `.sdlc/features/FEAT-NNNN-<slug>/telemetry.md` (optional, if a telemetry plan was produced): implement analytics events and telemetry alongside feature code
- `.sdlc/features/FEAT-NNNN-<slug>/observability.md` (optional, if an observability plan was produced): implement logging, metrics, tracing, and health checks alongside feature code
- Access to the codebase for reading and editing
- Test suite available (or created alongside the implementation)

## Workflow

```
Read spec / task
        |
        v
Create or reuse feature branch
        |
        v
Understand codebase context
(patterns, conventions, architecture)
        |
        v
Implement in small, verifiable steps
        |
        v
Run tests after each step
        |
        v
All acceptance criteria met?
     /         \
   Yes           No
    |             |
    v             v
  Done          Fix gaps
```

## Steps

1. Read the task, specification, acceptance criteria, telemetry plan, and observability plan (if present).
2. Set the task frontmatter `status: in-progress` in the corresponding `.sdlc/features/FEAT-NNNN-<slug>/tasks/NNNN-<slug>.md` file.
3. Update the Task Progress table in `progress.md` to reflect the in-progress status.
4. Set up a feature branch (see Branching Strategy below).
5. Explore the codebase to understand existing patterns, naming conventions, and architecture.
6. Identify which files need to be created or modified.
7. Implement the changes in small increments, verifying each step with tests.
8. If a telemetry plan exists, implement analytics events and telemetry as part of each relevant code change.
9. If an observability plan exists, implement logging, metrics, tracing, and health checks as part of each relevant code change.
9. Ensure all acceptance criteria are met.
10. Check for code quality issues (naming, duplication, dead code).
11. Run the full test suite and confirm it passes.

## Branching Strategy

The implementation must happen on a dedicated branch, never directly on `main`.

### Branch creation

1. Start from an up-to-date `main`:
   ```
   git checkout main
   git pull
   ```
2. Create a feature branch using the convention `feat/<issue-number>-<short-description>`:
   ```
   git checkout -b feat/42-add-order-endpoint
   ```
   If a plan branch already exists (e.g., `plan/42` from `publish-plan`), create the feature branch from `main`, not from the plan branch. The plan PR is for review only and will be closed separately.

### Commit discipline

- Make small, atomic commits with descriptive messages.
- Reference the issue number in at least the first commit (e.g., `feat: add POST /orders endpoint (#42)`).
- Rebase on `main` before pushing if the branch has been alive for a while:
   ```
   git fetch origin
   git rebase origin/main
   ```

### If a branch already exists

If you are resuming work on an existing feature branch, check it out and ensure it is up to date:
```
git checkout feat/42-add-order-endpoint
git pull
git rebase origin/main
```

## Implementation Guidelines

- Follow the existing code style and naming conventions in the codebase.
- Write the minimum code needed to meet the acceptance criteria — no speculative features.
- Add comments only where the WHY is non-obvious.
- Handle error cases at system boundaries; trust internal code and framework guarantees.
- Do not introduce new dependencies unless specified in the plan.
- Ensure new code is covered by the tests defined in the test plan.
- Design public contracts and persisted data for evolution: tolerate unknown fields, handle unknown enum values gracefully, and prefer additive changes so future versions stay forward compatible.

## Checklist Before Marking Done

- [ ] Working on a feature branch (not `main`)
- [ ] All acceptance criteria satisfied
- [ ] Analytics events implemented per telemetry plan (if present)
- [ ] Logging, metrics, tracing, and health checks implemented per observability plan (if present)
- [ ] Tests written and passing
- [ ] No linting or type errors
- [ ] No dead code or commented-out code introduced
- [ ] Public contracts and persisted data tolerate future additions (forward compatible)
- [ ] Existing tests still pass (no regressions)
- [ ] Branch rebased on latest `main`
- [ ] Task frontmatter updated: `status: done`, `completed_date: <today>`
- [ ] `progress.md` Task Progress table updated

## Handling Blockers

If a task cannot be completed due to an external dependency, missing information, or infrastructure issue:

1. Set the task frontmatter `status: blocked` and fill in `blocker` with a brief description.
2. Update the Task Progress table in `progress.md` and the Current Blocker section.
3. Record the blocker as an assumption via `/create-assumption` if it carries meaningful risk.
4. Move to the next task if it has no dependency on the blocked task.
5. If all remaining tasks depend on the blocked task, stop and write a session end marker to `progress.md`.

When a blocker is resolved:
1. Set the task frontmatter `status: in-progress` and `blocker: null`.
2. Update `progress.md` accordingly.
3. Continue implementation.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md` once the implementation `impl/` PR is opened. If no PR was opened (e.g. blocked), omit the file.

## Example Usage

**Scenario 1: API endpoint task**
Task T-03: "Implement POST /orders endpoint per spec."
Read spec for request/response schema, find existing endpoint patterns, create route + handler + validation + service layer, write integration test, confirm all test cases pass.

**Scenario 2: Bug fix task**
Task describes a null pointer in the login flow.
Locate the defect, implement the fix, write a regression test that would have caught the bug.

## Next Step

Run `/review-implementation` to audit correctness, quality, security, and spec alignment before moving on.
Once findings are resolved, continue with `/create-documentation` then `/create-pr`.

## Useful Commands Reference

Use the tools available in the current session to read files, run tests, and edit code.

| Action | Common commands |
|---|---|
| Run tests | `pytest`, `npm test`, `go test ./...` |
| Type check | `mypy`, `tsc`, `pyright` |
| Lint | `ruff check`, `eslint` |
| Format | `ruff format`, `prettier` |
