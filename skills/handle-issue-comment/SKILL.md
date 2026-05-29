---
name: handle-issue-comment
description: Reply to a comment on a GitHub issue using the codebase, issue description, and comment history as context.
argument-hint: "<issue-url>"
---

# Handle Issue Comment

Replies to a comment on a GitHub issue with a relevant, context-aware response drawn from the codebase, issue description, and prior discussion.

## Prerequisites

- `gh` CLI authenticated with access to the target repository
- Issue URL (`$1`) pointing to an existing GitHub issue

### Skill attribution (GitHub)

Before posting any issue comment with `gh`, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Posted with** footer for `SKILL_DIR` = `handle-issue-comment`.

## Steps

1. Fetch the issue and all its comments:
   ```
   gh-cached issue view $1 --comments --refresh
   ```
2. Clone the repository to gather codebase context:
   ```
   gh repo clone <owner>/<repo>
   ```
3. Review the full comment thread to understand the discussion.
4. Draft a reply that directly addresses the latest comment, grounded in codebase evidence and prior discussion.
5. Post the reply (body = main reply plus **Skill attribution** footer):
   ```
   ghx issue comment $1 --body "..."
   ```

## Example Usage

**Scenario 1: Answering a technical question**
```
/handle-issue-comment https://github.com/owner/repo/issues/20
```
Comment: "Where is the retry logic implemented?"
Action: Look up the codebase, find `src/retry.py`, post a reply pointing to the relevant file and lines.

**Scenario 2: Confirming a bug is reproducible**
```
/handle-issue-comment https://github.com/owner/repo/issues/45
```
Comment: "I can reproduce this on v2.3 but not v2.2."
Action: Review the changelog and relevant code between those versions, post a reply with findings.

**Scenario 3: Clarifying scope**
```
/handle-issue-comment https://github.com/owner/repo/issues/77
```
Comment: "Should this also fix the related problem in the admin panel?"
Action: Review the issue's acceptance criteria, reply stating whether the admin panel is in scope.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh-cached issue view <issue-url> --comments --refresh` | Fetch issue details and all comments (fresh) |
| `gh repo clone <owner>/<repo>` | Clone repository for codebase context |
| `ghx issue comment <issue-url> --body "..."` | Post a reply comment on the issue |
