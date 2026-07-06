---
name: resolve-pr-conflicts
description: Scan a repository for the current user's open pull requests that have merge conflicts, then resolve each one IN PARALLEL by fanning out to a separate agent session per PR. Each session reuses an existing git worktree or creates a new one, fixes the conflicts, verifies, and pushes. Use when the user says /resolve-pr-conflicts, "fix merge conflicts", "resolve PR conflicts", "my PRs have conflicts", "unblock my PRs", or wants to bulk-resolve merge conflicts on their own pull requests in parallel.
argument-hint: "[owner/repo] [--dry-run] [--limit N] [--concurrency N]"
---

# Resolve PR Conflicts

Finds every open pull request authored by the current user in a repository that has merge conflicts, then resolves each one **in parallel**. The skill is split into two roles:

- **Orchestrator (this session):** scans the repo, detects which of the user's PRs have conflicts, prepares one worktree per conflicting PR (reusing an existing one when present), discovers the project's verification commands once, then fans out to one sub-agent session per PR and aggregates the results.
- **Sub-agent (one per PR, concurrent):** works inside its assigned worktree, merges the base branch, resolves the conflict markers, runs verification, pushes, and posts a comment.

Because the PRs are independent, fixing them in separate concurrent sessions is dramatically faster than sequential resolution. Each sub-agent owns a distinct worktree and a distinct head branch, so there are no filesystem or git-push races.

Designed to be safe to run unattended: ambiguous conflicts and PRs that fail verification are aborted and reported by that PR's sub-agent, never pushed.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `gh` CLI authenticated with write access to the target repository (and to the PR head branches)
- `git worktree` available
- The current git user is the author of the target PRs (`@me`)
- The current working directory is a checkout of the target repository, or a target repo is passed as `owner/repo`
- A sub-agent capable of writing code (use the `general` subagent_type). If sub-agent dispatch is unavailable, fall back to processing PRs sequentially as described in "Fallback: sequential mode".
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `resolve-pr-conflicts`. Each sub-agent appends the same footer for its own PR comment.

## Arguments and Flags

- `$1` (optional): target repository in `owner/repo` form. If omitted, resolved from `gh repo set-default --view`, then from the `origin` remote of the current directory.
- `--dry-run`: each sub-agent resolves and verifies locally, but does NOT push and does NOT post a comment. Worktrees are left for review.
- `--limit N`: maximum number of PRs to scan for conflicts (default `50`). Caps API calls.
- `--concurrency N`: maximum sub-agents running at once (default `5`). The orchestrator launches in batches of this size.

## Parallelization Model

```
ORCHESTRATOR (this session)
  |
  +-- resolve repo, list @me open PRs
  +-- poll mergeable; keep CONFLICTING
  +-- for each conflicting PR (sequential, fast):
  |     reuse or create a worktree  ->  task = {PR, HEAD_REF, BASE_REF, WORKDIR, FORK?}
  +-- discover verification commands once (tests/lint/typecheck)
  +-- fan out: launch one sub-agent per task, CONCURRENTLY, in batches of --concurrency
        |
        |   sub-agent A (worktree A)   sub-agent B (worktree B)   sub-agent C ...
        |     merge origin/<base>        merge origin/<base>         ...
        |     resolve markers            resolve markers             ...
        |     verify (tests/lint)        verify                      ...
        |     commit + push              abort (ambiguous)           ...
        |     comment                    report verdict              ...
        |     return verdict             return verdict              ...
        |
  +-- aggregate all verdicts
  +-- print summary table
```

The orchestrator never edits code or resolves conflicts itself; it only prepares worktrees and dispatches. All per-PR work happens in a dedicated sub-agent so the PRs progress simultaneously.

Worktree creation is done by the orchestrator (not the sub-agents) so concurrent `git worktree add` calls cannot race on the shared `.git` worktree lock. This follows the worktrunk parallel sub-agent pattern: pre-create each worktree, then hand each sub-agent its absolute path.

## Orchestrator Steps

### 1. Resolve the target repository

