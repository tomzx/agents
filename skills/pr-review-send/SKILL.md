---
name: pr-review-send
description: Send PR review comments to GitHub using the pr-comment script.
---

# Send PR Review Comments

Posts individual PR review comments to GitHub by file and line number using the `pr-comment.py` script from the personal-automation repository.

## Prerequisites

- `uv` installed
- `pr-comment.py` script at `$HOME/repos/git/personal-automation/others/pr-comment.py`
- GitHub authentication configured for the script
- Must run from within `$HOME/repos/git/personal-automation`

## Steps

1. Navigate to the automation directory:
   ```
   cd $HOME/repos/git/personal-automation
   ```
2. Post a review comment:
   ```
   uv run $HOME/repos/git/personal-automation/others/pr-comment.py <owner>/<repo> <pr-number> \
     --file <path/to/file.py> \
     --line <line-number> \
     --comment "<comment text>"
   ```
3. Repeat for each additional comment on different files or lines.

## Example Usage

**Scenario 1: Comment on a specific line**
```
uv run $HOME/repos/git/personal-automation/others/pr-comment.py owner/myrepo 123 \
  --file src/main.py \
  --line 42 \
  --comment "This function should handle the case where input is None."
```

**Scenario 2: Multiple comments on different files**
Run the command once per comment location, varying `--file` and `--line` for each.

**Scenario 3: Comment on a migration file**
```
uv run $HOME/repos/git/personal-automation/others/pr-comment.py owner/api 88 \
  --file migrations/0042_add_index.sql \
  --line 5 \
  --comment "Consider adding a concurrent index to avoid table locking."
```

## Useful Commands Reference

| Command | Description |
|---|---|
| `uv run <script> <owner>/<repo> <pr> --file <f> --line <n> --comment "<text>"` | Post a line-specific PR review comment |
