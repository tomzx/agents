---
name: pr-review-send
description: Send PR review comments to GitHub by file and line number using the pr-comment script.
allowed-tools: Bash(gh:*, uv:*, ~/.agents/scripts/should-post-to-github:*), Read, Glob, Grep
---

# Send PR Review Comments

Posts individual PR review comments to GitHub by file and line number using the `pr-comment.py` script from the personal-automation repository. Whether the comments are actually sent to GitHub is decided by `should-post-to-github` (based on `~/.sdlc/config.yaml`); when posting is disabled the comments are composed and shown for review instead.

## Prerequisites

- `uv` installed
- `pr-comment.py` script at `$HOME/repos/git/personal-automation/others/pr-comment.py`
- GitHub authentication configured for the script
- Must run from within `$HOME/repos/git/personal-automation`

### Skill attribution (GitHub)

Before each `pr-comment.py` invocation, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Posted with** footer for `SKILL_DIR` = `pr-review-send` to the `--comment` text.

## Steps

1. Navigate to the automation directory:
   ```
   cd $HOME/repos/git/personal-automation
   ```
2. Compose each review comment (including the **Skill attribution** footer).
3. Decide whether to post: get the PR author with `gh pr view <pr-number> --repo <owner>/<repo> --json author --jq .author.login`, then run `~/.agents/scripts/should-post-to-github --repo "<owner>/<repo>" --author "<PR_AUTHOR>"`. If it exits 1, present the comments to the user and stop without posting.
4. If it exits 0, post a review comment (`--comment` includes main text plus **Skill attribution** footer):
   ```
   uv run $HOME/repos/git/personal-automation/others/pr-comment.py <owner>/<repo> <pr-number> \
     --file <path/to/file.py> \
     --line <line-number> \
     --comment "<comment text>"
   ```
5. Repeat for each additional comment on different files or lines.

## Example Usage

**Scenario 1: Comment on a specific line**
```
/pr-review-send owner/myrepo 123 \
  --file src/main.py \
  --line 42 \
  --comment "This function should handle the case where input is None."
```
Posts the comment to PR #123 on `src/main.py` line 42, unless `should-post-to-github` excludes the repo or author (in which case the comment is composed and shown without posting).

**Scenario 2: Multiple comments on different files**
Run the command once per comment location, varying `--file` and `--line` for each. Each is posted unless `should-post-to-github` disables posting.

**Scenario 3: Comment on a migration file**
```
/pr-review-send owner/api 88 \
  --file migrations/0042_add_index.sql \
  --line 5 \
  --comment "Consider adding a concurrent index to avoid table locking."
```

## Useful Commands Reference

| Command | Description |
|---|---|
| `uv run <script> <owner>/<repo> <pr> --file <f> --line <n> --comment "<text>"` | Post a line-specific PR review comment |
