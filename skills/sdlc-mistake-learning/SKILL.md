---
name: sdlc-mistake-learning
description: Analyze a change set to surface mistakes made during development, extract root causes, and encode durable lessons to prevent recurrence.
argument-hint: "[branch, commit range, or PR number]"
---

# SDLC Mistake Learning

Examines the development history of a change set to identify where things went wrong, why, and what patterns to avoid in the future.
Produces a structured mistake log with root causes and encodes actionable rules into AGENTS.md.

## Prerequisites

- A git repository with the change set in history (branch, commit range, or PR)
- Write access to AGENTS.md (or equivalent persistent rules file)

## What Counts as a Mistake

Look for evidence of:

- **Rework:** code written and then substantially rewritten or deleted in a later commit
- **Reverts:** `git revert` commits or "undo" / "revert" in commit messages
- **Bug fixes during development:** commits with "fix", "correct", "oops", "wrong", "broken", "typo" targeting code introduced in the same change set
- **Direction changes:** a design or approach adopted and then abandoned mid-branch
- **Repeated review cycles:** review comments addressing the same issue more than once
- **Test failures:** commits with "fix test", "make tests pass", "green", "failing" targeting test failures introduced in the same branch
- **Scope creep corrections:** features added and then removed or deferred
- **Integration issues:** problems discovered only when combining with other code or systems

## Steps

### 1. Identify the Change Set

Resolve the scope from `$1` (branch name, `commit1..commit2`, or PR number).
If not provided, ask: "What change set should I analyze? Provide a branch name, commit range, or PR number."

Run the following to gather raw material:

```bash
# Full commit log for the branch
git log --oneline main..HEAD

# Commit log with patches (for detailed analysis)
git log -p main..HEAD

# Files changed
git diff --stat main..HEAD

# Look for revert, fix, undo, wrong, broken commits
git log --oneline main..HEAD | grep -iE "(revert|fix|undo|wrong|broken|oops|correct|typo|failing|mistake)"
```

If analyzing a PR, also read the PR description and review comments for reported issues.

### 2. Classify Each Mistake

For each mistake found, record:

| Field | Description |
|---|---|
| **Type** | Category (rework, revert, bug-during-dev, direction-change, test-failure, integration-issue, scope-creep) |
| **What happened** | One sentence describing the mistake |
| **Trigger commit** | The commit that introduced the problem |
| **Resolution commit** | The commit that fixed or addressed it |
| **Cost** | Rough estimate of effort wasted (small = <1h, medium = 1–4h, large = >4h) |

### 3. Root Cause Analysis

For each mistake, drill into why it happened using the "5 Whys" method.
Stop at the deepest cause that a process change could address.

Common root cause categories:

- **Misunderstood requirements:** the spec or issue was ambiguous or not read carefully enough
- **Skipped verification:** the change was not tested or reviewed before moving on
- **Wrong mental model:** an incorrect assumption about how a system, API, or library works
- **Tooling/environment issue:** a local environment masked a problem that appeared in CI or staging
- **Premature implementation:** coding began before the design was clear
- **Missing context:** relevant code, constraints, or prior decisions were not consulted first
- **Rushed work:** time pressure led to shortcuts that had to be undone

### 4. Extract Patterns

Group mistakes by root cause category.
Look for recurring themes: if the same root cause appears more than once, it is a systemic issue, not a one-off.

For each pattern, draft a rule in the form:
> **Before [trigger action], always [preventive step].**

Examples:
- Before implementing, always read the full spec and confirm acceptance criteria are understood.
- Before merging a database migration, always run it against a copy of production data locally.
- Before assuming library behavior, always check the docs or write a small isolated test.

### 5. Update AGENTS.md

Open AGENTS.md and locate the most appropriate section for each new rule.
Add each rule that is not already present (check for semantic duplicates, not just textual ones).
Prefer adding to an existing section over creating a new one.

Mark each rule with a `<!-- learned: YYYY-MM-DD -->` comment so its origin is traceable.

### 6. Produce the Mistake Log

Write the findings as a structured report (to stdout or a file, depending on context).

## Output Format

```markdown
# Mistake Learning: <Change Set Name>

**Date:** <YYYY-MM-DD>
**Scope:** <branch / commit range / PR>
**Total mistakes found:** <N>
**Total estimated cost:** <Nh>

---

## Mistake Log

### 1. <Short label>

| | |
|---|---|
| **Type** | <type> |
| **What happened** | <one sentence> |
| **Trigger** | `<commit hash>` — <commit message> |
| **Resolution** | `<commit hash>` — <commit message> |
| **Cost** | <small / medium / large> |

**Root cause:** <deepest why>

---

(repeat for each mistake)

---

## Patterns

### <Root Cause Category>

Mistakes: #<N>, #<N>

<One paragraph describing the pattern and why it keeps occurring.>

**Rule:** Before <trigger>, always <preventive step>.

---

## AGENTS.md Updates

The following rules were added:

- **[Section]:** <rule text>

(or "No new rules added — all lessons were already encoded.")

## Summary

<2–3 sentences on the most important takeaway from this change set's mistakes.>
```

## Example Usage

**Scenario 1: Branch with rework**
A feature branch shows three commits with "fix" in the message targeting code from the same branch.
Root cause: the developer skipped writing a test first, so errors surfaced only after manual testing.
Rule added to AGENTS.md: "Before marking a task done, always run the test suite against the new code, not just the existing suite."

**Scenario 2: Direction change mid-branch**
Two commits establish a REST endpoint; three commits later the approach is scrapped and replaced with a GraphQL resolver.
Root cause: the API contract was not reviewed with the frontend team before implementation started.
Rule added: "Before implementing an API endpoint, always confirm the contract with consumers."

**Scenario 3: Test failures introduced during development**
Commit `abc123` breaks two existing tests; commit `def456` (three commits later) fixes them.
Root cause: CI was not run locally before pushing, and the broken tests were only caught in the pipeline.
Rule added: "Before pushing, always run the full test suite locally."

**Scenario 4: No mistakes found**
The branch has a clean, linear history with no reverts, no fix-ups, and no direction changes.
Report: "No mistakes detected in this change set. History is linear and intentional."

## Useful Commands Reference

| Command | Description |
|---|---|
| `git log --oneline main..HEAD` | Commits in the current branch not yet in main |
| `git log -p main..HEAD` | Full patches for all branch commits |
| `git diff --stat main..HEAD` | Files changed and line counts |
| `git log --oneline main..HEAD \| grep -iE "(revert\|fix\|undo\|wrong\|broken\|oops)"` | Filter for mistake-signal commits |
| `git show <hash>` | Inspect a specific commit |
| `git diff <hash1> <hash2>` | Diff between two commits |
