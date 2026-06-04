---
name: handle-pr-feedback
description: Review and respond to developer comments on a GitHub pull request, implementing valid feedback or explaining rejections, then push and re-request review.
argument-hint: "<pr-number>"
---

# Handle PR Feedback

Reviews and responds to all developer comments on a GitHub pull request, implementing valid feedback or explaining rejections with clear justification, then pushes changes and re-requests review.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- PR number identifying an open pull request with at least one review comment
  - If `$1` is provided, use it directly
  - If `$1` is not provided, resolve the PR number with: `gh pr list --head $(git branch --show-current) --json number --jq '.[0].number'`
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
  Evaluate: actionable or not?
        |
        v
  Present outcome to user for approval
     /         \
 Approved     Rejected
    |             |
    v             v
Implement       Skip
changes
    |
    v
Commit + push
    |
    v
Reply to each comment thread with outcome (ghx)
    |
    v
Re-request review
```

## Steps

1. Fetch all PR review threads:
   ```
   ghx pr threads $1 --ids
   ```
2. For each comment, evaluate whether it is appropriate and actionable.
3. Present the evaluation and proposed action (implement or reject with explanation) to the user for approval.
4. For actionable comments that the user approved: implement the requested changes in the codebase.
5. Commit and push the changes:
   ```
   git add -A && git commit -m "<message>"
   git push
   ```
6. Reply to each comment thread with the outcome using `ghx`. For actionable comments where changes were implemented: reply with a brief summary and a link to the commit (e.g., "Done: added null guard for `user` in abc1234."). For non-actionable comments: reply with the rejection explanation. Use the thread IDs from step 1:
   ```
   ghx pr comment $1 --reply-thread <thread-id> --body "<outcome summary>"
   ```
   Append the **Skill attribution** footer to each reply.
7. Re-request review from the original reviewers:
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
| `ghx pr threads <pr-number> --ids` | List review threads with IDs for replying |
| `ghx pr comment <pr-number> --reply-thread <thread-id> --body "..."` | Reply to a specific review thread |
| `ghx pr comment <pr-number> --body "..."` | Post a top-level reply comment on the PR |
| `git push` | Push committed changes to the remote branch |
| `gh pr edit <pr-number> --add-reviewer <handle>` | Re-request review from a reviewer |
