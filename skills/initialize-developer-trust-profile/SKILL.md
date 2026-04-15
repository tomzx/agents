---
name: initialize-developer-trust-profile
description: Bootstrap a developer trust profile by scanning the last N PRs they authored (merged and rejected), determining outcome from actual review results.
allowed-tools: Bash(gh:*)
argument-hint: "<github_username> [count] [--orgs <org>...]"
---

# Initialize Developer Trust Profile

Bootstraps a developer trust profile by processing the last N PRs authored by a developer across **all repositories** visible to `gh` (not a single repo), delegating each one to `/developer-trust-profile`. Samples both merged and rejected PRs to avoid survivorship bias, and derives the outcome from actual review data rather than assuming all merged PRs are clean approvals.

Optionally pass **`--orgs`** followed by one or more GitHub organization logins to restrict results to PRs in repos owned by those orgs (or use multiple `--owner` flags in the commands below). Omit `--orgs` to consider PRs in any repo the token can access.

## Prerequisites

- `gh` CLI authenticated with read access to the repositories you expect to search (public repos work without extra scope; private repos need appropriate token access)
- `$1`: GitHub username of the developer
- `$2` (optional): number of PRs to scan (default: 10). Must be a positive integer if provided.
- `--orgs` (optional): one or more organization names; only PRs under those orgs are included

## Workflow

```
Resolve arguments
      |
Build optional --owner flags from org list
      |
Fetch merged PRs + closed-without-merge PRs (global or org-scoped)
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

- `GITHUB_USERNAME`: first positional argument
- `COUNT`: second positional if it is a positive integer, otherwise default `10`
- `ORGS`: empty unless `--orgs` appears; every token after `--orgs` until the end of the argument list is an organization login (e.g. `acme-corp`, `myorg`)

Build an array of extra `gh` flags for org scoping. For each org in `ORGS`, add `--owner <org>` to **both** search invocations below. If `ORGS` is empty, do not pass `--owner` (search spans all visible repos).

### 2. Fetch PRs

Use `gh search prs` (not `gh pr list --repo`). It returns `repository.nameWithOwner` as the repo slug for later `gh pr view` calls.

**Owner flags:** If you use shell variables, something like `EXTRA_OWNERS=(--owner acme --owner beta)` when orgs are `acme` and `beta`.

Fetch merged PRs (newest first by last activity):

```bash
gh search prs --author {GITHUB_USERNAME} --merged \
  --sort updated --order desc \
  --limit {COUNT} \
  {EXTRA_OWNERS...} \
  --json number,repository,closedAt,updatedAt \
  --jq '[.[] | {number, repo: .repository.nameWithOwner, date: (.closedAt // .updatedAt), merged: true}]'
```

Fetch closed, not merged PRs:

```bash
gh search prs --author {GITHUB_USERNAME} --merged=false --state closed \
  --sort updated --order desc \
  --limit {COUNT} \
  {EXTRA_OWNERS...} \
  --json number,repository,closedAt,updatedAt \
  --jq '[.[] | {number, repo: .repository.nameWithOwner, date: (.closedAt // .updatedAt), merged: false}]'
```

Combine both JSON arrays, sort by `date` descending, take the first `COUNT` entries. If the combined list is empty, report to the user and stop. Do not create a profile.

**Note:** Search uses GitHub’s search index; very new PRs can appear slightly later than on the web UI. Results respect private-repo access for the authenticated user.

### 3. Determine outcome for each PR

For each PR, use the `repo` field (`owner/name`) from the search result:

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

`REPO` is `repository.nameWithOwner` from search (e.g. `acme/webapp`). This handles fetching the diff, synthesizing observations, updating the trust level, writing the profile, and committing.

### 5. Report summary

After all PRs are processed, report:
- Number of PRs processed, broken down by outcome (N approved, M not_approved)
- The final trust level and reason (read from the written profile)
- The profile path
- If orgs were used, note the org filter so the user knows the sample scope

## Example Usage

**Scenario 1: Initialize with default count (all repos)**

```
/initialize-developer-trust-profile alice
```

Fetches the last 10 PRs by alice across merged and closed-unmerged PRs anywhere visible, derives outcomes from review data, calls `/developer-trust-profile` for each.

**Scenario 2: Custom count**

```
/initialize-developer-trust-profile bob 25
```

Processes 25 PRs for a more grounded profile (still cross-repo).

**Scenario 3: Limit to specific organizations**

```
/initialize-developer-trust-profile carol 15 --orgs acme-corp beta-labs
```

Only PRs in repositories owned by `acme-corp` or `beta-labs` are considered.

**Scenario 4: Developer with no PRs**

```
/initialize-developer-trust-profile dave --orgs single-org
```

No PRs match the search. Reports the absence and stops.

**Scenario 5: Mixed history**

```
/initialize-developer-trust-profile erin 10
```

Finds merged and rejected PRs in various repos. Outcomes follow review data. Final profile reflects the mixed track record.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh search prs --author <u> --merged --sort updated --order desc --limit N --json number,repository,closedAt,updatedAt` | Merged PRs by author (cross-repo) |
| `gh search prs --author <u> --merged=false --state closed --sort updated --order desc --limit N ...` | Closed, unmerged PRs by author |
| `gh search prs ... --owner <org> --owner <org2>` | Restrict search to repos under those org owners |
| `gh pr view <n> --repo <owner/name> --json reviews` | Review events for a PR |
