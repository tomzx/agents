---
name: review-requested-prs
description: Orchestrate full PR reviews (validate-pr, verify-pr, review-pr) across all PRs where you are a requested reviewer, or on a specific PR by URL. Skips steps already completed for the current commit.
allowed-tools: Bash(gh:*, ghx:*)
argument-hint: "[pr-url ... | owner/repo ...]"
---

# Review Requested PRs

Finds all open PRs where you are a requested reviewer (or accepts specific PR URLs), checks each one for commits that are newer than the latest validate-pr / verify-pr / review-pr comment, and runs only the stale review steps in order: `/validate-pr`, then `/verify-pr`, then `/review-pr`.

Each sub-skill posts a comment with an HTML marker containing the commit SHA it was run against (`<!-- validate-pr:SHA -->`, `<!-- verify-pr:SHA -->`, `<!-- review-pr:SHA -->`). This orchestrator reads those markers to skip steps already completed for the current HEAD commit.

## Prerequisites

- `gh` CLI authenticated
- `validate-pr`, `verify-pr`, and `review-pr` skills available

## Workflow

```
Parse arguments (PR URLs vs owner/repo)
               |
               v
     Discover target PRs
  (PR URL -> single PR;  owner/repo -> search)
               |
               v
    For each PR: fetch HEAD_COMMIT
               |
               v
    Check markers for validate-pr,
    verify-pr, review-pr
               |
      All three match HEAD?
       /            \
     Yes             No
      |               |
   Skip         Run stale steps in order:
              validate-pr -> verify-pr -> review-pr
               |
               v
        Report summary table
```

## Steps

### 1. Parse arguments and discover PRs

Separate `$@` into two groups:

- **PR URLs**: arguments containing `github.com/` and `/pull/` (e.g. `https://github.com/acme/api/pull/42`)
- **Repos**: arguments in `owner/repo` format (contain `/` but are not URLs, e.g. `acme/api`)

#### If PR URLs are provided

For each PR URL, extract the owner/repo and PR number:

```
https://github.com/acme/api/pull/42  ->  REPO=acme/api, PR=42
```

The target list is exactly these PRs. Skip the search step.

#### If repos are provided (or no arguments)

Build the search command. With no arguments, search all review-requested PRs:

```bash
gh search prs --review-requested @me --state open \
  --json number,repository,title \
  --limit 100
```

For each `owner/repo` argument, add `--repo <owner/repo>` to scope the search.

This returns a list of PRs. For each entry extract:
- `REPO`: `repository.nameWithOwner`
- `PR`: `number`

#### Mixed arguments

If both PR URLs and repos are provided, process the union: the explicitly listed PRs plus the search results from the repos.

### 2. For each PR, fetch the HEAD commit

```bash
ghx pr view {PR} --repo {REPO} --json --refresh | jq -r '.headRefOid'
```

This gives you `HEAD_COMMIT` for the PR.

### 3. Check existing review markers

For each PR, fetch all issue comments and extract the latest marker SHA for each skill:

```bash
gh api repos/{REPO}/issues/{PR}/comments \
  --jq '.[].body'
```

Search the comment bodies (most recent first) for each marker pattern:

| Skill | Marker pattern |
|-------|----------------|
| validate-pr | `<!-- validate-pr:COMMIT_SHA -->` |
| verify-pr | `<!-- verify-pr:COMMIT_SHA -->` |
| review-pr | `<!-- review-pr:COMMIT_SHA -->` |

For each skill, find the **most recent** comment containing its marker and extract `COMMIT_SHA`.

Record three values:
- `VALIDATE_COMMIT`: SHA from the latest validate-pr marker, or empty if none found
- `VERIFY_COMMIT`: SHA from the latest verify-pr marker, or empty if none found
- `REVIEW_COMMIT`: SHA from the latest review-pr marker, or empty if none found

### 4. Determine which steps to run

