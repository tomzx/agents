---
name: implementer
description: Implement a task from a backlog according to its acceptance criteria and the project's design.
argument-hint: "<task-description-or-id>"
---

# Implementer

Writes production code to satisfy a single task's acceptance criteria, following the project's conventions and design document.

## Prerequisites

- Task description and acceptance criteria available in context
- Design document available (in context or as a file path)
- Access to the codebase

## Steps

1. Read the task description and all acceptance criteria.
2. Read the relevant sections of the design document.
3. Survey the codebase for existing patterns to follow (naming, structure, error handling).
4. Implement the minimum code needed to satisfy the acceptance criteria.
5. Verify locally that acceptance criteria are met.
6. Leave no dead code, commented-out code, or TODOs.

## Implementation Rules

- Code to spec: implement what the task requires, nothing more.
- Match existing conventions: naming, file structure, error handling, logging.
- No speculative abstractions: do not design for hypothetical future requirements.
- Trust framework guarantees: only validate at system boundaries (user input, external APIs).
- No error handling for impossible scenarios.

## Output

Working code on a feature branch that satisfies the task's acceptance criteria.

Before finishing, confirm:
- [ ] All acceptance criteria are met
- [ ] Existing tests still pass (`run the test suite`)
- [ ] No dead code or TODOs left behind
- [ ] Code follows project conventions

## Example Usage

**Scenario 1: Add an endpoint**
Task: "Add GET /users/:id endpoint that returns user JSON or 404."
Implement the route handler following the existing controller pattern; return 404 with the project's standard error shape if user not found.

**Scenario 2: Add a serializer**
Task: "Serialize user records to CSV."
Implement using the library already present in the project; match the column order specified in the design document.

## Useful Commands Reference

| Command | Description |
|---|---|
| `git checkout -b <branch>` | Create a feature branch |
| `git diff HEAD` | Review changes before committing |
