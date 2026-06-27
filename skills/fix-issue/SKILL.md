---
name: fix-issue
description: Orchestrate a bug fix from issue to PR by delegating to reproduce-issue, create-implementation, and create-pr.
allowed-tools: Bash(gh:*, git:*, gh-cached:*, scripts/get-env:*), Read, Write, Edit, Glob, Grep
argument-hint: "<issue-number> [repository]"
---

# Fix Issue

Orchestrates a bug fix from issue to PR by delegating to specialized skills:

1. **`check-duplicates`** -- search for duplicate issues and existing fix PRs
2. **`reproduce-issue`** -- fetch the issue, create a worktree, reproduce the bug, post results
3. **`create-implementation`** -- write a regression test, implement the fix, verify tests pass
4. **`create-pr`** -- push the branch and open a pull request

If duplicates are found or reproduction fails, the workflow stops at the relevant step.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, target the issue from `$ISSUE_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with write access to the target repository
- A GitHub issue number describing a bug
- Git worktree support (`git worktree` available)
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there

## Workflow

```
/check-duplicates
        |
        v
Duplicates found?
   /          \
 No             Yes
  |              |
  v              v
/reproduce-      Stop
issue            (comment posted)
        |
        v
Reproduced?
   /          \
 Yes            No
  |              |
  v              v
/create-         Stop
implementation   (comment posted)
        |
        v
/create-pr
        |
        v
Done (PR ready for review)
```

## Steps

### 1. Check for duplicates

Invoke `check-duplicates` with the same issue number and repository:

```
/check-duplicates $ISSUE_NUMBER $REPO
```

This skill handles:
- Searching for duplicate issues
- Checking for existing fix PRs
- Checking if the issue is already assigned

If duplicates or existing PRs are found, `check-duplicates` posts a comment and stops.
Do not proceed to step 2.

### 2. Reproduce the issue

Invoke `reproduce-issue` with the same issue number and repository:

```
/reproduce-issue $ISSUE_NUMBER $REPO
```

This skill handles:
- Fetching the issue details
- Creating a git worktree on a fix branch
- Analyzing the codebase
- Attempting reproduction
- Posting reproduction results as a comment on the issue

If the bug cannot be reproduced, `reproduce-issue` posts a comment and stops.
Do not proceed to step 3.

After `reproduce-issue` creates the worktree, `.sdlc/state.yml` is initialized with `current_phase: reproduce`. Update it to `current_phase: implementation` before invoking `create-implementation`, and to `current_phase: pr` before invoking `create-pr`.

### 3. Implement the fix

Invoke `create-implementation` in the worktree directory:

```
/create-implementation
```

Provide context about the bug and reproduction findings.
The implementation must:

1. Write a **regression test** first that demonstrates the bug (it should fail).
2. Run the regression test to confirm it fails.
3. Implement the minimal fix to make the test pass.
4. Run the full test suite to confirm no regressions.
5. Run linting and type checking.
6. Make atomic commits:
   - First commit: `test: add regression test for #<issue-number>`
   - Subsequent commits: `fix: <description> (#<issue-number>)`

If the fix is non-trivial (e.g., requires design changes, schema migrations, multi-component coordination), stop and suggest using the full SDLC pipeline:

```
/sdlc requirements
```

### 4. Create the pull request

Invoke `create-pr` with the issue number and repository:

```
/create-pr $REPO $ISSUE_NUMBER
```

This skill handles pushing the branch and opening a structured PR.

## Failure Modes

| Mode | Response |
|---|---|
| **Cannot reproduce** | `reproduce-issue` handles this; workflow stops |
| **Fix is non-trivial** | Escalate to the full SDLC pipeline at `requirements` |
| **Multiple root causes** | Fix the primary cause, file follow-up issues for secondary causes |
| **Fix breaks other tests** | Resolve before proceeding to `create-pr` |

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md` once the `fix/` PR is opened. If no PR was opened (reproduction failed, blocked, or it escalates to the full pipeline), omit the file.

## Example Usage

**Scenario 1: Reproducible bug**
```
/fix-issue 42 owner/myrepo
```
Reproduces issue #42, implements null check fix with regression test, submits PR.

**Scenario 2: Cannot reproduce**
```
/fix-issue 15
```
`reproduce-issue` cannot trigger the bug, posts a comment asking for details, stops.

**Scenario 3: Complex bug**
```
/fix-issue 88
```
Reproduces issue #88 but fix requires schema migration across 3 services. Stops and suggests `/sdlc requirements`.

## Next Step

After the PR is created, use `/handle-pr-ci` if CI is failing, `/handle-pr-feedback` to address reviewer comments, and `/merge-pr` once CI is green and the PR is approved.
Close the loop with `/create-learnings` after the fix is merged.
