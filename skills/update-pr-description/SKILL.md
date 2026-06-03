---
name: update-pr-description
description: Update an existing PR description with the minimum changes needed to keep it accurate after new commits have been added.
argument-hint: "[repository] [issue]"
---

# Update PR Description

Reads the current PR description, computes what has changed since it was written, and produces the smallest accurate update -- preserving all sections that are still correct and editing only what the new commits have changed or added.

## Prerequisites

- `gt` (Graphite CLI) installed and authenticated in a git repository
- `gh` CLI authenticated
- An open PR for the current branch with an existing description

### Skill attribution (GitHub)

Before returning the updated description, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Generated with** footer for `SKILL_DIR` = `update-pr-description`.

## Workflow

```
Fetch existing PR description (gh pr view)
        |
        v
Compute full diff (gt parent -> HEAD)
        |
        v
Identify new commits since description was last written
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
Re-assess       |
acceptance      |
criteria        |
  |             |
  +------+------+
         |
         v
Diff description vs new reality -- find minimum changes
         |
         v
Produce updated PR description markdown
```

## Steps

1. Fetch the existing PR description:
   ```
   gh pr view --json body --jq '.body'
   ```

2. Compute the full diff of the branch:
   ```
   git diff $(gt parent)..HEAD
   ```

3. List commits on the branch to understand what is new relative to the existing description:
   ```
   git log $(gt parent)..HEAD --oneline
   ```

4. If `$1` (repository) and `$2` (issue number) are provided, fetch the issue:
   ```
   gh issue view $2 --repo $1
   ```

5. Compare the existing description against the current diff and commit list. For each section of the existing description, decide:
   - **Keep as-is** -- the section is still accurate and complete.
   - **Edit minimally** -- only the parts that are now inaccurate or incomplete; do not rewrite prose that is still correct.
   - **Add** -- new information required by the new commits (e.g. a new "What" bullet, an additional test step).
   - **Remove** -- anything that described work that was reverted or superseded.

   Bias strongly toward keeping existing text. Only change what the new commits have made inaccurate or incomplete.

6. Resolve dot-claude attribution per [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md): compute `SKILL_COMMIT`, `SKILL_SHORT_SHA`, `SKILL_FILE_URL`, and `{BASE}` for `SKILL_DIR` = `update-pr-description`.

7. Produce the updated description following the output format below, substituting the resolved `SKILL_FILE_URL` and `SKILL_SHORT_SHA` into the footer.

8. Return the result inside a markdown code block with each sentence on its own line. Do not line wrap the description; each paragraph/bullet should be a single long line.

## Output Format

The output must follow the same structure as the existing PR description. Do not add or remove sections unless the new commits require it.

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
Updated with [update-pr-description](SKILL_FILE_URL) (`SKILL_SHORT_SHA`)
```

Substitute `SKILL_FILE_URL` and `SKILL_SHORT_SHA` per [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md).

If the existing description already has a `Generated with` or `Updated with` footer, replace it with the new `Updated with` line.

## Minimum-change principle

The goal is accuracy with the least disruption to the existing description:

- Do not rewrite sections that are still correct, even if you would phrase them differently.
- When adding a bullet, append it to the existing list rather than restructuring the list.
- When a test step changes, edit only that step.
- When acceptance criteria coverage changes, update only the affected items.
- If nothing has changed in a section, emit it verbatim.

## Example Usage

**Scenario 1: A few follow-up commits added**
```
/update-pr-description
```
Fetches the existing PR description, diffs it against the current branch state, adds the new bullet points to "What" and any new test steps to "How to test", leaves the rest unchanged.

**Scenario 2: PR linked to an issue with new criteria covered**
```
/update-pr-description owner/myrepo 42
```
Fetches issue #42 and re-assesses acceptance criteria. Adds newly covered items to "Acceptance criteria covered" without touching the rest of the section.

**Scenario 3: A commit reverted earlier work**
```
/update-pr-description
```
Removes the bullet in "What" that described the reverted change and drops the corresponding test step.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh pr view --json body --jq '.body'` | Fetch the current PR description |
| `git diff $(gt parent)..HEAD` | Diff current branch against its Graphite parent |
| `git log $(gt parent)..HEAD --oneline` | List commits on the branch |
| `gh issue view <issue> --repo <owner/repo>` | Fetch issue details via gh CLI |