```bash
REPO="${TARGET_REPO:-}"
[ -z "$REPO" ] && REPO="$(gh repo set-default --view 2>/dev/null)"
[ -z "$REPO" ] && REPO="$(git remote get-url origin | sed -E 's#.*[:/]([^/]+/[^/]+?)(\.git)?$#\1#')"
```

Print the resolved `$REPO`.

### 2. List the current user's open PRs

```bash
gh search prs --author @me --state open --repo "$REPO" \
  --json number,repository,title --limit "${LIMIT:-50}"
```

Record each PR number.

### 3. Detect which PRs have merge conflicts

GitHub computes `mergeable` asynchronously, so it can be `UNKNOWN` right after a push. Poll until it settles.

For each PR:

```bash
gh pr view $PR --repo "$REPO" \
  --json number,headRefName,baseRefName,headRepository,baseRepository,mergeable,mergeStateStatus
```

- If `mergeable == "UNKNOWN"`, wait a few seconds and re-query. Give up after ~30 seconds; treat as "mergeable unknown" (skip, report).
- Keep the PR if `mergeable == "CONFLICTING"` (or `mergeStateStatus == "CONFLICTING"`).

For each kept PR capture: `HEAD_REF`, `BASE_REF`, and whether it is same-repo (`headRepository == baseRepository`) or a fork.

### 4. Prepare one worktree per conflicting PR (reuse or create)

From the repository's main working directory:

```bash
git fetch origin
git fetch origin "$HEAD_REF" 2>/dev/null   # same-repo; may be empty for forks

WT=$(git worktree list --porcelain | awk -v b="refs/heads/$HEAD_REF" '
  $1=="worktree"{p=$2} $1=="branch"&&$2==b{print p; exit}
')
```

- **Worktree exists** (`$WT` non-empty): reuse it. `WORKDIR="$WT"`.
- **No worktree**: create one.
  ```bash
  REPO_BASE=$(basename "$(pwd)")
  WORKDIR="../${REPO_BASE}-pr-${PR}"
  git worktree add "$WORKDIR" "$HEAD_REF"
  ```
  `git worktree add <path> <branch>` checks out the existing local `<branch>`, or auto-creates a local tracking branch from `origin/<branch>` when only the remote-tracking ref exists. If `<branch>` is checked out elsewhere, the reuse path above already handles it.

Build a task record for the PR:

```
TASK = {
  PR, REPO, HEAD_REF, BASE_REF, WORKDIR (absolute),
  FORK: true|false,
  HEAD_REPO_OWNER (for fork push)
}
```

If worktree setup fails for a PR, record it as skipped ("worktree setup failed") and do not dispatch a sub-agent for it.

For fork PRs, create the worktree from the PR ref instead of `origin/<HEAD_REF>`:

```bash
git fetch origin "pull/$PR/head:pr-$PR"
git worktree add "$WORKDIR" "pr-$PR"
```

### 5. Discover verification commands once

Discover the project's test, lint, and typecheck commands the way `improve-codebase` does: `AGENTS.md` / `CLAUDE.md` first (authoritative), then the language manifest (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Makefile`). Record the resolved command strings. These are identical for every worktree (same repo), so they are discovered once and passed into every sub-agent prompt.

If no verification command can be found, still dispatch but pass `VERIFY_COMMANDS=()` and set `NO_VERIFY=true` in each prompt so sub-agents resolve without verification and default to `--dry-run` behavior for their PR (commit locally, do not push) unless the user opted in.

### 6. Fan out: launch one sub-agent per task, concurrently

Launch sub-agents with the `Task` tool, `subagent_type: "general"`. Put **multiple Task calls in a single message** so they run concurrently, in batches of `--concurrency`. Do not wait for one to finish before launching the next within a batch; wait for the batch to complete before launching the next batch.

Each sub-agent receives a fully self-contained prompt (it starts with a fresh context and cannot see this skill). Use the template below, substituting the task fields, the discovered verification commands, and the flags.

#### Sub-agent task prompt template

