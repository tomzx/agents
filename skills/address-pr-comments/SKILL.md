---
name: address-pr-comments
description: Pull and address review comments on a GitHub pull request, implementing appropriate changes or explaining why a change won't be made.
argument-hint: <pr-number>
---

# Address PR Review Comments

Reviews and responds to all comments on a GitHub pull request, implementing valid feedback or explaining rejections with clear justification.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- PR number (`$1`) identifying an open pull request with at least one review comment

## Workflow

```
Fetch PR comments ($1)
        |
        v
  For each comment
        |
        v
  Is it actionable?
     /         \
   Yes           No
    |             |
    v             v
Implement     Draft rejection
changes       explanation
    |             |
    +------+------+
           |
           v
  Present to user for approval
     /         \
 Approved     Rejected
    |             |
    v             v
Commit/post     Skip
```

## Steps

1. Fetch all PR comments:
   ```
   gh pr view $1 --comments
   ```
2. For each comment, display its content.
3. Evaluate whether the comment is appropriate and actionable.
4. If actionable: implement the requested changes in the codebase.
5. If not actionable: draft a reply explaining why the change will not be made.
6. Present the content, reasoning, and proposed action to the user for approval.
7. On approval: commit code changes or post the reply as a PR comment.

## Example Usage

**Scenario 1: Bug fix requested**
```
/address-pr-comments 42
```
Comment on line 37: "This function doesn't handle `user` being null."
Decision: Actionable. Add a null guard, commit, present for approval.

**Scenario 2: Stylistic disagreement**
```
/address-pr-comments 100
```
Comment: "Rename `processBatch` to `run`."
Decision: Not actionable - "run" is less descriptive. Draft reply: "Keeping `processBatch` as it communicates intent better than `run`."

**Scenario 3: Multiple mixed comments**
```
/address-pr-comments 77
```
Three comments: one requesting a missing test (implement), one asking for a type annotation (implement), one requesting an out-of-scope design change (reject with explanation). Address each independently, then present all decisions together.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh pr view <pr-number> --comments` | Fetch PR details and all review comments |
| `gh pr comment <pr-number> --body "..."` | Post a reply comment on the PR |
