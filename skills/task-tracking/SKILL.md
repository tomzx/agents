---
name: task-tracking
description: Plan and track feature implementation as a live checklist. Writes a TASKS.md file before starting work, updates it as each task completes, and verifies every task is checked at the end.
---

# Task Tracking

Plans a feature implementation as an explicit checklist in a `TASKS.md` file, keeps it updated during work, and confirms full completion at the end.

## Prerequisites

- A clear feature request or task description from the user

## Steps

### 1. Decompose the feature

Before writing any code or running any commands, analyze the request and break it into concrete, ordered tasks. Each task should be:

- A single action (read, write, run, verify, etc.)
- Completable in one focused step
- Specific enough that "done" is unambiguous

### 2. Write the initial checklist

Create `TASKS.md` in the repository root with all tasks unchecked before starting any work:

```markdown
# Tasks

- [ ] Task one
- [ ] Task two
- [ ] Task three
```

Example tasks for a typical feature:
- Explore codebase to understand existing patterns
- Identify files that need to change
- Implement core logic
- Add/update tests
- Run tests and confirm they pass
- Run linter/formatter and fix any issues
- Commit changes

Tailor the list to what the work actually requires. Do not use a generic template.

### 3. Execute and update

Work through the checklist in order:

1. Start the next unchecked task
2. Do the work
3. Immediately edit `TASKS.md` to mark that task checked (`- [x]`) before moving on
4. If a new step is discovered mid-task, append it to `TASKS.md` before continuing

Never batch-complete multiple tasks at once. Check each one the moment it finishes.

### 4. Handle blockers

If a task cannot be completed (missing information, unexpected state, external dependency), add a note inline in `TASKS.md` and surface the blocker to the user. Do not silently skip tasks or mark them complete without finishing them.

### 5. Final verification

After all tasks appear complete, read `TASKS.md` and confirm every item is `[x]`. If any remain `[ ]`, resolve them before declaring the feature done.

Report to the user: "All N tasks completed." or list any that remain open.

## Example

Feature request: "Add a --verbose flag to the CLI"

Initial `TASKS.md`:
```markdown
# Tasks

- [ ] Read existing CLI argument parsing code
- [ ] Identify where logging is configured
- [ ] Add --verbose argument definition
- [ ] Wire verbose flag to logging level
- [ ] Update help text / docstring
- [ ] Add test for --verbose flag behavior
- [ ] Run tests
- [ ] Run linter
- [ ] Commit
```

Final `TASKS.md` when done:
```markdown
# Tasks

- [x] Read existing CLI argument parsing code
- [x] Identify where logging is configured
- [x] Add --verbose argument definition
- [x] Wire verbose flag to logging level
- [x] Update help text / docstring
- [x] Add test for --verbose flag behavior
- [x] Run tests
- [x] Run linter
- [x] Commit
```
