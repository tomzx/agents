---
name: review-requested-prs
description: Orchestrate full PR reviews (validate-pr, verify-pr, review-pr) across all PRs where you are a requested reviewer, or on a specific PR by URL. Skips steps already completed for the current commit.
allowed-tools: Bash(uv run:*, gh:*, git:*), Task
argument-hint: "[pr-url ... | owner/repo ...]"
---

# Review Requested PRs

Finds all open PRs where you are a requested reviewer (or accepts specific PR URLs), checks each one for commits that are newer than the latest validate-pr / verify-pr / review-pr marker, and runs only the stale review steps in order: `/validate-pr`, then `/verify-pr`, then `/review-pr`.

The discovery and staleness check are handled by a deterministic Python script (`scripts/review_requested_prs.py`). The script checks both GitHub PR comments and local report files at `~/.sdlc/<owner>/<repo>/pull-requests/<pr>/` for markers, so it works even when `should-post-to-github` has disabled posting. The LLM orchestrator consumes the script's output and dispatches the stale steps as subagent tasks.

## Prerequisites

- `uv` installed (for running the Python script)
- `gh` CLI authenticated (used by the script as a token fallback)
- `validate-pr`, `verify-pr`, and `review-pr` skills available

## Workflow

```
Run scripts/review_requested_prs.py --dispatch
               |
               v
    Parse dispatch commands output
  (one /skill command per stale step)
               |
               v
    Group commands by PR
               |
               v
    For each PR (in parallel):
      Create shared worktree
      Run stale steps sequentially:
        validate-pr -> verify-pr -> review-pr
      Check for blocking verdict after each step
      Clean up worktree
               |
               v
    Report summary
```

## Steps

### 1. Run the discovery script

Run the script to discover PRs and determine which steps are stale:

```bash
uv run scripts/review_requested_prs.py $@ --dispatch
```

The script accepts the same arguments as the skill:
- No arguments: searches all open PRs where you are a requested reviewer
- `owner/repo` arguments: scopes the search to those repos
- PR URL arguments: processes only those specific PRs
- Mixed: processes the union of explicit PRs and search results

Useful flags:
- `--limit N`: cap the number of PRs discovered (default 100)
- `--log-level debug`: see API call timings for debugging
- `--workers N`: number of PRs to process in parallel for staleness checks (default 8)

The `--dispatch` flag makes the script output one command per line for each stale step, in execution order:

```
/validate-pr 42 acme/api
/verify-pr 42 acme/api
/review-pr 42 acme/api
/validate-pr 88 acme/web-app
/verify-pr 88 acme/web-app
/review-pr 88 acme/web-app
```

If the script outputs nothing, all PRs are up to date and no work is needed.

### 2. Parse dispatch commands

Parse the script output into a per-PR plan. Each line has the format:

```
/{skill} {PR_NUMBER} {REPO}
```

Group lines by `(REPO, PR_NUMBER)` to get the ordered list of stale steps per PR. The steps within each PR are already in the correct execution order (validate-pr before verify-pr before review-pr).

### 3. Run stale review steps

For each PR that needs processing, create a shared git worktree once and reuse it across all stale steps for that PR.

#### 3a. Create the shared worktree

Before dispatching the first stale step for a PR, fetch the PR's head branch and create the worktree:

```bash
git fetch origin $HEAD_BRANCH
WORKTREE_DIR=/tmp/sdlc/$REPO/${ISSUE_NUMBER:-pr-$PR_NUMBER}
mkdir -p /tmp/sdlc/$REPO
git worktree add $WORKTREE_DIR origin/$HEAD_BRANCH
```

If the worktree already exists (e.g. from a previous run), skip creation and reuse it.

#### 3b. Dispatch stale steps

Dispatch each stale skill as a subagent task via the Task tool. The subagent prompt MUST be the exact skill invocation command, not a paraphrased or self-authored description. Do not let the orchestrator generate its own task description, pass the literal command string below as the subagent prompt. Include the `WORKTREE_DIR` so the sub-skill reuses the shared worktree instead of creating its own.

Use the `general` subagent type for all three steps.

#### validate-pr

Dispatch a subagent with this exact prompt:

```
Run the validate-pr skill: /validate-pr {PR} {REPO}
The worktree is already created at {WORKTREE_DIR}. Set WORKTREE_DIR to that path so the skill reuses it and does not create or remove its own worktree.
```

#### verify-pr

Dispatch a subagent with this exact prompt:

```
Run the verify-pr skill: /verify-pr {PR} {REPO}
The worktree is already created at {WORKTREE_DIR}. Set WORKTREE_DIR to that path so the skill reuses it and does not create or remove its own worktree.
```

