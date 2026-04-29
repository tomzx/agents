---
name: github-post-attribution
description: >-
  Resolves dot-claude commit SHA and GitHub URL for a skill's SKILL.md, and
  formats footers for comments or issue bodies posted via gh. Use whenever a
  skill posts to GitHub (PR comments, issue comments, issue create, review
  comments) so readers see which skill and which repo revision produced the
  content. Other skills reference this instead of duplicating steps.
---

# GitHub post attribution (shared)

Skills that post content to GitHub should append a small footer: link to the **invoking** skill’s `SKILL.md` at the **current** dot-claude commit (the revision in use when the post was made).

## When to use

- Any `gh` command that creates or updates issue/PR text visible on GitHub.
- Invoked **by name** from other skills (e.g. “follow `skills/github-post-attribution/SKILL.md` before posting”).

## Resolve repository root, commit, and GitHub base URL

`REPO_ROOT` = the directory that contains `skills/` (the dot-claude checkout). The path to this file is always known from the `Read` call that loaded it. Use it directly -- no additional filesystem exploration needed.

Every skill file lives at `<REPO_ROOT>/skills/<SKILL_DIR>/SKILL.md`. Resolve symlinks (e.g. `~/.claude/skills → ~/src/dot-claude/skills`) and capture all values in one call:

```bash
SKILL_MD_DIR=$(dirname "$(readlink -f /path/to/this/SKILL.md)")
REPO_ROOT=$(cd "$SKILL_MD_DIR" && git rev-parse --show-toplevel)
SKILL_COMMIT=$(cd "$REPO_ROOT" && git rev-parse HEAD)
SKILL_SHORT_SHA=${SKILL_COMMIT:0:7}
REMOTE_URL=$(cd "$REPO_ROOT" && git remote get-url origin)
```

Replace `/path/to/this/SKILL.md` with the absolute path used in the `Read` call. `readlink -f` resolves any symlinks before `git` sees the path, so `--show-toplevel` always returns the real repo root.

From `REMOTE_URL`, normalize to `https://github.com/{owner}/{repo}`:

- `git@github.com:owner/repo.git` → `https://github.com/owner/repo`
- `https://github.com/owner/repo.git` → `https://github.com/owner/repo`

Call that `{BASE}`.

## Link to the invoking skill’s file

The skill that **performs** the post is the one whose `SKILL.md` should be linked (not this file unless the workflow is only about attribution).

- `SKILL_DIR` = directory name under `skills/` (e.g. `address-pr-comments`, `quick-pr-review`).
- `SKILL_FILE_URL` = `{BASE}/blob/{SKILL_COMMIT}/skills/{SKILL_DIR}/SKILL.md`

Optional feedback link (same repo as the skill): `{BASE}/issues/new`

## Footer lines (after main content)

Add a horizontal rule, then append one footer line. Patterns (use the real `SKILL_FILE_URL` and 7-char SHA from above):

- **Comment / line review:** end with
  `Posted with [SKILL_DIR](SKILL_FILE_URL) (` + short SHA + `)`
- **Issue create:** end with
  `Created with [SKILL_DIR](SKILL_FILE_URL) (` + short SHA + `)`
- **Quick PR review:** end with
  `Reviewed with [quick-pr-review](SKILL_FILE_URL) (` + short SHA + `)`
  Optional sub-line: feedback at `{BASE}/issues/new`.

Example:

```
---

Posted with [address-pr-comments](https://github.com/owner/repo/blob/abc1234.../skills/address-pr-comments/SKILL.md) (`abc1234`)
```

Link text in brackets must match the **invoking** skill’s `SKILL_DIR` (except quick-pr-review, which uses the fixed label `quick-pr-review`).

## Notes

- **No package manager**: skills do not declare dependencies in YAML; consuming skills must **read** this file (or follow a one-line pointer in their own `SKILL.md`) so the agent loads the procedure.
- **Forks and renames**: `{BASE}` comes from `origin`, so links stay correct if the remote is `dot-claude`, `claude-commands`, or a fork.
