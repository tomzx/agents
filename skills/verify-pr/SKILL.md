---
name: verify-pr
description: Verify that a PR conforms to its specified requirements (acceptance criteria). Combines static criteria-to-code traceability with runtime execution that proves each criterion by building and running the PR. Records CLI demos (asciinema) and web UI captures (Playwright). Does not judge code craft (that is review-pr) or whether the target is the right product (that is validate-pr).
allowed-tools: Bash(gh:*, git:*, ghx:*, asciinema:*, agg:*, npx:*, node:*, uv:*, python:*, python3:*, curl:*, ~/.agents/scripts/get-env:*, ~/.agents/scripts/should-post-to-github:*), Read, Write, Edit, Glob, Grep
argument-hint: "<pr-number> [repository]"
---

# Verify Pull Request

Answers the **verification** question: "Are we building the product right?" Checks that the implementation **conforms to its specified requirements** (the linked issue's acceptance criteria), by combining:

1. **Static traceability**: every criterion maps to specific code that implements it.
2. **Runtime proof**: build the PR and execute each criterion, recording the evidence.

It does **not** judge whether the target is the right product, that is `/validate-pr`'s job ("are we building the right product?"). It does **not** judge code craft (quality, architecture, security, tests), that is `/review-pr`'s job. CI handles build verification, linting, type checking, and test suite execution; verify-pr does not report on those. Its unique role is criteria-to-code traceability and per-criterion runtime proof (targeted scenario execution and demo recording). If a finding is about *how the code is written* rather than *whether the criteria are met*, route it to `/review-pr` instead.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, target the pull request from `$PR_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with read access to the target repository
- `git worktree` available
- For CLI changes: `asciinema` plus a renderer (`agg` preferred). Provided by [`/record-asciinema`](../record-asciinema/SKILL.md).
- For web UI changes: Playwright (Node or Python) with Chromium. Provided by [`/record-playwright`](../record-playwright/SKILL.md).
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `verify-pr`.

## Workflow

```
Fetch PR metadata + diff + linked issue(s) ($1)
          |
          v
Parse acceptance criteria + claims, build coverage map
          |
          v
Linked issue w/ acceptance criteria?
   /          \
  Yes           No
   |             |
   v             v
Static traceability   Post comment: link an issue
(criteria -> code)     or list criteria, stop
   |
   v
Create git worktree on PR branch
   |
   v
Install dependencies / build
(setup for runtime proof;
CI handles build status)
    |
    v
Build succeeded?
  /          \
 Yes           No
  |             |
  v             v
Validate each   Note build failure, stop
criterion at runtime
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
Write the conformance report (traceability + runtime evidence)
    |
    v
Clean up worktree
```

## Steps

### 1. Fetch PR metadata, diff, and linked issue(s)

```bash
gh pr view $PR_NUMBER --repo $REPO --json title,body,headRefName,headRefOid,author,baseRefName,files,additions,deletions,changedFiles,closingIssuesReferences
```

```bash
gh pr diff $PR_NUMBER --repo $REPO
```

Extract:
- PR title and description (body) with claims
- `HEAD_COMMIT`: the `headRefOid` (latest commit SHA, full)
- `SHORT_SHA`: first 7 characters of `HEAD_COMMIT`
- `PR_AUTHOR`: the `author.login` (GitHub username of the PR author)
- Head branch name (`headRefName`), base branch name (`baseRefName`)
- List of changed files and diff stats
- Linked closing issues from `closingIssuesReferences` (each has `number` and `url`)
- `ISSUE_NUMBER`: the first linked issue number from `closingIssuesReferences` (or empty if none)

#### 1a. Resolve and fetch linked issue(s)

Use `closingIssuesReferences` as the authoritative source of linked issues. If empty, fall back to scanning the PR body for `Fixes #N`, `Closes #N`, `Resolves #N`, or bare `#N` references.

For each linked issue number, fetch its full body:

```bash
gh issue view $ISSUE_NUMBER --repo $REPO --json number,title,body,state
```

### 2. Parse acceptance criteria and build the coverage map

#### 2a. Extract acceptance criteria from the linked issue(s)

For each linked issue body, look for the structured acceptance criteria produced by [`/create-issue`](../create-issue/SKILL.md): an `# Acceptance Criteria` heading followed by `## Must` and (optionally) `## Should` subsections, each containing `- [ ]` checklist items.

Parse every checklist item into a criterion record:
- The criterion text (quoted verbatim from the issue)
- Its priority: **Must** (gates conformance) or **Should** (deferrable)
- The source issue number

**Must** criteria are the conformance gate. **Should** criteria are verified if the PR addresses them but do not block conformance on their own.

If the linked issue does not use the structured format, extract requirements from whatever is present (a `## Requirements` section, numbered lists, prose) and convert each into a **Must** criterion unless clearly deferrable, noting in the report that criteria were inferred.

If multiple issues are linked, merge their criteria, preserving the source issue number on each.

If no linked issue can be resolved, or none yields parseable criteria, post a comment asking the author to link an issue with acceptance criteria (or list them explicitly) and stop. Do not verify PR claims in a vacuum.

#### 2b. Parse claims from the PR description

Extract runtime-validatable claims from the PR description (feature, fix, behavior, CLI, web UI, performance, test). Claims are hints that help pick what to run and what to record; the criteria, not the claims, decide what counts as conforming. Claims that map to no criterion are flagged as out of scope relative to the issue.

#### 2c. Build the coverage map

Cross-reference each acceptance criterion against the PR claims:

| Criterion state | Meaning |
|---|---|
| **Mapped** | At least one PR claim speaks to this criterion |
| **Unmapped (gap)** | No PR claim addresses this criterion. Still trace and attempt to validate it from the diff and codebase, and flag the gap |

Also track **Unmapped claims**: PR claims that correspond to no acceptance criterion. These are flagged as out of scope relative to the issue (a conformance concern, distinct from code-craft).

### 3. Static traceability: criteria to code

For each acceptance criterion, trace it to the specific code changes that implement it. This is the static half of conformance, done before building.

- Identify the exact files and functions/classes that implement each criterion
- Verify the implementation path is reachable (no dead code, no unused entry points)
- Check that imports and wiring connect the pieces correctly
- Verify no criterion depends on code that was not included in the PR

A criterion with no code backing it is a **gap**, regardless of whether a PR claim references it. Code that implements no criterion is out of scope and is called out.

Record the static mapping:

| Criterion (priority) | Source issue | Claim(s) | File(s) | Function(s)/Class(es) | Line(s) | Static status |
|---|---|---|---|---|---|---|

Where Static status is **Traced** (code backs the criterion) or **Gap** (no implementing code found).

### 4. Create a git worktree on the PR branch

If `$WORKTREE_DIR` is already set (e.g. by an orchestrator like `review-requested-prs`), use that directory directly and skip creation and cleanup. The orchestrator manages the worktree lifecycle.

```bash
_WORKTREE_OWNER=false
if [ -z "${WORKTREE_DIR:-}" ]; then
  git fetch origin $HEAD_BRANCH
  WORKTREE_DIR=/tmp/sdlc/$REPO/${ISSUE_NUMBER:-pr-$PR_NUMBER}
  mkdir -p /tmp/sdlc/$REPO
  git worktree add $WORKTREE_DIR origin/$HEAD_BRANCH
  _WORKTREE_OWNER=true
fi
```

All subsequent work happens inside the worktree directory.

If worktree creation fails, stop.

### 5. Install dependencies and build

CI typically handles build verification; this step is a setup prerequisite for per-criterion runtime proof, not a conformance finding.

Detect the project type and install/build:

```bash
ls package.json Cargo.toml pyproject.toml go.mod Makefile 2>/dev/null
```

Follow the project's standard install and build process. Check `.sdlc/context/` for project-specific build instructions if available.

If the build fails, note it and stop. CI would typically catch this first; do not report build status as a conformance finding.

### 6. Validate each acceptance criterion at runtime

For every acceptance criterion, prove or disprove through execution that the PR meets it. The criterion's nature (refined by any mapped claim) determines the method. **Must** criteria must all be validated for the PR to conform.

#### Behavior criteria

- Write a small script or test that exercises the behavior the criterion requires
- Run it and verify the output matches what the criterion specifies
- If the mapped claim references an existing test, run that specific test
- Capture stdout/stderr and exit code as evidence

#### CLI criteria

- Identify the CLI entry point from the codebase
- Run the command/flag the criterion requires and verify output
- Record the demonstration via `/record-asciinema` (see Step 7)

#### Web UI criteria

- Identify the route/page the criterion refers to from the codebase (router config, page components)
- Start the dev server (or confirm it is running) and load the route
- Verify the element/behavior the criterion requires is present in the rendered page
- Capture screenshots (and a video if the criterion is about interaction) via `/record-playwright` (see Step 7)
- Cover the viewports the criterion names (mobile, desktop); if unspecified, capture both

#### Fix criteria

- Reproduce the original bug scenario described in the issue on this branch
- Verify the fix prevents the reported behavior
- If the PR includes a regression test, run it

#### Test criteria

- Verify the referenced tests map to and prove the criterion (traceability)
- CI runs the test suite; do not re-report pass/fail status that CI already covers
- Verify the test count matches what the criterion requires

#### Performance criteria

- Run any benchmarks referenced in the criterion or PR
- Compare results against the baseline if provided

For each criterion, record the runtime result combined with its static status:

| Status | Meaning |
|--------|---------|
| **Conforms** | Code traced (Step 3) and runtime execution confirms the criterion is met |
| **Conforms (static only)** | Code traced but runtime could not confirm (test couldn't run, ambiguous result); note the reason |
| **Not verified** | Could not confirm (no path to verify at runtime, and static trace inconclusive) |
| **Nonconforming** | Runtime output, or the absence of implementing code, shows the criterion is not met |

A **Must** criterion that is Not verified or Nonconforming means the PR does not conform to its specification. Say so explicitly in the report.

### 7. Record demonstrations

Create a recordings directory, then delegate each demonstration to the matching recording skill. Both skills are self-contained: read their `SKILL.md`, pass the inputs below, and collect the rendered asset paths.

```bash
mkdir -p /tmp/verify-pr-$PR_NUMBER/recordings
```

#### CLI criteria -> `/record-asciinema`

For each CLI criterion, read [`../record-asciinema/SKILL.md`](../record-asciinema/SKILL.md) and invoke it with:

- `RECORD_SLUG` = a slug for the criterion (e.g. `verbose-flag`)
- `RECORD_TITLE` = `PR #$PR_NUMBER: <criterion description>`
- `RECORD_DIR` = `/tmp/verify-pr-$PR_NUMBER/recordings`
- `RECORD_COMMAND` = the command that demonstrates the criterion is met

Collect the returned GIF/SVG/`.cast` path for each criterion.

#### Web UI criteria -> `/record-playwright`

First ensure the dev server is running inside the worktree (start it in the background, e.g. `npm run dev`). Then for each web UI criterion, read [`../record-playwright/SKILL.md`](../record-playwright/SKILL.md) and invoke it with:

- `RECORD_SLUG` = a slug for the criterion (e.g. `login-page`)
- `RECORD_URL` = the route the criterion refers to (e.g. `http://localhost:3000/login`)
- `RECORD_DIR` = `/tmp/verify-pr-$PR_NUMBER/recordings`
- `RECORD_VIEWPORTS` = the viewports the criterion names; default to desktop + mobile
- `RECORD_SCENARIO` = the interaction steps to perform before capture (if the criterion is about behavior)
- `RECORD_VIDEO` = set if the criterion is about an interaction/animation

Collect the returned PNG/video paths for each criterion. Kill the dev server before moving on.

### 8. Upload assets and write the conformance report

Upload all rendered assets (GIFs, PNGs, videos, or raw `.cast` fallbacks) to the PR branch so they can be referenced inline:

```bash
RECORDINGS=/tmp/verify-pr-$PR_NUMBER/recordings
for asset in $RECORDINGS/*.gif $RECORDINGS/*.png $RECORDINGS/*.svg $RECORDINGS/*.webm $RECORDINGS/*.cast; do
  [ -f "$asset" ] || continue
  filename=$(basename "$asset")
  gh api repos/$REPO/contents/.verify-pr/$filename \
    --method PUT \
    -f message="Add demo: $filename" \
    -f content="$(base64 -w 0 "$asset")" \
    -f branch="$HEAD_BRANCH"
done
```

Write the report to a file:

```bash
BODY="$(cat <<'EOF'
<!-- {"step":"verify-pr","sha":"HEAD_COMMIT","verdict":"MARKER_VERDICT"} -->
## Verification Report

### Summary

Issue(s): #N
Verified commit: SHORT_SHA

| Status | Must | Should |
|--------|------|--------|
| Conforms | N | N |
| Conforms (static only) | N | N |
| Not verified | N | N |
| Nonconforming | N | N |

**PR conforms to specification:** Yes / No *(No if any Must criterion is Not verified or Nonconforming)*

The marker verdict is `pass` if the PR conforms (Yes), `fail` if it does not (No).

<details>
<summary>Details</summary>

### Criteria conformance

| # | Criterion | Priority | Static | Runtime | Evidence |
|---|---|---|---|---|---|
| 1 | "<criterion text>" | Must | Traced | Conforms | <what was run, observed output> |
| 2 | "<criterion text>" | Must | Gap | Nonconforming | <reason> |

### Unmapped PR claims (out of scope relative to issue)

- "<claim text>" — no acceptance criterion maps to this

### Demonstrations

<embedded GIFs (CLI) / screenshots + video (web UI) / links, one per criterion>

</details>

---

EOF
 )"
 
 # Substitute the marker verdict: pass if PR conforms, fail if not
 BODY="${BODY//MARKER_VERDICT/pass}"  # replace with pass or fail
 BODY="${BODY//HEAD_COMMIT/$HEAD_COMMIT}"
 BODY="${BODY//SHORT_SHA/$SHORT_SHA}"
 
 # Report location is reviewer-owned, not in the repo: see sdlc/references/shared.md
 # (PR Review Reports). Survives worktree removal and never pollutes the checked-out repo.
 PR_REVIEW_DIR="$HOME/.sdlc/$REPO/pull-requests/$PR_NUMBER"
 mkdir -p "$PR_REVIEW_DIR"
 printf '%s\n' "${BODY}" > "$PR_REVIEW_DIR/verify-pr.$SHORT_SHA.md"
```

### Post the conformance report as a PR comment

The report is saved to `$PR_REVIEW_DIR/verify-pr.$SHORT_SHA.md`. Posting it as a PR comment is decided by `should-post-to-github`.

Run `~/.agents/scripts/should-post-to-github --repo "$REPO" --author "$PR_AUTHOR"`. If it exits 1, skip posting; the report is already saved to `$PR_REVIEW_DIR/verify-pr.$SHORT_SHA.md`.

If it exits 0, post the report file as a comment on the PR. The file already contains the `<!-- {"step":"verify-pr","sha":"HEAD_COMMIT","verdict":"MARKER_VERDICT"} -->` marker.

```bash
FOOTER="Posted with [verify-pr](${SKILL_FILE_URL}) (\`${SKILL_SHORT_SHA}\`)"
gh pr comment $PR_NUMBER --repo $REPO --body "$(cat "$PR_REVIEW_DIR/verify-pr.$SHORT_SHA.md")

${FOOTER}"
```

### 9. Clean up

After posting results, clean up:

```bash
if [ "$_WORKTREE_OWNER" = true ]; then
  git worktree remove $WORKTREE_DIR
fi
```

## Failure Modes

| Mode | Response |
|------|----------|
| **No linked issue, or no parseable acceptance criteria** | Save a comment asking author to link an issue with acceptance criteria (or list them explicitly), stop. Do not verify PR claims in a vacuum |
| **PR description has no claims** | Proceed; criteria drive verification, claims are optional hints. Note the absence of claims in the report |
| **Worktree creation fails** | Stop |
| **Build fails** | Note it and stop; CI would typically catch this first. Do not report as a conformance finding |
| **asciinema not available** | `/record-asciinema` returns nothing; capture CLI stdout/stderr as text, skip the GIF |
| **Playwright/Chromium not available** | `/record-playwright` returns nothing; describe the web UI change in text, skip the screenshot |
| **Dev server won't start** | Skip web UI capture; note in the report and verify via unit tests where possible. Criteria that needed the server become Conforms (static only) if traced, else Not verified |
| **No rendering tool available** | Upload raw `.cast` files with playback instructions |
| **Upload fails** | Include command output as text in the comment |
| **Large diff (>1000 lines)** | Focus on entry points and public API changes for traceability; note that full static review is impractical |

## Example Usage

**Scenario 1: Feature PR with CLI changes, conforms**
```
/verify-pr 42 owner/myrepo
```
PR #42 is linked to issue #31 whose Must criteria require a `--verbose` flag and an `export` command. Traces both criteria to code, creates a worktree, builds, runs `tool --verbose` and `tool export`, records both via `/record-asciinema`, uploads GIFs and saves a conformance report. All Must criteria Conform. Posts the report as a PR comment unless `should-post-to-github` excludes the repo or author.

**Scenario 2: Feature PR with web UI changes**
```
/verify-pr 77 owner/myrepo
```
PR #77 is linked to an issue requiring a login page at `/login` with a mobile layout. Traces the criterion to the page component, creates a worktree, builds, starts the dev server, captures desktop and mobile screenshots via `/record-playwright`, uploads them and saves a conformance report with the images embedded. Posts the report as a PR comment unless `should-post-to-github` excludes the repo or author.

**Scenario 3: Bug fix PR, nonconforming**
```
/verify-pr 88
```
PR #88 is linked to a bug report whose Must criterion is "no null pointer on empty email field". Traces a check into the controller, but reproducing the crash scenario at runtime still throws because the fix is in the wrong layer. Reports the criterion as Nonconforming and the PR as not conforming to spec.

**Scenario 4: Out-of-scope PR**
```
/verify-pr 90
```
PR #90 implements a `--quiet` flag the author claims, but no acceptance criterion covers it, and one Must criterion is left with no implementing code. Verification flags the claim as out of scope and the criterion as a Gap, and reports the PR as not conforming.

**Scenario 5: Build fails**
```
/verify-pr 15
```
PR #15 fails to build due to missing dependency. Notes the build failure and stops. CI would typically catch this first.

## Next Step

After conformance is confirmed, use `/review-pr` for the code-craft review (quality, architecture, security, tests, operational concerns). If `/validate-pr` has not yet run, consider running it first to confirm the target is the right product before investing in craft review.