#### review-pr

Dispatch a subagent with this exact prompt:

```
Run the review-pr skill: /review-pr {PR} {REPO}
The worktree is already created at {WORKTREE_DIR}. Set WORKTREE_DIR to that path so the skill reuses it and does not create or remove its own worktree.
```

Process PRs in parallel by dispatching one subagent per PR in a single message with multiple Task tool calls. Each PR is independent, so all PRs run concurrently. Within a PR, steps run sequentially (validate-pr, then verify-pr, then review-pr), waiting for each subagent to finish before starting the next. Do not parallelize steps within a single PR, because each step may halt the pipeline. Each sub-skill reuses the shared worktree, runs its analysis, and posts a comment (or writes locally when posting is disabled) with the commit SHA marker.

If a step fails (e.g. build failure in verify-pr, no linked issue), the sub-skill posts a comment explaining the failure and stops. Do not run subsequent steps for that PR. Record the failure in the summary. Treat a blocking verdict from any step the same way: a **Wrong thing** verdict from `validate-pr` (the target is the wrong product) should halt the pipeline before `verify-pr` spends a build, since verifying conformance to a wrong spec is wasted effort.

#### 3c. Clean up the shared worktree

After all stale steps for a PR complete (or the pipeline halts), remove the shared worktree:

```bash
git worktree remove $WORKTREE_DIR
```

### 4. Report summary

After processing all PRs, output a summary table:

| Repository | PR | Steps run | Result |
|---|---|---|---|
| owner/repo | #42 | validate, verify, review | Completed |
| owner/repo | #88 | verify, review | Completed |
| owner/repo | #55 | review | Completed |
| owner/repo | #77 | validate, verify, review | Failed at validate (build error) |
| owner/repo | #33 | — | Skipped (all up to date) |

## Example Usage

**Scenario 1: No arguments, all review-requested PRs**
```
/review-requested-prs
```
Finds 4 open PRs across multiple repos. 1 is fully reviewed already (skipped), 2 need all three steps, 1 needs only review-pr. Runs the stale steps on each.

**Scenario 2: Filter to specific repositories**
```
/review-requested-prs acme/api acme/web-app
```
Searches only those two repos. Finds 2 PRs in `acme/api` and 1 in `acme/web-app`. Runs stale steps on each.

**Scenario 3: Single PR by URL**
```
/review-requested-prs https://github.com/acme/api/pull/42
```
Processes only PR #42 in `acme/api`. Checks markers: validate-pr and verify-pr are current, review-pr is stale. Runs only `/review-pr 42 acme/api`.

**Scenario 4: Multiple PR URLs**
```
/review-requested-prs https://github.com/acme/api/pull/42 https://github.com/acme/web-app/pull/88
```
Processes exactly those two PRs. No search is performed.

**Scenario 5: All PRs already reviewed**
```
/review-requested-prs
```
The script outputs nothing (all markers match HEAD). Reports all as skipped.

**Scenario 6: PR with no prior reviews**
```
/review-requested-prs acme/api
```
A PR has no validate-pr, verify-pr, or review-pr comments or local files. Runs all three in sequence.

**Scenario 7: validate-pr returns Wrong thing**
```
/review-requested-prs https://github.com/acme/api/pull/15
```
validate-pr judges the PR to be the wrong product (the need is not addressed). It posts its Wrong-thing verdict. verify-pr and review-pr are not run, because verifying conformance to, or the craft of, the wrong target is wasted effort. Summary shows "Stopped at validate (wrong product)".

**Scenario 8: Mixed URL and repo arguments**
```
/review-requested-prs https://github.com/acme/api/pull/42 acme/web-app
```
Processes PR #42 in acme/api explicitly, plus searches acme/web-app for review-requested PRs. Processes the union.

## Script Reference

| Script | Description |
|---|---|
| `scripts/review_requested_prs.py` | Discovers PRs, checks marker staleness (GitHub comments + local `.sdlc` files), outputs dispatch commands. Run with `--dispatch` for command output, `--json` for structured data, `--log-level debug` for timings. |

## Related Skills

| Skill | Relationship |
|---|---|
| `quick-pr-reviews` | Lightweight counterpart: runs `quick-pr-review` (auto-approve) on changed PRs. Use this skill when you need rapid unblocking, not deep review. |
| `validate-pr` | Needs-alignment sub-skill (does the PR solve the right problem; are the acceptance criteria sound). Build-free early gate. |
| `verify-pr` | Conformance sub-skill (criteria-to-code traceability plus runtime proof that each criterion is met). Owns the build. |
| `review-pr` | Code-craft sub-skill (quality, architecture, security, tests, operational concerns). |
