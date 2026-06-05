---
name: create-tasks-decomposition
description: Decompose a feature or plan into discrete, actionable tasks with effort estimates and dependencies.
argument-hint: "[plan or specification]"
---

# Create Tasks Decomposition

Breaks down a feature, plan, or specification into discrete, actionable tasks.
Each task gets its own file under `.sdlc/features/FEAT-NNNN-<slug>/tasks/` with a unique sequence number, frontmatter status, and explicit dependencies.

## Prerequisites

- `.sdlc/features/FEAT-NNNN-<slug>/plan.md` (must have `status: approved`), or an implementation plan/specification provided in context or as a file path (`$1`)
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there to the produced document

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
3. For each task, define: description, acceptance criteria, effort size, and dependencies on other tasks.
4. Order tasks and assign sequence numbers starting at `0001` within this feature.
5. Identify the critical path through the dependency graph.
6. Write one file per task to `.sdlc/features/FEAT-NNNN-<slug>/tasks/NNNN-<slug>.md`, where `NNNN` restarts at `0001` for each feature.

## Output Format (one file per task)

```markdown
---
id: "NNNN"
title: "<Task title>"
status: draft
size: <XS|S|M|L>
depends_on: []    # list of task IDs this task cannot start until complete, e.g. ["0001", "0003"]
completed_date: null
blocker: null
---

# Task NNNN: <Task title>

## Description

<What needs to be done and why.>

## Acceptance Criteria

- [ ] <Testable condition>
- [ ] <Testable condition>

## Notes

<Optional: implementation hints, risks, or constraints specific to this task.>
```

### Task Status Lifecycle

Tasks follow a strict status progression:

```
draft → pending → in-progress → done
                   |                 ↑
                   → blocked ────────┘
                   |                 |
                   → cancelled       |
                                     ↓
                              (restart if needed)
```

| Status | Meaning | Who sets it |
|---|---|---|
| `draft` | Initial state, created by decomposition | `create-tasks-decomposition` |
| `pending` | Reviewed and approved, ready to start | `review-tasks-decomposition` |
| `in-progress` | Actively being worked on | `create-implementation` (or manually) |
| `blocked` | Cannot proceed due to external dependency or issue | `create-implementation` (or manually) |
| `done` | All acceptance criteria met, tests passing | `create-implementation` after checklist passes |
| `cancelled` | No longer needed (superseded or descoped) | Manually |

When setting a task to `done`, also set `completed_date` to the current date (ISO format, e.g. `2025-06-05`).
When setting a task to `blocked`, also set `blocker` to a brief description of what is blocking (e.g. `"Waiting on API access from infra team"`).
When a blocked task resumes, set status back to `in-progress` and clear `blocker` to `null`.

After writing all task files, output a summary to the conversation:

```markdown
## Tasks created: <Feature Name>

| ID | Title | Size | Depends on |
|---|---|---|---|
| 0001 | <title> | S | — |
| 0002 | <title> | M | 0001 |

**Critical path:** 0001 → 0002 → 0005 → 0008

**Total:** N tasks — X person-days estimated
```

## Example Usage

**Scenario 1: API feature**
Plan has three phases.
Tasks: 0001 DB migration `[S]`, 0002 model layer `[S]` (depends 0001), 0003 endpoint A `[M]` (depends 0002), 0004 endpoint B `[M]` (depends 0002), 0005 validation `[S]` (depends 0003, 0004), 0006 tests `[M]` (depends 0005), 0007 docs `[XS]` (depends 0006).
Critical path: 0001 → 0002 → 0003 → 0005 → 0006 → 0007.

**Scenario 2: Oversized task**
A task described as "implement the entire payment module" is XL.
Break into: 0001 payment intent `[M]`, 0002 webhook handler `[M]`, 0003 refund endpoint `[S]`, 0004 idempotency `[S]`, 0005 integration tests `[M]`.

## Next Step

Run `/review-tasks-decomposition` to audit granularity, completeness, and dependencies before moving on.
Once tasks are approved, continue with `/create-tests`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
