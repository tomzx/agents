---
name: validate-pr
description: Checkout a PR's branch in a worktree, build it, run it, and validate that the linked issue's acceptance criteria are actually met through runtime proof. Cross-references PR claims against issue criteria, records CLI demos (via record-asciinema) and web UI demos (via record-playwright), and posts a coverage report to the PR.
allowed-tools: Bash(gh:*, git:*, asciinema:*, agg:*, npx:*, node:*, uv:*, python:*, python3:*, curl:*, scripts/get-env:*, scripts/should-post-github-comment:*), Read, Write, Edit, Glob, Grep
argument-hint: "<pr-number> [repository]"
---

# Validate Pull Request

Checkout a PR's branch in a worktree, build, run, and prove that the linked issue's acceptance criteria are met through actual execution. The acceptance criteria from the linked issue drive validation. Claims in the PR description are cross-referenced against those criteria: every criterion must be validated, and claims that don't map to any criterion are flagged as out of scope. For CLI changes, records demonstrations via `/record-asciinema` (rendered to GIF). For web UI changes, captures screenshots/video via `/record-playwright`. Uploads all assets and posts a coverage report to the PR.

This is runtime validation: "did you build the right thing, and does it satisfy what was asked?" Static code inspection is handled by `/verify-pr`.

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
Fetch PR metadata + diff + linked issue(s) ($1)
         |
         v
Parse acceptance criteria from issue(s)
+ claims from PR description
         |
         v
Build coverage map (criteria <-> claims)
         |
         v
Linked issue w/ acceptance criteria?
    /          \
   Yes           No
    |             |
    v             v
Create git       Post comment: link an issue
worktree          or list criteria, stop
on PR branch
    |
    v
Install dependencies / build
    |
    v
Build succeeded?
   /          \
  Yes           No
   |             |
   v             v
Validate each   Post build failure, stop
acceptance criterion
at runtime (criteria
gate, claims give hints)
    |
    v
Detect change surface
    |
    +--- CLI changes? ----> /record-asciinema per criterion
    |
    +--- Web UI changes? --> /record-playwright per criterion
    |
    v
Collect assets (GIFs / PNGs / video)
    |
    v
Upload assets to PR branch
    |
    v
Post coverage report + recordings
    |
    v
Clean up worktree
```

## Steps

### 1. Fetch PR metadata and linked issue(s)

```bash
gh pr view $PR_NUMBER --repo $REPO --json title,body,headRefName,headRefOid,author,baseRefName,files,additions,deletions,changedFiles,closingIssuesReferences
```

Extract:
- PR title and description (body)
- Head branch name (`headRefName`)
- `HEAD_COMMIT`: the `headRefOid` (latest commit SHA, full)
- `SHORT_SHA`: first 7 characters of `HEAD_COMMIT`
- `PR_AUTHOR`: the `author.login` (GitHub username of the PR author)
- Base branch name (`baseRefName`)
- List of changed files
- Diff stats
- Linked closing issues from `closingIssuesReferences` (each has `number` and `url`)

Also fetch the full diff to identify changed modules and entry points:

```bash
gh pr diff $PR_NUMBER --repo $REPO
```

#### 1a. Resolve and fetch linked issue(s)

Use the `closingIssuesReferences` from the PR metadata as the authoritative source of linked issues. If it is empty, fall back to scanning the PR body for `Fixes #N`, `Closes #N`, `Resolves #N`, or bare `#N` references (in that order of priority).

For each linked issue number, fetch its full body:

```bash
gh issue view $ISSUE_NUMBER --repo $REPO --json number,title,body,state
```

Keep the issue bodies for Step 2. If no linked issue can be resolved, see the "No linked issue" failure mode (Step 2) rather than silently falling back to PR claims alone.

### 2. Parse acceptance criteria from the issue(s) and build the coverage map

The linked issue's acceptance criteria are the validation target. PR description claims are secondary: they tell you how the author says the work was done, but the criteria decide what counts as met.

#### 2a. Extract acceptance criteria from the linked issue(s)

For each linked issue body, look for the structured acceptance criteria produced by [`/create-issue`](../create-issue/SKILL.md):

- An `# Acceptance Criteria` heading followed by `## Must` and (optionally) `## Should` subsections, each containing `- [ ]` checklist items.

Parse every checklist item into a criterion record:

- The criterion text (quoted verbatim from the issue)
- Its priority: **Must** (gates "done") or **Should** (deferrable)
- The source issue number

**Must** criteria are the validation gate. **Should** criteria are validated if the PR addresses them but do not block success on their own.

