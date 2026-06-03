---
name: create-pr-description
description: Generate a PR description based on changes. If a repository/issue is provided, use its description to assess issue completeness.
argument-hint: "[repository] [issue]"
---

# Generate PR Description

Generates a structured PR description from the current branch's diff against its Graphite parent, optionally cross-referencing a GitHub issue to assess acceptance criteria coverage.

## Prerequisites

- `gt` (Graphite CLI) installed and authenticated in a git repository
- `gh` CLI authenticated (required only when `$1` and `$2` are provided)
- Current branch must have commits relative to its parent

> **Note:** This skill uses the Graphite CLI (`gt`) and diffs against the Graphite parent branch. For a `gh`-based workflow that diffs against the git merge base and creates the PR directly, use `/create-pr` instead.

### Skill attribution (GitHub)

Before returning the PR description, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Generated with** footer for `SKILL_DIR` = `create-pr-description` to the end of the description body. This footer travels with the description when the user posts it to GitHub via `gh pr create` or `gh pr edit`.

## Workflow

```
Compute diff (gt parent -> HEAD)
        |
        v
Issue provided? ($1 $2)
   /         \
 Yes           No
  |             |
  v             v
Fetch issue   Skip issue
details       lookup
  |             |
  v             |
Assess          |
acceptance      |
criteria        |
  |             |
  +------+------+
         |
         v
Generate PR description markdown
```

## Steps

1. Compute the diff:
   ```
   git diff $(gt parent)..HEAD
   ```
2. If `$1` (repository) and `$2` (issue number) are provided, fetch the issue:
   ```
   gt issue view $2 --repo $1
   ```
3. Resolve dot-claude attribution per [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md): compute `SKILL_COMMIT`, `SKILL_SHORT_SHA`, `SKILL_FILE_URL`, and `{BASE}` for `SKILL_DIR` = `create-pr-description`.
4. Generate the PR description following the output format below, substituting the resolved `SKILL_FILE_URL` and `SKILL_SHORT_SHA` into the footer.
5. Return the result inside a markdown code block with each sentence on its own line. Do not line wrap the description; each paragraph/bullet should be a single long line.

## Output Format

```markdown
# What

<present-tense summary of changes; bullet points where appropriate>

# Why

<reason for the changes>

# How to test

<testing steps>

# Acceptance criteria covered

<which criteria from the issue are addressed>

# References

- https://github.com/$1/issues/$2

---
Generated with [create-pr-description](SKILL_FILE_URL) (`SKILL_SHORT_SHA`)
```

Substitute `SKILL_FILE_URL` and `SKILL_SHORT_SHA` per [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md).

## Example Usage

**Scenario 1: PR without issue**
```
/create-pr-description
```
Diffs current branch vs parent, produces description with "To be filled by the user" in the References section.

**Scenario 2: PR linked to an issue**
```
/create-pr-description owner/myrepo 42
```
Fetches issue #42 from `owner/myrepo`, maps its acceptance criteria to the changes, and includes the issue link in References.

**Scenario 3: Partial implementation**
```
/create-pr-description owner/api-service 100
```
Issue has 5 acceptance criteria; this PR covers 3. "Acceptance criteria covered" lists only the 3 addressed and notes the remaining 2 are out of scope.

## Useful Commands Reference

| Command | Description |
|---|---|
| `git diff $(gt parent)..HEAD` | Diff current branch against its Graphite parent |
| `gt issue view <issue> --repo <owner/repo>` | Fetch issue details via Graphite CLI |
| `gh issue view <issue> --repo <owner/repo>` | Fetch issue details via gh CLI |
