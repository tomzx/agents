---
name: create-implementation
description: Implement a feature or task following the specification and plan, producing working, tested code.
argument-hint: "[task or specification]"
---

# Create Implementation

Implements a feature or task following its specification, plan, and task decomposition.
Produces working code that passes tests and meets all acceptance criteria.

## Prerequisites

- A task description, specification, or plan provided in context or as `$1`
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

1. Read the task, specification, and acceptance criteria.
2. Set up a feature branch (see Branching Strategy below).
3. Explore the codebase to understand existing patterns, naming conventions, and architecture.
4. Identify which files need to be created or modified.
5. Implement the changes in small increments, verifying each step with tests.
6. Ensure all acceptance criteria are met.
7. Check for code quality issues (naming, duplication, dead code).
8. Run the full test suite and confirm it passes.

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

## Checklist Before Marking Done

- [ ] Working on a feature branch (not `main`)
- [ ] All acceptance criteria satisfied
- [ ] Tests written and passing
- [ ] No linting or type errors
- [ ] No dead code or commented-out code introduced
- [ ] Existing tests still pass (no regressions)
- [ ] Branch rebased on latest `main`

## Example Usage

**Scenario 1: API endpoint task**
Task T-03: "Implement POST /orders endpoint per spec."
Read spec for request/response schema, find existing endpoint patterns, create route + handler + validation + service layer, write integration test, confirm all test cases pass.

**Scenario 2: Bug fix task**
Task describes a null pointer in the login flow.
Locate the defect, implement the fix, write a regression test that would have caught the bug.

## Useful Commands Reference

Use the tools available in the current session to read files, run tests, and edit code.

| Action | Common commands |
|---|---|
| Run tests | `pytest`, `npm test`, `go test ./...` |
| Type check | `mypy`, `tsc`, `pyright` |
| Lint | `ruff check`, `eslint` |
| Format | `ruff format`, `prettier` |
