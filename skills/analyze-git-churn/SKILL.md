---
name: analyze-git-churn
description: Analyze git history to identify high-churn files and suggest targeted improvements such as refactoring, test coverage, dead code removal, or library replacements.
allowed-tools: Bash(git:*), Read, Glob, Grep
argument-hint: "[day|week|month]"
---

TODAY=!`date +%Y-%m-%d`

# Git Churn Analysis

Analyzes the git commit history over a chosen period to surface the files that changed most frequently, then inspects each high-churn file and produces concrete, prioritized improvement suggestions.

## Prerequisites

- `git` repository with commit history
- Working directory is the root of the repository (or a subdirectory of it)
- Optional: `$1` — period to analyze: `day`, `week`, or `month` (defaults to `week`)

## Period Mapping

| Argument | `--since` value |
|----------|----------------|
| `day`    | `1 day ago`    |
| `week`   | `1 week ago`   |
| `month`  | `1 month ago`  |

If `$1` is not provided, default to `week`.

## Steps

### 1. Determine the Analysis Window

Map `$1` → a `git log --since` value using the table above.

### 2. Collect Churn Data

Run the following to count how many commits touched each file in the window:

```
git log --since="<period>" --name-only --pretty=format: | sort | uniq -c | sort -rn | head -30
```

Also capture per-file insertion/deletion totals to measure change volume:

```
git log --since="<period>" --numstat --pretty=format: | awk 'NF==3 {add[$3]+=$1; del[$3]+=$2; commits[$3]++} END {for (f in commits) printf "%d\t%d\t%d\t%s\n", commits[f], add[f], del[f], f}' | sort -rn | head -30
```

Exclude files that no longer exist (deleted files are noise). For each candidate path, confirm it still exists:

```
git ls-files --error-unmatch <path> 2>/dev/null
```

### 3. Rank High-Churn Files

Build a ranked table using the commit-count as the primary sort key:

| Rank | File | Commits | Lines Added | Lines Deleted | Net |
|------|------|---------|-------------|---------------|-----|
| 1    | …    | N       | +X          | −Y            | Z   |

Focus the analysis on the **top 10** files. If fewer than 3 files show more than 1 commit, widen the period automatically and note the change.

### 4. Inspect Each High-Churn File

For each of the top files:

1. Read the file contents.
2. Review recent commit messages that touched the file:
   ```
   git log --since="<period>" --oneline -- <path>
   ```
3. Look at the diff for representative recent changes:
   ```
   git diff HEAD~5 HEAD -- <path>
   ```

### 5. Generate Improvement Suggestions

For each high-churn file, produce a focused set of suggestions drawn from the categories below. Only include categories that genuinely apply — do not pad with generic advice.

#### Suggestion Categories

**Refactor**
- God class / god function: split into smaller, single-responsibility units
- Repeated logic across files: extract a shared helper or module
- Deeply nested conditionals: flatten with early returns or a state machine
- Mixed abstraction levels in a single function: separate into layers

**Add Tests**
- No test file exists alongside the file
- High churn with few or no tests suggests the code is hard to reason about safely
- Recommend specific test types: unit, integration, property-based, snapshot

**Remove Dead Code**
- Functions, methods, or branches that are never called
- Feature flags that are always true or always false
- Config keys that are read but never used

**Extract to a Library / Package**
- Logic that is domain-agnostic and reused (or should be) across the repo
- Utilities that could live in a separate installable package

**Replace with an Existing Library**
- Custom implementations of things well-covered by standard or popular libraries
- Examples: hand-rolled retry logic → `tenacity`; custom date parsing → `arrow` or `dateutil`; bespoke HTTP client → `httpx`

**Replace a Library with a Better One**
- Outdated, unmaintained, or poorly-typed dependencies
- Libraries with known issues that have better-maintained alternatives
- Examples: `requests` → `httpx` for async support; `argparse` → `typer` or `click` for ergonomics; `unittest.mock` → `pytest-mock`

**Improve Structure / Architecture**
- Circular imports between modules
- Business logic leaking into I/O layers (routes, handlers, CLI entrypoints)
- Configuration scattered across multiple files without a single source of truth

**Documentation**
- Public API with no docstrings or type hints
- Complex algorithm with no explanation of invariants

**Other Observations**
- Any pattern not covered above that a senior engineer would flag on review

### 6. Prioritize Suggestions

Rank suggestions using this rubric:

| Priority | Criteria |
|----------|----------|
| 🔴 High  | Likely causing bugs, blocking safe refactor, or slowing every contributor who touches the file |
| 🟡 Medium | Adds friction or technical debt but isn't blocking |
| 🟢 Low   | Polish, convenience, or future-proofing |

### 7. Write the Report

Print the report to the terminal (do not write to a file unless the user asks).

```
# Git Churn Analysis — <period> ending {TODAY}

## Summary

- Period: <since date> → {TODAY}
- Total files changed: N
- Commits analyzed: N

## High-Churn Files

<ranked table from Step 3>

## File-by-File Suggestions

### 1. `<path>` — N commits

<2–3 sentence description of what this file does and why it is churning>

#### Suggestions

- 🔴 **[Category]** <specific, actionable suggestion>
- 🟡 **[Category]** <specific, actionable suggestion>
- 🟢 **[Category]** <specific, actionable suggestion>

### 2. `<path>` — N commits

…

## Quick Wins

List the 3–5 changes that would have the highest impact for the lowest effort across all files.

## Next Steps

Suggest a concrete order of operations for addressing the findings.
```

## Example Usage

**Scenario 1: Default (week)**
```
/git-churn-analysis
```
Analyzes the past week. Finds `src/api/routes.py` (12 commits) and `src/db/queries.py` (9 commits) as top churners. Suggests splitting the 800-line routes file and replacing a hand-rolled connection-retry loop with `tenacity`.

**Scenario 2: Monthly view**
```
/git-churn-analysis month
```
Identifies a test helper that has been patched 20 times over the month, recommends extracting it into a proper fixture module and adding property-based tests with `hypothesis`.

**Scenario 3: Daily hotspot**
```
/git-churn-analysis day
```
Three files changed today. One config file was touched 4 times — suggests consolidating environment-specific overrides into a single `settings.py` with `pydantic-settings`.

## Useful Commands Reference

| Command | Description |
|---------|-------------|
| `git log --since="1 week ago" --name-only --pretty=format:` | List files touched in commits |
| `git log --since="1 week ago" --numstat --pretty=format:` | Per-file line addition/deletion counts |
| `git log --oneline -- <path>` | Commit history for a specific file |
| `git diff HEAD~5 HEAD -- <path>` | Diff of last 5 commits for a file |
| `git ls-files --error-unmatch <path>` | Check if a file is tracked |
| `git shortlog --since="1 week ago" -sn` | Commits per author (context) |
