---
name: ghx
description: >
  Use ghx to perform GitHub pull request and issue comment operations that the
  standard `gh` CLI does not support: inline PR review comments, line-range
  comments, thread replies, pending reviews, local comment stashes, and
  edit/delete of issue and PR comments. Trigger when the user wants to comment
  on a PR (especially inline / on a specific file or line), reply to an existing
  review thread, manage a pending review, stash review comments locally, or
  edit/delete an existing comment.
---

# ghx Skill

`ghx` is an extended GitHub CLI that uses the GitHub GraphQL API directly to
provide PR and issue comment operations beyond what `gh` supports — most
notably inline review comments, line-range comments, thread replies, pending
reviews, and a local "stash" for offline review comments.

---

## Prerequisites

### Binary

Check whether the binary is on PATH; install from the latest release if not:

```bash
if ! command -v ghx &>/dev/null; then
  go install github.com/tomzxcode/ghx@main
fi
```

Pre-built binaries are also available at
<https://github.com/tomzxcode/ghx/releases>.

### Authentication

`ghx` reads `GH_TOKEN` or `GITHUB_TOKEN` from the environment, and falls back
to `gh auth token` (GitHub CLI). Set the token if neither is available:

```bash
export GH_TOKEN=<token>
```

### Target repository

All commands accept `--repo OWNER/REPO` (or `-R`). When omitted, the repo is
auto-detected from the current git remote. Confirm the target before running
write operations:

```bash
git remote get-url origin
```

---

## PR comments

### Top-level comment

```bash
ghx pr comment 42 --body "Looks good"
```

### Inline comment on a single line

```bash
ghx pr comment 42 --file src/main.go --line 10 --body "Nit: use fmt.Errorf"
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

By default the comment is posted immediately. Use `--pending` to attach the
comment to a pending review instead:

```bash
ghx pr comment 42 --file src/main.go --line 10 --body "Nit" --pending
ghx pr comment 42 --reply-thread <thread-id> --body "Reply"   --pending
```

GitHub does not allow mixing immediate and pending review comments on the same
PR. When you submit an immediate inline/reply comment while a pending review
exists, `ghx` automatically stashes the pending comments to disk, posts the
immediate comment, then restores the pending review.

### Stash a comment locally (no API call)

`--stash` saves the comment to a local YAML file under a stash entry instead
of contacting GitHub. Stashes work like `git stash` and support multiple
entries:

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
ghx pr review discard <review-id>        # discard a pending review
```

---

## Review-comment stashes

The stash stores pending-review comments locally so you can post immediate
comments, accumulate review notes offline, or move them between PR states.

```bash
ghx pr review stash push 42                  # save pending -> stash@{0}, delete pending
ghx pr review stash push 42 -m "nit comments"
ghx pr review stash list 42                  # list stash entries for this PR
ghx pr review stash pop  42                  # restore stash@{0} into a pending review
ghx pr review stash pop  42 --stash 1        # restore stash@{1}
ghx pr review stash drop 42                  # discard stash@{0} without restoring
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
```

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

`ghx pr comment edit/delete` and `ghx issue comment edit/delete` operate on
the same underlying GitHub comment types; ghx auto-detects whether a PR
comment id refers to a review comment or an issue comment.

---

## Tips

- For inline review comments on multiple lines, prefer one `--pending`
  comment per location, then `ghx pr review submit` once with the desired
  `--event`. This shows up as a single review on GitHub.
- Use `--stash` (no API call) when iterating on draft feedback you are not
  ready to send.
- Use `ghx pr threads 42 --ids` to recover comment IDs needed by
  `ghx pr comment edit/delete`.
- Read bodies from a file (`--body-file`) for multi-line markdown — easier
  than escaping in the shell.

---

## Wrap up

After completing the user's request, summarise:

1. Which repository and PR/issue was targeted.
2. Whether the comment was posted immediately, added to a pending review, or
   saved to a local stash.
3. The IDs (comment id, thread id, review id) of any objects created, so the
   user can edit/delete/submit later.
