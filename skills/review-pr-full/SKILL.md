---
name: review-pr-full
description: Orchestrate a full PR review (validate-pr, verify-pr, review-pr) for a single PR. Skips steps already completed for the current commit. Accepts a PR URL or a PR number with optional repository.
allowed-tools: Bash(uv run:*, gh:*, git:*, ~/.agents/scripts/review_requested_prs.py:*), Task
argument-hint: "<pr-number> [repository] | <pr-url>"
---

# Review PR Full

Runs the complete three-step review pipeline on a single PR: `/validate-pr` (are we building the right product?), then `/verify-pr` (does it conform to the acceptance criteria?), then `/review-pr` (is the code well-crafted?). Each step posts its own report and marks the commit it reviewed.

Staleness checking is handled by the same deterministic Python script used by `review-requested-prs` (`~/.agents/scripts/review_requested_prs.py`). It checks both GitHub PR comments and local report files at `~/.sdlc/<owner>/<repo>/pull-requests/<pr>/` for markers, so it works even when `should-post-to-github` has disabled posting. Only stale steps are run, so re-running after a partial completion picks up where it left off.

## Prerequisites

- `uv` installed (for running the Python script)
- `gh` CLI authenticated (used by the script as a token fallback)
- `validate-pr`, `verify-pr`, and `review-pr` skills available

## Workflow

```
Resolve PR argument (URL or number + repo)
                |
                v
Run ~/.agents/scripts/review_requested_prs.py --dispatch
                |
                v
  Parse dispatch commands (stale steps for this PR)
                |
                v
  Any stale steps?
   /          \
  No           Yes
   |             |
   v             v
 Report       Create shared worktree
 "up to          |
 date"           v
            Run stale steps sequentially:
              validate-pr -> verify-pr -> review-pr
            Check for blocking verdict after each step
                |
                v
            Clean up worktree
                |
                v
            Report summary
```

## Steps

### 1. Resolve the PR argument

Accept one of:
- A PR URL: `https://github.com/owner/repo/pull/42`
- A PR number with a repository: `42 owner/repo`
- A PR number alone: `42` (uses `$REPO` from the environment)

If a PR URL is given, pass it directly to the script. If a PR number and repo are given, construct the URL:

```bash
PR_URL="https://github.com/${REPO}/pull/${PR_NUMBER}"
```

If only a PR number is given and `$REPO` is not set, stop and ask for the repository.

### 2. Run the staleness script

Run the script to determine which steps are stale for this PR:

```bash
~/.agents/scripts/review_requested_prs.py "$PR_URL" --dispatch
```

The `--dispatch` flag makes the script output one command per line for each stale step, in execution order:

```
/validate-pr 42 acme/api
/verify-pr 42 acme/api
/review-pr 42 acme/api
```

If the script outputs nothing, all steps are up to date for the current commit. Report "All review steps are up to date for PR #N in owner/repo" and stop.

Each line has the format:

```
/{skill} {PR_NUMBER} {REPO}
```

The steps are already in the correct execution order (validate-pr before verify-pr before review-pr).

### 3. Create the shared worktree

Before dispatching the first stale step, fetch the PR's head branch and create a worktree that all stale steps will reuse:

```bash
gh pr view $PR_NUMBER --repo $REPO --json headRefName --jq '.headRefName'
```

```bash
ISSUE_NUMBER=$(gh pr view $PR_NUMBER --repo $REPO --json closingIssuesReferences --jq '.closingIssuesReferences[0].number // empty')
WORKTREE_DIR=/tmp/sdlc/$REPO/${ISSUE_NUMBER:-pr-$PR_NUMBER}
mkdir -p /tmp/sdlc/$REPO
git fetch origin $HEAD_BRANCH
git worktree add $WORKTREE_DIR origin/$HEAD_BRANCH
```

If the worktree already exists (e.g. from a previous run), skip creation and reuse it.

### 4. Dispatch stale review steps

Dispatch each stale skill as a subagent task via the Task tool. The subagent prompt MUST be the exact skill invocation command, not a paraphrased or self-authored description. Do not let the orchestrator generate its own task description, pass the literal command string below as the subagent prompt. Include the `WORKTREE_DIR` so the sub-skill reuses the shared worktree instead of creating its own.

Use the `general` subagent type for all three steps.

Steps run sequentially (validate-pr, then verify-pr, then review-pr), waiting for each subagent to finish before starting the next. Do not parallelize steps, because each step may halt the pipeline. Each sub-skill reuses the shared worktree, runs its analysis, and posts a comment (or writes locally when posting is disabled) with the commit SHA marker.

#### validate-pr

Dispatch a subagent with this exact prompt:

