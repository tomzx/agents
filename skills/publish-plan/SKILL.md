---
name: publish-plan
description: Commit an implementation plan to a branch, open a draft PR linked to the originating issue, and post a comment on the issue pointing to the PR.
allowed-tools: Bash(gh:*, gh-cached:*, git:*, scripts/get-env:*), Read, Write
argument-hint: "<issue-url-or-number> [plan-file]"
---

# Publish Plan

Commits the implementation plan produced by `/create-plan` to a dedicated branch, opens a draft PR linked to the originating issue, and posts a comment on the issue so the author knows a plan is ready for their review.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, target the issue from `$ISSUE_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with write access to the repository
- A reviewed plan file in context or at `$2` (defaults to `.sdlc/features/FEAT-NNNN-<slug>/plan.md`; falls back to `plan.md` in the working directory)
- Issue URL or number (`$1`)
- Clean or committable working tree

### Skill attribution (GitHub)

Before posting the issue comment with `gh`, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Posted with** footer for `SKILL_DIR` = `publish-plan`.

Because `publish-plan` always runs within the `sdlc` pipeline, include the **SDLC phase footer** described in `github-post-attribution/SKILL.md` (prepend the `SDLC phase: plan (<FEAT-id> #<issue>)` line above the `Posted with` line).

## Workflow

```
Read plan file ($2 or plan.md)
           |
           v
Create branch: plan/<issue-number>
           |
           v
Commit plan file
           |
           v
Push branch
           |
           v
Open draft PR (linked to issue)
           |
           v
Post comment on issue (links to PR)
```

## Steps

1. Resolve the issue number from `$1`:
   ```
   gh-cached issue view $1
   ```
   Extract the issue number and repository (`owner/repo`).

2. Determine the plan file path: use `$2` if provided, otherwise look for `.sdlc/features/FEAT-NNNN-<slug>/plan.md` (where `<feature>` matches the issue number), then fall back to `plan.md` in the current directory.
   Stop and inform the user if no plan file is found.

3. Create and switch to a plan branch:
   ```
   git checkout -b plan/<issue-number>
   ```

4. Stage and commit the `.sdlc/features/FEAT-NNNN-<slug>/` directory (which contains requirements, specification, and plan artifacts):
   ```
   git add .sdlc/features/FEAT-NNNN-<slug>/
   git commit -m "docs: add implementation plan for #<issue-number>"
   ```

5. Push the branch:
   ```
   git push -u origin plan/<issue-number>
   ```

6. Open a draft PR with the description below:
   ```
   gh pr create --draft --title "Plan: <issue-title>" --body "$(cat <<'EOF'
   <description>
   EOF
   )"
   ```

7. Post a comment on the issue (include **Skill attribution** footer):
   ```
   gh issue comment $1 --body "$(cat <<'EOF'
   <comment>
   EOF
   )"
   ```

## PR Description Format

```markdown
# Implementation Plan: <issue-title>

This PR contains the implementation plan for <issue-link>.

The plan is open as a **draft** for author review and sign-off before development begins.
Once approved, this branch will be closed and development will proceed on a feature branch.

## Plan summary

<2-4 sentence summary of the plan's phases and approach, drawn from the plan file.>

## References

- Related to #<issue-number>

---

Posted with [publish-plan]({SKILL_FILE_URL}) (`SKILL_SHORT_SHA`)
```

Resolve `SKILL_FILE_URL` and `SKILL_SHORT_SHA` per [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md).

Use `Related to #N` (not `Closes #N`) — the plan PR does not close the issue.

## Issue Comment Format

```markdown
An implementation plan has been drafted for this issue and is open for review:

**PR:** <pr-url>

Please review the plan and leave feedback directly on the PR.
Development will begin once the plan is approved.

---

Posted with [publish-plan]({SKILL_FILE_URL}) (`SKILL_SHORT_SHA`)
```

## Example Usage

**Scenario 1: Plan in .sdlc directory**
```
/publish-plan https://github.com/owner/repo/issues/42
```
Finds `.sdlc/42-<slug>/plan.md`, commits the full `.sdlc/42-<slug>/` directory, creates branch `plan/42`, pushes, opens draft PR, posts issue comment.

**Scenario 2: Explicit plan file path**
```
/publish-plan 88 docs/implementation-plan.md
```
Uses `docs/implementation-plan.md` as the plan file, otherwise same flow.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh-cached issue view <issue>` | Fetch issue details (cached) |
| `git checkout -b plan/<number>` | Create the plan branch |
| `git add <file> && git commit -m "..."` | Stage and commit the plan |
| `git push -u origin plan/<number>` | Push branch and set upstream |
| `gh pr create --draft --title "..." --body "..."` | Open a draft PR |
| `gh issue comment <issue> --body "..."` | Post a comment on the issue |
