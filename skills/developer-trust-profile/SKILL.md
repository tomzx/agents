---
name: developer-trust-profile
description: Create, view, or update a developer trust profile for a GitHub user. Tracks trust level, strengths, weaknesses, PR patterns, and review history.
allowed-tools: Bash(gh:*, git:*), Read, Write, Glob
argument-hint: <github_username> [--after-review <owner/repo> <pr_number> <approved|not_approved>]
---

# Developer Trust Profile

Manages per-developer trust profiles that inform PR review behavior. Each profile lives in its own file and accumulates observations across reviews. Call this skill to view a profile, create one from scratch, or update it after a PR review.

## Prerequisites

- GitHub username (`$1`) of the developer
- Optional: `--after-review <owner/repo> <pr_number> <approved|not_approved>` to update after a review

## Profile Location

```
~/.developer-trust/{github_username}.md
```

## Trust Levels

| Level | Meaning | Effect on quick-pr-review |
|-------|---------|--------------------------|
| `trusted` | Developer consistently produces high-quality PRs | Standard checks, lean toward approval on borderline cases |
| `neutral` | Unknown or mixed track record | Standard checks, default behavior |
| `cautious` | History of issues, missed edge cases, or unclear PRs | Apply stricter interpretation of checks, flag marginal cases |
| `always_reject` | Persistent quality/policy issues warranting manual review | Never auto-approve; always require human review |

## Workflow

```
Read existing profile (or start fresh)
              |
      Mode: view or update?
       /                  \
     View                Update
      |                    |
  Print profile      Fetch PR metadata
                           |
                    Synthesize observations
                    (strengths, weaknesses,
                     patterns seen in diff)
                           |
                    Update profile sections
                    + append review history row
                           |
                    Write profile file
```

## Steps

### 1. Resolve paths and arguments

Parse `$@`:
- `GITHUB_USERNAME`: `$1`
- If `--after-review` flag present, extract:
  - `REPO`: next argument (`owner/repo`)
  - `PR_NUMBER`: next argument
  - `OUTCOME`: next argument (`approved` or `not_approved`)

`PROFILE_PATH`: `~/.developer-trust/{GITHUB_USERNAME}.md`

### 2. Load existing profile

If `PROFILE_PATH` exists, read it. Extract current trust level, strengths, weaknesses, patterns, and review history. If it does not exist, initialize with defaults (trust level: `neutral`, all sections empty).

### 3a. View mode (no `--after-review`)

Print the profile contents and summarize:
- Trust level and reason
- Strengths count
- Weaknesses count
- Number of reviews in history

Stop here.

### 3b. Update mode (`--after-review` present)

#### Fetch PR context

```bash
gh pr view {PR_NUMBER} --repo {REPO} \
  --json number,title,body,author,additions,deletions,changedFiles,labels,headRefName
gh pr diff {PR_NUMBER} --repo {REPO}
```

#### Synthesize observations

Based on the PR diff, title, description, and outcome, identify:

- **Strengths**: positive patterns (e.g., "well-structured tests", "clear commit messages", "good error handling", "thorough documentation")
- **Weaknesses**: problem areas (e.g., "missing test coverage", "unclear PR description", "mixed concerns in single commit", "ignores edge cases")
- **PR patterns**: recurring behaviors (e.g., "tends to include unrelated refactors", "consistently links issues", "PRs are atomic and focused")

Merge new observations with existing ones: add new items, update or reinforce existing ones (do not duplicate), and remove items that are contradicted by recent evidence.

#### Update trust level

Recalculate trust level based on the full review history and current observations:
- If the developer has a long track record of clean, approved PRs: consider upgrading to `trusted`
- If recurring issues appear across multiple reviews: consider downgrading to `cautious`
- If issues are severe or repeated despite feedback: consider `always_reject`
- Do not change trust level based on a single review alone unless it is egregious

Update the trust level reason to reflect the current evidence.

#### Append review history row

Add a new row to the Review History table:
```
| {ISO_DATE} | {REPO} | #{PR_NUMBER} | {Approved/Not approved} | {one-line observation} |
```

### 4. Write the profile

Write or overwrite `PROFILE_PATH` with the updated content using the format below.

## Profile Format

```markdown
# Developer Trust Profile: {github_username}

_Last updated: {ISO_DATE}_

## Trust Level

**Level**: trusted | neutral | cautious | always_reject
**Reason**: <brief rationale for the current trust level>

## Overview

<2-3 sentence summary of the developer's overall style, habits, and track record>

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
| {ISO_DATE} | {owner/repo} | #{number} | Approved | <one-line note> |
```

## Example Usage

**Scenario 1: View an existing profile**
```
/developer-trust-profile alice
```
Reads `~/.developer-trust/alice.md` and prints a summary. If no profile exists, reports that alice has no profile yet.

**Scenario 2: Create a profile from scratch via first review**
```
/developer-trust-profile bob --after-review acme/api 42 approved
```
No existing profile for bob. Fetches PR #42, synthesizes initial observations, creates a new profile with trust level `neutral` and the first review history entry.

**Scenario 3: Update an existing profile**
```
/developer-trust-profile alice --after-review acme/api 55 not_approved
```
Loads alice's profile, fetches PR #55 diff, merges new observations, appends review history row. Reconsiders trust level if patterns suggest a change is warranted.

**Scenario 4: Developer with persistent issues**
```
/developer-trust-profile carol --after-review acme/api 88 not_approved
```
Carol's profile shows 4 consecutive non-approvals, all due to missing tests. Updates trust level to `cautious` with reason "Consistently submits PRs without adequate test coverage despite prior feedback."

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh pr view <pr> --repo <owner/repo> --json ...` | Fetch PR metadata |
| `gh pr diff <pr> --repo <owner/repo>` | Fetch the PR diff |
