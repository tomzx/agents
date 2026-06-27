---
name: check-duplicates
description: Check a GitHub issue for duplicate issues and existing fix PRs before investing effort.
allowed-tools: Bash(gh:*, git:*, gh-cached:*, scripts/get-env:*), Read, Write, Glob, Grep
argument-hint: "<issue-number> [repository]"
---

# Check Duplicates

Checks a GitHub issue for duplicate issues and existing fix PRs.
Use before starting work on any issue to avoid wasted effort.

This skill performs read-only checks and posts a comment only if a duplicate is found.
It does not modify the issue or create any branches.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `gh` CLI authenticated with read access to the target repository
- A GitHub issue number to check

### Skill attribution (GitHub)

If posting a comment about a duplicate, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `check-duplicates`.

## Steps

### 1. Fetch the issue

Fetch the issue details to extract search keywords:

```bash
gh-cached issue view $ISSUE_NUMBER --repo $REPO
```

Extract keywords from:
- Title
- Error messages or stack traces
- Key nouns describing the affected component or behavior

### 2. Search for duplicate issues

Using 2-3 different keyword combinations, search for similar open and closed issues:

```bash
gh-cached issue list --repo $REPO --search "<keywords>" --state all --limit 10
```

Exclude the current issue from results.
For each candidate, compare:
- Whether it describes the same root cause or behavior
- Whether it is still open (closed may indicate a previous fix)
- Whether it covers the same scope or a subset

If a duplicate is found, comment on the current issue and stop:

```bash
gh issue comment $ISSUE_NUMBER --repo $REPO --body "$(cat <<'EOF'
Duplicate of #<existing-issue-number>.

---

Posted with [check-duplicates](SKILL_FILE_URL) (`SKILL_SHORT_SHA`)
EOF
)"
```

### 3. Check for existing fix PRs

Search for open PRs that reference this issue:

```bash
gh-cached pr list --repo $REPO --search "$ISSUE_NUMBER" --state open --limit 10
```

If a fix PR already exists, inform the user and stop. Optionally offer to review it with `/review-pr`.

### 4. Check assignment and status

Check if the issue is already assigned or has an in-progress label.
If someone else is working on it, inform the user before proceeding.

### 5. Report results

If no duplicates, no existing PRs, and no assignment conflicts are found, report that the issue is clear to work on.
Do not post a comment on the issue in this case.

## Outcome

| Finding | Action |
|---|---|
| Duplicate issue found | Comment on current issue linking to duplicate, stop |
| Existing fix PR found | Inform user, offer to review, stop |
| Someone already assigned | Inform user, let them decide whether to proceed |
| No conflicts | Issue is clear to work on, proceed |

If `$OUTCOME_YAML` is set, also emit your routing verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `novel` | No conflicts, issue is clear to work on |
| `duplicate` | Duplicate issue or existing fix PR found |

## Example Usage

**Scenario 1: Duplicate found**
```
/check-duplicates 20 owner/myrepo
```
Finds issue #12 describes the same bug. Comments on #20 linking to #12.

**Scenario 2: Existing PR found**
```
/check-duplicates 30 owner/myrepo
```
Finds PR #45 already references issue #30. Informs user and offers to review.

**Scenario 3: Clear to work on**
```
/check-duplicates 42 owner/myrepo
```
No duplicates, no existing PRs, no assignment conflicts. Reports clear.
