---
name: gh-cached
description: >
  Use gh-cached to browse GitHub issues and pull requests with local disk caching.
  Trigger when the user wants to list, search, or view issues/PRs for a GitHub
  repository and gh-cached is available (or can be built) in the environment.
  Also use when the user wants to pre-populate the local cache to reduce API calls.
---

# gh-cached Skill

`gh-cached` is a GitHub CLI that fetches issues, pull requests, and their comments
via the GitHub GraphQL API and caches every result to
`~/.cache/gh-cached/<host>/<owner>/<repo>` to minimise API calls.

---

## Prerequisites

### Binary

Check whether the binary is already on PATH, and install it if not:

```bash
if ! command -v gh-cached &>/dev/null; then
  wget -qO /usr/local/bin/gh-cached \
    https://github.com/TomzxCode/gh-cached/releases/download/latest/gh-cached-linux-amd64
  chmod +x /usr/local/bin/gh-cached
fi
```

Adjust the asset name for other platforms:

| Platform | Asset |
|---|---|
| Linux x86-64 | `gh-cached-linux-amd64` |
| Linux ARM64 | `gh-cached-linux-arm64` |
| macOS x86-64 | `gh-cached-darwin-amd64` |
| macOS ARM64 | `gh-cached-darwin-arm64` |

### Authentication

`gh-cached` reads `GH_TOKEN` from the environment.  If it is absent it falls
back to `gh auth token` (GitHub CLI).  Set the token when it is missing:

```bash
export GH_TOKEN=<token>
```

---

## Workflow

### 1. Determine target repository

`--repo` accepts `[HOST/]OWNER/REPO`.  When omitted, the repo is auto-detected
from the `origin` remote of the current directory.  Confirm which repo will be
used before running expensive commands:

```bash
# shows the remote that will be detected
git remote get-url origin
```

### 2. Pre-populate the cache (optional but recommended)

Run `cache` once to pull everything down so all subsequent list/view commands
are served instantly from disk:

```bash
gh-cached cache                          # default: stale after 60 min
gh-cached cache --repo owner/repo
gh-cached cache --cache-duration 120     # stale after 2 hours
gh-cached cache --cache-duration 0      # always re-fetch
```

### 3. List issues

```bash
gh-cached issue list                     # open issues, up to 30
gh-cached issue list --state all
gh-cached issue list --state closed
gh-cached issue list --author alice
gh-cached issue list --assignee bob
gh-cached issue list --label bug
gh-cached issue list --label bug --label p1   # AND logic
gh-cached issue list --milestone v2.0
gh-cached issue list --mention carol
gh-cached issue list --app dependabot
gh-cached issue list --search "memory leak"
gh-cached issue list --limit 50
gh-cached issue list --json              # machine-readable output
gh-cached issue list --no-truncate       # full titles
```

### 4. View a single issue

```bash
gh-cached issue view 42
gh-cached issue view 42 --comments      # include all comments
gh-cached issue view 42 --json
```

### 5. List pull requests

```bash
gh-cached pr list                        # open PRs, up to 30
gh-cached pr list --state merged
gh-cached pr list --state all
gh-cached pr list --author alice
gh-cached pr list --assignee bob
gh-cached pr list --label enhancement
gh-cached pr list --base main
gh-cached pr list --head feat/dark-mode
gh-cached pr list --draft
gh-cached pr list --search "fix crash"
gh-cached pr list --limit 50
gh-cached pr list --json
gh-cached pr list --no-truncate
```

### 6. View a single PR

```bash
gh-cached pr view 10
gh-cached pr view 10 --comments
gh-cached pr view 10 --json
```

---

## Caching behaviour reference

| Command | Cache behaviour |
|---|---|
| `cache` | Fetches all issues/PRs (all states, with comments); writes one JSON file each. Skips items whose file is younger than `--cache-duration`. |
| `issue list` / `pr list` | Reads all cached files and filters in memory when the full cache is fresh; falls back to the GitHub API otherwise. |
| `issue view` / `pr view` | Serves from the per-item file when it is < 60 min old; fetches from the API and updates the cache otherwise. When a full cache is fresh it is treated as authoritative (a missing item means it doesn't exist). |

---

## Tips

- Run `gh-cached cache` at the start of a session to avoid hitting the API
  rate-limit during bulk investigation.
- Use `--json` and pipe to `jq` for scripting:
  ```bash
  gh-cached issue list --json | jq '[.[] | {number, title, state}]'
  ```
- Multiple `--label` flags use AND logic (all labels must match).
- `--mention` and `--app` filters are only applied server-side (they cannot be
  verified from cached data, so they trigger an API call).

---

## Wrap up

After completing the user's request, summarise:

1. Which repository was targeted.
2. Whether the cache was used or the API was called.
3. A brief description of the results (count, key items, etc.).
