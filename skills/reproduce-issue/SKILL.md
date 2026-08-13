---
name: reproduce-issue
description: Reproduce a bug reported in a GitHub issue by creating a worktree, analyzing the codebase, and attempting to trigger the bug.
allowed-tools: Bash(gh:*, git:*, ghx:*, asciinema:*, agg:*, npx:*, node:*, uv:*, python:*, python3:*, curl:*, ~/.agents/scripts/get-env:*), Read, Write, Edit, Glob, Grep
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

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, target the issue from `$ISSUE_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with write access to the target repository
- A GitHub issue number describing a bug
- Git worktree support (`git worktree` available)
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there
- For before/after visual proof (optional, best-effort): `asciinema` + renderer for CLI bugs, or Playwright for web UI bugs. If unavailable, the recording step is skipped silently.

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
Record before   Post comment
(if surface      (unable to reproduce,
 classifiable)   ask for details)
        |
        v
Post comment
(reproduced,
 ready to fix)
```

## Steps

### 1. Fetch the bug report

Fetch the issue details to understand the bug:

```bash
ghx issue view $ISSUE_NUMBER --repo $REPO
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

After creating the worktree, write `.sdlc/state.yml` inside it:

```yaml
current_phase: reproduce
github_ref: "#<issue-number>"
feature: null
```

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

### 5. Record the before state (when reproduced)

When the bug is reproduced, capture a recording of the buggy behavior so `validate-implementation` can pair it with an after-the-fix recording before the PR is opened. This runs only on the bug-fix fast path and is best-effort: if the recording tools are unavailable or the surface cannot be classified, skip silently and proceed.

All proof assets for this issue live under a per-repo, per-issue directory so they never collide with other work:

```bash
PROOF_DIR="/tmp/$REPO/$ISSUE_NUMBER"   # expands to /tmp/<owner>/<repo>/<issue-id>
mkdir -p "$PROOF_DIR"
```

Classify the change surface from the reproduction (mirrors `validate-implementation`'s classification):

- **CLI bug** (the reproduction runs a CLI entry point, command, or script): identify the single command that triggers the bug. Read [`../record-asciinema/SKILL.md`](../record-asciinema/SKILL.md) and invoke it with:
  - `RECORD_SLUG` = `before-bug`
  - `RECORD_DIR` = `$PROOF_DIR`
  - `RECORD_COMMAND` = the triggering command
- **Web UI bug** (the reproduction loads a route or page): identify the route URL and the dev server command. Read [`../record-playwright/SKILL.md`](../record-playwright/SKILL.md) and invoke it with:
  - `RECORD_SLUG` = `before-bug`
  - `RECORD_DIR` = `$PROOF_DIR`
  - `RECORD_URL` = the route that exhibits the bug
  - `RECORD_VIEWPORTS` = `1280x720`
  - `RECORD_SERVER_CMD` = the dev server command
- **Neither / not determinable**: skip the recording.

The recording must show the bug manifesting (the error, crash, or wrong output). Re-record with `--overwrite` if the first take does not demonstrate the defect.

After a recording is produced, write a manifest so `validate-implementation` can replay the exact same demonstration on the fixed code:

```bash
# CLI surface
cat > "$PROOF_DIR/proof-manifest.txt" <<EOF
surface: cli
command: <the triggering command>
EOF

# Web UI surface
cat > "$PROOF_DIR/proof-manifest.txt" <<EOF
surface: web
url: <the route URL>
server_cmd: <the dev server command>
EOF
```

The rendered before asset lands at `$PROOF_DIR/before-bug.gif` (or `.png` / `.svg`). If no asset was produced (tools absent or surface unclassifiable), do not write a manifest; `validate-implementation` will report `surface: none` / `tools-missing` and `create-pr` will omit proof.

### 6. Post reproduction results

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

**Before recording:** captured at `$PROOF_DIR/before-bug.*` (pairs with an after-the-fix recording captured by `/validate-implementation` before the PR). Omit this line if no recording was taken.

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

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `reproduced` | Bug reproduced in the worktree |
| `cannot-reproduce` | Could not reproduce; needs more information |

## Example Usage

**Scenario 1: Reproducible bug**
```
/reproduce-issue 42 owner/myrepo
```
Fetches issue #42 (null pointer on login), creates worktree on `fix/42-null-pointer-login`, reproduces by sending a request with missing field, records the crash to `/tmp/<owner>/<repo>/42/before-bug.gif` with a manifest, posts reproduction details on the issue. Ready for `create-implementation`.

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
then `validate-implementation` to capture the after recording and confirm the fix before opening a PR,
then `create-pr` to submit the pull request.
Or use `fix-issue` to orchestrate the remaining steps automatically.
