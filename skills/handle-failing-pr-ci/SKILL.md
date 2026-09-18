---
name: handle-failing-pr-ci
description: List your open pull requests and their CI status, then fix failing CI across all of them in parallel by fanning out one handle-pr-ci session per failing PR. Use when the user says /handle-failing-pr-ci, "fix my failing CI", "my PRs have failing checks", "get my PRs green", "check my PRs CI", or wants to bulk-fix CI on their own pull requests.
allowed-tools: Bash(uv run:*, gh:*, git:*, ~/.agents/scripts/my_prs_ci.py:*, opencode run:*), Read, Write, Glob, Grep, Task
argument-hint: "[owner/repo ... | pr-url ...] [--limit N] [--concurrency N] [--exclude-check NAME ...] [--include-check NAME ...]"
---

# Handle Failing PR CI

Lists the current user's open pull requests with their combined CI status, then fixes every PR whose checks are failing by handing each one to its own `handle-pr-ci` session. PRs are independent, so they are processed in parallel: one sub-agent per failing PR, each with its own worktree.

The orchestrator (this session) only discovers work and prepares worktrees. It never edits code. Each failing PR is owned end to end by one sub-agent running `handle-pr-ci`.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `uv` installed (for running the Python script)
- `gh` CLI authenticated with read/write access to the target repositories
- `git` with `git worktree` available
- The `handle-pr-ci` skill available
- Sub-agent dispatch via the `Task` tool (`subagent_type: "general"`). If unavailable, fall back to sequential mode.

## Workflow

```
Run ~/.agents/scripts/my_prs_ci.py --json
              |
              v
  Keep PRs with checks_state == "failing"
              |
              v
  Group by repo, prepare one worktree per failing PR
              |
              v
  Fan out: one general subagent per PR, concurrently
              |
              |   subagent A -> /handle-pr-ci <PR A>   subagent B -> <PR B>   ...
              |      (owns its worktree; diagnoses, fixes, pushes, watches CI)
              |
              v
  Collect VERDICT lines -> summary table
```

## Steps

### 1. Discover my PRs and their CI status

Run the discovery script:

```bash
~/.agents/scripts/my_prs_ci.py $@ --exclude-check "PR Review Bot Comments Addressed" --json
```

The `PR Review Bot Comments Addressed` check is excluded by default because it is a noisy bot gate that does not reflect real CI health. Any `--exclude-check` / `--include-check` the user passes is applied on top of it, and exclusions take precedence, so the bot check stays excluded. To include it in a particular run, scope the query with an explicit PR URL and call the script directly without this skill.

The script accepts the same arguments as the skill:

- No arguments: searches all of your open PRs across GitHub
- `owner/repo` arguments: scopes the search to those repos
- PR URL arguments: processes only those specific PRs

Useful flags:

- `--limit N`: cap the number of PRs discovered (default 100)
- `--draft`: include draft PRs (excluded by default)
- `--workers N`: PRs fetched in parallel (default 8)
- `--exclude-check NAME`: exclude a check from the CI status so an excluded failing check does not make a PR fail. Repeatable, accepts shell-style globs (e.g. `buildkite/*`), case-insensitive. The skill already applies `--exclude-check "PR Review Bot Comments Addressed"`; pass this to exclude additional checks. Excluded checks are dropped during dispatch, so no sub-agent is launched for a PR whose only failures are excluded.
- `--include-check NAME`: the inverse, consider only the named checks and exclude every other check. Repeatable, accepts shell-style globs, case-insensitive. Combining it with `--exclude-check` narrows further (a check must match `--include-check` and not match `--exclude-check`).
- `--only-failing`: show only PRs with failing checks (the JSON output is what matters; use this only when eyeballing)
- `--log-level debug`: see API call timings

For example, to also skip a flaky deploy check across all PRs:

```bash
/handle-failing-pr-ci --exclude-check "buildkite/deploy-smoke"
```

To act only on Buildkite checks and exclude everything else:

```bash
/handle-failing-pr-ci --include-check "buildkite/*"
```

The script emits a JSON array. Each entry has: `repo`, `number`, `title`, `author`, `url`, `draft`, `head_commit`, `head_branch`, `head_repo`, `mergeable`, `review_decision`, `checks_state` (`passing`, `failing`, `pending`, `none`, or `error`), `failing_checks`, `pending_checks`, `excluded_checks`, `total_checks`, `considered_checks`, `error`.

Keep every entry where `checks_state == "failing"` and `error` is empty. These are the PRs to fix.

If there are none, print "No PRs with failing CI." and stop. Optionally show the full table by re-running the script without `--json`.

### 2. Prepare one worktree per failing PR

Each sub-agent must work on the PR's head branch, and multiple PRs may live in the same repository, so prepare a dedicated worktree per PR. The orchestrator does this (single-threaded) so concurrent `git worktree add` calls cannot race on a repository's worktree lock.

Group failing PRs by `repo` (the base repository). For each repo, keep one base clone under a cache directory, then add one worktree per PR:

```bash
CACHE="$HOME/.cache/agents/pr-ci"
BASE="$CACHE/repos/<owner>/<repo>"

# Base clone, reused across runs (bare-ish: no working tree needed)
if [ -d "$BASE/.git" ]; then
  git -C "$BASE" fetch origin --prune
else
  mkdir -p "$(dirname "$BASE")"
  git clone --no-checkout "https://github.com/<owner>/<repo>.git" "$BASE"
fi

# Same-repo PR (head_repo == repo)
git -C "$BASE" fetch origin "+refs/heads/<head_branch>:refs/remotes/origin/<head_branch>"
WT="$CACHE/worktrees/<owner>-<repo>-pr-<number>"
git -C "$BASE" worktree add -B "pr-<number>" "$WT" "origin/<head_branch>"

# Fork PR (head_repo != repo)
git -C "$BASE" fetch "https://github.com/<head_repo>.git" "+refs/heads/<head_branch>:refs/remotes/fork/<head_branch>"
WT="$CACHE/worktrees/<owner>-<repo>-pr-<number>"
git -C "$BASE" worktree add -B "pr-<number>" "$WT" "refs/remotes/fork/<head_branch>"
```

