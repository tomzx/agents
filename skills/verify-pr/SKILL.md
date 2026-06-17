---
name: verify-pr
description: Static code inspection of a PR after runtime validation passes. Checks code quality, correctness, architecture alignment, and claim-to-code traceability without building or executing.
allowed-tools: Bash(gh:*, git:*, gh-cached:*, scripts/get-env:*), Read, Write, Edit, Glob, Grep
argument-hint: "<pr-number> [repository]"
---

# Verify Pull Request

Static code inspection of a PR that has already passed runtime validation via `/validate-pr`. Checks that the implementation is well-constructed: correct abstractions, no dead code, proper error handling, test quality, and architectural fit.

This answers "did you build the thing right?" Runtime proof is handled by `/validate-pr`.

## Prerequisites

- `gh` CLI authenticated with read access to the target repository
- PR number (`$1`) identifying an open pull request
- Ideally, `/validate-pr` has already been run and claims are confirmed at runtime
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `verify-pr`.

## Workflow

```
Fetch PR metadata + diff ($1)
         |
         v
Read validation report (if exists)
         |
         v
Static inspection
 (claims, code quality,
  architecture, tests)
         |
         v
Post verification report
```

## Steps

### 1. Fetch PR metadata and diff

```bash
gh-cached pr view $PR_NUMBER --repo $REPO --comments --refresh
```

```bash
gh pr diff $PR_NUMBER --repo $REPO
```

Extract:
- PR title and description with claims
- List of changed files and diff stats
- Any prior validation report from `/validate-pr`

### 2. Check validation prerequisites

If `/validate-pr` has been run, read its comment on the PR to understand which claims were validated, partially validated, or contradicted. Focus verification on validated claims to confirm the code backing them is sound.

If `/validate-pr` has not been run, note this in the report and proceed with verification against the PR description claims.

### 3. Claim-to-code traceability

For each claim in the PR description, trace it to the specific code changes:

- Identify the exact files and functions that implement each claim
- Verify the implementation path is reachable (no dead code, no unused entry points)
- Check that imports and wiring connect the pieces correctly
- Verify no claim depends on code that was not included in the PR

Record a mapping of:

| Claim | File(s) | Function(s)/Class(es) | Line(s) |
|-------|---------|----------------------|---------|

### 4. Code quality inspection

#### Scope and relevance

- Are there changes unrelated to the PR's stated purpose?
- Should unrelated changes be split into separate PRs?

#### Design and correctness

- Does the code follow SOLID principles?
- Does it match existing design patterns in the codebase?
- Are there code duplications that violate DRY?
- Are magic numbers/strings extracted as constants or configuration?
- Is there dead code or commented-out code?

#### Error handling

- Are errors handled gracefully?
- Are error messages meaningful and actionable?
- Is there proper cleanup of resources (connections, file handles, temp files)?

#### Type safety

- In typed or type-hinted languages, are parameters and return types annotated?
- Are there unsafe casts or type assertions that could fail at runtime?

#### Security

- Is input validated and sanitized?
- No hardcoded secrets or credentials in the diff?
- Parameterized queries to prevent injection?
- Authentication/authorization checks where needed?

### 5. Architecture and structure

- Are new files in the right directories with appropriate names?
- Are new dependencies justified and versions pinned?
- Are lock files updated?
- Is backward compatibility maintained or are breaking changes documented?
- Are contracts and persisted data forward compatible (unknown fields tolerated, unknown enum values handled, additive-only changes, versioning strategy)?
- Do any design decisions look like one-way doors that should be reconsidered?

### 6. Test quality

- Do tests exist for the new code?
- Do tests cover edge cases and error scenarios, not just happy paths?
- Are test names descriptive of what they test?
- Do tests test behavior rather than implementation details?
- Are there tests that would catch regressions for fix claims?

### 7. Documentation

- Are public APIs documented?
- Does README or user-facing documentation need updates?
- Are breaking changes documented?
- Are complex algorithms or business logic commented where needed?

### 8. Post verification report

```bash
gh pr comment $PR_NUMBER --repo $REPO --body "$(cat <<'EOF'
## Verification Report

### Summary

| Area | Status |
|------|--------|
| Claim traceability | Complete / Gaps found |
| Code quality | Sound / Issues found |
| Architecture | Aligned / Concerns |
| Tests | Adequate / Gaps |
| Security | Clean / Issues found |
| Documentation | Up to date / Needs updates |

### Claim Traceability

| Claim | Location | Status |
|-------|----------|--------|
| "<claim>" | `file.py:42` | Traced / Gap |

### Findings

#### Finding 1: <title>
- **Severity**: Must fix / Should fix / Nitpick
- **Location**: `file.py:42`
- **Description**: <what was found>
- **Suggestion**: <how to fix>

#### Finding 2: <title>
...

### Notes

<Any additional observations>

---

Posted with [verify-pr](SKILL_FILE_URL) (`SKILL_SHORT_SHA`)
EOF
)"
```

## Failure Modes

| Mode | Response |
|------|----------|
| **PR has no description or claims** | Post comment noting missing description, stop |
| **Large diff (>1000 lines)** | Focus on entry points and public API changes, note that full review is impractical |

## Example Usage

**Scenario 1: After successful validation**
```
/validate-pr 42
/verify-pr 42
```
PR #42 passed runtime validation. Verification traces each claim to code, finds a missing error handler and a TODO that should be resolved. Posts findings.

**Scenario 2: Without prior validation**
```
/verify-pr 55
```
No validation report found. Notes this in the report, verifies claims against code statically. Finds dead code and a backward-incompatible API change. Posts findings.

**Scenario 3: Clean PR**
```
/verify-pr 88
```
PR #88 is a focused bug fix. All claims trace cleanly, tests are adequate, no quality issues. Posts clean report.

## Next Step

After verification, use `/review-pr` for a full code review with reviewer communication guidelines, or `/quick-pr-review` for a rapid approval pass.
