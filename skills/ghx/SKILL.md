---
name: ghx
description: >
  Use ghx as an extended GitHub CLI. It browses issues and pull requests with
  local disk caching, and performs PR/issue comment operations the standard `gh`
  CLI does not support: inline PR review comments, line-range comments, thread
  replies, pending reviews, local comment stashes, and edit/delete of comments.
  Trigger when the user wants to list/search/view issues or PRs, pre-populate the
  cache, comment on a PR (especially inline / on a specific file or line), reply
  to a review thread, manage a pending review, stash review comments, or
  edit/delete a comment.
cli: ghx
---

# ghx Skill

`ghx` is an extended GitHub CLI.
It talks to the GitHub GraphQL API directly to provide three kinds of capability:

1. **Cached browsing** — fetches issues, pull requests, and their comments and caches every result locally (SQLite at `~/.cache/ghx/cache/cache.db` by default, or one JSON file per entry under `~/.cache/ghx/cache/<host>/<owner>/<repo>/` with `--storage file`) to minimise API calls.
2. **Comment operations** — inline review comments, line-range comments, thread replies, pending reviews, and a local "stash" for offline review comments, none of which the standard `gh` CLI supports.
3. **Remote execution** — `ghx rpc serve` exposes the same operations over JSON-RPC, and `--remote <url>` runs any command against that server instead of locally.

---

## Prerequisites

### Binary

Check whether the binary is on PATH; install from the latest release if not:

```bash
if ! command -v ghx &>/dev/null; then
  go install github.com/tomzxcode/ghx@main
fi
```

Pre-built binaries are also available at <https://github.com/TomzxCode/ghx/releases/tag/latest>.

### Authentication

`ghx` reads `GH_TOKEN` or `GITHUB_TOKEN` from the environment, and falls back to `gh auth token` (GitHub CLI).
Set the token if neither is available:

```bash
export GH_TOKEN=<token>
```

### Target repository

All commands accept `--repo [HOST/]OWNER/REPO` (or `-R`).
When omitted, the repo is auto-detected from the `origin` remote of the current directory.
Confirm the target before running expensive or write operations:

```bash
git remote get-url origin
```

---

## Cached browsing

### Pre-populate the cache

Run `cache` to populate and refresh the local cache, so subsequent list/view commands are served instantly from disk:

```bash
ghx cache                            # delta refresh from the last cache write
ghx cache --repo owner/repo
ghx cache --if-stale                 # skip while the cache is newer than --cache-duration (60 min)
ghx cache --if-stale --cache-duration 120   # ... newer than 2 hours
ghx cache --since 2026-09-01         # refresh entries created/updated since a date
ghx cache --type issues              # refresh only issues (or prs)
ghx cache --force                    # discard resume state and do a full re-fetch
ghx cache --retries 5                # retry transient errors (default 2; total attempts = retries + 1)
```

### List issues

```bash
ghx issue list                       # open issues (default)
ghx issue list --state all
ghx issue list --author alice
ghx issue list --assignee bob
ghx issue list --label bug
ghx issue list --label bug --label p1   # AND logic
ghx issue list --milestone v2.0
ghx issue list --search "memory leak"
ghx issue list --mention alice
ghx issue list --app dependabot
ghx issue list --limit 50
ghx issue list --no-truncate         # keep long titles on one line
ghx issue list --json                # machine-readable output
```

### View an issue

```bash
ghx issue view 42
ghx issue view 42 --comments         # include all comments
ghx issue view 42 --ids              # include comment IDs (for edit/delete)
ghx issue view 42 --refresh          # force fetch from GitHub and update cache
```

### List pull requests

```bash
ghx pr list                          # open PRs (default)
ghx pr list --state merged
ghx pr list --author alice
ghx pr list --assignee bob
ghx pr list --app dependabot
ghx pr list --label enhancement
ghx pr list --base main
ghx pr list --head feat/dark-mode
ghx pr list --draft
ghx pr list --search "fix crash"
ghx pr list --no-truncate            # keep long titles on one line
ghx pr list --json                   # all fields
ghx pr list --json number,title,state,headRefOid   # field list (comma-separated)
```

Only `pr list` takes a field list; `issue list`/`issue view`/`pr view` take a boolean `--json` and emit the whole object.

### View a PR

```bash
ghx pr view 10
ghx pr view 10 --comments
ghx pr view 10 --refresh             # force fetch from GitHub and update cache
```

### Cached repositories

