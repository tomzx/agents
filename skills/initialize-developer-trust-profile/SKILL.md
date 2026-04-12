---
name: initialize-developer-trust-profile
description: Bootstrap a developer trust profile by scanning the last N merged PRs they authored in a repository, delegating to developer-trust-profile for each one.
allowed-tools: Bash(gh:*)
argument-hint: <github_username> <owner/repo> [count]
---

# Initialize Developer Trust Profile

Bootstraps a developer trust profile by processing the last N merged PRs authored by a developer, delegating each one to `/developer-trust-profile`. The profile accumulates incrementally across all PRs, producing a well-grounded initial state.

## Prerequisites

- `gh` CLI authenticated with read access to the target repository
- `$1`: GitHub username of the developer
- `$2`: repository in `owner/repo` format
- `$3` (optional): number of PRs to scan (default: 10)

## Workflow

```
Resolve arguments
      |
Fetch last N merged PRs by author
(fallback to closed if none found)
      |
Any PRs found?
  /         \
No            Yes
 |             |
Stop       For each PR (oldest first):
           /developer-trust-profile
           {username} --after-review
           {repo} {pr_number} approved
              |
           Report summary
```

## Steps

### 1. Resolve arguments

- `GITHUB_USERNAME`: `$1`
- `REPO`: `$2` (`owner/repo`)
- `COUNT`: `$3` if provided, otherwise `10`

### 2. Fetch merged PRs by the author

```bash
gh pr list --repo {REPO} \
  --author {GITHUB_USERNAME} \
  --state merged \
  --limit {COUNT} \
  --json number,mergedAt \
  --jq 'sort_by(.mergedAt) | .[].number'
```

If the result is empty, fall back to closed PRs:

```bash
gh pr list --repo {REPO} \
  --author {GITHUB_USERNAME} \
  --state closed \
  --limit {COUNT} \
  --json number,closedAt \
  --jq 'sort_by(.closedAt) | .[].number'
```

If still no PRs are found, report to the user and stop. Do not create a profile.

### 3. Process each PR

For each PR number (oldest first), invoke:

```
/developer-trust-profile {GITHUB_USERNAME} --after-review {REPO} {PR_NUMBER} approved
```

This handles fetching the diff, synthesizing observations, updating the trust level, writing the profile, and committing — once per PR.

### 4. Report summary

After all PRs are processed, report:
- Number of PRs processed
- The final trust level and reason (read from the written profile)
- The profile path

## Example Usage

**Scenario 1: Initialize with default count**
```
/initialize-developer-trust-profile alice owner/myrepo
```
Fetches last 10 merged PRs by alice (oldest first), calls `/developer-trust-profile` for each, leaving a fully populated profile at `~/.developer-trust/alice.md`.

**Scenario 2: Initialize with custom count**
```
/initialize-developer-trust-profile bob owner/myrepo 25
```
Processes 25 PRs, producing a more grounded initial profile.

**Scenario 3: Developer with no merged PRs**
```
/initialize-developer-trust-profile carol owner/myrepo
```
No merged or closed PRs found. Reports the absence and stops without writing a file.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh pr list --repo <owner/repo> --author <user> --state merged --limit N --json number,mergedAt --jq 'sort_by(.mergedAt) | .[].number'` | Fetch last N merged PR numbers by author, oldest first |
| `gh pr list --repo <owner/repo> --author <user> --state closed --limit N --json number,closedAt --jq 'sort_by(.closedAt) | .[].number'` | Fallback: fetch closed PR numbers |
