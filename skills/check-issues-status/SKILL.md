---
name: check-issues-status
description: Orchestrate check-issue-status across a list of issues to find which are already addressed in the code. Supports checking every open issue in a repository, issues authored by a specific user, or issues matching a custom search query, and these scopes combine. Use to triage a backlog for stale or already-implemented issues, audit a user's open reports, or filter a query before investing effort. Triggers on "check these issues", "which issues are already done", "find stale issues", "batch check issue status", "check issues by <user>", or "are any of these already fixed".
allowed-tools: Bash(gh:*, git:*, ghx:*, ~/.agents/scripts/get-env:*), Read, Write
argument-hint: "[owner/repo] [--author <user>] [--query <text>] [--limit <n>] [--state <state>] [--post]"
---

# Check Issues Status

Runs `check-issue-status` across a list of issues and aggregates the verdicts.
Use it to find issues that are already addressed in the code so effort is not spent on them, and to find stale issues worth closing.

Supports three scoping modes, which compose freely:
- **Repository**: every open issue in a repo (default when only a repo is given).
- **Author**: issues authored by a specific user.
- **Query**: issues matching a custom GitHub search query.

This is the batch counterpart of `check-issue-status`, which owns all per-issue code inspection.
For a single issue, invoke `/check-issue-status <number> [repository]` directly.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `gh` CLI authenticated with read access to the target repositories.
- `check-issue-status` skill available.
- No local checkout is required: `check-issue-status` clones each repository it needs (see its step 1).

## Scope and modes

Resolve the scope from the arguments, then `$REPO`, then the current directory's `origin` remote.
The three modes are filters on `gh search issues`:

| Mode | Argument | Adds to search |
|---|---|---|
| Repository | positional `owner/repo` (or omit for current repo) | `--repo <owner/repo>` |
| Author | `--author <user>` | `--author <user>` |
| Query | `--query "<text>"` | the free-text query |

If neither `--author` nor `--query` is given, repository mode lists all open issues in the repo.

## Workflow

```
Resolve scope + filters
        |
        v
gh search issues --json repository,number,title
        |
        v
Group results by repository
        |
        v
For each issue:
  delegate to /check-issue-status <number> <repo>
  (report-only unless --post;
   it clones the repo when not checked out)
        |
        v
Aggregate combined summary (implemented first)
```

## Steps

### 1. Resolve scope and filters

Parse the arguments:
- Positional `owner/repo` (optional) sets the repository scope.
  If absent, use `$REPO`, then the current directory's `git remote get-url origin`.
- `--author <user>` filters by author.
- `--query "<text>"` adds a free-text search.
- `--state <state>` (default `open`).
- `--limit <n>` (default 30) caps how many issues are fetched and processed.
- `--post` allows `check-issue-status` to post comments on `implemented` verdicts.
  Off by default, so a batch run is report-only.

### 2. Build and run the search

```bash
gh search issues \
  --state open \
  --limit 30 \
  --json repository,number,title \
  [--repo <owner/repo>] \
  [--author <user>] \
  ["<query text>"]
```

Include `--repo` only when a repository scope is resolved.
Include `--author` and the query text only when provided.
This single command covers all three modes.

If the search returns no results, report "No issues matched the scope." and stop.

### 3. Group by repository

`gh search issues` can return issues from multiple repositories (author or query mode without a repo scope).
Group the results by `repository.nameWithOwner`.

### 4. Delegate per issue

Load `check-issue-status` (via the skill tool) before processing the first issue, then apply its workflow to each issue.
For each issue, in result order, delegate to the singular skill:

```
/check-issue-status <number> <owner/repo>
```

Unless `--post` is set, run `check-issue-status` in report-only mode: perform the analysis and return the verdict and evidence, but skip its comment-posting step.
Collect these for the aggregate report.

`check-issue-status` resolves code access itself: it uses a matching local checkout when one exists and otherwise clones the repository into its cache directory, so issues from several repositories can be processed in one run.
A first pass over a repository not yet cloned costs one clone (shallow, default branch); later runs reuse and refresh it.

