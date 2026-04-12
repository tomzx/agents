---
name: initialize-developer-trust
description: Bootstrap a developer trust profile by scanning the last N merged PRs they authored in a repository. Synthesizes observations across all PRs and writes an initial trust profile.
allowed-tools: Bash(gh:*, git:*), Read, Write, Glob
argument-hint: <github_username> <owner/repo> [count]
---

# Initialize Developer Trust

Bootstraps a developer trust profile by analyzing the last N merged PRs they authored in a given repository. Applies the same observation and trust-level principles as `developer-trust-profile`, but processes a batch of PRs in one pass to produce a well-grounded initial profile.

## Prerequisites

- `gh` CLI authenticated with read access to the target repository
- `$1`: GitHub username of the developer
- `$2`: repository in `owner/repo` format
- `$3` (optional): number of PRs to scan (default: 10)

## Profile Location

```
~/.developer-trust/{github_username}.md
```

## Trust Levels

| Level | Meaning |
|-------|---------|
| `trusted` | Developer consistently produces high-quality PRs |
| `neutral` | Unknown or mixed track record |
| `cautious` | History of issues, missed edge cases, or unclear PRs |
| `always_reject` | Persistent quality/policy issues warranting manual review |

## Workflow

```
Ensure ~/.developer-trust is a git repo
              |
     Check for existing profile
              |
      Profile exists?
       /             \
     Yes              No
      |                |
  Warn user        Continue
  (confirm         (fresh start)
   overwrite)
              |
   Fetch last N merged PRs by author
              |
   For each PR: fetch metadata + diff
              |
   Synthesize observations across all PRs
   (strengths, weaknesses, patterns)
              |
   Determine trust level from evidence
              |
   Write profile file
              |
   git commit
```

## Steps

### 1. Initialize repository

Ensure `~/.developer-trust` exists and is a git repository:

```bash
mkdir -p ~/.developer-trust
git -C ~/.developer-trust init
```

### 2. Resolve arguments

Parse `$@`:
- `GITHUB_USERNAME`: `$1`
- `REPO`: `$2` (`owner/repo`)
- `COUNT`: `$3` if provided, otherwise `10`

`PROFILE_PATH`: `~/.developer-trust/{GITHUB_USERNAME}.md`

### 3. Check for existing profile

If `PROFILE_PATH` already exists, notify the user that a profile exists and that it will be overwritten by this initialization run. Continue with the process (no interactive confirmation needed, the user explicitly invoked this skill).

### 4. Fetch merged PRs by the author

```bash
gh pr list --repo {REPO} \
  --author {GITHUB_USERNAME} \
  --state merged \
  --limit {COUNT} \
  --json number,title,body,additions,deletions,changedFiles,labels,headRefName,mergedAt
```

If the result is empty (no merged PRs found), also try closed PRs:

```bash
gh pr list --repo {REPO} \
  --author {GITHUB_USERNAME} \
  --state closed \
  --limit {COUNT} \
  --json number,title,body,additions,deletions,changedFiles,labels,headRefName,closedAt
```

If still no PRs are found, report to the user that no PRs were found for `{GITHUB_USERNAME}` in `{REPO}` and stop. Do not create an empty profile.

Record the list of PR numbers found: `PR_NUMBERS`.

### 5. Fetch diffs for each PR

For each PR number in `PR_NUMBERS`, fetch the diff:

```bash
gh pr diff {PR_NUMBER} --repo {REPO}
```

Collect the diff alongside the PR metadata. Process all PRs before synthesizing.

### 6. Synthesize observations across all PRs

Analyze the full set of PRs (metadata + diffs) holistically. Identify recurring patterns, not one-off occurrences. For each category below, extract observations that appear in multiple PRs or are strongly evidenced:

#### Strengths
Positive patterns seen consistently across PRs, for example:
- Well-structured or thorough tests
- Clear, descriptive PR titles and descriptions
- Good error handling
- Atomic, focused commits
- Consistent documentation updates
- Clean diff with no unrelated changes

#### Weaknesses
Problem areas observed in multiple PRs, for example:
- Missing or thin test coverage
- Vague PR descriptions
- Mixed concerns in a single PR
- Ignored edge cases
- Missing documentation for user-facing changes
- Large, hard-to-review diffs

