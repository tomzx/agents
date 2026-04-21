---
name: create-issue
description: Create a GitHub issue with background, acceptance criteria, and time budget sections.
argument-hint: "[repository]"
---

# Create GitHub Issue

Creates a structured GitHub issue in the specified repository with background, acceptance criteria, and (for private repositories) a time budget so implementers have clear scope and exit criteria.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- Repository name in `owner/repo` format (`$1`), or omitted to use the repository in the current working directory

### Skill attribution (GitHub)

Before creating an issue with `gh issue create`, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Created with** footer for `SKILL_DIR` = `create-issue` to the issue body.

## Steps

1. If the issue is a bug report, ask the user: "Which version are you on?" and wait for their answer before proceeding.
2. Determine if the repository is public or private using `gh repo view [--repo $1] --json isPrivate --jq '.isPrivate'`. A public repository is treated as open source; omit the **Time budget** section. A private repository includes it.
3. Choose labels: defaults `not-urgent` and `not-important`, or whatever the user asked for instead.
4. **Search for duplicates** before creating. Run `gh issue list --repo $1 --search "<keywords from title>" --state all --limit 10` with 2-3 different keyword combinations. If a duplicate is found, stop and inform the user with the existing issue URL. Do not create a new issue unless the user confirms it is not a duplicate.
5. Create the issue with the structured body (no label preflight). For bug reports, include a **Version** section with the version the user provided. Omit `--repo` if no repository was provided (gh will infer it from the cwd):
   ```
   gh issue create [--repo $1] --title "<title>" --body "$(cat <<'EOF'
   # Background

   <context and motivation>

   # Version

   <version the user reported> (include only for bug reports)

   # Acceptance Criteria

   - [ ] <criterion 1>
   - [ ] <criterion 2>

   # Time budget

   <estimate>, after which the implementer should reassess or seek help.
   (omit this section entirely for public/open-source repositories)

   ---

   Created with [create-issue]({SKILL_FILE_URL}) (`SKILL_SHORT_SHA`)
   EOF
   )" --label "not-urgent" --label "not-important"
   ```
   Resolve `SKILL_FILE_URL` and the short SHA per [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) before running the command.
6. If `gh issue create` fails because a label is missing: only if you are a contributor who can manage labels, run `gh label create "<label-name>" --repo $1` and retry `gh issue create` (repeat as needed). If you are not a contributor, or `gh label create` fails with permission errors, create the issue again **without** `--label` and note that labels were skipped.

## Example Usage

**Scenario 1: Simple bug report**
```
/create-issue owner/myrepo
```
Creates an issue titled "Fix null pointer in user login" with background explaining the crash, acceptance criteria requiring a regression test and the fix, and a 2-hour time budget (if private). Labels: `not-urgent`, `not-important`.

**Scenario 2: Feature request with custom labels**
```
/create-issue owner/myrepo
```
User specifies "this is urgent and important." Apply `urgent` and `important` labels instead of the defaults.

**Scenario 3: Acceptance criteria provided upfront**
```
/create-issue owner/api-service
```
User provides a list of requirements. Convert each into a checklist item under Acceptance Criteria.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh repo view [--repo <repo>] --json isPrivate --jq '.isPrivate'` | Check if a repository is private |
| `gh issue list --repo <repo> --search "<keywords>" --state all --limit 10` | Search for duplicate issues before creating |
| `gh issue create --repo <repo> --title "..." --body "..." --label "..."` | Create a new issue with labels |
| `gh label create <name> --repo <repo>` | Add a missing label before retrying (only if you have permission) |
