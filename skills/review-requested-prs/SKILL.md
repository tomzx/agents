---
name: review-requested-prs
description: Orchestrate full PR reviews (assess-pr-risk in parallel with analyze-test-coverage, validate-pr, verify-pr, review-pr) across all PRs where you are a requested reviewer, or on a specific PR by URL. Fans out one independent review-pr-full session per PR so a slow step on one PR never blocks another. Never posts anything to GitHub directly; each sub-skill posts its own report.
allowed-tools: Bash(uv run:*, gh:*, git:*, ~/.agents/scripts/review_requested_prs.py:*, opencode run:*), Read, Write, Glob, Grep, Task
argument-hint: "[pr-url ... | owner/repo ...]"
---

# Review Requested PRs

Finds all open PRs where you are a requested reviewer (or accepts specific PR URLs), computes for each PR which of `/assess-pr-risk`, `/analyze-test-coverage`, `/validate-pr`, `/verify-pr`, and `/review-pr` are stale for its current HEAD, then hands each PR to its own `review-pr-full` session that runs that PR's stale steps to completion (the risk assessment concurrently with the chain).

The orchestrator (this session) only discovers work and aggregates results. It never runs a review step itself. Each PR is owned end to end by one `review-pr-full` subagent, so a slow step on one PR (for example a `verify-pr` build) cannot hold up any other PR.

The discovery, staleness check, and head-ref resolution are done by a deterministic Python script (`~/.agents/scripts/review_requested_prs.py`). Its `--dispatch-prs` output is one self-contained `/review-pr-full` command per PR, carrying the precomputed stale steps and head refs:

```
/review-pr-full 42 acme/api --steps validate-pr,verify-pr --head-repo acme/api --head-branch feature-x
```

Because the command is self-contained, `review-pr-full` starts the checks immediately: it does not re-query GitHub for staleness or PR status. This is what keeps the orchestrator from being a bottleneck.

## Marker format

Each sub-skill posts a comment (or writes locally when posting is disabled) with an HTML marker containing a JSON object with the step name, commit SHA, tree hash, and verdict:

```
<!-- {"step":"validate-pr","sha":"abc123","tree":"3f9c2e1","verdict":"pass"} -->
```

The verdict is either `pass` (continue to the next step) or `fail` (halt the pipeline for this PR). Each sub-skill maps its own verdict vocabulary to these two values:

| Step | Internal verdicts | `pass` | `fail` |
|------|-------------------|--------|--------|
| assess-pr-risk | fast-track, confirm, investigate, decide, block, hold | All (advisory only) | None (never gates the chain) |
| validate-pr | Right thing, Partially right, Wrong thing, Inconclusive | Right thing, Partially right | Wrong thing, Inconclusive |
| verify-pr | Conforms, Nonconforming | Conforms (PR conforms: Yes) | Nonconforming (PR conforms: No) |
| review-pr | approved, changes-requested, rejected | approved | changes-requested, rejected |
| analyze-test-coverage | pass, fail | Fully covered (every behavior change covered, no uncovered code) | At least one uncovered change or code path |

The script reads these markers (both GitHub PR comments and local report files under `~/.sdlc/<owner>/<repo>/pull-requests/<pr>/`) to decide which steps are stale, applies the pass/fail cutoff (chain steps after a failed prior step are not dispatched), and emits the resulting plan. `assess-pr-risk` sits outside the cutoff: it is stale independently of the chain, is never dropped because a chain step failed, and never drops a chain step. `analyze-test-coverage` also sits outside the cutoff: it runs before `validate-pr`, its `fail` verdict never gates anything, and a failed `validate-pr` does not drop it. The legacy marker format (`<!-- validate-pr:SHA -->`) is still supported for backward compatibility, though it does not carry a verdict.

## Prerequisites

- `uv` installed (for running the Python script)
- `gh` CLI authenticated (used by the script as a token fallback, and by `review-pr-full` to fetch head branches)
- `validate-pr`, `verify-pr`, `review-pr`, `analyze-test-coverage`, and `assess-pr-risk` skills available
- Sub-agent dispatch via the `Task` tool (`subagent_type: "general"`). If unavailable, fall back to sequential mode.

## Workflow

