---
name: user-code-familiarity
description: Build a profile of users' familiarity with a codebase based on their GitHub contributions, including areas contributed to, issue types resolved, and technologies used.
argument-hint: "<username> [organization]"
---

BASE_DIR=!`scripts/get-env NOTES_DIR`

# Profile User Code Familiarity

Builds per-user familiarity profiles by analyzing GitHub contributions - commits, PRs, and issues - within a codebase or organization, capturing the areas, issue types, and technologies each person has worked with.

## Prerequisites

- `gh` CLI authenticated with access to the target repositories
- `NOTES_DIR` environment variable set (resolved via `scripts/get-env NOTES_DIR`)
- Username(s) (`{USERS}`) and optional organization (`{ORGANIZATIONS}`) provided as arguments

## Steps

1. Resolve the notes directory:
   ```
   scripts/get-env NOTES_DIR
   ```
2. For each user in `{USERS}` within `{ORGANIZATIONS}`, retrieve contributions:
   ```
   gh search commits --author=<username> --owner=<org> --limit 100
   gh search prs --author=<username> --owner=<org> --limit 100
   gh search issues --assignee=<username> --owner=<org> --limit 100
   ```
3. Analyze contributions to identify:
   - Areas of the codebase (directories, modules) they have contributed to
   - Types of issues resolved (bug, feature, chore)
   - Technologies and languages used in the context of this codebase
4. Include the time period covered by the data.
5. Write each profile to `{BASE_DIR}/users/{USERNAME}/codebase-familiarity.md`.

## Example Usage

**Scenario 1: Single user profile**
```
/user-code-familiarity alice
```
Fetches alice's commits and PRs, finds she primarily contributes to `src/auth/` and `src/payments/`, resolves mostly `bug` and `security` issues, works in Python and SQL. Writes to `{NOTES_DIR}/users/alice/codebase-familiarity.md`.

**Scenario 2: User within a specific organization**
```
/user-code-familiarity bob MyOrg
```
Scopes the search to the MyOrg GitHub organization. Profiles bob's contributions across all repos in that org.

**Scenario 3: Multiple users**
```
/user-code-familiarity alice bob carol
```
Generates separate profile files for each user, ideally processed in parallel.

## Useful Commands Reference

| Command | Description |
|---|---|
| `scripts/get-env NOTES_DIR` | Resolve the notes directory path |
| `gh search commits --author=<user> --owner=<org> --limit 100` | Fetch commits by a user in an org |
| `gh search prs --author=<user> --owner=<org> --limit 100` | Fetch PRs authored by a user in an org |
| `gh search issues --assignee=<user> --owner=<org> --limit 100` | Fetch issues assigned to a user in an org |
