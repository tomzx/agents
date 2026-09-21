---
name: review-pr-full
description: Orchestrate a full PR review for a single PR, running assess-pr-risk in parallel with the analyze-test-coverage -> validate-pr -> verify-pr -> review-pr chain. Skips steps already completed for the current commit. Accepts a PR URL or a PR number with optional repository.
allowed-tools: Bash(uv run:*, gh:*, git:*, ~/.agents/scripts/review_requested_prs.py:*), Task
argument-hint: "<pr-number> [repository] | <pr-url>"
---

# Review PR Full

Runs the complete review pipeline on a single PR: `/assess-pr-risk` (how risky is this change, how confident is that estimate) dispatched in parallel with the sequential chain `/analyze-test-coverage` (is the change well covered by tests?), then `/validate-pr` (are we building the right product?), then `/verify-pr` (does it conform to the acceptance criteria?), then `/review-pr` (is the code well-crafted?). Each step posts its own report and marks the commit it reviewed.

`/analyze-test-coverage` runs as the first chain step so the coverage determination is explicit, tracked, and available before anything else judges the change: it is cheap static analysis, its report is posted before the rest of the chain starts, and the later steps (`validate-pr`, `verify-pr`, `review-pr`, and the concurrent `assess-pr-risk`) can read it as evidence. `verify-pr` and `review-pr` also embed parts of the coverage analysis in their own reports; the standalone step guarantees the introduced-tests / change-coverage / uncovered-code determination exists for the current commit even when the chain halts early. It never halts the pipeline: a `fail` verdict (uncovered changes found) is reported in the summary for the human reviewer, who decides what to do with it.

The risk assessment is independent of the chain: it never halts the chain and is never halted by it. Its verdict token (`fast-track` / `confirm` / `investigate` / `decide` / `block` / `hold`) is advisory for the human reviewer, and because it runs early it reads whichever sibling reports exist when it gathers evidence, saying in its report what would raise its confidence.

Staleness checking is handled by the same deterministic Python script used by `review-requested-prs` (`~/.agents/scripts/review_requested_prs.py`). It checks both GitHub PR comments and local report files at `~/.sdlc/<owner>/<repo>/pull-requests/<pr>/` for markers, so it works even when `should-post-to-github` has disabled posting. Only stale steps are run, so re-running after a partial completion picks up where it left off.

When called by `review-requested-prs`, the staleness check and head-ref resolution have already been done. The caller passes them as `--steps`, `--head-repo`, and `--head-branch`, and this skill skips its own GitHub queries and starts the checks immediately. This keeps the parent orchestrator from being the bottleneck: one `review-pr-full` session owns each PR end to end.

## Prerequisites

- `uv` installed (for running the Python script)
- `gh` CLI authenticated (used by the script as a token fallback)
- `validate-pr`, `verify-pr`, `review-pr`, `analyze-test-coverage`, and `assess-pr-risk` skills available

## Workflow

```
Resolve PR argument (URL or number + repo)
                |
                v
   Precomputed plan given?
     (--steps passed)
    /          \
   No           Yes
    |             |
    v             v
Run script    Use STALE_STEPS as-is
--dispatch    (skip GitHub staleness check)
    |             |
    +------+------+
           |
           v
  Parse stale steps for this PR
           |
           v
  Any stale steps?
   /          \
  No           Yes
   |             |
   v             v
Report       Create shared worktree
"up to          |  (use --head-repo/--head-branch when given,
date"           |   else resolve via gh pr view)
                |
                v
            Dispatch stale steps:
              assess-pr-risk concurrently
              with the chain:
              analyze-test-coverage -> validate-pr
              -> verify-pr -> review-pr
            Check for blocking verdict after each chain step
                |
                v
            Clean up worktree
                |
                v
            Emit VERDICT line + summary
```

## Steps

### 1. Resolve the PR argument

Accept one of:
- A PR URL: `https://github.com/owner/repo/pull/42`
- A PR number with a repository: `42 owner/repo`
- A PR number alone: `42` (uses `$REPO` from the environment)

Optional precomputed arguments, normally supplied by `review-requested-prs`:
- `--steps a,b,c`: comma-separated list of the stale steps to run, already ordered and already trimmed of steps blocked by an earlier failed step. When present, step 2 is skipped entirely.
- `--head-repo owner/repo`: the PR head repository (the fork for cross-repository PRs). When present, step 3 uses it instead of calling `gh pr view`.
- `--head-branch name`: the PR head branch. When present, step 3 uses it instead of calling `gh pr view`.

