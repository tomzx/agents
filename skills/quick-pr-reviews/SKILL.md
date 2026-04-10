---
name: quick-pr-reviews
description: Check all PRs where you are a requested reviewer for new commits and run quick-pr-review on each one that has changed since last reviewed. Optionally filter to specific organizations.
allowed-tools: Bash(gh:*)
argument-hint: [org1 org2 ...]
---

# Quick PR Reviews

Finds all open PRs where you are a requested reviewer, checks each one for new commits since the last quick-pr-review comment, and runs `/quick-pr-review` on those that have changed. Accepts an optional list of organizations to limit the scope.

## Prerequisites

- `gh` CLI authenticated
- `quick-pr-review` skill available

## Workflow

```
Fetch open PRs with review requested
              |
     Filter by org(s) if provided
              |
              v
  For each PR, check existing
  <!-- quick-pr-review --> comment
              |
       Commit changed?
        /          \
      No             Yes
      |               |
    Skip         /quick-pr-review
                  <owner/repo> <pr>
```

## Steps

### 1. Fetch PRs awaiting your review

```bash
gh search prs --review-requested @me --state open \
  --json number,repository,title,headRefOid \
  --limit 100
```

This returns a list of PRs. For each entry extract:
- `REPO`: `repository.nameWithOwner`
- `PR`: `number`
- `HEAD_COMMIT`: `headRefOid`
- `ORG`: the owner portion of `repository.nameWithOwner` (everything before `/`)

### 2. Filter by organization (if arguments provided)

If one or more organizations are provided as `$@`, discard any PR whose `ORG` does not appear in the list.

If no arguments are provided, process all PRs returned in step 1.

### 3. For each PR, check for an existing review comment

```bash
gh api repos/{REPO}/issues/{PR}/comments \
  --jq '[.[] | select(.body | test("<!-- quick-pr-review -->"))] | last | {id: .id, body: .body}'
```

Extract `COMMENT_COMMIT` from the marker line `<!-- quick-pr-review:COMMIT_SHA -->` in the comment body, if present.

- If `COMMENT_COMMIT == HEAD_COMMIT`: skip (no changes since last review).
- Otherwise: needs review.

### 4. Run quick-pr-review on changed PRs

For each PR that needs review, invoke:

```
/quick-pr-review {REPO} {PR}
```

Process PRs sequentially to avoid rate limiting.

### 5. Report summary

After processing all PRs, output a summary table:

| Repository | PR | Status |
|---|---|---|
| owner/repo | #42 | Reviewed (approved) |
| owner/repo | #88 | Reviewed (comment posted) |
| owner/repo | #55 | Skipped (no changes) |

## Example Usage

**Scenario 1: All orgs, some PRs updated**
```
/quick-pr-reviews
```
Finds 5 open PRs across multiple orgs. 2 have new commits, 3 unchanged. Runs `/quick-pr-review` on the 2 updated ones.

**Scenario 2: Filter to specific organizations**
```
/quick-pr-reviews acme widgets-inc
```
Fetches all review-requested PRs, then discards any not belonging to `acme` or `widgets-inc` before checking for changes.

**Scenario 3: No PRs awaiting review**
```
/quick-pr-reviews
```
Search returns no results. Report "No open PRs awaiting your review."

**Scenario 4: All PRs already reviewed**
```
/quick-pr-reviews
```
All existing review comments match the current HEAD commit. Report all as skipped.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh search prs --review-requested @me --state open --json number,repository,title,headRefOid` | List open PRs where you are a requested reviewer |
| `gh api repos/{owner}/{repo}/issues/{pr}/comments` | List comments on a PR |