```bash
ghx repo list                        # locally cached repositories
ghx repo delete owner/repo           # drop one repo's cached rows (local only; refetched on next use)
```

### Caching behaviour reference

| Command | Cache behaviour |
|---|---|
| `cache` | Fetches all issues/PRs (all states, with comments) into the local cache (SQLite by default, one JSON file each with `--storage file`). Every run delta-refreshes from the last cache write. `--if-stale` skips the run while the cache is younger than `--cache-duration`; without it the run always delta-refreshes. `--since <date>` refreshes only entries created/updated on or after the date. `--type issues` or `--type prs` refreshes one portion only. `--force` discards the resume state and does a full re-fetch. Explicit `--since`/`--type` bypass the freshness check; `--since` cannot combine with `--force`. |
| `issue list` / `pr list` | Reads the local cache and filters in memory when the full cache is fresh; falls back to the GitHub API otherwise. |
| `issue view` / `pr view` | Serves from the cache when the entry is < 60 min old; fetches from the API and updates the cache otherwise. `--refresh` bypasses all cache checks, always fetches from the API, and updates the cache. |

---

## Other commands

```bash
ghx serve                              # local web UI (and JSON-RPC endpoint) over the cache
ghx rpc methods                        # list the methods a running ghx RPC server exposes
ghx stats --from 2026-01-01 --to 2026-06-30 -o report.html   # PR activity report
ghx telemetry summary                  # local API/cache timing report
ghx cache migrate                      # copy a file-backed cache into SQLite (source left intact)
ghx mock serve                         # mock GraphQL server for testing
ghx completion bash                    # shell completion script (also zsh, fish, powershell)
```

- `ghx serve` (`--host`, `--port`, `--open`) browses every cached repository over a local web UI.
  The UI is read-only against the cache except for its refresh action.
  It also mounts the JSON-RPC endpoint at `POST /rpc`; `--rpc-token` requires a bearer token and `--rpc-allow-exec` (default on) exposes `cli.run`.
- `ghx rpc` is the JSON-RPC surface.
  `rpc serve` listens on `127.0.0.1:8090` and accepts `--host` and `--port`.
  `rpc methods` lists the exposed methods, `rpc call <method> [params-json]` calls one, and `rpc exec -- <ghx args...>` runs a whole CLI command on the server and mirrors its output and exit code.
  Pass `--token` (or `GHX_RPC_TOKEN`) and `--url` (or `GHX_RPC_URL`) to reach a non-default server.
- `ghx stats [REPO...]` writes an HTML report of pull request activity (an author by reviewer matrix with time to first review); it serves from the cache when available and falls back to the API.
- `ghx telemetry` (`status`, `enable`, `disable`, `summary`, `export`, `clear`) reads or controls the local telemetry database; recording is on by default (opt out with `--telemetry=false` or `GHX_TELEMETRY=0`).
- `ghx cache migrate` copies a file-backed cache into the SQLite backend (the default storage) and leaves the source cache intact, so it is safe to re-run.
- `ghx completion` (`bash`, `zsh`, `fish`, `powershell`) prints a completion script for the shell; pass `--no-descriptions` to omit completion descriptions.

Global flags apply to every command: `--repo/-R [HOST/]OWNER/REPO`, `--cache-dir <path>`, `--storage sqlite|file` (env `GHX_STORAGE`), `--log-level <debug|info|warn|error>`, `--telemetry` (env `GHX_TELEMETRY`), `--telemetry-db <path>`, and `--api-url <url>` (override the GraphQL endpoint, for testing).
Any command also accepts `--remote <url>` to run against a running `ghx rpc serve` instance instead of locally; the flag is not listed in `--help` but the CLI accepts it.

---

## PR comments

### Top-level comment

```bash
ghx pr comment 42 --body "Looks good"
```

### Inline comment on a single line

```bash
ghx pr comment 42 --file src/main.go --line 10 --body "Nit: use fmt.Errorf"
ghx pr comment 42 --file src/main.go --line 10 --side LEFT --body "Line removed"
```

### Inline comment on a line range

```bash
ghx pr comment 42 --file src/main.go --line 10-15 --body "Consider extracting"
```

### File-level comment

```bash
ghx pr comment 42 --file src/main.go --body "Overall looks clean"
```

### Reply to an existing review thread

Find the thread id with `ghx pr threads <number>`, then:

```bash
ghx pr comment 42 --reply-thread <thread-id> --body "Agreed"
```

### Body from stdin or a file

```bash
ghx pr comment 42 --body-file -
ghx pr comment 42 --body-file comment.txt
```

