---
name: quick-pr-reviews
description: Check all PRs where you are a requested reviewer for new commits and run quick-pr-review on each one that has changed since last reviewed. Optionally filter to specific organizations or repositories (owner/repo).
allowed-tools: Bash(uv:*)
argument-hint: [org1 org2 ... | owner/repo1 owner/repo2 ...]
---

# Quick PR Reviews

Finds all open PRs where you are a requested reviewer, determines which ones need a new review, and runs `/quick-pr-review` on each of them. Accepts an optional list of organizations (e.g. `acme`) or repositories in `owner/repo` format (e.g. `acme/api`) to limit scope.

## Prerequisites

- `GITHUB_TOKEN` env var set with repo read access, or `gh` CLI authenticated (`gh auth login`)
- `uv` available on PATH
- `quick-pr-review` skill available

## Workflow

```
scripts/quick-pr-reviews [args]
              |
    For each PR with needs_review=true
              |
       /quick-pr-review <repo> <pr>
              |
       Report summary table
```

## Steps

### 1. List PRs that need review

```bash
uv run scripts/quick-pr-reviews $@
```

This outputs a JSON array. Each entry has:
- `repo` - "owner/repo"
- `pr` - PR number
- `title` - PR title
- `needs_review` - true if a review run is warranted
- `reason` - one of: `no_prior_review`, `new_commit`, `ci_now_passing`, `no_changes`, `ci_still_failing`, `error`

If the array is empty, report "No open PRs awaiting your review." and stop.

### 2. Run quick-pr-review on each PR that needs review

For each entry where `needs_review == true`, invoke:

```
/quick-pr-review {repo} {pr}
```

Process PRs sequentially to avoid rate limiting.

### 3. Report summary

Output a summary table covering every PR returned by the script:

| Repository | PR | Title | Status |
|---|---|---|---|
| owner/repo | #42 | Add feature X | Reviewed (approved) |
| owner/repo | #88 | Fix bug Y | Reviewed (comment posted) |
| owner/repo | #55 | Refactor Z | Skipped (no changes) |
| owner/repo | #77 | Update deps | Skipped (CI still failing) |

## Example Usage

**Scenario 1: All orgs, some PRs updated**
```
/quick-pr-reviews
```
Finds 5 open PRs. 2 have new commits, 3 unchanged. Runs `/quick-pr-review` on the 2.

**Scenario 2: Filter to specific organizations**
```
/quick-pr-reviews acme widgets-inc
```
Only PRs from those orgs are considered.

**Scenario 3: Filter to specific repositories**
```
/quick-pr-reviews acme/api acme/web-app
```
Only PRs from those repos are considered.

**Scenario 4: No PRs awaiting review**
```
/quick-pr-reviews
```
Script returns empty array. Report "No open PRs awaiting your review."

**Scenario 5: Same commit but CI was failing, now passes**
```
/quick-pr-reviews
```
Script returns `reason: ci_now_passing`. Runs `/quick-pr-review` to update comment and approve.

**Scenario 6: Same commit, CI still failing**
```
/quick-pr-reviews
```
Script returns `reason: ci_still_failing`, `needs_review: false`. Skip and report in table.