Compare each marker SHA against `HEAD_COMMIT`:

| Condition | Action |
|-----------|--------|
| All three == `HEAD_COMMIT` | Skip this PR entirely (already fully reviewed) |
| `VALIDATE_COMMIT` != `HEAD_COMMIT` | Run validate-pr, verify-pr, review-pr (all three) |
| `VALIDATE_COMMIT` == `HEAD_COMMIT` but `VERIFY_COMMIT` != `HEAD_COMMIT` | Run verify-pr, then review-pr |
| First two match but `REVIEW_COMMIT` != `HEAD_COMMIT` | Run review-pr only |

Rationale: if validate-pr is stale, the downstream skills must also re-run because the code changed. If validate-pr is current but verify-pr is stale, only verify-pr and review-pr need to re-run. If only review-pr is stale, only it re-runs.

### 5. Run stale review steps

For each PR that needs processing, dispatch each stale skill as a subagent task via the Task tool. The subagent prompt MUST be the exact skill invocation command, not a paraphrased or self-authored description. Do not let the orchestrator generate its own task description, pass the literal command string below as the subagent prompt.

Use the `general` subagent type for all three steps.

#### validate-pr

Dispatch a subagent with this exact prompt:

```
Run the validate-pr skill: /validate-pr {PR} {REPO}
```

#### verify-pr

Dispatch a subagent with this exact prompt:

```
Run the verify-pr skill: /verify-pr {PR} {REPO}
```

#### review-pr

Dispatch a subagent with this exact prompt:

```
Run the review-pr skill: /review-pr {PR} {REPO}
```

Process PRs in parallel by dispatching one subagent per PR in a single message with multiple Task tool calls. Each PR is independent, so all PRs run concurrently. Within a PR, steps run sequentially (validate-pr, then verify-pr, then review-pr), waiting for each subagent to finish before starting the next. Do not parallelize steps within a single PR, because each step may halt the pipeline. Each sub-skill checks out the PR branch in a worktree, runs its analysis, and posts a comment with the commit SHA marker.

If a step fails (e.g. build failure in verify-pr, no linked issue), the sub-skill posts a comment explaining the failure and stops. Do not run subsequent steps for that PR. Record the failure in the summary. Treat a blocking verdict from any step the same way: a **Wrong thing** verdict from `validate-pr` (the target is the wrong product) should halt the pipeline before `verify-pr` spends a build, since verifying conformance to a wrong spec is wasted effort.

### 6. Report summary

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
All PRs have markers matching their HEAD commit for all three skills. Reports all as skipped.

**Scenario 6: PR with no prior reviews**
```
/review-requested-prs acme/api
```
A PR has no validate-pr, verify-pr, or review-pr comments at all. Runs all three in sequence.

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

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh search prs --review-requested @me --state open --json number,repository,title --limit 100` | List open PRs where you are a requested reviewer |
| `gh search prs --review-requested @me --state open --repo <owner/repo> --json number,repository,title` | Scope search to a specific repo |
| `ghx pr view <pr> --repo <owner/repo> --json --refresh \| jq -r '.headRefOid'` | Fetch the HEAD commit SHA for a PR |
| `gh api repos/{owner}/{repo}/issues/{pr}/comments --jq '.[].body'` | List all comment bodies on a PR |

## Related Skills

| Skill | Relationship |
|---|---|
| `quick-pr-reviews` | Lightweight counterpart: runs `quick-pr-review` (auto-approve) on changed PRs. Use this skill when you need rapid unblocking, not deep review. |
| `validate-pr` | Needs-alignment sub-skill (does the PR solve the right problem; are the acceptance criteria sound). Build-free early gate. |
| `verify-pr` | Conformance sub-skill (criteria-to-code traceability plus runtime proof that each criterion is met). Owns the build. |
| `review-pr` | Code-craft sub-skill (quality, architecture, security, tests, operational concerns). |
