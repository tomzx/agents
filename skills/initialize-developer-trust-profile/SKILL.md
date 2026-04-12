---
name: initialize-developer-trust-profile
description: Bootstrap a developer trust profile by scanning the last N PRs they authored (merged and rejected), determining outcome from actual review results.
allowed-tools: Bash(gh:*)
argument-hint: <github_username> <owner/repo> [count]
---

# Initialize Developer Trust Profile

Bootstraps a developer trust profile by processing the last N PRs authored by a developer, delegating each one to `/developer-trust-profile`. Samples both merged and rejected PRs to avoid survivorship bias, and derives the outcome from actual review data rather than assuming all merged PRs are clean approvals.

## Prerequisites

- `gh` CLI authenticated with read access to the target repository
- `$1`: GitHub username of the developer
- `$2`: repository in `owner/repo` format
- `$3` (optional): number of PRs to scan (default: 10)

## Workflow

```
Resolve arguments
      |
Fetch merged PRs + closed-without-merge PRs
      |
Merge, sort by date, take most recent N
      |
Any PRs found?
  /         \
No            Yes
 |             |
Stop       For each PR (oldest first):
               |
           Fetch reviews
               |
           Determine outcome
           (approved / not_approved)
               |
           /developer-trust-profile
           {username} --after-review
           {repo} {pr_number} {outcome}
              |
           Report summary
```

## Steps

### 1. Resolve arguments

- `GITHUB_USERNAME`: `$1`
- `REPO`: `$2` (`owner/repo`)
- `COUNT`: `$3` if provided, otherwise `10`

### 2. Fetch PRs

Fetch merged PRs:

```bash
gh pr list --repo {REPO} \
  --author {GITHUB_USERNAME} \
  --state merged \
  --limit {COUNT} \
  --json number,mergedAt \
  --jq '[.[] | {number, date: .mergedAt, merged: true}]'
```

Fetch closed-without-merge PRs (closed state in gh CLI includes merged; filter them out):

```bash
gh pr list --repo {REPO} \
  --author {GITHUB_USERNAME} \
  --state closed \
  --limit {COUNT} \
  --json number,closedAt,mergedAt \
  --jq '[.[] | select(.mergedAt == null) | {number, date: .closedAt, merged: false}]'
```

Combine both lists, sort by date descending, take the most recent `COUNT` entries. If no PRs are found at all, report to the user and stop. Do not create a profile.

### 3. Determine outcome for each PR

For each PR, fetch its review data:

```bash
gh pr view {PR_NUMBER} --repo {REPO} --json reviews \
  --jq '.reviews | map(select(.state != "COMMENTED" and .state != "DISMISSED"))'
```

Determine outcome:

- **`not_approved`** if any of:
  - The PR was closed without merging (rejected or abandoned)
  - The PR has a `CHANGES_REQUESTED` review that was not superseded by a later `APPROVED` review from the same reviewer
- **`approved`** otherwise (merged with only approvals, or no formal reviews)

### 4. Process each PR

For each PR (oldest first), invoke:

```
/developer-trust-profile {GITHUB_USERNAME} --after-review {REPO} {PR_NUMBER} {OUTCOME}
```

This handles fetching the diff, synthesizing observations, updating the trust level, writing the profile, and committing.

### 5. Report summary

After all PRs are processed, report:
- Number of PRs processed, broken down by outcome (N approved, M not_approved)
- The final trust level and reason (read from the written profile)
- The profile path

## Example Usage

**Scenario 1: Initialize with default count**
```
/initialize-developer-trust-profile alice owner/myrepo
```
Fetches last 10 PRs by alice across merged and rejected, derives outcomes from review data, calls `/developer-trust-profile` for each.

**Scenario 2: Initialize with custom count**
```
/initialize-developer-trust-profile bob owner/myrepo 25
```
Processes 25 PRs for a more grounded profile.

**Scenario 3: Developer with no PRs**
```
/initialize-developer-trust-profile carol owner/myrepo
```
No PRs found. Reports the absence and stops.

**Scenario 4: Developer with mixed history**
```
/initialize-developer-trust-profile dave owner/myrepo
```
Finds 6 merged PRs and 4 rejected ones. Of the merged PRs, 2 had CHANGES_REQUESTED reviews before eventually being approved. Those 2 are labeled `not_approved`. Final profile reflects the mixed track record.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh pr list --repo <r> --author <u> --state merged --limit N --json number,mergedAt` | Fetch merged PRs |
| `gh pr list --repo <r> --author <u> --state closed --limit N --json number,closedAt,mergedAt --jq '[.[] \| select(.mergedAt == null)]'` | Fetch closed-without-merge PRs |
| `gh pr view <pr> --repo <r> --json reviews` | Fetch review events for a PR |