```
You are resolving merge conflicts on a single pull request. Work ONLY inside
the worktree directory given below; do not touch any other path.

Repository:   {REPO}
PR number:    {PR}
Worktree:     {WORKDIR}        (absolute path; cd here first)
Head branch:  {HEAD_REF}       (push back here)
Base branch:  {BASE_REF}
Fork PR:      {FORK}           (if true, push to git@github.com:{HEAD_REPO_OWNER}/{HEAD_REPO}.git)
Dry run:      {DRY_RUN}        (true: do not push, do not comment)
Verify cmds:  {VERIFY_COMMANDS}  (e.g. "uv run ruff check .", "uv run pytest -q")
               (empty means no verification available)

Steps:
1. cd {WORKDIR} && git fetch origin {BASE_REF}
2. Reproduce the conflict: git merge origin/{BASE_REF} --no-edit
   (the merge will report conflicts; this is expected)
3. List conflicted files: git diff --name-only --diff-filter=U
4. For each conflicted file: read the <<<<<<< ======= >>>>>>> markers,
   understand both sides, edit to the correct resolution (remove all markers),
   git add <file>.
5. AMBIGUITY RULE: only resolve when the correct resolution is unambiguous
   (adjacent additions, one side superset, pure rename/reformat, one side no-op).
   If both sides change the same logic in semantically different ways with no
   clearly-correct union, ABORT: run `git merge --abort`, and return the verdict
   "needs-manual" with the list of files. Never guess on a semantic conflict.
6. Verify (skip only if VERIFY_COMMANDS is empty):
   run each command in {VERIFY_COMMANDS}.
   - green  -> continue
   - red    -> run `git merge --abort`, return verdict "verify-failed" with output
7. Commit the merge: git commit --no-edit
8. Unless DRY_RUN is true:
     - push: git push origin {HEAD_REF}
       (fork: git push git@github.com:{HEAD_REPO_OWNER}/{HEAD_REPO}.git {LOCAL_BRANCH}:{HEAD_REF})
     - post a short comment via gh pr comment {PR} --repo {REPO} with the list of
       resolved files and the resolve-pr-conflicts attribution footer
       (see skills/github-post-attribution/SKILL.md). Never force-push.
9. Return EXACTLY one line in this format, nothing else:
   VERDICT <status> | PR #{PR} | <short note>
   where <status> is one of: pushed, needs-manual, verify-failed, aborted, no-verify
```

Sub-agents must stay inside their assigned `WORKDIR` and must not create or remove worktrees (the orchestrator owns worktree lifecycle).

### 7. Aggregate verdicts and report

Collect each sub-agent's `VERDICT ...` line. Print a summary table:

| PR | Title | Status |
|---|---|---|
| #42 | Add export command | Pushed (2 files) |
| #88 | Refactor cache layer | Needs-manual (semantic conflict in cache.py) |
| #55 | Bump deps | Verify-failed (pytest) |
| #77 | Docs tweak | Skipped (mergeable unknown) |

Include any PRs skipped during orchestration (worktree setup failed, mergeable unknown).

## Fallback: sequential mode

If sub-agent dispatch is unavailable (no Task tool, or the user passes `--sequential`), the orchestrator performs the per-PR work itself, one PR at a time, following the same steps as the sub-agent prompt template above. Print the same summary table at the end.

## Conflict Resolution Rules (applies to every sub-agent)

- Read every `<<<<<<<`, `=======`, `>>>>>>>` block before editing. Understand what each side changed.
- Prefer a resolution that preserves both sides' intent (both edits apply, or one trivially supersedes).
- **Ambiguity rule (non-negotiable):** only auto-resolve unambiguous conflicts (adjacent additions, one side a superset, pure rename/reformat, one side a no-op given the other). If both sides change the same logic in semantically different ways with no clearly-correct union, abort with `git merge --abort` and report "needs-manual". Never guess on a semantic conflict.
- Remove ALL conflict markers; never leave a `<<<<<<<` in a pushed file.
- Never force-push. The merge commit is a normal addition to the head branch.

## Failure Modes

