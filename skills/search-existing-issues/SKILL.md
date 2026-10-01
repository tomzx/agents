---
name: search-existing-issues
description: Search a GitHub repository for potentially already reported issues matching a free-text problem description. Use when the user describes a bug, error, or feature they want to report, before creating a new issue. Triggers on "is this already reported", "search existing issues", "check if someone reported", or when the user describes a problem and wants to know if an issue exists.
allowed-tools: Bash(gh:*, ghx:*), Read
argument-hint: "<description> [--repo owner/repo]"
---

# Search Existing Issues

Takes a free-text description of a problem (bug, error, feature request) and searches a GitHub repository for potentially matching open or closed issues. Use before creating a new issue to avoid duplicates.

Unlike `check-duplicates` (which takes an existing issue number), this skill starts from a raw description the user provides.

## Prerequisites

- `gh` CLI authenticated with read access to the target repository
- A natural-language description of the problem or feature

## Steps

### 1. Determine the repository

If `--repo` is provided, use it. Otherwise, infer the repository from:

1. The current working directory's git remote (`gh repo view --json nameWithOwner --jq .nameWithOwner`)
2. Any `.sdlc/context/` files that reference a repository
3. Ask the user if neither source is available

### 2. Extract search terms from the description

From the user's description, extract 2-4 distinct keyword combinations for searching. Good search terms come from:

- **Error messages**: exact or partial error strings (quote them in the search)
- **Component or module names**: file paths, class names, function names
- **Observable behavior**: key nouns describing what goes wrong
- **Version or environment specifics**: runtime version, OS, provider name

Prioritize unique identifiers (error strings, stack trace excerpts, function names) over generic terms (crash, error, broken).

### 3. Search for matching issues

Run 2-4 searches using different keyword combinations:

```bash
ghx issue list --repo $REPO --search "<keywords>" --state all --limit 10
```

Search strategies to cover:

1. **Exact error/message search**: `"exact error message in quotes"`
2. **Component + behavior**: `component-name behavior-keyword`
3. **Broader fallback**: `area keyword1 keyword2`

For each search, collect issue numbers, titles, state (open/closed), and creation date.

### 4. Rank and filter candidates

Deduplicate results across searches, then score each candidate by relevance:

| Signal | Weight |
|---|---|
| Identical or near-identical error message | High |
| Same file path, function, or class mentioned | High |
| Same root cause or symptom described | Medium |
| Same component/area but different symptom | Low |
| Same symptom but different component | Low |

Exclude results that are clearly unrelated after reading their titles.

### 5. Read top candidates

For the top 3-5 candidates, fetch their details:

```bash
ghx issue view $ISSUE_NUMBER --repo $REPO
```

Compare the full issue body against the user's description to confirm relevance.

### 6. Report results

Present results grouped by relevance:

```markdown
## Existing Issues Found

### Strong Matches
- **#42** (open) - *Login crash on mobile when using SSO*
  Same error message (`AUTH_TOKEN_EXPIRED`), same reproduction steps.
  Opened 2025-01-15, last commented 2025-01-20.

### Possible Matches
- **#38** (closed) - *SSO token handling fails intermittently*
  Similar area but different error. Closed by PR #40 (fixed in v2.1).

### No Match
No existing issues match your description of [...].
```

### 7. Recommend next step

Based on findings:

| Finding | Recommendation |
|---|---|
| Strong open match found | Suggest adding details to the existing issue rather than creating a duplicate |
| Strong closed match found | Note the fix, suggest testing if the fix version covers their case |
| Possible match found | Suggest the user review and decide whether to add to the existing issue |
| No match found | Suggest proceeding with `/create-issue` |

## Example Usage

**Scenario 1: Bug with error message**
```
/search-existing-issues "Getting 'ConnectionPool exhausted' error when running bulk imports with 100+ concurrent workers" --repo myorg/api-service
```
Extracts search terms: `"ConnectionPool exhausted"`, `ConnectionPool bulk import`, `ConnectionPool concurrent`.
Finds #55 (open) with the same error. Recommends adding details to #55.

**Scenario 2: Feature request**
```
/search-existing-issues "We need a way to export audit logs as CSV"
```
Finds #12 (open, feature request for audit log export in JSON format) and #8 (closed, added JSON export).
Recommends adding a comment to #12 requesting CSV format support.

**Scenario 3: No match**
```
/search-existing-issues "Dashboard widgets disappear after browser refresh since v3.2" --repo myorg/dashboard
```
No matching issues found. Recommends proceeding with `/create-issue`.

**Scenario 4: Fixed in a previous version**
```
/search-existing-issues "File upload returns 500 error for files over 10MB"
```
Finds #30 (closed), fixed in v2.4. User is on v2.3. Recommends upgrading.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh repo view --json nameWithOwner --jq .nameWithOwner` | Get repo from current directory |
| `ghx issue list --repo <repo> --search "<terms>" --state all --limit 10` | Search issues by keywords |
| `ghx issue view <number> --repo <repo>` | Read issue details |
