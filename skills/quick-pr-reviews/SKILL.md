---
name: quick-pr-reviews
description: Check all PRs where you are a requested reviewer for new commits and run quick-pr-review on each one that has changed since last reviewed. Optionally filter to specific organizations or repositories (owner/repo).
allowed-tools: Bash(gh:*)
argument-hint: [org1 org2 ... | owner/repo1 owner/repo2 ...]
---

# Quick PR Reviews

Finds all open PRs where you are a requested reviewer, checks each one for new commits since the last quick-pr-review comment, and runs `/quick-pr-review` on those that have changed. Accepts an optional list of organizations (e.g. `acme`) or repositories in `owner/repo` format (e.g. `acme/api`) to limit the scope. Filters are applied at the GitHub search API level for efficiency.

## Prerequisites

- `gh` CLI authenticated
- `quick-pr-review` skill available

## Workflow

```
Parse arguments into orgs and repos
              |
     Build search with --owner / --repo
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

### 1. Parse arguments and build search command

Separate `$@` into two groups:
- **Orgs**: arguments that do not contain `/` (e.g. `acme`, `widgets-inc`)
- **Repos**: arguments in `owner/repo` format (contain a `/`, e.g. `acme/api`, `org/web-app`)

Build the `gh search prs` command as follows:

```bash
gh search prs --review-requested @me --state open \
  --json number,repository,title \
  --limit 100
```

Append filter flags based on parsed arguments:
- For each org, add `--owner <org>`
- For each repo, add `--repo <owner/repo>`

If no arguments are provided, run the base command without `--owner` or `--repo` flags (fetches all review-requested PRs).

This returns a list of PRs. For each entry extract:
- `REPO`: `repository.nameWithOwner`
- `PR`: `number`

Then fetch the head commit SHA for each PR:

```bash
gh pr view {PR} --repo {REPO} --json headRefOid --jq '.headRefOid'
```

This gives you:
- `HEAD_COMMIT`: the output of the above command

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

**Scenario 1: All orgs, some PRs updated**
```
/quick-pr-reviews
```
Finds 5 open PRs across multiple orgs. 2 have new commits, 3 unchanged. Runs `/quick-pr-review` on the 2 updated ones.

**Scenario 2: Filter to specific organizations**
```
/quick-pr-reviews acme widgets-inc
```
Adds `--owner acme --owner widgets-inc` to the search. Only PRs from those orgs are returned.

**Scenario 3: Filter to specific repositories**
```
/quick-pr-reviews acme/api acme/web-app
```
Adds `--repo acme/api --repo acme/web-app` to the search. Only PRs from those repos are returned.

**Scenario 4: Mixed org and repo filters**
```
/quick-pr-reviews acme acme/api other-org/toolkit
```
Adds `--owner acme --repo acme/api --repo other-org/toolkit`. Results include all `acme` org PRs plus the two specific repos.

**Scenario 5: No PRs awaiting review**
```
/quick-pr-reviews
```
Search returns no results. Report "No open PRs awaiting your review."

**Scenario 6: All PRs already reviewed**
```
/quick-pr-reviews
```
All existing review comments match the current HEAD commit. Report all as skipped.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh search prs --review-requested @me --state open --json number,repository,title,headRefOid` | List open PRs where you are a requested reviewer |
| `gh api repos/{owner}/{repo}/issues/{pr}/comments` | List comments on a PR |
