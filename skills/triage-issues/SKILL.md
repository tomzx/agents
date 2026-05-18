---
name: triage-issues
description: Classify and label incoming GitHub issues by type, urgency, and importance.
allowed-tools: Bash(gh:*, gh-cached:*, scripts/get-env:*), Read, Write
argument-hint: "[repository]"
---

# Triage Issues

Reviews open, unlabeled issues in a GitHub repository and classifies each by type, urgency, and importance.
Applies labels and posts a clarification comment when an issue lacks enough information to classify.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- Repository in `owner/repo` format (`$1`), or omit to use the repository in the current working directory
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there to the produced document

## Workflow

```
List open issues (unlabeled/untriaged)
            |
            v
  For each issue:
    Read title + description + comments
            |
            v
  Classify: type / urgency / importance
            |
            v
  Sufficient info?
     /          \
   Yes            No
    |              |
    v              v
Apply labels   Request clarification
               via comment
            |
            v
  Output triage summary
```

## Classification

### Type Labels

| Type | Criteria |
|---|---|
| `bug` | Something is broken or behaves unexpectedly |
| `feature` | New functionality requested |
| `question` | User seeking clarification or guidance |
| `chore` | Maintenance, refactoring, or dependency updates |
| `documentation` | Docs are missing, wrong, or unclear |
| `security` | Vulnerability or security concern |

### Urgency Labels

| Label | Criteria |
|---|---|
| `urgent` | Blocking production or multiple users right now |
| `not-urgent` | Can be scheduled without immediate impact |

### Importance Labels

| Label | Criteria |
|---|---|
| `important` | High business value or affects core functionality |
| `not-important` | Nice-to-have or low business impact |

## Steps

1. List open issues that need triage:
   ```
   gh-cached issue list [--repo $1] --state open --limit 50
   ```
2. For each issue, read its full description and comments.
3. Classify the issue using the tables above.
4. If the issue is too vague to classify, post a comment asking for: steps to reproduce (bugs), use case details (features), or more context.
5. Apply the appropriate labels:
   ```
   gh issue edit <number> [--repo $1] --add-label "<type>" --add-label "<urgency>" --add-label "<importance>"
   ```
6. Output a triage summary table.

## Output Format

```markdown
## Triage Summary

| Issue | Title | Type | Urgency | Importance | Action |
|---|---|---|---|---|---|
| #42 | Login crash on mobile | bug | urgent | important | Labeled |
| #43 | Add dark mode | feature | not-urgent | not-important | Labeled |
| #44 | How do I reset password? | question | not-urgent | not-important | Comment posted |
```

## Example Usage

**Scenario 1: Repository with a backlog of unlabeled issues**
```
/triage-issues owner/myrepo
```
Lists all open issues, classifies each, and applies type + urgency + importance labels.

**Scenario 2: Vague bug report**
```
/triage-issues
```
Issue #10 says "it doesn't work." Post comment: "Could you describe the expected behavior, what you observed instead, and the steps to reproduce?"

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh-cached issue list [--repo <repo>] --state open --limit 50` | List open issues (cached) |
| `gh-cached issue view <number> [--repo <repo>] --comments` | Read issue details and comments (cached) |
| `gh issue edit <number> [--repo <repo>] --add-label "<label>"` | Apply a label to an issue |
| `gh issue comment <number> [--repo <repo>] --body "..."` | Post a clarification comment |
