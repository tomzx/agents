---
name: review-requested-prs
description: Check all PRs where you are a requested reviewer for new commits and run quick-pr-review on each one that has changed since last reviewed.
allowed-tools: Bash(gh:*)
---

# Review Requested PRs

Finds all open PRs where you are a requested reviewer, checks each one for new commits since the last quick-pr-review comment, and runs `/quick-pr-review` on those that have changed.

## Prerequisites

- `gh` CLI authenticated
- `quick-pr-review` skill available

## Workflow

```
Fetch open PRs with review requested
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

### 2. For each PR, check for an existing review comment

```bash
gh api repos/{REPO}/issues/{PR}/comments \
  --jq '[.[] | select(.body | test("<!-- quick-pr-review -->"))] | last | {id: .id, body: .body}'
```

Extract `COMMENT_COMMIT` from the marker line `<!-- quick-pr-review:COMMIT_SHA -->` in the comment body, if present.

- If `COMMENT_COMMIT == HEAD_COMMIT`: skip (no changes since last review).
- Otherwise: needs review.

### 3. Run quick-pr-review on changed PRs

For each PR that needs review, invoke:

```
/quick-pr-review {REPO} {PR}
```

Process PRs sequentially to avoid rate limiting.

### 4. Report summary

After processing all PRs, output a summary table:

| Repository | PR | Status |
|---|---|---|
| owner/repo | #42 | Reviewed (approved) |
| owner/repo | #88 | Reviewed (comment posted) |
| owner/repo | #55 | Skipped (no changes) |

## Example Usage

**Scenario 1: Several PRs, some updated**
```
/review-requested-prs
```
Finds 5 open PRs. 2 have new commits since last review, 3 are unchanged. Runs `/quick-pr-review` on the 2 updated ones and reports the summary.

**Scenario 2: No PRs awaiting review**
```
/review-requested-prs
```
Search returns no results. Report "No open PRs awaiting your review."

**Scenario 3: All PRs already reviewed**
```
/review-requested-prs
```
All existing review comments match the current HEAD commit. Report all as skipped.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh search prs --review-requested @me --state open --json number,repository,title,headRefOid` | List open PRs where you are a requested reviewer |
| `gh api repos/{owner}/{repo}/issues/{pr}/comments` | List comments on a PR |
