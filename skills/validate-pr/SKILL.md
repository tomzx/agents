---
name: validate-pr
description: Checkout a PR's branch in a worktree, build it, run it, and validate every claim in the PR description through runtime proof. Records CLI demos with asciinema, renders to video, and attaches results to the PR.
allowed-tools: Bash(gh:*, git:*, scripts/get-env:*), Read, Write, Edit, Glob, Grep
argument-hint: "<pr-number> [repository]"
---

# Validate Pull Request

Checkout a PR's branch in a worktree, build, run, and prove every claim in the PR description through actual execution. For CLI changes, records demonstrations with asciinema, renders to GIF, and uploads. Posts a validation report to the PR.

This is runtime validation: "did you build the right thing?" Static code inspection is handled by `/verify-pr`.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `gh` CLI authenticated with read access to the target repository
- `git worktree` available
- `asciinema` installed (for CLI changes)
- `agg`, `asciicast2gif`, or `svg-term-cli` installed (for rendering .cast to video)
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
CLI changes detected?
    /          \
  Yes            No
   |              |
   v              v
Record with     Compile
asciinema       results
   |
   v
Render .cast to GIF
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
- Use asciinema to record the demonstration (see Step 6)

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

### 6. Record CLI changes with asciinema

If the PR changes CLI code (commands, flags, output format, help text, etc.):

1. Create a recordings directory:

```bash
mkdir -p /tmp/validate-pr-$PR_NUMBER/recordings
```

2. For each CLI claim, record a demonstration:

```bash
asciinema rec /tmp/validate-pr-$PR_NUMBER/recordings/<claim-slug>.cast \
  --overwrite \
  --command="<command to demonstrate>" \
  --title="PR #$PR_NUMBER: <claim description>"
```

For multi-step demonstrations:

```bash
asciinema rec /tmp/validate-pr-$PR_NUMBER/recordings/<claim-slug>.cast \
  --overwrite \
  --title="PR #$PR_NUMBER: <claim description>"
# Run the relevant CLI commands
# Type exit or Ctrl-D when done
```

3. Verify the recording matches the claim:

```bash
asciinema cat /tmp/validate-pr-$PR_NUMBER/recordings/<claim-slug>.cast
```

### 7. Render .cast files to GIF

Convert each recording to GIF for GitHub embedding. Try tools in order:

```bash
RECORDINGS=/tmp/validate-pr-$PR_NUMBER/recordings

# Try agg first (fastest, best quality)
if command -v agg &>/dev/null; then
  for cast in $RECORDINGS/*.cast; do
    slug=$(basename "$cast" .cast)
    agg "$cast" "$RECORDINGS/${slug}.gif"
  done

# Fall back to asciicast2gif
elif command -v asciicast2gif &>/dev/null; then
  for cast in $RECORDINGS/*.cast; do
    slug=$(basename "$cast" .cast)
    asciicast2gif "$cast" "$RECORDINGS/${slug}.gif"
  done

# Last resort: svg-term
elif command -v svg-term &>/dev/null; then
  for cast in $RECORDINGS/*.cast; do
    slug=$(basename "$cast" .cast)
    svg-term --in "$cast" --out "$RECORDINGS/${slug}.svg" --window
  done
fi
```

### 8. Upload recordings and post validation report

Upload GIFs to the PR branch so they can be referenced inline:

```bash
for gif in /tmp/validate-pr-$PR_NUMBER/recordings/*.gif; do
  filename=$(basename "$gif")
  gh api repos/$REPO/contents/.validate-pr/$filename \
    --method PUT \
    -f message="Add demo: $filename" \
    -f content="$(base64 -w 0 "$gif")" \
    -f branch="$HEAD_BRANCH"
done
```

Then post the validation report:

```bash
gh pr comment $PR_NUMBER --repo $REPO --body "$(cat <<'EOF'
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
- **Type**: feature / fix / behavior / CLI / test / performance
- **Status**: Validated / Partially validated / Not validated / Contradicted
- **Evidence**: <what was run, what output was observed>
- **Recording**: ![demo](raw-github-url-to-gif) *(CLI claims only)*

#### 2. "<claim text>"
...

### CLI Demonstrations

<embedded GIFs or links>

</details>

---

Posted with [validate-pr](SKILL_FILE_URL) (`SKILL_SHORT_SHA`)
EOF
)"
```

### 9. Clean up

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
| **asciinema not available** | Validate CLI claims by capturing stdout/stderr as text, skip recording |
| **No rendering tool available** | Upload raw .cast files with playback instructions |
| **Upload fails** | Include command output as text in the comment |

## Example Usage

**Scenario 1: Feature PR with CLI changes**
```
/validate-pr 42 owner/myrepo
```
PR #42 adds `--verbose` flag and `export` command. Creates worktree, builds, runs `tool --verbose` and `tool export`, records both with asciinema, renders to GIF, uploads and posts validation report.

**Scenario 2: Bug fix PR**
```
/validate-pr 88
```
PR #88 fixes a null pointer on empty email field. Reproduces the crash scenario, confirms it no longer crashes, runs regression test. Posts validation report.

**Scenario 3: Build fails**
```
/validate-pr 15
```
PR #15 fails to build due to missing dependency. Posts build error as comment and stops.

## Next Step

After validation passes, use `/verify-pr` for static code inspection, or `/review-pr` for a comprehensive code review.
