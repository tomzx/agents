---
name: create-issue
description: Create a GitHub issue with background, acceptance criteria, and time budget sections.
argument-hint: <repository>
---

# Create GitHub Issue

Creates a structured GitHub issue in the specified repository with background, acceptance criteria, and a time budget so implementers have clear scope and exit criteria.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- Repository name in `owner/repo` format (`$1`)

## Steps

1. List available labels to verify which exist:
   ```
   gh label list --repo $1
   ```
2. Create the issue with the structured body:
   ```
   gh issue create --repo $1 --title "<title>" --body "$(cat <<'EOF'
   # Background

   <context and motivation>

   # Acceptance Criteria

   - [ ] <criterion 1>
   - [ ] <criterion 2>

   # Time budget

   <estimate>, after which the implementer should reassess or seek help.
   EOF
   )" --label "not-urgent" --label "not-important"
   ```
3. Apply additional labels if specified in the request instead of the defaults.

## Example Usage

**Scenario 1: Simple bug report**
```
/create-issue owner/myrepo
```
Creates an issue titled "Fix null pointer in user login" with background explaining the crash, acceptance criteria requiring a regression test and the fix, and a 2-hour time budget. Labels: `not-urgent`, `not-important`.

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
| `gh issue create --repo <repo> --title "..." --body "..." --label "..."` | Create a new issue with labels |
| `gh label list --repo <repo>` | List available labels in the repository |
