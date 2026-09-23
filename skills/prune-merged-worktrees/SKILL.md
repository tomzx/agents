---
name: prune-merged-worktrees
description: Remove local git worktrees (and their branches) whose associated pull request was merged, verifying merge state against GitHub instead of git ancestry. Use when the user says /prune-merged-worktrees, "prune worktrees", "clean up merged worktrees", "remove worktrees for merged PRs", or wants stale worktree cleanup after merges.
argument-hint: "[repo-path] [--dry-run] [--force]"
---

# Prune Merged Worktrees

Finds local git worktrees whose branch's remote was deleted, verifies through GitHub that the branch's pull request was actually merged, then removes the worktree and the local branch after user confirmation.
Verification goes through the forge because squash and rebase merges (the `/merge-pr` default) land the work under a new SHA, so `git branch -d`, `git merge-base --is-ancestor`, and `git rev-list main..<branch>` all misclassify fully shipped branches as unmerged.

## Prerequisites

- Current working directory is a checkout of the target repository, or a repo path is passed as `$1`
- `git worktree` available
- `ghx` (preferred) or `gh` CLI authenticated with access to the repository
- The skill never removes the main checkout, a bare entry, or the worktree containing the current directory

## Arguments and Flags

- `$1` (optional): path to the repository checkout (default: current directory)
- `--dry-run`: print the classification table and exit without removing anything
- `--force`: allow removing worktrees with uncommitted changes; without it, dirty worktrees are reported and skipped

## Steps

### 1. List worktrees and candidates

```
git -C <repo> worktree list --porcelain
```

Skip the main checkout (the first entry) and any worktree containing the current directory.
For each remaining worktree, read its branch from the `branch` line.

### 2. Fetch and find stale branches

```
git -C <repo> fetch --prune origin
git -C <repo> branch -vv
```

A worktree is a candidate only when its branch's upstream is `gone` (the remote branch was deleted, typically by the merge).
Worktrees whose upstream still exists (open PRs, shared branches) are kept.
Worktrees on branches with no upstream at all were never pushed, so there is no PR to verify: report them as skipped.

### 3. Verify merge state against GitHub

For each candidate branch, list merged PRs from that head, preferring `ghx` and falling back to `gh`:

```
ghx pr list --state merged --head <branch> --json number,headRefOid,mergedAt
gh pr list --state merged --head <branch> --json number,headRefOid,mergedAt
```

Compare the newest merged PR's `headRefOid` with the local tip (`git rev-parse <branch>`) and classify:

- **Merged (verified)**: a merged PR exists and its head SHA equals the local tip, so nothing was added to the branch after the merge. Safe to remove.
- **At risk**: no merged PR for that head, or the local tip differs from the PR head (commits after the merge). Keep the worktree and report why.
- **Unverifiable**: `ghx`/`gh` is unavailable or unauthenticated. Treat every candidate as at risk, say that verification was impossible, and stop before any deletion.

Gone upstream alone never proves the work shipped: a branch can be deleted on the remote while still holding unmerged commits.

### 4. Check each verified worktree for dirty state

```
git -C <worktree-path> status --porcelain
```

Classify each merged worktree as clean (removable) or dirty (removable only with `--force` or explicit approval).

### 5. Present the plan and confirm

| Worktree | Branch | PR | State | Action |
|---|---|---|---|---|
| `<path>` | `<branch>` | #42 | clean, merged | remove |
| `<path>` | `<branch>` | #17 | dirty, 3 changes | remove with `--force`, or skip |
| `<path>` | `<branch>` | none, or tip differs from PR head | at risk | keep |

Call out the at-risk rows explicitly so the decision is made with the merge state in view.
On `--dry-run`, print the table and stop.
Otherwise wait for the user's confirmation before deleting anything.

### 6. Remove confirmed worktrees and branches

```
git -C <repo> worktree remove <path>
git -C <repo> branch -D <branch>
git -C <repo> tag -d "prs/<pr-number>/review" 2>/dev/null || true
```

Add `--force` to `worktree remove` only for dirty worktrees the user explicitly approved.
Use `-D` and not `-d`: a squash or rebase merge makes `-d` refuse to delete a fully shipped branch.
The tag deletion cleans up the review checkpoint left by validate-pr, verify-pr, and review-pr (see `sdlc/references/shared.md`, Review checkpoint tags), which matters when the PR was merged from another machine or through the UI.
Then prune orphaned worktree metadata:

```
git -C <repo> worktree prune -v
```

### 7. Report

Summarize what was removed, what was kept and why, and anything skipped.

## Output Format

```
Pruned N worktrees in <repo>:

| Worktree | Branch | PR | Result |
|---|---|---|---|
| <path> | <branch> | #42 | removed (clean, merged) |
| <path> | <branch> | #17 | removed (dirty, force approved) |
| <path> | <branch> | at risk | kept (tip differs from PR #9 head) |
| <path> | <branch> | none | skipped (never pushed) |

Branches deleted: <branch>, <branch>
Review tags deleted: prs/42/review
```

If everything was already clean, report "nothing to prune" with the count of worktrees inspected.

## Example Usage

**Scenario 1: Routine cleanup after a batch of merges**
```
/prune-merged-worktrees
```
Three worktrees exist, two branches are `gone` upstream, both have merged PRs whose head SHAs match the local tips, both worktrees are clean. Present the table, get confirmation, remove both worktrees, delete both branches with `-D`, delete the `prs/<n>/review` tags, run `git worktree prune -v`.

**Scenario 2: Dirty worktree on a merged branch**
```
/prune-merged-worktrees --force
```
PR #17 is merged but the worktree holds 3 uncommitted files. With `--force` the worktree is removed after the user confirms the summary table; without `--force` it would be reported and skipped.

**Scenario 3: Squash-merged branch that git thinks is unmerged**
```
/prune-merged-worktrees
```
`git branch -d` would refuse and `git rev-list main..<branch>` shows commits, because the squash merge created a new SHA. `ghx pr list --state merged --head <branch>` finds merged PR #23 with `headRefOid` equal to the local tip, so the branch is classified merged (verified) and pruned.

**Scenario 4: Commits added after the merge**
```
/prune-merged-worktrees
```
PR #9 is merged, but the local tip differs from the PR head: someone committed to the branch after the merge. The worktree is classified at risk, kept, and surfaced in the report for a human decision.

## Useful Commands Reference

| Command | Description |
|---|---|
| `git worktree list --porcelain` | List worktrees with their branches |
| `git fetch --prune origin` | Refresh remote refs and drop deleted branches |
| `ghx pr list --state merged --head <branch> --json number,headRefOid,mergedAt` | Find merged PRs for a head branch |
| `git worktree remove <path>` | Remove a worktree (`--force` for dirty ones) |
| `git branch -D <branch>` | Delete a local branch whose merge was squashed |
| `git tag -d "prs/<pr-number>/review"` | Delete the review checkpoint tag after merging |
| `git worktree prune -v` | Remove orphaned worktree metadata |