Treat a precomputed plan as authoritative: do not re-run discovery or the staleness script, and do not call GitHub for staleness or PR status. It was computed against the same HEAD moments earlier.

If a PR URL is given, pass it directly to the script. If a PR number and repo are given, construct the URL:

```bash
PR_URL="https://github.com/${REPO}/pull/${PR_NUMBER}"
```

If only a PR number is given and `$REPO` is not set, stop and ask for the repository.

### 2. Run the staleness script

**Skip this step when `--steps` was provided.** Set `STALE_STEPS` from the flag and continue to step 3.

Otherwise, run the script to determine which steps are stale for this PR:

```bash
~/.agents/scripts/review_requested_prs.py "$PR_URL" --dispatch
```

The `--dispatch` flag makes the script output one command per line for each stale step, in execution order:

```
/assess-pr-risk 42 acme/api
/analyze-test-coverage 42 acme/api
/validate-pr 42 acme/api
/verify-pr 42 acme/api
/review-pr 42 acme/api
```

If the script outputs nothing, all steps are up to date for the current commit. Report "All review steps are up to date for PR #N in owner/repo" and stop.

Each line has the format:

```
/{skill} {PR_NUMBER} {REPO}
```

The steps are already in the correct execution order. `assess-pr-risk` is listed first so it can be dispatched concurrently with the first stale chain step; the chain steps follow in their sequential order (analyze-test-coverage before validate-pr before verify-pr before review-pr). Set `STALE_STEPS` to the ordered list of step names.

### 3. Create the shared worktree

Before dispatching the first stale step, resolve where the PR's head lives. The head may be on a fork rather than the base repository, so query the head repository up front instead of assuming `origin`:

```bash
gh pr view $PR_NUMBER --repo $REPO --json headRefName,headRepository --jq '"\(.headRepository.nameWithOwner) \(.headRefName)"'
```

Set `HEAD_REPO` from `headRepository.nameWithOwner`. For same-repo PRs this is the base repository itself; for cross-repository PRs it is the fork, so `https://github.com/${HEAD_REPO}.git` is the correct fetch URL in both cases. Set `HEAD_BRANCH` from `headRefName`.

**When `--head-repo` and `--head-branch` were provided, skip the `gh pr view` above and use those values directly** (`HEAD_REPO="${HEAD_REPO_ARG}"`, `HEAD_BRANCH="${HEAD_BRANCH_ARG}"`). The caller already resolved them, so no GitHub call is needed.

Then create the worktree that all stale steps will reuse:

```bash
ISSUE_NUMBER=$(gh pr view $PR_NUMBER --repo $REPO --json closingIssuesReferences --jq '.closingIssuesReferences[0].number // empty')
WORKTREE_DIR=/tmp/sdlc/$REPO/${ISSUE_NUMBER:-pr-$PR_NUMBER}
mkdir -p /tmp/sdlc/$REPO
git fetch https://github.com/$HEAD_REPO.git $HEAD_BRANCH
git worktree add $WORKTREE_DIR FETCH_HEAD
```

When a precomputed plan was given, skip the `ISSUE_NUMBER` lookup (it is a naming convenience only) and use `WORKTREE_DIR=/tmp/sdlc/$REPO/pr-$PR_NUMBER`.

If the worktree already exists (e.g. from a previous run), skip creation and reuse it.

### 4. Dispatch stale review steps

Dispatch each skill in `STALE_STEPS` as a subagent task via the Task tool. The subagent prompt MUST be the exact skill invocation command, not a paraphrased or self-authored description. Do not let the orchestrator generate its own task description, pass the literal command string below as the subagent prompt. Include the `WORKTREE_DIR` so the sub-skill reuses the shared worktree instead of creating its own.

Use the `general` subagent type for all five steps.

**Parallel dispatch of assess-pr-risk.** When `STALE_STEPS` contains `assess-pr-risk`, dispatch it concurrently with the first stale chain step: put the two Task calls in a single message so they run at the same time. The risk assessment is cheap (no build, static analysis only) and independent of the chain.

The chain steps run sequentially (analyze-test-coverage, then validate-pr, then verify-pr, then review-pr), waiting for each subagent to finish before starting the next. Do not parallelize chain steps, because each step may halt the pipeline. If `assess-pr-risk` is stale but no chain step is (or the chain halts before finishing), the risk assessment still runs and stands on its own.

