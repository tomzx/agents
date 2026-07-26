---
name: validate-pr
description: Checkout a PR's branch in a worktree, build it, run it, and validate every claim in the PR description through runtime proof. Records CLI demos (via record-asciinema) and web UI demos (via record-playwright), and attaches results to the PR.
allowed-tools: Bash(gh:*, git:*, asciinema:*, agg:*, npx:*, node:*, uv:*, python:*, python3:*, curl:*, scripts/get-env:*), Read, Write, Edit, Glob, Grep
argument-hint: "<pr-number> [repository]"
---

# Validate Pull Request

Checkout a PR's branch in a worktree, build, run, and prove every claim in the PR description through actual execution. For CLI changes, records demonstrations via `/record-asciinema` (rendered to GIF). For web UI changes, captures screenshots/video via `/record-playwright`. Uploads all assets and posts a validation report to the PR.

This is runtime validation: "did you build the right thing?" Static code inspection is handled by `/verify-pr`.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, target the pull request from `$PR_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with read access to the target repository
- `git worktree` available
- For CLI changes: `asciinema` plus a renderer (`agg` preferred). Provided by [`/record-asciinema`](../record-asciinema/SKILL.md).
- For web UI changes: Playwright (Node or Python) with Chromium. Provided by [`/record-playwright`](../record-playwright/SKILL.md).
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `validate-pr`.

## Workflow

```
Fetch PR metadata + diff ($1)
         |
         v
Parse claims from PR description
         |
         v
Create git worktree on PR branch
         |
         v
Install dependencies / build
         |
         v
Build succeeded?
    /          \
  Yes            No
   |              |
   v              v
Validate each    Post build failure, stop
claim at runtime
   |
   v
Detect change surface
   |
   +--- CLI changes? ----> /record-asciinema per CLI claim
   |
   +--- Web UI changes? --> /record-playwright per UI claim
   |
   v
Collect assets (GIFs / PNGs / video)
   |
   v
Upload assets to PR branch
   |
   v
Post validation report + recordings
   |
   v
Clean up worktree
```

## Steps

### 1. Fetch PR metadata

```bash
gh pr view $PR_NUMBER --repo $REPO --json title,body,headRefName,baseRefName,files,additions,deletions,changedFiles
```

Extract:
- PR title and description (body)
- Head branch name (`headRefName`)
- Base branch name (`baseRefName`)
- List of changed files
- Diff stats

Also fetch the full diff to identify changed modules and entry points:

```bash
gh pr diff $PR_NUMBER --repo $REPO
```

### 2. Parse claims from the PR description

Analyze the PR description and extract runtime-validatable claims:

- **Feature claims**: "Adds X", "Implements Y", "New command Z"
- **Fix claims**: "Fixes bug where X happens", "Resolves issue with Y"
- **Behavior claims**: "Now outputs X when Y", "Returns Z for input W"
- **CLI claims**: "New flag `--flag`", "Command `foo bar` now supports X"
- **Web UI claims**: "Adds a login page at /login", "New dashboard chart", "Renders X on mobile", "Button Y now disabled when Z"
- **Performance claims**: "Reduces latency by X%", "Improves throughput"
- **Test claims**: "Adds N tests for X", "Test coverage for Y"

For each claim, record:
- The claim text (quoted from the PR description)
- The claim type
- The runtime test to perform (command to run, output to expect, exit code, etc.)

If the PR description has no specific claims, post a comment requesting the author list them and stop.

### 3. Create a git worktree on the PR branch

```bash
git fetch origin $HEAD_BRANCH
WORKTREE_NAME=$(basename $(pwd))-validate-pr-$PR_NUMBER
git worktree add ../$WORKTREE_NAME origin/$HEAD_BRANCH
```

All subsequent work happens inside the worktree directory.

If worktree creation fails, fall back to:

```bash
git fetch origin $HEAD_BRANCH
git checkout origin/$HEAD_BRANCH
```

### 4. Install dependencies and build

Detect the project type and install/build:

```bash
ls package.json Cargo.toml pyproject.toml go.mod Makefile 2>/dev/null
```

Follow the project's standard install and build process. Check `.sdlc/context/` for project-specific build instructions if available.

If the build fails, post a comment reporting the build failure with the error output and stop. Do not attempt to fix build issues.

### 5. Validate each claim at runtime

For every parsed claim, prove or disprove it through execution.

#### Behavior claims

- Write a small script or test that exercises the claimed behavior
- Run it and verify the output matches expectations
- If the claim references an existing test, run that specific test
- Capture stdout/stderr and exit code as evidence

#### CLI claims

- Identify the CLI entry point from the codebase
- Run the claimed command/flag and verify output
- Record the demonstration via `/record-asciinema` (see Step 6)

#### Web UI claims

- Identify the route/page the claim refers to from the codebase (router config, page components)
- Start the dev server (or confirm it is running) and load the route
- Verify the claimed element/behavior is present in the rendered page
- Capture screenshots (and a video if the claim is about interaction) via `/record-playwright` (see Step 6)
- Cover the viewports the claim names (mobile, desktop); if unspecified, capture both

#### Fix claims

- Reproduce the original bug scenario on this branch
- Verify the fix prevents the reported behavior
- If the PR includes a regression test, run it

#### Test claims

- Run the referenced tests
- Verify they pass
- Verify the test count matches claims

#### Performance claims

- Run any benchmarks referenced in the PR
- Compare results against the baseline if provided
- Note whether the methodology is sound

For each claim, record the result:

| Status | Meaning |
|--------|---------|
| **Validated** | Runtime execution confirms the claim |
| **Partially validated** | Mostly true but has caveats |
| **Not validated** | Could not confirm (test couldn't run, ambiguous result) |
| **Contradicted** | Runtime output contradicts the claim |

### 6. Record demonstrations

Create a recordings directory, then delegate each demonstration to the matching recording skill. Both skills are self-contained: read their `SKILL.md`, pass the inputs below, and collect the rendered asset paths.

```bash
mkdir -p /tmp/validate-pr-$PR_NUMBER/recordings
```

#### CLI claims -> `/record-asciinema`

For each CLI claim, read [`../record-asciinema/SKILL.md`](../record-asciinema/SKILL.md) and invoke it with:

- `RECORD_SLUG` = a slug for the claim (e.g. `verbose-flag`)
- `RECORD_TITLE` = `PR #$PR_NUMBER: <claim description>`
- `RECORD_DIR` = `/tmp/validate-pr-$PR_NUMBER/recordings`
- `RECORD_COMMAND` = the command that demonstrates the claim

