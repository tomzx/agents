---
name: analyze-test-coverage
description: Analyze a set of code changes (diff or files) and produce a structured test coverage report with three parts: introduced tests, change coverage, and uncovered code. Called by review-pr, review-implementation, and verify-pr; can also be invoked directly on any diff.
allowed-tools: Bash(git:*), Read, Glob, Grep
argument-hint: "[diff-ref | worktree-dir]"
---

# Analyze Test Coverage

Given a set of code changes, produce a structured test coverage analysis that answers three questions:

1. **What tests were introduced or modified?** (and what behavior does each one verify)
2. **Is every behavior change covered by a test?** (change coverage)
3. **Is there code that no test exercises at all?** (uncovered code)

Changing behavior without a test is a reliable way to lose that behavior in a future refactor. This skill surfaces those risks explicitly.

## Prerequisites

- A git worktree or repository with the changes to analyze
- If called by a parent skill, `$WORKTREE_DIR` may be set and the diff context may be provided
- If invoked directly, `$1` is either a diff ref (e.g. `origin/main..HEAD`) or a worktree directory

## Inputs

The skill accepts its context in one of these forms:

| Source | How |
|---|---|
| Worktree + diff ref | `$WORKTREE_DIR` set by parent skill; diff is `git diff` against the base branch |
| Direct invocation with diff ref | `$1` is a git ref range (e.g. `origin/main..HEAD`); run in the current repo |
| Direct invocation with worktree | `$1` is a directory path; diff is `origin/<base>..HEAD` inside that worktree |

From the parent skill, the following may be available:
- `CHANGED_FILES`: list of files changed in the diff
- `DIFF`: the full diff text
- `HEAD_COMMIT` / `SHORT_SHA`: the commit being reviewed

If not provided, derive them:

```bash
if [ -n "${WORKTREE_DIR:-}" ]; then
  cd "$WORKTREE_DIR"
fi
DIFF_REF="${1:-origin/main..HEAD}"
git diff --name-only "$DIFF_REF"
git diff "$DIFF_REF"
```

## Steps

### 1. Separate test files from source files

From the changed files list, split into:

- **Test files**: files matching the project's test conventions (`test_*.py`, `*_test.py`, `*.test.ts`, `*.spec.ts`, `*_test.go`, etc.)
- **Source files**: all other changed files (excluding config, docs, lock files, etc.)

```bash
# Identify test files by convention
git diff --name-only "$DIFF_REF" | grep -E '(test_|_test\.|\.test\.|\.spec\.|_test\.go|tests/)' || true
```

### 2. Build the introduced tests table

For each test file added or modified in the diff:

1. Read the test file
2. Identify each new or modified test (function, method, or `it()`/`test()` block)
3. Summarize what behavior the test verifies, not just what function it calls
4. Note whether the test is new, modified, or unchanged but now exercising changed code

Output:

| Test file | Test(s) | What it tests |
|---|---|---|
| `<path>` | `<test name>` | `<behavior verified>` |

If no test files were added or modified, state "No tests introduced or modified in this changeset."

### 3. Build the change coverage table

For each behavior change in the source diff:

1. Read the diff hunk and the surrounding code for context
2. Identify the behavior change (new function, modified logic, changed branch, new endpoint, changed error handling, etc.)
3. Search the test files (and existing tests if needed) for a test that exercises this specific change
4. Mark as covered or uncovered

Output:

| Changed file | Behavior changed | Covered by test? | Gap |
|---|---|---|---|
| `<path>` | `<description>` | Yes / No | `<gap description or em-dash>` |

Prioritize gaps by risk: changes to public APIs, business logic, or error paths matter more than changes to internal helpers or formatting.

### 4. Build the uncovered code table

Beyond behavior changes, identify code in the diff that no test exercises at all:

1. For each new or modified function/method in the source diff, check whether any test file calls or invokes it
2. For functions that are called by tests, check whether key branches or error paths within them are exercised
3. List anything unexercised

This is distinct from change coverage: change coverage asks "is this behavior change tested?"; uncovered code asks "is this code reached by any test at all?"

Output:

| File | Function / branch / path | Why it matters |
|---|---|---|
| `<path>` | `<description>` | `<risk if this code regresses silently>` |

Include code that is technically covered by a test call path but whose key branch or error path is never exercised.

### 5. Produce findings for uncovered changes

Each uncovered behavior change or uncovered code item should be formatted as a finding for the parent skill to include in its Findings section. Severity is proportional to risk:

- 🔴 MUST: uncovered change to a public API, security-sensitive path, or business-critical logic
- 🟡 SHOULD: uncovered change to error handling, edge cases, or internal logic with side effects
- 🟢 MAY: uncovered change to internal helpers, formatting, or low-risk utilities

If invoked directly (not by a parent skill), include these findings in the report directly.

### 6. Return the analysis

Return the three tables and the findings list. If called by a parent skill, the parent embeds them into its own report. If invoked directly, output the full report.

## Output Format

```markdown
## Test Coverage Analysis

### Introduced tests

| Test file | Test(s) | What it tests |
|---|---|---|
| <path> | <test name> | <behavior verified> |

### Change coverage

| Changed file | Behavior changed | Covered by test? | Gap |
|---|---|---|---|
| <path> | <description> | Yes / No | <gap or em-dash> |

### Uncovered code

| File | Function / branch / path | Why it matters |
|---|---|---|
| <path> | <description> | <risk if this code regresses silently> |

### Findings

#### <severity> / <title>

<description of the coverage gap and what test should be added>
```

## Example Usage

**Scenario 1: Called by review-pr**
```
review-pr dispatches analyze-test-coverage with the PR diff and worktree.
```
The skill reads the diff, identifies 3 new tests in `test_routes.py`, maps 4 behavior changes (2 covered, 2 not), and finds 1 uncovered function. Returns the tables; review-pr embeds them in its Coverage section and raises findings for the 2 uncovered changes.

**Scenario 2: Direct invocation on a branch**
```
/analyze-test-coverage origin/main..HEAD
```
Analyzes all changes on the current branch vs main. Reports that no tests were added despite 5 behavior changes, and lists all 5 as uncovered.

**Scenario 3: No test files in the diff**
```
/analyze-test-coverage
```
The diff contains only source changes, no test files. Reports "No tests introduced or modified" and lists all behavior changes as uncovered with appropriate findings.

## Related Skills

| Skill | Relationship |
|---|---|
| `review-pr` | Calls this skill to produce the Coverage section of its PR review report |
| `review-implementation` | Calls this skill to produce the Test Coverage section of its implementation review |
| `verify-pr` | Calls this skill to produce the test inventory alongside criteria conformance |
| `find-coverage-gaps` | Repo-wide coverage analysis using coverage tools; this skill is diff-focused and static |