Each sub-skill reuses the shared worktree, runs its analysis, and posts a comment (or writes locally when posting is disabled) with the commit SHA marker.

#### assess-pr-risk

Dispatch a subagent with this exact prompt:

```
Run the assess-pr-risk skill: /assess-pr-risk {PR} {REPO}
The worktree is already created at {WORKTREE_DIR}. Set WORKTREE_DIR to that path so the skill reuses it and does not create or remove its own worktree.
```

Never gate anything on its result and never halt because of it: a `block` or `hold` token is information for the human reviewer, not a pipeline failure. Because it runs concurrently, it may finish before the chain does; sibling reports that appear later are picked up by the next run of the skill, and its report states what would raise its confidence.

#### analyze-test-coverage

Dispatch first among the chain steps (concurrently with assess-pr-risk when both are stale). Dispatch a subagent with this exact prompt:

```
Run the analyze-test-coverage skill: /analyze-test-coverage {PR} {REPO}
The worktree is already created at {WORKTREE_DIR}. Set WORKTREE_DIR to that path so the skill reuses it and does not create or remove its own worktree.
```

The coverage step is static analysis only (no build, no test execution) and never halts the pipeline: nothing is gated by its verdict. A `fail` verdict means at least one behavior change or code path is uncovered; report it in the summary so the human reviewer can weigh it. Its report is saved under `$PR_REVIEW_DIR` and carries the same commit marker as the other steps, so staleness tracking works identically, and because it is written before the rest of the chain runs, the later steps can read it as evidence.

#### validate-pr

Dispatch a subagent with this exact prompt:

```
Run the validate-pr skill: /validate-pr {PR} {REPO}
The worktree is already created at {WORKTREE_DIR}. Set WORKTREE_DIR to that path so the skill reuses it and does not create or remove its own worktree.
```

If validate-pr returns a **Wrong thing** verdict, stop the chain. Do not run verify-pr or review-pr, because verifying conformance to, or the craft of, the wrong target is wasted effort. The coverage report (already posted) and the concurrent assess-pr-risk report are unaffected and stand. Record the failure in the summary.

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

After processing, output the summary table and finish with a single machine-readable verdict line, so a parent orchestrator (`review-requested-prs`) can aggregate results without parsing the table:

```
VERDICT <status> | PR #{PR} | {REPO} | steps={STALE_STEPS} | <short note>
```

`<status>` is one of:

| Status | Meaning |
|---|---|
| `completed` | Every stale step ran and passed (or there were none left to run after a partial pass); includes runs whose only stale step was assess-pr-risk or analyze-test-coverage |
| `up-to-date` | Nothing was stale; all steps already match the current HEAD |
| `stopped-validate` | validate-pr returned Wrong thing or Inconclusive; later chain steps not run (analyze-test-coverage already ran; assess-pr-risk unaffected) |
| `stopped-verify` | verify-pr failed (build failure, nonconforming, missing issue/criteria); review-pr not run |
| `stopped-review` | review-pr returned changes-requested or rejected |
| `error` | The pipeline could not run (worktree setup failed, script error) |

The risk assessment never changes the status: its verdict token is reported in the summary and the table, and routing on it is the human reviewer's call. The same applies to analyze-test-coverage: it is the first chain step and nothing is gated on it, so even a coverage `fail` verdict leaves the status `completed`, with the outcome reported in the summary note and the table.

Then show the table:

| Repository | PR | Steps run | Result |
|---|---|---|---|
| owner/repo | #42 | assess, coverage, validate, verify, review | Completed |
| owner/repo | #42 | verify, review | Completed (assess, coverage, validate up to date) |
| owner/repo | #42 | assess | Completed (chain up to date) |
| owner/repo | #42 | coverage | Completed (rest up to date; gaps found, see note) |
| owner/repo | #42 | — | Skipped (all up to date) |
| owner/repo | #42 | assess, coverage, validate | Stopped at validate (wrong product) |
| owner/repo | #42 | assess, coverage, validate, verify | Stopped at verify (build failure) |

## Example Usage

**Scenario 1: Fresh PR, all five steps needed**
```
/review-pr-full 42 acme/api
```
No prior markers found. Dispatches assess-pr-risk concurrently with analyze-test-coverage, then validate-pr, verify-pr, and review-pr in sequence. All pass. Summary shows "Completed".