| Mode | Where handled | Response |
|---|---|---|
| **Semantic / ambiguous conflict** | sub-agent | `git merge --abort`, verdict `needs-manual` |
| **Verification fails after resolution** | sub-agent | `git merge --abort`, verdict `verify-failed` |
| **`mergeable` stays UNKNOWN** | orchestrator | Skip PR before dispatch, report "mergeable unknown" |
| **Worktree creation fails** | orchestrator | Skip PR before dispatch, report "worktree setup failed" |
| **No push access to fork head** | sub-agent | Skip push, verdict `aborted` |
| **Head branch checked out in main worktree** | orchestrator | Reuse the main worktree as the existing worktree |
| **Sub-agent returns no parseable verdict** | orchestrator | Report that PR as "no-verdict", surface raw output |

## Example Usage

**Scenario 1: Parallel unblock (default)**
```
/resolve-pr-conflicts
```
Scans the current repo. 4 of my 8 open PRs have conflicts. The orchestrator prepares 4 worktrees and launches 4 sub-agents (batch of 5, so all at once). Two resolve cleanly and push; one is a semantic conflict (needs-manual); one fails pytest (verify-failed). Summary table printed. Wall-clock is roughly the slowest single PR, not the sum.

**Scenario 2: Scoped to a specific repo, bounded parallelism**
```
/resolve-pr-conflicts acme/api --concurrency 3
```
9 conflicting PRs. Orchestrator creates 9 worktrees, launches sub-agents in batches of 3.

**Scenario 3: Dry run before trusting it**
```
/resolve-pr-conflicts --dry-run
```
Each sub-agent resolves and verifies but commits locally without pushing or commenting. Review the worktrees before a real run.

**Scenario 4: Reuses existing worktrees**
```
/resolve-pr-conflicts
```
PR #207's head branch `feature-billing` already has a worktree at `../api-pr-207` from an earlier session. `git worktree list` finds it; that sub-agent operates there instead of creating a new one.

**Scenario 5: Nothing to do**
```
/resolve-pr-conflicts
```
All my open PRs are mergeable. Report "No conflicting PRs found." No sub-agents launched.

**Scenario 6: No sub-agent dispatch available**
```
/resolve-pr-conflicts --sequential
```
Falls back to sequential processing in the current session, same resolution rules and summary.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `handle-pr-ci` | Fixes failing CI on a single PR. This skill fixes merge conflicts (a different blocker) across all of the user's PRs, in parallel. |
| `merge-pr` | Merges a PR after approvals and CI are green. Run this first to clear conflicts, then `merge-pr`. |
| `quick-pr-reviews` | Same batch-over-my-PRs shape, but for reviewing PRs others asked you to review. This is the analog for unblocking your own PRs. |
| `reproduce-issue` / `validate-pr` | Establish the worktree naming and reuse conventions this skill follows. |
| `improve-codebase` | Same "discover verification commands, run before pushing" safety pattern. |
| `worktrunk` | Documents the parallel sub-agent worktree pattern (`wt switch --create <branch> --no-cd --no-hooks`, then hand each sub-agent its path) this skill generalizes with plain `git worktree`. |

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh search prs --author @me --state open --repo <owner/repo> --json number,title` | List the current user's open PRs in a repo |
| `gh pr view <pr> --json mergeable,mergeStateStatus,headRefName,baseRefName,headRepository,baseRepository` | Detect conflicts and fetch branch names (poll if `mergeable` is `UNKNOWN`) |
| `git worktree list --porcelain` | Find an existing worktree on a branch (reuse path) |
| `git worktree add <path> <branch>` | Create a worktree on a PR head branch (orchestrator only) |
| `git merge origin/<base> --no-edit` | Reproduce the conflict by merging the base branch (sub-agent) |
| `git diff --name-only --diff-filter=U` | List files with unresolved conflict markers |
| `git merge --abort` | Discard an ambiguous or verify-failing resolution (sub-agent) |
| `Task(subagent_type=general, ...)` | Launch one concurrent resolver session per PR |
