---
name: handle-pr-comment
description: Reply to a comment on a GitHub pull request, implementing changes if appropriate, using the codebase and comment history as context.
argument-hint: "<pr-url>"
---

# Handle PR Comment

Evaluates a comment on a GitHub pull request and responds appropriately - either implementing the requested change and pushing it, or posting a reply explaining why the change will not be made.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- PR URL (`$1`) pointing to an open pull request
- Git push access to the PR branch

### Skill attribution (GitHub)

Before posting any PR comment with `gh`, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Posted with** footer for `SKILL_DIR` = `handle-pr-comment`.

## Workflow

```
Fetch PR metadata + comment history
            |
            v
      Clone repository
            |
            v
   Is the comment actionable?
         /          \
       Yes            No
        |              |
        v              v
  Implement       Draft rejection
  changes         explanation
        |              |
        +------+--------+
               |
               v
     Present to user for approval
         /          \
     Approved      Rejected
        |              |
        v              v
  Commit + push      Skip
  (or post reply)
```

## Steps

1. Fetch PR details and full comment history:
   ```
   gh pr view $1 --comments
   ```
2. Clone the repository locally:
   ```
   gh repo clone <owner>/<repo>
   ```
3. Display the target comment's content.
4. Evaluate whether the feedback is appropriate and actionable.
5. If actionable: implement the changes in the codebase.
6. If not actionable: draft a reply explaining the rejection.
7. Present reasoning to the user for approval.
8. On approval:
   - For code changes: commit and push to the PR branch.
   - For rejections: post the reply comment via `gh` with the **Skill attribution** footer on the comment body.

## Example Usage

**Scenario 1: Valid refactor request**
```
/handle-pr-comment https://github.com/owner/repo/pull/55
```
Comment: "Extract this logic into a helper function."
Action: Implement refactor, commit to PR branch, push.

**Scenario 2: Out-of-scope request**
```
/handle-pr-comment https://github.com/owner/repo/pull/88
```
Comment: "Can you also fix the unrelated bug in `utils.py`?"
Action: Post reply: "That's out of scope for this PR. I'll open a separate issue."

**Scenario 3: Incorrect suggestion**
```
/handle-pr-comment https://github.com/owner/repo/pull/33
```
Comment: "Use a `global` variable here instead of passing it as a parameter."
Action: Draft rejection with technical reasoning; present to user before posting.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh pr view <pr-url> --comments` | Fetch PR details and all comments |
| `gh repo clone <owner>/<repo>` | Clone the repository locally |
| `gh pr comment <pr-number> --body "..."` | Post a reply to the PR |
| `git commit -m "..."` | Commit code changes |
| `git push` | Push changes to the PR branch |