Reuse an existing worktree if `git -C "$BASE" worktree list --porcelain` already has one for `pr-<number>`. If worktree setup fails for a PR, skip it and record "worktree setup failed" in the summary; do not dispatch a sub-agent for it.

Record a task per PR: `{repo, number, head_branch, head_repo, fork, workdir, failing_checks}`.

### 3. Fan out one sub-agent per failing PR

Launch one sub-agent per PR with the `Task` tool, `subagent_type: "general"`. Put **multiple Task calls in a single message** so they run concurrently, in batches of `--concurrency` (default 5). Wait for a batch before starting the next.

Each sub-agent starts with a fresh context, so its prompt must be self-contained. Use this template verbatim, substituting the fields:

```
Run the handle-pr-ci skill for a single pull request, then report the result.

Repository:    <repo>
PR number:     <number>
Head branch:   <head_branch>
Push target:   <"origin" for same-repo, or https://github.com/<head_repo>.git for a fork>
Worktree:      <workdir>   (absolute path; cd here first and stay inside it)
Failing checks: <comma-separated check names>

Steps:
1. cd <workdir>.
2. Run the handle-pr-ci skill for PR #<number>:
   - Fetch current checks:   gh pr checks <number> --repo <repo> --watch=false
   - Fetch each failing log:  gh run view <run-id> --log-failed
   - Diagnose the root cause and implement the fix in this worktree.
3. This run is pre-approved: do NOT pause for approval. Make the smallest fix
   that addresses the root cause, commit, and push to the head branch
   (git push origin HEAD:<head_branch>, or push to the fork URL when the PR is
   from a fork).
4. ABORT and report instead of pushing when:
   - the failure is transient (network, rate limit, timeout) -> rerun the failed
     jobs with `gh run rerun <run-id> --failed` and report "transient";
   - the root cause is unclear or the fix would touch unrelated code -> report
     "needs-manual" with your diagnosis;
   - the same failure keeps recurring after 2 fix attempts -> report "unresolved".
5. After pushing, monitor the re-run until checks settle:
   gh pr checks <number> --repo <repo> --watch
   If new failures appear, loop back to diagnosing (at most 2 further attempts).

Do not create or remove worktrees; the orchestrator owns the worktree lifecycle.
Do not touch any path outside <workdir>.

Return exactly one line as your final answer, nothing else:
VERDICT <status> | PR #<number> | <repo> | <short note>
where <status> is one of: fixed, transient, needs-manual, unresolved, no-failure, error.
```

#### Fallback: no Task tool

If the `Task` tool is unavailable, process each PR sequentially in the current session with `opencode run`:

```bash
opencode run --auto "Run /handle-pr-ci <number> <repo>"
```

This loses the parallelism across PRs. Record in the summary that sequential mode was used.

### 4. Aggregate and report

Collect each sub-agent's final `VERDICT ...` line and print a summary table:

| Repository | PR | Failing checks | Result |
|---|---|---|---|
| owner/repo | #42 | test, lint | Fixed (CI green) |
| owner/repo | #88 | integration-tests | Transient (re-run triggered) |
| owner/repo | #55 | build | Needs-manual (diagnosis in comment) |
| owner/repo | #77 | — | Skipped (worktree setup failed) |
| owner/repo | #33 | — | No failure (checks turned green before dispatch) |

If a sub-agent returns no parseable verdict, surface its raw output and mark that PR as `no-verdict`.

## Example Usage

**Scenario 1: All my PRs, fix every failure**
```
/handle-failing-pr-ci
```
Lists all open PRs. 5 have failing checks across 2 repos. Prepares 5 worktrees and fans out 5 sub-agents. Three push fixes and go green; one is a transient network failure (re-run triggered); one needs manual attention. Summary table printed.

**Scenario 2: Scoped to a repository**
```
/handle-failing-pr-ci acme/api
```
Only searches `acme/api`. Failing PRs there are fixed in parallel.

**Scenario 3: Single PR by URL**
```
/handle-failing-pr-ci https://github.com/acme/api/pull/42
```
Fetches only PR #42. If its checks are failing, one sub-agent is dispatched; otherwise it reports "No PRs with failing CI."

**Scenario 4: Nothing failing**
```
/handle-failing-pr-ci
```
All checks are passing or pending. Reports "No PRs with failing CI." and launches nothing.

**Scenario 5: Bounded parallelism**
```
/handle-failing-pr-ci --concurrency 3
```
12 failing PRs; sub-agents are launched in batches of 3.

## Related Skills

| Skill | Relationship |
|---|---|
| `handle-pr-ci` | Per-PR executor this skill delegates to. Normally asks for approval before pushing; the sub-agent prompt here pre-approves the fix so it can run unattended. |
| `review-requested-prs` | Same fan-out shape, but for reviewing other people's PRs instead of fixing your own CI. |
| `resolve-pr-conflicts` | Same batch-over-my-PRs pattern for merge conflicts; establishes the worktree-per-PR convention used here. |
| `merge-pr` | Merge a PR once its checks are green. |
