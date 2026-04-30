---
name: quick-pr-reviews
description: Check all PRs where you are a requested reviewer for new commits and run quick-pr-review on each one that has changed since last reviewed. Optionally filter to specific organizations or repositories (owner/repo).
allowed-tools: Bash(gh:*)
argument-hint: "[org1 org2 ... | owner/repo1 owner/repo2 ...]"
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
  <!-- quick-pr-review: marker
              |
       Commit changed?
        /          \
      No             Yes
      |               |
 Was "Tests pass"     |
 failing last time?   |
    /        \        |
  No          Yes     |
   |           |      |
   |    CI now green? |
   |     /       \    |
   |   No         \   |
   |    |          \  |
 Skip  Skip   /quick-pr-review
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
gh-cached pr view {PR} --repo {REPO} --json --refresh | jq -r '.headRefOid'
```

This gives you:
- `HEAD_COMMIT`: the output of the above command

### 2. For each PR, check for an existing review comment

```bash
gh api repos/{REPO}/issues/{PR}/comments \
  --jq '[.[] | select(.body | test("<!-- quick-pr-review:"))] | last | {id: .id, body: .body}'
```

Extract `COMMENT_COMMIT` from the marker line `<!-- quick-pr-review:COMMIT_SHA -->` in the comment body, if present.

- If `COMMENT_COMMIT == HEAD_COMMIT`: the PR has not changed since last review. Before skipping, check whether the previous comment contains `- [ ] Tests pass` (i.e., CI was failing). If it does, re-fetch the current CI status:

  ```bash
  gh-cached pr view {PR} --repo {REPO} --json --refresh | jq '.statusCheckRollup'
  ```

  If all checks are now passing or skipped, the PR needs review (proceed to step 3). If CI is still failing, skip and report "Skipped (CI still failing)".

  If the previous comment does not have a "Tests pass" failure, skip (no changes since last review).

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
| owner/repo | #77 | Skipped (CI still failing) |

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

**Scenario 6: Same commit but CI was failing, now passes**
```
/quick-pr-reviews
```
A PR has no new commits but the previous review comment contains `- [ ] Tests pass`. Re-fetches CI status: all checks are now green. Runs `/quick-pr-review` to update the comment and approve.

**Scenario 7: Same commit, CI still failing**
```
/quick-pr-reviews
```
A PR has no new commits but the previous review comment contains `- [ ] Tests pass`. Re-fetches CI status: checks are still failing. Skips and reports "Skipped (CI still failing)".

**Scenario 8: All PRs already reviewed**
```
/quick-pr-reviews
```
All existing review comments match the current HEAD commit. Report all as skipped.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh search prs --review-requested @me --state open --json number,repository,title,headRefOid` | List open PRs where you are a requested reviewer |
| `gh-cached pr view <pr> --repo <owner/repo> --json --refresh` | Fetch PR metadata including CI status (fresh) |
| `gh api repos/{owner}/{repo}/issues/{pr}/comments` | List comments on a PR |