```
Run the validate-pr skill: /validate-pr {PR} {REPO}
The worktree is already created at {WORKTREE_DIR}. Set WORKTREE_DIR to that path so the skill reuses it and does not create or remove its own worktree.
```

If validate-pr returns a **Wrong thing** verdict, stop. Do not run verify-pr or review-pr, because verifying conformance to, or the craft of, the wrong target is wasted effort. Record the failure in the summary.

#### verify-pr

Only dispatch if validate-pr passed (or was already up to date and is not stale). Dispatch a subagent with this exact prompt:

```
Run the verify-pr skill: /verify-pr {PR} {REPO}
The worktree is already created at {WORKTREE_DIR}. Set WORKTREE_DIR to that path so the skill reuses it and does not create or remove its own worktree.
```

If verify-pr fails (e.g. build failure, no linked issue), the sub-skill notes the failure and stops; it posts a comment for missing issues or criteria, but not for build failures (CI typically catches those). Do not run review-pr. Record the failure in the summary.

#### review-pr

Only dispatch if verify-pr passed (or was already up to date and is not stale). Dispatch a subagent with this exact prompt:

```
Run the review-pr skill: /review-pr {PR} {REPO}
The worktree is already created at {WORKTREE_DIR}. Set WORKTREE_DIR to that path so the skill reuses it and does not create or remove its own worktree.
```

### 5. Clean up the shared worktree

After all stale steps complete (or the pipeline halts), remove the shared worktree:

```bash
git worktree remove $WORKTREE_DIR
```

### 6. Report summary

After processing, output a summary:

| Repository | PR | Steps run | Result |
|---|---|---|---|
| owner/repo | #42 | validate, verify, review | Completed |
| owner/repo | #42 | verify, review | Completed (validate up to date) |
| owner/repo | #42 | review | Completed (validate, verify up to date) |
| owner/repo | #42 | — | Skipped (all up to date) |
| owner/repo | #42 | validate | Stopped at validate (wrong product) |
| owner/repo | #42 | validate, verify | Stopped at verify (build failure) |

## Example Usage

**Scenario 1: Fresh PR, all three steps needed**
```
/review-pr-full 42 acme/api
```
No prior markers found. Runs validate-pr, verify-pr, and review-pr in sequence. All pass. Summary shows "Completed".

**Scenario 2: PR URL**
```
/review-pr-full https://github.com/acme/api/pull/42
```
Same as Scenario 1 but using a PR URL.

**Scenario 3: Partial completion, re-run**
```
/review-pr-full 42 acme/api
```
validate-pr and verify-pr markers match HEAD, but review-pr is stale. Runs only `/review-pr 42 acme/api`. Summary shows "Completed (validate, verify up to date)".

**Scenario 4: All steps up to date**
```
/review-pr-full 42 acme/api
```
All three markers match HEAD. Script outputs nothing. Reports "All review steps are up to date for PR #42 in acme/api".

**Scenario 5: validate-pr returns Wrong thing**
```
/review-pr-full 15 acme/api
```
validate-pr judges the PR to be the wrong product. It posts its Wrong-thing verdict. verify-pr and review-pr are not run. Summary shows "Stopped at validate (wrong product)".

**Scenario 6: verify-pr build failure**
```
/review-pr-full 88 acme/api
```
validate-pr passes. verify-pr fails to build. Notes the build failure and stops (CI would typically catch this). review-pr is not run. Summary shows "Stopped at verify (build failure)".

**Scenario 7: PR number with $REPO from environment**
```
/review-pr-full 42
```
`$REPO` is set in the environment. Uses it as the repository. Runs the pipeline.

## Script Reference

| Script | Description |
|---|---|
| `~/.agents/scripts/review_requested_prs.py` | Discovers PRs, checks marker staleness (GitHub comments + local `.sdlc` files), outputs dispatch commands. Run with `--dispatch` for command output, `--json` for structured data, `--log-level debug` for timings. Pass a single PR URL to scope it to one PR. |

## Related Skills

| Skill | Relationship |
|---|---|
| `review-requested-prs` | Multi-PR counterpart: discovers all review-requested PRs and runs the same pipeline across each in parallel. Use that when reviewing your queue; use this skill for a single PR. |
| `validate-pr` | Needs-alignment sub-skill (does the PR solve the right problem; are the acceptance criteria sound). Build-free early gate. |
| `verify-pr` | Conformance sub-skill (criteria-to-code traceability plus runtime proof that each criterion is met). Owns the build. |
| `review-pr` | Code-craft sub-skill (quality, architecture, security, tests, operational concerns). |
| `quick-pr-review` | Lightweight counterpart: rapid auto-approve to unblock. Use this skill when you need deep review, not rapid unblocking. |
