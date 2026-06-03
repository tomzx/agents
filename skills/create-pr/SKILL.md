---
name: create-pr
description: Create a GitHub pull request with a structured description linked to its issue, with acceptance criteria coverage and reviewer assignment.
allowed-tools: Bash(gh:*, git:*, gh-cached:*, scripts/get-env:*), Read, Write, Glob, Grep
argument-hint: "[repository] [issue-number]"
---

# Create Pull Request

Opens a GitHub pull request for the current branch with a structured description that maps implementation changes to acceptance criteria, links the originating issue, and requests reviewers.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- Current branch has commits not on the base branch
- A related GitHub issue number (strongly recommended; omit only for housekeeping PRs)
- Tests passing locally before the PR is opened
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there to the produced document

> **Note:** This skill uses `gh` (GitHub CLI) directly. For a Graphite-based workflow that diffs against the Graphite parent branch, use `/create-pr-description` instead.

### Skill attribution (GitHub)

Before creating the PR with `gh pr create`, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Created with** footer for `SKILL_DIR` = `create-pr` to the PR body.

## Workflow

```
Verify branch has commits + tests pass
            |
            v
Compute diff (base..HEAD)
            |
            v
Issue provided? ($1 $2)
   /              \
 Yes               No
  |                 |
  v                 v
Fetch issue       Skip AC
+ map ACs         coverage
  |                 |
  +--------+--------+
           |
           v
Draft PR description
           |
           v
gh pr create (draft if incomplete)
           |
           v
Assign reviewers (if known)
```

## Steps

1. Confirm the branch has commits ahead of the base:
   ```
   git log origin/$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null | sed 's|origin/||')..HEAD --oneline
   ```
   If no commits, stop and inform the user.

2. Confirm tests pass before opening:
   Run the project's test command. If tests fail, stop and list the failures.

3. Compute the diff against the base branch:
   ```
   git diff $(git merge-base HEAD origin/main)..HEAD
   ```

4. If `$1` (repository) and `$2` (issue number) are provided, fetch the issue:
   ```
   gh-cached issue view $2 --repo $1
   ```
   Map each acceptance criterion to the changes in the diff.
   Note any ACs not yet addressed (to call out in the description).

5. Draft the PR description following the output format below. Do not line wrap the description; each paragraph/bullet should be a single long line.

6. Create the PR. Use `--draft` if any acceptance criteria are unmet:
   ```
   gh pr create --repo $1 --title "<title>" --body "$(cat <<'EOF'
   <description>
   EOF
   )" [--draft]
   ```
   Omit `--repo` if the repository can be inferred from the current working directory.

7. If reviewer GitHub handles are known from context, assign them:
   ```
   gh pr edit <pr-number> --add-reviewer <handle>
   ```

## PR Description Format

```markdown
# What

<Present-tense summary of changes. Bullet points for multiple changes.>

# Why

<Problem being solved or feature being added. Reference the issue.>

# How to test

1. <Step to verify the change works>
2. <Step for an edge case or error path>

# Acceptance criteria coverage

- [x] <AC that is fully addressed>
- [x] <AC that is fully addressed>
- [ ] <AC not addressed in this PR — note why (out of scope, follow-up issue)>

# References

- Closes #<issue-number>

---

Created with [create-pr]({SKILL_FILE_URL}) (`SKILL_SHORT_SHA`)
```

Resolve `SKILL_FILE_URL` and `SKILL_SHORT_SHA` per [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md).

Use `Closes #N` to auto-close the issue on merge. Use `Related to #N` if the PR only partially addresses the issue.

## Example Usage

**Scenario 1: Feature PR linked to an issue**
```
/create-pr owner/myrepo 42
```
Diffs branch, fetches issue #42, maps all 4 ACs to changes, creates PR with "Closes #42" and requests reviewers.

**Scenario 2: PR covering only part of an issue**
```
/create-pr owner/myrepo 88
```
Issue has 5 ACs; this branch addresses 3. Creates a ready-for-review PR, marks the 2 unmet ACs as unchecked with a note, uses "Related to #88".

**Scenario 3: Housekeeping PR without an issue**
```
/create-pr
```
No issue provided. Creates PR with What/Why/How-to-test sections; omits AC coverage and References sections.

**Scenario 4: Incomplete implementation**
```
/create-pr owner/myrepo 100
```
One AC not yet met. Opens as a draft PR so it is not accidentally merged.

## Next Step

After the PR is open, use `/handle-pr-ci` if CI is failing, `/handle-pr-feedback` to address reviewer comments, and `/merge-pr` once CI is green and the PR is approved.
Close the loop with `/create-learnings` after the feature is merged.

## Useful Commands Reference

| Command | Description |
|---|---|
| `git log origin/<base>..HEAD --oneline` | List commits ahead of the base branch |
| `git diff $(git merge-base HEAD origin/main)..HEAD` | Diff against the merge base |
| `gh-cached issue view <number> --repo <owner/repo>` | Fetch issue details (cached) |
| `gh pr create --repo <repo> --title "..." --body "..." [--draft]` | Open the pull request |
| `gh pr edit <number> --add-reviewer <handle>` | Assign a reviewer after creation |