Collect the returned GIF/SVG/`.cast` path for each claim.

#### Web UI claims -> `/record-playwright`

First ensure the dev server is running inside the worktree (start it in the background, e.g. `npm run dev`). Then for each web UI claim, read [`../record-playwright/SKILL.md`](../record-playwright/SKILL.md) and invoke it with:

- `RECORD_SLUG` = a slug for the claim (e.g. `login-page`)
- `RECORD_URL` = the route the claim refers to (e.g. `http://localhost:3000/login`)
- `RECORD_DIR` = `/tmp/validate-pr-$PR_NUMBER/recordings`
- `RECORD_VIEWPORTS` = the viewports the claim names; default to desktop + mobile
- `RECORD_SCENARIO` = the interaction steps to perform before capture (if the claim is about behavior)
- `RECORD_VIDEO` = set if the claim is about an interaction/animation

Collect the returned PNG/video paths for each claim. Kill the dev server before moving on.

### 7. Upload assets and post validation report

Upload all rendered assets (GIFs, PNGs, videos, or raw `.cast` fallbacks) to the PR branch so they can be referenced inline:

```bash
RECORDINGS=/tmp/validate-pr-$PR_NUMBER/recordings
for asset in $RECORDINGS/*.gif $RECORDINGS/*.png $RECORDINGS/*.svg $RECORDINGS/*.webm $RECORDINGS/*.cast; do
  [ -f "$asset" ] || continue
  filename=$(basename "$asset")
  gh api repos/$REPO/contents/.validate-pr/$filename \
    --method PUT \
    -f message="Add demo: $filename" \
    -f content="$(base64 -w 0 "$asset")" \
    -f branch="$HEAD_BRANCH"
done
```

Then post the validation report:

```bash
BODY="$(cat <<'EOF'
## Validation Report

### Summary

| Status | Count |
|--------|-------|
| Validated | N |
| Partially validated | N |
| Not validated | N |
| Contradicted | N |

<details>
<summary>Details</summary>

### Claims

#### 1. "<claim text>"
- **Type**: feature / fix / behavior / CLI / web UI / test / performance
- **Status**: Validated / Partially validated / Not validated / Contradicted
- **Evidence**: <what was run, what output was observed>
- **Recording**: ![demo](raw-github-url-to-asset) *(CLI and web UI claims)*

#### 2. "<claim text>"
...

### Demonstrations

<embedded GIFs (CLI) / screenshots + video (web UI) / links>

</details>

---

EOF
)"
FOOTER="Posted with [validate-pr](${SKILL_FILE_URL}) (\`${SKILL_SHORT_SHA}\`)"
gh pr comment $PR_NUMBER --repo $REPO --body "${BODY}

${FOOTER}"
```

### 8. Clean up

After posting results, offer to clean up:

```bash
git worktree remove ../$WORKTREE_NAME
rm -rf /tmp/validate-pr-$PR_NUMBER
```

## Failure Modes

| Mode | Response |
|------|----------|
| **No verifiable claims in PR description** | Post comment asking author to list specific claims, stop |
| **Worktree creation fails** | Fall back to a regular checkout |
| **Build fails** | Post build failure with error output, stop |
| **asciinema not available** | `/record-asciinema` returns nothing; capture CLI stdout/stderr as text, skip the GIF |
| **Playwright/Chromium not available** | `/record-playwright` returns nothing; describe the web UI change in text, skip the screenshot |
| **Dev server won't start** | Skip web UI capture; note in the report and validate via unit tests where possible |
| **No rendering tool available** | Upload raw `.cast` files with playback instructions |
| **Upload fails** | Include command output as text in the comment |

## Example Usage

**Scenario 1: Feature PR with CLI changes**
```
/validate-pr 42 owner/myrepo
```
PR #42 adds `--verbose` flag and `export` command. Creates worktree, builds, runs `tool --verbose` and `tool export`, records both via `/record-asciinema`, uploads GIFs and posts validation report.

**Scenario 2: Feature PR with web UI changes**
```
/validate-pr 77 owner/myrepo
```
PR #77 adds a login page at `/login` with a mobile layout. Creates worktree, builds, starts the dev server, captures desktop and mobile screenshots via `/record-playwright`, uploads them and posts a validation report with the images embedded.

**Scenario 3: Bug fix PR**
```
/validate-pr 88
```
PR #88 fixes a null pointer on empty email field. Reproduces the crash scenario, confirms it no longer crashes, runs regression test. Posts validation report.

**Scenario 4: Build fails**
```
/validate-pr 15
```
PR #15 fails to build due to missing dependency. Posts build error as comment and stops.

## Next Step

After validation passes, use `/verify-pr` for static code inspection, or `/review-pr` for a comprehensive code review.