```
Run ~/.agents/scripts/review_requested_prs.py --dispatch-prs
                |
                v
  Parse one /review-pr-full command per PR
                |
                v
  Fan out: one general subagent per PR, concurrently
                |
                |   subagent A -> /review-pr-full <PR A>   subagent B -> <PR B>   ...
                |      (owns its worktree; runs its stale steps to completion)
                |
                v
  Collect VERDICT lines -> summary table
```

## Steps

### 1. Run the discovery script

Run the script to discover PRs and get one ready-to-run command per PR with stale steps:

```bash
~/.agents/scripts/review_requested_prs.py $@ --dispatch-prs
```

The script accepts the same arguments as the skill:
- No arguments: searches all open PRs where you are a requested reviewer (plus open PRs you have already reviewed)
- `owner/repo` arguments: scopes the search to those repos
- PR URL arguments: processes only those specific PRs
- Mixed: processes the union of explicit PRs and search results

Useful flags:
- `--limit N`: cap the number of PRs discovered (default 100)
- `--workers N`: number of PRs to process in parallel for staleness checks (default 8)
- `--draft`: include draft PRs (excluded by default)
- `--log-level debug`: see API call timings for debugging

`--dispatch-prs` emits one self-contained `/review-pr-full` command per PR needing work, in execution order, with PR plan blocks separated by `---`:

```
/review-pr-full 42 acme/api --steps assess-pr-risk,analyze-test-coverage,validate-pr,verify-pr,review-pr --head-repo acme/api --head-branch feature-x
---
/review-pr-full 88 acme/web-app --steps assess-pr-risk,verify-pr,review-pr --head-repo alice/web-app --head-branch fix-cache
---
/review-pr-full 55 acme/api --steps analyze-test-coverage,review-pr --head-repo acme/api --head-branch add-export
```

If the script outputs nothing, print "nothing to dispatch" and stop. Every discovered PR is already fully reviewed for its current HEAD.

### 2. Parse the plans

Split the script output on `---` into per-PR blocks. Each block is a single `/review-pr-full` command line. Extract the PR number and repository from it (the second and third tokens); the rest is passed through verbatim.

Each command is already in the exact form `review-pr-full` expects, so do not reconstruct or reorder it. The script has already dropped steps blocked by an earlier failed verdict.

### 3. Fan out one subagent per PR

Launch one subagent per PR with the `Task` tool, `subagent_type: "general"`. Put **multiple Task calls in a single message** so they run concurrently; if there are many PRs, launch in batches (for example 5 at a time) and wait for each batch before starting the next.

This is the whole point of the skill: the orchestrator dispatches and waits; each subagent runs its PR's pipeline to completion on its own, so PRs progress independently.

Each subagent starts with a fresh context, so its prompt must be self-contained. Use this template verbatim, substituting the command:

```
Run the review-pr-full skill for this PR. Its plan was computed against the
current HEAD moments ago, so do not re-run discovery or staleness checks and do
not call GitHub for PR status; run the command exactly as given:

<COMMAND_FROM_STEP_2>

Do not create or remove the worktree yourself; review-pr-full owns the worktree
lifecycle. Do not run the review steps yourself; review-pr-full dispatches them.

Return exactly one line as your final answer, nothing else:
VERDICT <status> | PR #<PR> | <REPO> | steps=<steps> | <short note>
where <status> is one of: completed, up-to-date, stopped-validate,
stopped-verify, stopped-review, error.
```

For example:

```
Run the review-pr-full skill for this PR. Its plan was computed against the
current HEAD moments ago, so do not re-run discovery or staleness checks and do
not call GitHub for PR status; run the command exactly as given:

/review-pr-full 42 acme/api --steps validate-pr,verify-pr --head-repo acme/api --head-branch feature-x

Do not create or remove the worktree yourself; review-pr-full owns the worktree
lifecycle. Do not run the review steps yourself; review-pr-full dispatches them.

Return exactly one line as your final answer, nothing else:
VERDICT <status> | PR #<PR> | <REPO> | steps=<steps> | <short note>
where <status> is one of: completed, up-to-date, stopped-validate,
stopped-verify, stopped-review, error.
```

#### Fallback: no Task tool

If the `Task` tool is unavailable, run each command sequentially with `opencode run`:

```bash
opencode run --auto "<COMMAND_FROM_STEP_2>"
```

This loses the parallelism across PRs; process them one at a time and aggregate the same way. Record in the summary that sequential mode was used.

