---
name: task-tracking
description: Plan and track feature implementation as a live checklist. Creates a TodoWrite task list before starting work, marks each task complete as it finishes, and verifies every task is checked at the end.
---

# Task Tracking

Plans a feature implementation as an explicit checklist, keeps it updated during work, and confirms full completion at the end.

## Prerequisites

- A clear feature request or task description from the user
- TodoWrite tool available

## Steps

### 1. Decompose the feature

Before writing any code or running any commands, analyze the request and break it into concrete, ordered tasks. Each task should be:

- A single action (read, write, run, verify, etc.)
- Completable in one focused step
- Specific enough that "done" is unambiguous

### 2. Write the initial checklist

Call TodoWrite with all tasks set to status `pending` before starting any work. Use descriptive content strings so the list is readable without context.

Example tasks for a typical feature:
- Explore codebase to understand existing patterns
- Identify files that need to change
- Implement core logic
- Add/update tests
- Run tests and confirm they pass
- Run linter/formatter and fix any issues
- Commit changes

Add, remove, or reorder tasks to fit the actual feature. Do not use a generic template, tailor the list to what the work actually requires.

### 3. Execute and update

Work through the checklist in order:

1. Start the next `pending` task
2. Do the work
3. Immediately mark that task `completed` via TodoWrite before moving to the next
4. If you discover mid-task that an additional step is needed, add it to the list before continuing

Never batch-complete multiple tasks at once. Mark each one complete the moment it finishes.

### 4. Handle blockers

If a task cannot be completed (missing information, unexpected state, external dependency), mark it `in_progress` and surface the blocker to the user. Do not silently skip tasks or mark them complete without finishing them.

### 5. Final verification

After all tasks appear complete, call TodoWrite (or review the current list) to confirm every task has status `completed`. If any remain `pending` or `in_progress`, resolve them before declaring the feature done.

Report to the user: "All N tasks completed." or list any that remain open.

## Example

Feature request: "Add a --verbose flag to the CLI"

Initial checklist:
- [ ] Read existing CLI argument parsing code
- [ ] Identify where logging is configured
- [ ] Add --verbose argument definition
- [ ] Wire verbose flag to logging level
- [ ] Update help text / docstring
- [ ] Add test for --verbose flag behavior
- [ ] Run tests
- [ ] Run linter
- [ ] Commit

As work proceeds each item flips to checked. The feature is done when the list is entirely checked.