**Scenario 2: PR URL**
```
/review-pr-full https://github.com/acme/api/pull/42
```
Same as Scenario 1 but using a PR URL.

**Scenario 3: Precomputed plan from review-requested-prs**
```
/review-pr-full 42 acme/api --steps validate-pr,verify-pr --head-repo acme/api --head-branch feature-x
```
The caller already ran the staleness check and resolved the head refs. The skill skips its own GitHub queries, creates the worktree from `acme/api@feature-x`, runs validate-pr then verify-pr, and stops before review-pr. Ends with `VERDICT completed | PR #42 | acme/api | steps=validate-pr,verify-pr | ...`.

**Scenario 4: Partial completion, re-run**
```
/review-pr-full 42 acme/api
```
The validate-pr, verify-pr, analyze-test-coverage, and assess-pr-risk markers match HEAD, but review-pr is stale. Runs only `/review-pr 42 acme/api`. Summary shows "Completed (assess, coverage, validate, verify up to date)".

**Scenario 5: All steps up to date**
```
/review-pr-full 42 acme/api
```
All five markers match HEAD. Script outputs nothing. Reports "All review steps are up to date for PR #42 in acme/api".

**Scenario 6: validate-pr returns Wrong thing**
```
/review-pr-full 15 acme/api
```
validate-pr judges the PR to be the wrong product. It posts its Wrong-thing verdict. verify-pr and review-pr are not run; the coverage report was already posted first and the concurrent assess-pr-risk completed, so both reports stand (useful context for the human deciding what to do with the PR). Summary shows "Stopped at validate (wrong product)".

**Scenario 7: verify-pr build failure**
```
/review-pr-full 88 acme/api
```
validate-pr passes. verify-pr fails to build. Notes the build failure and stops (CI would typically catch this). review-pr is not run. Summary shows "Stopped at verify (build failure)".

**Scenario 8: PR number with $REPO from environment**
```
/review-pr-full 42
```
`$REPO` is set in the environment. Uses it as the repository. Runs the pipeline.

**Scenario 9: Only the risk assessment is stale**
```
/review-pr-full 55 acme/api
```
The chain markers match HEAD (the pipeline ran before assess-pr-risk existed), but the assess marker is old. Dispatches only `/assess-pr-risk 55 acme/api`, which reads the current sibling reports for full evidence. Summary shows "Completed (chain up to date)".

**Scenario 10: Only the coverage step is stale**
```
/review-pr-full 77 acme/api
```
The assess and chain markers match HEAD, but the analyze-test-coverage marker is missing (the pipeline ran before the coverage step existed). Dispatches only `/analyze-test-coverage 77 acme/api`. It finds two uncovered behavior changes and posts its report with a `fail` verdict. Summary shows "Completed" with a note that coverage found gaps; the human reviewer decides whether to request tests.

## Script Reference

| Script | Description |
|---|---|
| `~/.agents/scripts/review_requested_prs.py` | Discovers PRs, checks marker staleness (GitHub comments + local `.sdlc` files), outputs dispatch commands. Run with `--dispatch` for per-step commands, `--dispatch-prs` for one self-contained `/review-pr-full` command per PR, `--json` for structured data, `--log-level debug` for timings. Pass a single PR URL to scope it to one PR. |

## Related Skills

| Skill | Relationship |
|---|---|
| `review-requested-prs` | Multi-PR counterpart: discovers all review-requested PRs and fans out one `review-pr-full` session per PR in parallel, passing a precomputed plan so no GitHub re-check is needed. Use that when reviewing your queue; use this skill for a single PR. |
| `validate-pr` | Needs-alignment sub-skill (does the PR solve the right problem; are the acceptance criteria sound). Build-free early gate. |
| `verify-pr` | Conformance sub-skill (criteria-to-code traceability plus runtime proof that each criterion is met). Owns the build. |
| `review-pr` | Code-craft sub-skill (quality, architecture, security, tests, operational concerns). Delegates test coverage analysis to `/analyze-test-coverage` for its Coverage section. |
| `analyze-test-coverage` | Coverage sub-skill and first chain step (introduced tests, change coverage, uncovered code), so its report exists as evidence before validate/verify/review run. Static analysis only; never halts the pipeline. |
| `assess-pr-risk` | Risk and confidence assessment dispatched concurrently with the chain; advisory only, never halts the pipeline. |
| `quick-pr-review` | Lightweight counterpart: rapid auto-approve to unblock. Use this skill when you need deep review, not rapid unblocking. |
