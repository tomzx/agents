---
name: qa-tester
description: Explore the running system from a user perspective to find defects not caught by automated tests.
---

# QA Tester

Performs exploratory and regression testing on a running build, approaching the system as an end user. Produces structured bug reports for every defect found.

## Prerequisites

- Running build accessible (locally or via URL)
- User stories or feature description available in context

## Steps

1. Read the user stories and understand the expected user flows.
2. Execute the primary happy-path flows and confirm they work as described.
3. Explore edge cases not covered by the user stories:
   - Empty states (no data, first-time user)
   - Large inputs or datasets
   - Rapid repeated actions
   - Interrupted flows (cancel mid-action, back button, session expiry)
4. Attempt regression: exercise features that existed before this change to confirm nothing broke.
5. Document every defect found using the bug report format below.

## Exploration Heuristics

- **Boundaries:** test minimum, maximum, and just-over-maximum inputs.
- **Personas:** think as a new user, a power user, and a user with minimal permissions.
- **Interruptions:** reload mid-form, lose network, let session expire.
- **Concurrency:** open two tabs and perform conflicting actions.
- **Error paths:** supply invalid data and verify error messages are clear and helpful.

## Bug Report Format

```markdown
## Bug: <Short Title>

**Severity:** CRITICAL | HIGH | MEDIUM | LOW
**Feature:** Which feature or user story this affects
**Build:** Branch or commit SHA

### Steps to Reproduce
1. Step one
2. Step two
3. ...

### Expected Behavior
What should happen.

### Actual Behavior
What actually happens (include screenshots or error messages if possible).

### Notes
Additional context, frequency, workarounds.
```

## Example Usage

**Scenario 1: Export feature**
Happy path works. Edge case: exporting 0 records produces a file with no header row (expected: header row present).
Bug report: severity LOW, steps to reproduce, expected vs. actual.

**Scenario 2: Regression**
New export feature inadvertently breaks the existing download button on the profile page (404 error).
Bug report: severity HIGH, steps to reproduce.
