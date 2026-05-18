---
name: create-tasks-decomposition
description: Decompose a feature or plan into discrete, actionable tasks with effort estimates and dependencies.
argument-hint: "[plan or specification]"
---

# Create Tasks Decomposition

Breaks down a feature, plan, or specification into discrete, actionable tasks that can be assigned and tracked individually.
Each task has a clear scope, effort estimate, acceptance criteria, and dependency links.

## Prerequisites

- `.sdlc/features/<feature>/plan.md` (must have `status: approved`), or an implementation plan/specification provided in context or as a file path (`$1`)

## Task Sizing Guidelines

| Size | Effort | Description |
|---|---|---|
| XS | < 2h | Configuration change, single-file edit |
| S | 0.5d | Small feature, single component |
| M | 1d | Moderate feature, 2–5 files |
| L | 2d | Complex feature, multiple components |
| XL | > 2d | Must be broken down further |

Tasks estimated XL must be decomposed into smaller tasks before being considered actionable.

## Steps

1. Read the plan or specification.
2. Identify all units of work, targeting tasks completable in 0.5–2 days each.
3. For each task, define: description, acceptance criteria, effort, and dependencies.
4. Group tasks by phase or component.
5. Identify the critical path.
6. Write the output to `.sdlc/features/<feature>/tasks.md`.

## Output Format

```markdown
---
issue: "#<N>"
title: "<Feature Name>"
status: draft
---

# Tasks: <Feature Name>

## Phase 1: <Name>

- [ ] **T-01** <Task title> `[S]`
  - **Description:** <What needs to be done.>
  - **Acceptance:** <How to know it's done.>
  - **Depends on:** None

- [ ] **T-02** <Task title> `[M]`
  - **Description:** <What needs to be done.>
  - **Acceptance:** <How to know it's done.>
  - **Depends on:** T-01

## Phase 2: <Name>

...

## Critical Path

T-01 → T-03 → T-07 → T-12

## Summary

| Total Tasks | XS | S | M | L | Estimated Total |
|---|---|---|---|---|---|
| N | n | n | n | n | X person-days |
```

## Example Usage

**Scenario 1: API feature**
Plan has three phases.
Decompose into: DB migration task, model layer task, two endpoint tasks, validation task, test task, and docs task.
Identify DB migration as the critical-path root.

**Scenario 2: Oversized task**
A task described as "implement the entire payment module" is XL.
Break into: payment intent creation, webhook handler, refund endpoint, idempotency key support, and integration tests.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