If the linked issue does not use the structured format, extract requirements from whatever is present (a `## Requirements` section, numbered requirement lists, the issue body prose). Convert each into a criterion with priority **Must** unless the text clearly marks it deferrable, and note in the report that the criteria were inferred rather than structured.

If multiple issues are linked, merge their criteria, preserving the source issue number on each.

If no linked issue was resolved in Step 1, or none of the linked issues yield any parseable criteria, post a comment asking the author to link an issue with acceptance criteria (or to list the criteria explicitly) and stop. Do not validate PR claims in a vacuum.

#### 2b. Parse claims from the PR description

Analyze the PR description and extract runtime-validatable claims (the same categories as before: feature, fix, behavior, CLI, web UI, performance, test). For each claim, record the claim text and type.

Claims are hints, not the gate. They help you pick what to run and what to record, and they surface work the author did that may be out of scope for the issue.

#### 2c. Build the coverage map

Cross-reference each acceptance criterion against the PR claims:

| Criterion state | Meaning |
|---|---|
| **Mapped** | At least one PR claim speaks to this criterion |
| **Unmapped (gap)** | No PR claim addresses this criterion. Still attempt to validate it from the diff and codebase, and flag the gap in the report. |

Also track **Unmapped claims**: PR claims that do not correspond to any acceptance criterion. These are flagged as out of scope relative to the issue.

The output of this step is a list of validation targets, one per acceptance criterion, each carrying:
- The criterion text and priority
- The mapped PR claim(s), if any
- The runtime test to perform (command to run, output to expect, exit code, route to load, etc.) derived primarily from the criterion, refined by the mapped claim(s) and the diff

**Must** criteria with no mapped claim and no derivable runtime test are recorded as "Not validated, no path to verify" and called out in the report.

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

### 5. Validate each acceptance criterion at runtime

For every acceptance criterion, prove or disprove that the PR meets it through execution. The criterion's nature (refined by any mapped claim) determines the method. **Must** criteria must all be validated for the issue to count as resolved.

#### Behavior criteria

- Write a small script or test that exercises the behavior the criterion requires
- Run it and verify the output matches what the criterion specifies
- If the mapped claim references an existing test, run that specific test
- Capture stdout/stderr and exit code as evidence

#### CLI criteria

- Identify the CLI entry point from the codebase
- Run the command/flag the criterion requires and verify output
- Record the demonstration via `/record-asciinema` (see Step 6)

#### Web UI criteria

- Identify the route/page the criterion refers to from the codebase (router config, page components)
- Start the dev server (or confirm it is running) and load the route
- Verify the element/behavior the criterion requires is present in the rendered page
- Capture screenshots (and a video if the criterion is about interaction) via `/record-playwright` (see Step 6)
- Cover the viewports the criterion names (mobile, desktop); if unspecified, capture both

#### Fix criteria

- Reproduce the original bug scenario described in the issue on this branch
- Verify the fix prevents the reported behavior
- If the PR includes a regression test, run it

#### Test criteria

- Run the referenced tests
- Verify they pass
- Verify the test count matches what the criterion requires

#### Performance criteria

- Run any benchmarks referenced in the criterion or PR
- Compare results against the baseline if provided
- Note whether the methodology is sound

For each criterion, record the result:

| Status | Meaning |
|--------|---------|
| **Validated** | Runtime execution confirms the criterion is met |
| **Partially validated** | Mostly met but has caveats |
| **Not validated** | Could not confirm (test couldn't run, ambiguous result, no path to verify) |
| **Contradicted** | Runtime output shows the criterion is not met |

A **Must** criterion that is Not validated or Contradicted means the issue is not resolved by this PR. Say so explicitly in the report.

### 6. Record demonstrations

Create a recordings directory, then delegate each demonstration to the matching recording skill. Both skills are self-contained: read their `SKILL.md`, pass the inputs below, and collect the rendered asset paths.

```bash
mkdir -p /tmp/validate-pr-$PR_NUMBER/recordings
```

#### CLI criteria -> `/record-asciinema`

For each CLI criterion, read [`../record-asciinema/SKILL.md`](../record-asciinema/SKILL.md) and invoke it with:

- `RECORD_SLUG` = a slug for the criterion (e.g. `verbose-flag`)
- `RECORD_TITLE` = `PR #$PR_NUMBER: <criterion description>`
- `RECORD_DIR` = `/tmp/validate-pr-$PR_NUMBER/recordings`
- `RECORD_COMMAND` = the command that demonstrates the criterion is met

Collect the returned GIF/SVG/`.cast` path for each criterion.

#### Web UI criteria -> `/record-playwright`

First ensure the dev server is running inside the worktree (start it in the background, e.g. `npm run dev`). Then for each web UI criterion, read [`../record-playwright/SKILL.md`](../record-playwright/SKILL.md) and invoke it with:

- `RECORD_SLUG` = a slug for the criterion (e.g. `login-page`)
- `RECORD_URL` = the route the criterion refers to (e.g. `http://localhost:3000/login`)
- `RECORD_DIR` = `/tmp/validate-pr-$PR_NUMBER/recordings`
- `RECORD_VIEWPORTS` = the viewports the criterion names; default to desktop + mobile
- `RECORD_SCENARIO` = the interaction steps to perform before capture (if the criterion is about behavior)
- `RECORD_VIDEO` = set if the criterion is about an interaction/animation

Collect the returned PNG/video paths for each criterion. Kill the dev server before moving on.

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

Write the report to a file:

```bash
BODY="$(cat <<'EOF'
<!-- validate-pr:HEAD_COMMIT -->
## Validation Report

### Summary

Issue(s): #N

Validated commit: SHORT_SHA

| Status | Must | Should |
|--------|------|--------|
| Validated | N | N |
| Partially validated | N | N |
| Not validated | N | N |
| Contradicted | N | N |

**Issue resolved:** Yes / No *(No if any Must criterion is Not validated or Contradicted)*

<details>
<summary>Details</summary>

### Criteria coverage

| # | Criterion | Priority | Status | Mapped claim | Evidence |
|---|---|---|---|---|---|
| 1 | "<criterion text>" | Must | Validated | "<claim>" | <what was run, observed output> |
| 2 | "<criterion text>" | Must | Not validated | — | <reason> |

### Unmapped PR claims (out of scope relative to issue)

- "<claim text>" — no acceptance criterion maps to this

### Demonstrations

<embedded GIFs (CLI) / screenshots + video (web UI) / links, one per criterion>

</details>

---

EOF
)"

mkdir -p ".sdlc/pull-requests/$PR_NUMBER"
printf '%s\n' "${BODY}" > ".sdlc/pull-requests/$PR_NUMBER/validate-pr.$SHORT_SHA.md"
```

### Post the validation report as a PR comment

Run `scripts/should-post-github-comment --repo "$REPO" --author "$PR_AUTHOR"`. If it exits 1, skip posting.

If it exits 0, post the report file as a comment on the PR. The file already contains the `<!-- validate-pr:HEAD_COMMIT -->` marker.

```bash
FOOTER="Posted with [validate-pr](${SKILL_FILE_URL}) (\`${SKILL_SHORT_SHA}\`)"
gh pr comment $PR_NUMBER --repo $REPO --body "$(cat .sdlc/pull-requests/$PR_NUMBER/validate-pr.$SHORT_SHA.md)

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
| **No linked issue, or no parseable acceptance criteria** | Post comment asking author to link an issue with acceptance criteria (or list them explicitly), stop. Do not validate PR claims in a vacuum |
| **PR description has no claims** | Proceed; criteria drive validation, claims are optional hints. Note the absence of claims in the report |
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
PR #42 is linked to issue #31 whose Must criteria require a `--verbose` flag and an `export` command. Creates worktree, builds, runs `tool --verbose` and `tool export` against those criteria, records both via `/record-asciinema`, uploads GIFs and posts a coverage report.

**Scenario 2: Feature PR with web UI changes**
```
/validate-pr 77 owner/myrepo
```
PR #77 is linked to an issue requiring a login page at `/login` with a mobile layout. Creates worktree, builds, starts the dev server, captures desktop and mobile screenshots via `/record-playwright`, uploads them and posts a coverage report with the images embedded.

**Scenario 3: Bug fix PR**
```
/validate-pr 88
```
PR #88 is linked to a bug report whose Must criterion is "no null pointer on empty email field". Reproduces the crash scenario, confirms it no longer crashes, runs regression test. Posts coverage report.

**Scenario 4: Out-of-scope PR**
```
/validate-pr 90
```
PR #90 implements a `--quiet` flag the author claims, but no acceptance criterion covers it, and one Must criterion is left unmet. Validation flags the claim as out of scope and the criterion as Contradicted, and reports the issue as not resolved.

**Scenario 5: Build fails**
```
/validate-pr 15
```
PR #15 fails to build due to missing dependency. Posts build error as comment and stops.

## Next Step

After validation passes, use `/verify-pr` for static code inspection, or `/review-pr` for a comprehensive code review.
