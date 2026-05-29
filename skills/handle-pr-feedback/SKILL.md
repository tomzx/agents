---
name: handle-pr-feedback
description: Review and respond to developer comments on a GitHub pull request, implementing valid feedback or explaining rejections, then push and re-request review.
argument-hint: "<pr-number>"
---

# Handle PR Feedback

Reviews and responds to all developer comments on a GitHub pull request, implementing valid feedback or explaining rejections with clear justification, then pushes changes and re-requests review.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- PR number (`$1`) identifying an open pull request with at least one review comment
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there to the produced document

### Skill attribution (GitHub)

Before posting any PR comment with `gh`, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Posted with** footer for `SKILL_DIR` = `handle-pr-feedback`.

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
    |
    v
Push branch + re-request review
```

## Steps

1. Fetch all PR comments:
   ```
   gh-cached pr view $1 --comments --refresh
   ```
2. For each comment, display its content.
3. Evaluate whether the comment is appropriate and actionable.
4. If actionable: implement the requested changes in the codebase.
5. If not actionable: draft a reply explaining why the change will not be made.
6. Present the content, reasoning, and proposed action to the user for approval.
7. On approval: commit code changes or post the reply as a PR comment using `ghx`. When posting a reply, include the **Skill attribution** footer on the comment body (omit the footer if you only push commits and do not post a comment).
8. After all comments are addressed, push the branch:
   ```
   git push
   ```
9. Re-request review from the original reviewers:
   ```
   gh pr edit $1 --add-reviewer <handles>
   ```

## Example Usage

**Scenario 1: Bug fix requested**
```
/handle-pr-feedback 42
```
Comment on line 37: "This function doesn't handle `user` being null."
Decision: Actionable. Add a null guard, commit, push, re-request review.

**Scenario 2: Stylistic disagreement**
```
/handle-pr-feedback 100
```
Comment: "Rename `processBatch` to `run`."
Decision: Not actionable - "run" is less descriptive. Draft reply: "Keeping `processBatch` as it communicates intent better than `run`." Push and re-request review.

**Scenario 3: Multiple mixed comments**
```
/handle-pr-feedback 77
```
Three comments: one requesting a missing test (implement), one asking for a type annotation (implement), one requesting an out-of-scope design change (reject with explanation). Address each independently, present all decisions together, then push and re-request review.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh-cached pr view <pr-number> --comments --refresh` | Fetch PR details and all review comments (fresh) |
| `ghx pr comment <pr-number> --body "..."` | Post a reply comment on the PR |
| `git push` | Push committed changes to the remote branch |
| `gh pr edit <pr-number> --add-reviewer <handle>` | Re-request review from a reviewer |
