---
name: github-post-attribution
description: >-
  Resolves agents commit SHA and GitHub URL for a skill's SKILL.md, and
  formats footers for comments or issue bodies posted via gh. Use whenever a
  skill posts to GitHub (PR comments, issue comments, issue create, review
  comments) so readers see which skill and which repo revision produced the
  content. Other skills reference this instead of duplicating steps.
---

# GitHub post attribution (shared)

Skills that post content to GitHub should append a small footer: link to the **invoking** skill's `SKILL.md` at the **current** agents commit (the revision in use when the post was made), plus the model name that executed the skill.

## When to use

- Any `gh` command that creates or updates issue/PR text visible on GitHub.
- Invoked **by name** from other skills (e.g. "follow `skills/github-post-attribution/SKILL.md` before posting").

## Resolve repository root, commit, and GitHub base URL

`REPO_ROOT` = the directory that contains `skills/` (the agents checkout). The path to this file is always known from the `Read` call that loaded it. Use it directly -- no additional filesystem exploration needed.

Every skill file lives at `<REPO_ROOT>/skills/<SKILL_DIR>/SKILL.md`. Resolve symlinks (e.g. `~/.claude/skills → ~/src/agents/skills`) and capture all values in one call:

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

## Resolve model name

The model that executed the skill is identified by its short name (e.g. `glm-5.1`, `claude-sonnet-4-20250514`). The agent knows its own model at runtime from its environment. Set `MODEL_NAME` to the model's human-facing label:

```bash
MODEL_NAME="glm-5.1"  # replace with the actual model name at runtime
```

## Link to the invoking skill's file

The skill that **performs** the post is the one whose `SKILL.md` should be linked (not this file unless the workflow is only about attribution).

- `SKILL_DIR` = directory name under `skills/` (e.g. `handle-pr-feedback`, `quick-pr-review`).
- `SKILL_FILE_URL` = `{BASE}/blob/{SKILL_COMMIT}/skills/{SKILL_DIR}/SKILL.md`

Optional feedback link (same repo as the skill): `{BASE}/issues/new`

## Footer lines (after main content)

Add a horizontal rule, then append one footer line. Patterns (use the real `SKILL_FILE_URL`, 7-char SHA, and `MODEL_NAME` from above):

- **Comment / line review:** end with
  `Posted with [SKILL_DIR](SKILL_FILE_URL) via MODEL_NAME (` + short SHA + `)`
- **Issue create:** end with
  `Created with [SKILL_DIR](SKILL_FILE_URL) via MODEL_NAME (` + short SHA + `)`
- **Quick PR review:** end with
  `Reviewed with [quick-pr-review](SKILL_FILE_URL) via MODEL_NAME (` + short SHA + `)`
  Optional sub-line: feedback at `{BASE}/issues/new`.

Example:

```
---

Posted with [handle-pr-feedback](https://github.com/owner/repo/blob/abc1234.../skills/handle-pr-feedback/SKILL.md) via glm-5.1 (`abc1234`)
```

Link text in brackets must match the **invoking** skill's `SKILL_DIR` (except quick-pr-review, which uses the fixed label `quick-pr-review`).

## SDLC phase footer (when posting during an `sdlc` pipeline run)

When the post is produced while running the SDLC pipeline (the `sdlc` skill or any of its `create-*` / `review-*` / `publish-*` sub-skills operating on a feature), prepend an **SDLC phase line** above the `Posted with` / `Created with` line, under the same horizontal rule. Use exactly this two-line footer:

```
---
SDLC phase: <phase> (<FEAT-id> #<issue>)
Posted with [SKILL_DIR](SKILL_FILE_URL) via MODEL_NAME (`SKILL_SHORT_SHA`)
```

- `<phase>` is the current pipeline phase (e.g. `issue`, `requirements`, `specifications`, `plan`, `implementation`).
- `<FEAT-id>` is the feature directory ID (e.g. `FEAT-1`), or the epic ID (e.g. `EPIC-745`) for epic-level posts.
- `#<issue>` is the GitHub issue the post concerns.
- Keep the second line verb consistent with the post type (`Created with` for issue bodies, `Posted with` for comments and reviews, `Reviewed with [quick-pr-review]` for quick PR reviews).
- Outside an SDLC pipeline run, omit the `SDLC phase:` line entirely and use only the single `Posted with` / `Created with` line as described above.

Example (comment posted during the requirements phase):

```
---
SDLC phase: requirements (FEAT-1 #969)
Posted with [review-requirements](https://github.com/owner/repo/blob/abc1234.../skills/review-requirements/SKILL.md) via glm-5.1 (`abc1234`)
```

## Shell escaping: do NOT backslash-escape backticks

Inside a `<<'EOF'` heredoc, backticks are literal. Never write `\`abc1234\`` -- write `(`abc1234`)` with plain backticks. Resolve `SKILL_SHORT_SHA` to the actual 7-char SHA before constructing the command.

## Notes

- **No package manager**: skills do not declare dependencies in YAML; consuming skills must **read** this file (or follow a one-line pointer in their own `SKILL.md`) so the agent loads the procedure.
- **Forks and renames**: `{BASE}` comes from `origin`, so links stay correct if the remote is `agents`, `claude-commands`, or a fork.