#### PR Patterns
Recurring behaviors (positive or negative) that characterize this developer's style:
- PR size tendencies (small/large)
- Frequency of linked issues
- Common file types or areas changed
- Consistency of code style
- Whether PRs tend to be self-contained

### 7. Determine trust level

Based on the synthesized observations and the number of PRs reviewed, assign an initial trust level:

- **`trusted`**: Strong positive signal across most PRs (clean diffs, tests present, clear descriptions, no recurring issues). Requires at least 5 PRs to assign.
- **`neutral`**: Mixed or insufficient signal, or fewer than 5 PRs reviewed. Default when evidence is ambiguous.
- **`cautious`**: Recurring issues across multiple PRs (e.g., consistently missing tests, repeated unclear descriptions, frequent scope creep).
- **`always_reject`**: Reserved for severe or persistent policy violations that would warrant human review on every PR. Do not assign this level from batch analysis alone unless the evidence is unambiguous and severe.

Write a brief reason summarizing the evidence that led to the trust level.

### 8. Write the profile

Write `PROFILE_PATH` using the format below. Populate the Review History table with one row per PR scanned.

### 9. Commit the profile

```bash
git -C ~/.developer-trust add {GITHUB_USERNAME}.md
git -C ~/.developer-trust commit -m "Initialize {GITHUB_USERNAME} trust profile from {COUNT} PRs in {REPO}"
```

## Profile Format

```markdown
# Developer Trust Profile: {github_username}

_Last updated: {ISO_DATE}_

## Trust Level

**Level**: trusted | neutral | cautious | always_reject
**Reason**: <brief rationale based on the batch analysis>

## Overview

<2-3 sentence summary of the developer's overall style, habits, and track record based on the PRs reviewed>

## Strengths

- <strength observed across PRs>
- <strength>

## Weaknesses

- <weakness observed across PRs>
- <weakness>

## PR Patterns

- <recurring behavior, positive or negative>
- <pattern>

## Review History

| Date | Repository | PR | Outcome | Notes |
|------|------------|----|---------|-------|
| {mergedAt date} | {owner/repo} | #{number} | Merged | <one-line note about this PR> |
```

Note: The Outcome column uses `Merged` for all rows written by this skill, since it only processes merged (or closed) PRs. The `developer-trust-profile` skill uses `Approved` / `Not approved` when updating after a manual review.

## Output

Report to the user:
- Number of PRs scanned
- The trust level assigned and the reason
- Key strengths and weaknesses found
- The profile path written
- Whether an existing profile was overwritten

## Example Usage

**Scenario 1: Initialize with default count**
```
/initialize-developer-trust alice owner/myrepo
```
Fetches last 10 merged PRs by alice in `owner/myrepo`, synthesizes observations, writes `~/.developer-trust/alice.md` with an initial trust level.

**Scenario 2: Initialize with custom count**
```
/initialize-developer-trust bob owner/myrepo 25
```
Fetches last 25 merged PRs by bob, producing a more grounded initial profile.

**Scenario 3: Developer with no merged PRs**
```
/initialize-developer-trust carol owner/myrepo
```
No merged or closed PRs found for carol. Reports the absence and stops without writing a file.

**Scenario 4: Overwriting an existing profile**
```
/initialize-developer-trust alice owner/myrepo
```
`~/.developer-trust/alice.md` already exists. Notifies the user it will be overwritten, then proceeds with the batch analysis and rewrites the file.

**Scenario 5: Developer with consistently poor quality PRs**
```
/initialize-developer-trust dave owner/myrepo 15
```
All 15 PRs show missing tests, vague descriptions, and frequent scope creep. Trust level set to `cautious` with reason documenting the recurring issues.

## Useful Commands Reference

| Command | Description |
|---|---|
| `mkdir -p ~/.developer-trust && git -C ~/.developer-trust init` | Initialize the trust store as a git repo |
| `gh pr list --repo <owner/repo> --author <user> --state merged --limit N --json ...` | Fetch last N merged PRs by author |
| `gh pr list --repo <owner/repo> --author <user> --state closed --limit N --json ...` | Fetch last N closed PRs by author (fallback) |
| `gh pr diff <pr> --repo <owner/repo>` | Fetch the PR diff |
| `git -C ~/.developer-trust add <file> && git -C ~/.developer-trust commit -m "..."` | Stage and commit a profile |
