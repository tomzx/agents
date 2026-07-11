---
name: create-tasks-decomposition
description: Decompose a feature or plan into discrete, actionable tasks with effort estimates and dependencies.
argument-hint: "[plan or specification]"
---

# Create Tasks Decomposition

Breaks down a feature, plan, or specification into discrete, actionable tasks.
Each task gets its own file under `.sdlc/features/N-<slug>/tasks/` with a unique sequence number, frontmatter status, and explicit dependencies.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/plan.md` (must have passed review with findings verdict `approved`), or an implementation plan/specification provided in context or as a file path (`$1`)

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
4. Order tasks and assign sequence numbers starting at `1` within this feature.
5. Identify the critical path through the dependency graph.
6. Write one file per task to `.sdlc/features/N-<slug>/tasks/N-<slug>.md`, where `N` restarts at `1` for each feature.

## Output Format (one file per task)

Use the template at `skills/sdlc/templates/features/task.md` (copied to `.sdlc/templates/features/task.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write one file per task to `.sdlc/features/N-<slug>/tasks/<id>-<slug>.md`.

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

When setting a task to `done`, also set `completed_date` to the current date (ISO format, e.g. `2025-6-5`).
When setting a task to `blocked`, also set `blocker` to a brief description of what is blocking (e.g. `"Waiting on API access from infra team"`).
When a blocked task resumes, set status back to `in-progress` and clear `blocker` to `null`.

After writing all task files, output a summary to the conversation:

```markdown
## Tasks created: <Feature Name>

| ID | Title | Size | Depends on |
|---|---|---|---|
| 1 | <title> | S | — |
| 2 | <title> | M | 1 |

**Critical path:** 1 → 2 → 5 → 8

**Total:** N tasks — X person-days estimated
```

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md`, If the decomposition could not be produced, omit the file.

## Example Usage

**Scenario 1: API feature**
Plan has three phases.
Tasks: 1 DB migration `[S]`, 2 model layer `[S]` (depends 1), 3 endpoint A `[M]` (depends 2), 4 endpoint B `[M]` (depends 2), 5 validation `[S]` (depends 3, 4), 6 tests `[M]` (depends 5), 7 docs `[XS]` (depends 6).
Critical path: 1 → 2 → 3 → 5 → 6 → 7.

**Scenario 2: Oversized task**
A task described as "implement the entire payment module" is XL.
Break into: 1 payment intent `[M]`, 2 webhook handler `[M]`, 3 refund endpoint `[S]`, 4 idempotency `[S]`, 5 integration tests `[M]`.

## Next Step

Run `/review-tasks-decomposition` to audit granularity, completeness, and dependencies before moving on.
Once tasks are approved, continue with `/create-tests`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