### Pending vs immediate

By default the comment is posted immediately.
Use `--pending` to attach the comment to a pending review instead:

```bash
ghx pr comment 42 --file src/main.go --line 10 --body "Nit" --pending
ghx pr comment 42 --reply-thread <thread-id> --body "Reply"   --pending
```

GitHub does not allow mixing immediate and pending review comments on the same PR.
When you submit an immediate inline/reply comment while a pending review exists, `ghx` automatically stashes the pending comments to disk, posts the immediate comment, then restores the pending review.

### Stash a comment locally (no API call)

`--stash` saves the comment to a local YAML file under a stash entry instead of contacting GitHub.
Stashes work like `git stash` and support multiple entries:

```bash
ghx pr comment 42 --file src/main.go --line 10 --body "Nit" --stash
ghx pr comment 42 --file src/main.go --line 30 --body "Another" --stash=1
```

### Edit / delete a PR comment

```bash
ghx pr comment edit   <comment-id> --body "Updated text"
ghx pr comment edit   <comment-id> --body-file updated.txt
ghx pr comment delete <comment-id>
```

Use `ghx pr threads <number> --ids` to discover comment IDs.

---

## Pending reviews

```bash
ghx pr review create  42                 # start a pending review
ghx pr review list    42                 # your pending reviews on this PR
ghx pr review submit  42 --event COMMENT
ghx pr review submit  42 --event APPROVE        --body "LGTM"
ghx pr review submit  42 --event REQUEST_CHANGES --body "See comments"
ghx pr review submit  42 --event COMMENT --body-file summary.md
ghx pr review submit  42 --review <review-id>   # submit a specific pending review
ghx pr review discard <review-id>        # discard a pending review
```

---

## Review-comment stashes

The stash stores pending-review comments locally so you can post immediate comments, accumulate review notes offline, or move them between PR states.

```bash
ghx pr review stash push 42                  # save pending -> stash@{0}, delete pending
ghx pr review stash push 42 -m "nit comments"
ghx pr review stash list 42                  # list stash entries for this PR
ghx pr review stash pop  42                  # restore stash@{0} into a pending review
ghx pr review stash pop  42 --stash 1        # restore stash@{1}
ghx pr review stash drop 42                  # discard stash@{0} without restoring
ghx pr review stash drop 42 --stash 1        # discard stash@{1}
```

Stash entries are also the destination for `ghx pr comment ... --stash`.

---

## Review threads

```bash
ghx pr threads 42                       # open threads
ghx pr threads 42 --thread <thread-id>  # show one thread
ghx pr threads 42 --ids                 # include comment IDs (for edit/delete)
ghx pr threads 42 --state all
ghx pr threads 42 --state resolved

ghx pr threads resolve <thread-id>...     # mark threads resolved
ghx pr threads unresolve <thread-id>...   # reopen resolved threads
```

`resolve` and `unresolve` attempt every thread id given and exit non-zero if any fail. Get ids from `ghx pr threads 42 --ids` (add `--state resolved` before reopening).

---

## Issue comments

```bash
ghx issue comment 42 --body "This is fixed in #50"
ghx issue comment 42 --body-file -
ghx issue comment 42 --body-file comment.txt

ghx issue view 42                       # description + comments
ghx issue view 42 --ids                 # include comment IDs

ghx issue comment edit   <comment-id> --body "Updated text"
ghx issue comment edit   <comment-id> --body-file updated.txt
ghx issue comment delete <comment-id>
```

`ghx pr comment edit/delete` and `ghx issue comment edit/delete` operate on the same underlying GitHub comment types; ghx auto-detects whether a comment id refers to a review comment or an issue comment.

---

## Tips

- Run `ghx cache` at the start of a session to avoid hitting the API rate-limit during bulk investigation.
- Use `--json` and pipe to `jq` for scripting:
  ```bash
  ghx issue list --json | jq '[.[] | {number, title, state}]'
  ```
- For inline review comments on multiple lines, prefer one `--pending` comment per location, then `ghx pr review submit` once with the desired `--event`.
- Use `--stash` (no API call) when iterating on draft feedback you are not ready to send.
- Read bodies from a file (`--body-file`) for multi-line markdown.

---

## Wrap up

After completing the user's request, summarise:

1. Which repository and PR/issue was targeted.
2. Whether the cache was used, the API was called, or a comment was posted immediately, added to a pending review, or saved to a local stash.
3. The IDs (comment id, thread id, review id) of any objects created, so the user can edit/delete/submit later.