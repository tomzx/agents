---
name: prepare-issue
description: Analyze a GitHub issue and create a detailed implementation plan, requesting more information if needed.
argument-hint: "<issue-url>"
---

BASE_DIR=!`scripts/get-env ISSUES_DIR`

# Prepare Issue Implementation Plan

Fetches a GitHub issue, clones the relevant codebase, and produces a detailed implementation plan. If the issue lacks sufficient information, requests clarification via a comment before planning.

## Prerequisites

- `gh` CLI authenticated with access to the repository
- `ISSUES_DIR` environment variable set (resolved via `scripts/get-env ISSUES_DIR`)
- Write access to the issue (for posting clarification comments)
- `scripts/get-env` utility available

### Skill attribution (GitHub)

Before posting any clarification comment with `gh`, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Posted with** footer for `SKILL_DIR` = `prepare-issue`.

## Workflow

```
Fetch issue + comments ($1)
            |
            v
     Clone repository
     (trunk branch)
            |
            v
   Is information sufficient?
         /          \
       Yes            No
        |              |
        v              v
  Write plan      Post clarification
  to file         comment via gh
                  then wait
```

## Steps

1. Fetch issue details and comments:
   ```
   gh issue view $1 --comments
   ```
   Write raw output to `{BASE_DIR}/{REPOSITORY}/{ISSUE_NUMBER}/issue.md`.

2. Clone the repository at the trunk branch:
   ```
   gh repo clone <owner>/<repo> src/<owner>/<repo>
   cd src/<owner>/<repo> && git checkout main
   ```

3. Given the codebase, issue description, and comments, assess whether there is enough information to implement.
   - If not: post a comment requesting specifics (body includes **Skill attribution** footer):
     ```
     gh issue comment $1 --body "..."
     ```
   - If yes: proceed to write the plan.

4. Write the plan to `{BASE_DIR}/{REPOSITORY}/{ISSUE_NUMBER}/prepare-issue.md`:

```markdown
---
created_at: <ISO 8601 timestamp>
issue: $1
---

# Summary

# Expectations and Assumptions

# Current State

# Related Issues

# Information Sufficiency Assessment

# Open Questions

# Implementation Plan
```

## Example Usage

**Scenario 1: Well-defined feature issue**
```
/prepare-issue https://github.com/owner/repo/issues/42
```
Issue has clear requirements. Clone repo, analyze codebase, produce a full implementation plan with file-level steps.

**Scenario 2: Vague bug report**
```
/prepare-issue https://github.com/owner/repo/issues/77
```
Issue says "login is broken" with no reproduction steps. Post comment: "Could you provide steps to reproduce, the expected behavior, and what you observe instead?"

**Scenario 3: Issue with related dependencies**
```
/prepare-issue https://github.com/owner/repo/issues/100
```
Issue references two related issues. Include them in the "Related Issues" section and note how they affect the implementation plan.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh issue view <issue-url> --comments` | Fetch issue and all comments |
| `gh repo clone <owner>/<repo> <directory>` | Clone repository into a local directory |
| `gh issue comment <issue-url> --body "..."` | Post a clarification comment on the issue |
| `scripts/get-env ISSUES_DIR` | Resolve the issues directory path |
| `git checkout main` | Check out the trunk branch |
