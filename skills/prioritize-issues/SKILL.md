---
name: prioritize-issues
description: Score and rank a backlog of GitHub issues by reach, impact, confidence, and effort (RICE).
allowed-tools: Bash(gh:*, gh-cached:*, scripts/get-env:*), Read, Write
argument-hint: "[repository]"
---

# Prioritize Issues

Scores and ranks open GitHub issues using the RICE framework (Reach, Impact, Confidence, Effort) to produce a prioritized backlog ordered by highest value first.

## Prerequisites

- `gh` CLI authenticated with read access to the target repository
- Repository in `owner/repo` format (`$1`), or omit to infer from the current working directory

## RICE Scoring

**RICE score = (Reach × Impact × Confidence) / Effort**

| Factor | Scale | Description |
|---|---|---|
| Reach | 1–10 | How many users are affected per period |
| Impact | 1–5 | Effect on the goal (1=minimal, 5=massive) |
| Confidence | 0.5–1.0 | How confident we are in the estimates |
| Effort | 0.5–5 | Person-weeks of work required |

## Steps

1. Fetch all open issues:
   ```
   gh-cached issue list [--repo $1] --state open --limit 100
   ```
2. For each issue, read its title, description, and labels.
3. Estimate RICE factors based on:
   - `urgent` label → higher Reach/Impact
   - `important` label → higher Impact
   - Scope described in the issue body → Effort
4. Compute the RICE score for each issue.
5. Sort issues by RICE score descending.
6. Output the prioritized backlog table and scoring notes.

## Output Format

```markdown
## Prioritized Backlog

| Rank | Issue | Title | Reach | Impact | Confidence | Effort | RICE Score |
|---|---|---|---|---|---|---|---|
| 1 | #12 | Fix checkout crash | 8 | 5 | 0.9 | 1 | 36.0 |
| 2 | #7  | Add OAuth login | 6 | 4 | 0.8 | 3 | 6.4 |

## Scoring Notes

<Explain significant assumptions or confidence factors for any non-obvious scores.>
```

## Example Usage

**Scenario 1: Rank a full backlog**
```
/prioritize-issues owner/myrepo
```
Fetches all open issues, scores them on RICE, and outputs a ranked table.

**Scenario 2: Focus on a milestone**
```
/prioritize-issues owner/myrepo
```
User says "only issues in milestone v2.0." Filter with:
```
gh-cached issue list [--repo $1] --milestone "v2.0" --state open
```

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh-cached issue list [--repo <repo>] --state open --limit 100` | List open issues (cached) |
| `gh-cached issue list [--repo <repo>] --milestone "<name>" --state open` | Filter by milestone (cached) |
| `gh-cached issue view <number> [--repo <repo>]` | Read a single issue (cached) |
