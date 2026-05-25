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

### Issue Type Mapping

Map the classified type to the closest GitHub Issue Type for the repository.
First fetch available issue types, then apply the mapping:

```
gh api graphql -f query='{ repository(owner:"<owner>", name:"<repo>") { issueTypes(first: 20) { nodes { id name } } } }'
```

| Classified Type | GitHub Issue Type (preferred) |
|---|---|
| `bug` | Bug |
| `feature` | Feature |
| `question` | Task |
| `chore` | Task |
| `documentation` | Task |
| `security` | Bug |

Use the closest match from the available issue types. If no matching type exists, skip issue type assignment.

Set the issue type via REST API (accepts the type name as a string):
```
echo '{"type": "<TypeName>"}' | gh api --method PATCH repos/<owner>/<repo>/issues/<number> --input -
```

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

### Priority Mapping

Derive a priority from the urgency and importance classification.

| Urgency | Importance | Priority |
|---|---|---|
| `urgent` | `important` | Urgent |
| `urgent` | `not-important` | High |
| `not-urgent` | `important` | High |
| `not-urgent` | `not-important` | Medium |

Priority is an organization-level issue field (not a project field).
Discover available fields and their option IDs via GraphQL:

```
gh api graphql -f query='{ repository(owner:"<owner>", name:"<repo>") { issueFields(first: 20) { nodes { ... on IssueFieldSingleSelect { id name options { id name } } } } } }'
```

If a field named "Priority" exists, set it using the `setIssueFieldValue` GraphQL mutation:

```
gh api graphql -f query='mutation($issueId: ID!, $fieldId: ID!, $optionId: ID!) { setIssueFieldValue(input: { issueId: $issueId, issueFields: [{ fieldId: $fieldId, singleSelectOptionId: $optionId }] }) { issue { issueFieldValues(first: 10) { nodes { ... on IssueFieldValueSingleSelect { name field { ... on IssueFieldSingleSelect { name } } } } } } } }' -f issueId=<ISSUE_NODE_ID> -f fieldId=<PRIORITY_FIELD_ID> -f optionId=<OPTION_ID>
```

If no Priority field exists on the repository, skip this step.

## Steps

1. Fetch the repository's available issue types and issue fields (once, before processing issues):
   ```
   gh api graphql -f query='{ repository(owner:"<owner>", name:"<repo>") { issueTypes(first: 20) { nodes { id name } } issueFields(first: 20) { nodes { ... on IssueFieldSingleSelect { id name options { id name } } } } } }'
   ```
   Store the issue type name-to-ID map and the Priority field ID with its option ID-to-name map.
2. List open issues that need triage:
   ```
   gh-cached issue list [--repo $1] --state open --limit 50
   ```
3. For each issue, read its full description and comments.
4. Classify the issue using the tables above (type, urgency, importance, priority).
5. If the issue is too vague to classify, post a comment asking for: steps to reproduce (bugs), use case details (features), or more context.
6. Apply the appropriate labels:
   ```
   gh issue edit <number> [--repo $1] --add-label "<type>" --add-label "<urgency>" --add-label "<importance>"
   ```
7. Set the GitHub Issue Type via REST API (if a matching type is available):
   ```
   echo '{"type": "<TypeName>"}' | gh api --method PATCH repos/<owner>/<repo>/issues/<number> --input -
   ```
8. Set the Priority field via GraphQL `setIssueFieldValue` mutation (if a Priority field was found in step 1):
   - Look up the Priority option ID for the derived priority level (Urgent/High/Medium)
   - Get the issue node ID: `gh api repos/<owner>/<repo>/issues/<number> --jq '.node_id'`
   - Call `setIssueFieldValue` with the issue node ID, Priority field ID, and option ID
9. Output a triage summary table.

## Output Format

```markdown
## Triage Summary

| Issue | Title | Type | Issue Type | Urgency | Importance | Priority | Action |
|---|---|---|---|---|---|---|---|
| #42 | Login crash on mobile | bug | Bug | urgent | important | Urgent | Labeled, type set, priority set |
| #43 | Add dark mode | feature | Feature | not-urgent | not-important | Medium | Labeled, type set, priority set |
| #44 | How do I reset password? | question | Task | not-urgent | not-important | Medium | Labeled, type set |
| #45 | Something broke | bug | - | - | - | - | Comment posted |
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
| `gh api graphql -f query='{ repository(owner:"<o>", name:"<r>") { issueTypes(first: 20) { nodes { id name } } issueFields(first: 20) { nodes { ... on IssueFieldSingleSelect { id name options { id name } } } } } }'` | Fetch available issue types and fields |
| `gh-cached issue list [--repo <repo>] --state open --limit 50` | List open issues (cached) |
| `gh-cached issue view <number> [--repo <repo>] --comments` | Read issue details and comments (cached) |
| `gh api repos/<owner>/<repo>/issues/<number> --jq '.node_id'` | Get issue node ID for GraphQL mutations |
| `echo '{"type": "<name>"}' \| gh api --method PATCH repos/<owner>/<repo>/issues/<number> --input -` | Set issue type by name |
| `gh api graphql -f query='mutation($issueId: ID!, $fieldId: ID!, $optionId: ID!) { setIssueFieldValue(input: { issueId: $issueId, issueFields: [{ fieldId: $fieldId, singleSelectOptionId: $optionId }] }) { issue { issueFieldValues(first: 10) { nodes { ... on IssueFieldValueSingleSelect { name field { ... on IssueFieldSingleSelect { name } } } } } } } }' -f issueId=<ID> -f fieldId=<FIELD_ID> -f optionId=<OPTION_ID>` | Set org-level issue field (e.g. Priority) |
| `gh issue edit <number> [--repo <repo>] --add-label "<label>"` | Apply a label to an issue |
| `gh issue comment <number> [--repo <repo>] --body "..."` | Post a clarification comment |