If the clone fails for an issue's repository (private repository without access, no network), record the issue as deferred with the reason and continue with the rest.

Process issues sequentially to avoid rate limiting.

### 5. Aggregate and report

Sort the inspected issues with `implemented` first (the actionable findings), then `partial`, then `not-implemented`.
Output a combined table:

```markdown
## Issues Status (scope: <scope description>)

### Already addressed (candidates to close)

| Issue | Title | Verdict | Evidence |
|---|---|---|---|
| owner/repo#42 | Add CSV export | implemented | `src/export/csv.go:88` |
| owner/repo#15 | NPE on SSO login | implemented (bug fixed) | `auth/sso.py:31` |

### Partially addressed

| Issue | Title | Missing |
|---|---|---|
| owner/repo#30 | Rate limiting | per-IP limit absent |

### Not addressed (clear to work on)

| Issue | Title |
|---|---|
| owner/repo#7 | Dark mode |

### Deferred

- `other/private-repo#9` (clone failed: no access)
- 14 more issues beyond --limit 30 (re-run with a higher limit to include them)
```

### 6. Optional posting

If `--post` was set, posting already happened per issue during delegation.
Otherwise, if there are `implemented` findings, offer to post their comments now, or let the user rerun with `--post`.
Do not post without an explicit choice.

## Failure Modes

| Mode | Response |
|---|---|
| **No scope resolvable and no author/query** | Stop and ask the user for a repository, author, or query |
| **Issues span several repositories** | Inspect all of them; `check-issue-status` clones repositories that are not checked out |
| **Clone fails for one repository** | Defer that repository's issues with the reason and continue; do not verdict without code |
| **Large backlog** | Process up to `--limit`, defer the remainder, suggest re-running with a higher limit or a narrower query |
| **Search returns zero issues** | Report "No issues matched the scope." and stop |

## Outcome

If `$OUTCOME_YAML` is set, emit a batch verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `has-implemented` | At least one inspected issue is `implemented` |
| `mixed-or-partial` | None `implemented`, but at least one `partial` (or a mix) |
| `all-not-implemented` | Every inspected issue is `not-implemented` |
| `none-inspected` | All issues were deferred (clone failures or none fetched) |

## Example Usage

**Scenario 1: Whole repository**
```
/check-issues-status owner/myrepo
```
Lists all open issues in `owner/myrepo`, delegates each to `/check-issue-status` (report-only), aggregates the table.
`implemented` findings are surfaced as close candidates.

**Scenario 2: Current repository, default**
```
/check-issues-status
```
No repo given, so scope resolves to the current directory's `origin`.
Lists its open issues and checks each.

**Scenario 3: Issues by a user**
```
/check-issues-status owner/myrepo --author jane
```
Searches open issues authored by `jane` in `owner/myrepo`, inspects each, reports which are already addressed.

**Scenario 4: Custom query**
```
/check-issues-status owner/myrepo --query "export audit logs"
```
Searches open issues matching the query, inspects each, reports status.

**Scenario 5: Cross-repo author search**
```
/check-issues-status --author jane --limit 50
```
No repo scope, so the search spans repositories.
Each repository is inspected in turn; ones not checked out locally are cloned into `check-issue-status`'s cache directory on first use, so all matching issues get a verdict without any manual setup.

**Scenario 6: Post close-suggestion comments**
```
/check-issues-status owner/myrepo --post
```
Same as scenario 1, but `implemented` findings post their evidence comment on the issue via `check-issue-status`.

## Notes

- Default mode is report-only so a batch run never posts unneeded comments.
  Use `--post` once the report is reviewed.
- Repeated runs are safe: `check-issue-status` checks for its own prior comment marker before posting and edits in place when the code has moved, so even `--post` runs do not repost an already-flagged issue.
- The orchestrator does not inspect code itself; it delegates to `check-issue-status`, which uses a local checkout when the repository is already checked out and otherwise clones it into its cache directory.
- For a single issue, skip this orchestrator and call `/check-issue-status <number> [repository]` directly.
