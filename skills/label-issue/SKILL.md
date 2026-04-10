---
name: label-issue
description: Add relevant labels to a GitHub issue based on its description, and recommend new labels if needed.
argument-hint: <issue-number>
---

# Label GitHub Issue

Reads a GitHub issue and applies appropriate existing labels based on its content, then recommends new labels if the current set is insufficient.

## Prerequisites

- `gh` CLI authenticated with triage or write access to the repository
- Issue number (`$1`) referencing an existing issue in the current repository context

## Workflow

```
Fetch issue details ($1)
        |
        v
Fetch available labels
        |
        v
Match issue content to labels
        |
        v
Matching labels found?
   /         \
 Yes           No
  |             |
  v             v
Apply labels  Skip label
via gh        add step
  |             |
  +------+------+
         |
         v
New labels needed?
   /         \
 Yes           No
  |             |
  v             v
Recommend     Done
new labels
```

## Steps

1. Fetch the issue details:
   ```
   gh issue view $1
   ```
2. Fetch all available labels:
   ```
   gh label list
   ```
3. Match the issue content to existing labels and apply them:
   ```
   gh issue edit $1 --add-label "<label1>" --add-label "<label2>"
   ```
4. If no existing labels adequately categorize the issue, recommend new labels with suggested names and descriptions.

## Example Usage

**Scenario 1: Bug report**
```
/label-issue 42
```
Issue describes a crash in the login flow. Applies: `bug`, `authentication`. No new labels needed.

**Scenario 2: Feature request with no matching label**
```
/label-issue 100
```
Issue requests a dark mode toggle. No `ui` or `enhancement` label exists. Applies `feature-request` if available, recommends creating a `ui` label.

**Scenario 3: Duplicate issue**
```
/label-issue 55
```
Issue is a known duplicate. Applies `duplicate` label. Recommends closing with a reference to the original.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh issue view <issue-number>` | Fetch issue title, body, and current labels |
| `gh label list` | List all available labels in the repository |
| `gh issue edit <issue-number> --add-label "<label>"` | Apply one or more labels to an issue |
