---
name: reproduce-issue
description: Reproduce a bug reported in a GitHub issue by creating a worktree, analyzing the codebase, and attempting to trigger the bug.
allowed-tools: Bash(gh:*, git:*, gh-cached:*, scripts/get-env:*), Read, Write, Edit, Glob, Grep
argument-hint: "<issue-number> [repository]"
---

# Reproduce Issue

Takes a GitHub issue that describes a bug, creates a git worktree on a fix branch,
and attempts to reproduce the reported behavior.
Posts the reproduction results as a comment on the issue.

Assumes `check-duplicates` has already been run to verify no duplicates or existing fix PRs.
This skill stops after reproduction. Use `fix-issue` to continue with the fix, or
call `create-implementation` directly if the issue is already reproduced.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- A GitHub issue number describing a bug
- Git worktree support (`git worktree` available)
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `reproduce-issue`.

## Workflow

```
Fetch bug report issue
        |
        v
Create git worktree on fix branch
        |
        v
Analyze issue + explore codebase
        |
        v
Attempt to reproduce
        |
        v
Bug reproduced?
   /          \
 Yes            No
  |              |
  v              v
Post comment   Post comment
(reproduced,   (unable to reproduce,
 ready to fix) ask for details)
```

## Steps

### 1. Fetch the bug report

Fetch the issue details to understand the bug:

```bash
gh-cached issue view $ISSUE_NUMBER --repo $REPO
```

Extract from the issue:
- Expected behavior
- Actual behavior
- Steps to reproduce
- Environment details (version, OS, etc.)
- Error messages, stack traces, or logs
- Any labels that indicate severity or area

If the issue lacks clear reproduction steps, check the issue author.
If the author is the current user, attempt to gather additional information from the codebase, logs, or error context and help update the original issue description with clearer steps.
If the author is someone else, comment on the issue asking for reproduction details before proceeding.

### 2. Create a git worktree

Create a worktree so the main working directory is not disturbed:

```bash
git fetch origin
WORKTREE_NAME=$(basename $(pwd))-fix-$ISSUE_NUMBER
git worktree add ../$WORKTREE_NAME -b fix/$ISSUE_NUMBER-<slug> origin/main
```

Where `<slug>` is a short hyphenated description derived from the issue title (e.g., `null-pointer-login`).

All subsequent work happens inside the worktree directory.

If worktree creation fails (e.g., branch already exists, directory conflict), fall back to a regular branch:

```bash
git checkout -b fix/$ISSUE_NUMBER-<slug> origin/main
```

### 3. Analyze the codebase

- Search for the relevant code area based on the bug description.
- Identify the files, functions, and data flows involved.
- Read `.sdlc/context/architecture.md` and `.sdlc/context/conventions.md` if available.
- Note any existing tests related to the buggy behavior.

### 4. Attempt to reproduce

Based on the issue's reproduction steps, attempt to trigger the bug:

1. Follow the reported steps exactly as described.
2. If the steps are incomplete, try to infer missing steps from the error description.
3. Check out the specific commit or version mentioned in the issue if applicable.
4. Run the application or relevant test suite to observe the failure.

Record the reproduction attempt:
- What steps were taken
- Whether the bug was reproduced
- Any differences from the reported behavior
- Environment or version discrepancies

### 5. Post reproduction results

#### If the bug is reproduced

Comment on the issue to confirm reproduction and signal that a fix is in progress.
Include relevant details from the reproduction attempt (exact steps that triggered it, observed error, environment differences from the report):

```bash
gh issue comment $ISSUE_NUMBER --repo $REPO --body "$(cat <<'EOF'
Reproduced. Working on a fix.

**Reproduction details:**
- <Exact steps that triggered the bug>
- <Observed error or behavior>
- <Any environment or version differences from the original report>

---

Posted with [reproduce-issue](SKILL_FILE_URL) (`SKILL_SHORT_SHA`)
EOF
)"
```

The worktree and fix branch are now ready for implementation.
Proceed with `create-implementation` or `fix-issue`.

#### If the bug cannot be reproduced

1. Comment on the issue explaining what was tried and why reproduction failed.
2. Ask the reporter for additional details (specific version, environment, input data, etc.).
3. Do NOT proceed with a fix. Stop and inform the user.
4. Clean up the worktree if the user confirms no further action is needed:
   ```bash
   git worktree remove ../$WORKTREE_NAME
   git branch -d fix/$ISSUE_NUMBER-<slug>
   ```
5. If the user confirms the bug exists despite reproduction failure, leave the worktree in place and proceed with a best-effort fix based on code analysis.

## Failure Modes

| Mode | Response |
|---|---|
| **Cannot reproduce** | Comment on issue, ask for more details, clean up worktree |
| **Worktree creation fails** | Fall back to a regular branch in the main working directory |
| **Issue is not a bug** | Comment on the issue suggesting it be reclassified, stop |

## Example Usage

**Scenario 1: Reproducible bug**
```
/reproduce-issue 42 owner/myrepo
```
Fetches issue #42 (null pointer on login), creates worktree on `fix/42-null-pointer-login`, reproduces by sending a request with missing field, posts reproduction details on the issue. Ready for `create-implementation`.

**Scenario 2: Cannot reproduce**
```
/reproduce-issue 15
```
Fetches issue #15 (intermittent timeout), follows reproduction steps, cannot trigger the timeout. Comments on issue asking for logs and specific timing details.

**Scenario 3: Cannot determine reproduction steps**
```
/reproduce-issue 20 owner/myrepo
```
Fetches issue #20, but the description lacks clear steps. The author is someone else, so posts a comment asking for reproduction details.

## Next Step

If reproduced, continue with `create-implementation` to write the regression test and fix,
then `create-pr` to submit the pull request.
Or use `fix-issue` to orchestrate the remaining steps automatically.