### 4. Aggregate and report

Collect each subagent's final `VERDICT ...` line. Map statuses to the summary:

| Repository | PR | Steps run | Result |
|---|---|---|---|
| owner/repo | #42 | assess, validate, verify, review | Completed |
| owner/repo | #88 | assess, verify, review | Completed (validate up to date) |
| owner/repo | #55 | review | Completed (assess, validate, verify up to date) |
| owner/repo | #77 | assess, validate | Stopped at validate (wrong product) |
| owner/repo | #33 | assess, validate, verify | Stopped at verify (build failure) |
| owner/repo | #11 | — | Up to date |

If a subagent returns no parseable verdict, surface its raw output and mark that PR as `no-verdict`.

## Example Usage

**Scenario 1: No arguments, all review-requested PRs**
```
/review-requested-prs
```
Finds 4 open PRs across multiple repos. 1 is fully reviewed already (the script omits it), 2 need all five steps, 1 needs only analyze-test-coverage and review-pr. Fans out 3 subagents, one per PR; each runs its steps to completion (the risk assessment concurrently with the chain). A slow verify-pr build on one PR does not delay the others.

**Scenario 2: Filter to specific repositories**
```
/review-requested-prs acme/api acme/web-app
```
Searches only those two repos. Fans out one subagent per PR with stale steps.

**Scenario 3: Single PR by URL**
```
/review-requested-prs https://github.com/acme/api/pull/42
```
Processes only PR #42. validate-pr and verify-pr are current, analyze-test-coverage and review-pr are stale, so the script emits `/review-pr-full 42 acme/api --steps analyze-test-coverage,review-pr --head-repo ... --head-branch ...` and one subagent runs it.

**Scenario 4: Multiple PR URLs**
```
/review-requested-prs https://github.com/acme/api/pull/42 https://github.com/acme/web-app/pull/88
```
Processes exactly those two PRs. No search is performed.

**Scenario 5: All PRs already reviewed**
```
/review-requested-prs
```
The script outputs nothing (all markers match HEAD). Reports "nothing to dispatch".

**Scenario 6: Fork PR**
```
/review-requested-prs acme/api
```
A PR whose head is on a contributor's fork is emitted with `--head-repo alice/api --head-branch fix-x`, so the `review-pr-full` subagent fetches from the fork directly, again without any extra GitHub lookup.

**Scenario 7: validate-pr failed on a prior run**
```
/review-requested-prs
```
PR #15 has a `fail` validate-pr marker. The script's cutoff drops verify-pr and review-pr but keeps assess-pr-risk and analyze-test-coverage (coverage precedes validate and is never gated), so the only command emitted is `--steps assess-pr-risk,analyze-test-coverage,validate-pr`, and no time is spent verifying conformance to a wrong target while the risk and coverage reports still land for the human deciding what to do with the PR.

## Script Reference

| Script | Description |
|---|---|
| `~/.agents/scripts/review_requested_prs.py` | Discovers PRs, checks marker staleness (GitHub comments + local `.sdlc` files), resolves head repos/branches, and outputs dispatch commands. Run with `--dispatch-prs` for one self-contained `/review-pr-full` command per PR (used by this skill), `--dispatch` for raw per-step commands, `--json` for structured data, `--log-level debug` for timings. |

## Related Skills

| Skill | Relationship |
|---|---|
| `review-pr-full` | Per-PR executor this skill delegates to. It owns that PR's worktree and runs the stale steps sequentially, halting on a blocking verdict. |
| `quick-pr-reviews` | Lightweight counterpart: runs `quick-pr-review` (auto-approve) on changed PRs. Use that skill when you need rapid unblocking, not deep review. |
| `validate-pr` | Needs-alignment sub-skill (does the PR solve the right problem; are the acceptance criteria sound). Build-free early gate. |
| `verify-pr` | Conformance sub-skill (criteria-to-code traceability plus runtime proof that each criterion is met). Owns the build. |
| `review-pr` | Code-craft sub-skill (quality, architecture, security, tests, operational concerns). Delegates test coverage analysis to `/analyze-test-coverage`. |
| `analyze-test-coverage` | Coverage sub-skill (introduced tests, change coverage, uncovered code). First chain step (before validate-pr); its verdict never halts the pipeline. |
