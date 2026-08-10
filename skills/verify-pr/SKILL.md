---
name: verify-pr
description: Static code inspection of a PR after runtime validation passes. Checks code quality, correctness, architecture alignment, and acceptance-criteria-to-code traceability without building or executing.
allowed-tools: Bash(gh:*, git:*, ghx:*, scripts/get-env:*, scripts/should-post-github-comment:*), Read, Write, Edit, Glob, Grep
argument-hint: "<pr-number> [repository]"
---

# Verify Pull Request

Static code inspection of a PR that has already passed runtime validation via `/validate-pr`. Checks that the implementation is well-constructed and that it actually satisfies the linked issue's acceptance criteria: correct abstractions, no dead code, proper error handling, test quality, and architectural fit.

This answers "did you build the thing right, and does it implement what was asked?" Runtime proof is handled by `/validate-pr`.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, target the pull request from `$PR_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with read access to the target repository
- PR number (`$1`) identifying an open pull request
- Ideally, `/validate-pr` has already been run and acceptance criteria are confirmed met at runtime
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `verify-pr`.

## Workflow

```
Fetch PR metadata + diff + linked issue(s) ($1)
         |
         v
Parse acceptance criteria from issue(s)
+ claims from PR description, build coverage map
         |
         v
Read validation report (if exists)
         |
         v
Static inspection
 (criteria-to-code traceability,
  code quality, architecture, tests)
         |
         v
Post verification report
```

## Steps

### 1. Fetch PR metadata, diff, and linked issue(s)

```bash
gh pr view $PR_NUMBER --repo $REPO --json title,body,headRefName,headRefOid,author,baseRefName,files,additions,deletions,changedFiles,closingIssuesReferences
```

```bash
gh pr diff $PR_NUMBER --repo $REPO
```

Extract:
- PR title and description with claims
- `HEAD_COMMIT`: the `headRefOid` (latest commit SHA, full)
- `SHORT_SHA`: first 7 characters of `HEAD_COMMIT`
- `PR_AUTHOR`: the `author.login` (GitHub username of the PR author)
- List of changed files and diff stats
- Linked closing issues from `closingIssuesReferences` (each has `number` and `url`)
- Any prior validation report from `/validate-pr`

#### 1a. Resolve and fetch linked issue(s)

Use `closingIssuesReferences` as the authoritative source of linked issues. If empty, fall back to scanning the PR body for `Fixes #N`, `Closes #N`, `Resolves #N`, or bare `#N` references.

For each linked issue number, fetch its full body:

```bash
gh issue view $ISSUE_NUMBER --repo $REPO --json number,title,body,state
```

### 2. Parse acceptance criteria and build the coverage map

Apply the same parsing as `/validate-pr` Step 2:

- Extract acceptance criteria from the linked issue's `# Acceptance Criteria` section (`## Must` and `## Should` checklist items). If the issue does not use the structured format, infer requirements from the body and note that in the report.
- Parse claims from the PR description as secondary hints.
- Build a coverage map: each criterion mapped (or unmapped) to PR claims, plus any unmapped claims flagged as out of scope.

If no linked issue can be resolved, or none yields parseable criteria, post a comment asking the author to link an issue with acceptance criteria and stop. Do not verify PR claims in a vacuum.

### 3. Check validation prerequisites

If `/validate-pr` has been run, read its comment on the PR to understand which acceptance criteria were validated, partially validated, or contradicted at runtime. Focus verification on criteria confirmed at runtime to confirm the code backing them is sound, and pay extra attention to any criteria `/validate-pr` could not confirm.

If `/validate-pr` has not been run, note this in the report. Verification can still establish criteria-to-code traceability statically, but it is not a substitute for runtime proof.

### 4. Criteria-to-code traceability

For each acceptance criterion from the coverage map, trace it to the specific code changes that implement it:

- Identify the exact files and functions that implement each criterion
- Verify the implementation path is reachable (no dead code, no unused entry points)
- Check that imports and wiring connect the pieces correctly
- Verify no criterion depends on code that was not included in the PR

A criterion with no code backing it is a **gap**, regardless of whether a PR claim references it. Conversely, code that implements no criterion is out of scope and should be called out (see Step 5).

Use the mapped PR claim(s) as a starting pointer, but confirm the trace against the criterion itself, not just the claim.

Record a mapping of:

| Criterion (priority) | Source issue | Claim(s) | File(s) | Function(s)/Class(es) | Line(s) | Status |
|---|---|---|---|---|---|---|

Where Status is **Traced** (code backs the criterion) or **Gap** (no implementing code found).

### 5. Code quality inspection

#### Scope and relevance

- Do the changes stay within the scope of the linked issue's acceptance criteria?
- Are there changes that implement no acceptance criterion (out of scope) and should be split into separate PRs?

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

### 6. Architecture and structure

- Are new files in the right directories with appropriate names?
- Are new dependencies justified and versions pinned?
- Are lock files updated?
- Is backward compatibility maintained or are breaking changes documented?
- Are contracts and persisted data forward compatible (unknown fields tolerated, unknown enum values handled, additive-only changes, versioning strategy)?
- Do any design decisions look like one-way doors that should be reconsidered?

### 7. Test quality

- Do tests exist for the code backing each acceptance criterion?
- Do tests cover edge cases and error scenarios, not just happy paths?
- Are test names descriptive of what they test?
- Do tests test behavior rather than implementation details?
- For each **Must** criterion, is there a test that would fail if the criterion were not met?
- Are there tests that would catch regressions for fix criteria?

### 8. Documentation

- Are public APIs documented?
- Does README or user-facing documentation need updates?
- Are breaking changes documented?
- Are complex algorithms or business logic commented where needed?

### 9. Post verification report

Write the report to a file:

```bash
BODY="$(cat <<'EOF'
<!-- verify-pr:HEAD_COMMIT -->
## Verification Report

### Summary

Verified commit: SHORT_SHA

| Area | Status |
|------|--------|
| Criteria traceability | Complete / Gaps found |
| Code quality | Sound / Issues found |
| Architecture | Aligned / Concerns |
| Tests | Adequate / Gaps |
| Security | Clean / Issues found |
| Documentation | Up to date / Needs updates |

<details>
<summary>Details</summary>

### Criteria Coverage

| Criterion (priority) | Issue | Traced to | Status |
|---|---|---|---|
| "<criterion>" (Must) | #N | `file.py:42` | Traced / Gap |

### Unmapped PR claims (out of scope relative to issue)

- "<claim>" — no acceptance criterion maps to this

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

</details>

---

EOF
)"

mkdir -p ".sdlc/pull-requests/$PR_NUMBER"
printf '%s\n' "${BODY}" > ".sdlc/pull-requests/$PR_NUMBER/verify-pr.$SHORT_SHA.md"
```

### Post the verification report as a PR comment

Run `scripts/should-post-github-comment --repo "$REPO" --author "$PR_AUTHOR"`. If it exits 1, skip posting, the report is already saved to `.sdlc/pull-requests/$PR_NUMBER/verify-pr.$SHORT_SHA.md`.

If it exits 0, post the report file as a comment on the PR. The file already contains the `<!-- verify-pr:HEAD_COMMIT -->` marker.

```bash
FOOTER="Posted with [verify-pr](${SKILL_FILE_URL}) (\`${SKILL_SHORT_SHA}\`)"
gh pr comment $PR_NUMBER --repo $REPO --body "$(cat .sdlc/pull-requests/$PR_NUMBER/verify-pr.$SHORT_SHA.md)

${FOOTER}"
```

## Failure Modes

| Mode | Response |
|------|----------|
| **No linked issue or no parseable acceptance criteria** | Post comment asking author to link an issue with acceptance criteria, stop |
| **PR has no description or claims** | Proceed; criteria drive verification, claims are optional hints. Note the absence of claims in the report |
| **Large diff (>1000 lines)** | Focus on entry points and public API changes, note that full review is impractical |

## Example Usage

**Scenario 1: After successful validation**
```
/validate-pr 42
/verify-pr 42
```
PR #42 passed runtime validation against the linked issue's criteria. Verification traces each criterion to code, finds a missing error handler and a TODO that should be resolved. Posts findings.

**Scenario 2: Without prior validation**
```
/verify-pr 55
```
No validation report found. Notes this in the report, traces each acceptance criterion to code statically. Finds dead code and a backward-incompatible API change. Posts findings.

**Scenario 3: Clean PR**
```
/verify-pr 88
```
PR #88 is a focused bug fix. All criteria trace cleanly to code, tests are adequate, no quality issues. Posts clean report.

**Scenario 4: Out-of-scope PR**
```
/verify-pr 91
```
PR #91 implements a PR claim that no acceptance criterion covers, and leaves one Must criterion unaddressed. Verification flags the unmapped claim as out of scope and the criterion as a gap. Posts findings.

## Next Step

After verification, use `/review-pr` for a full code review with reviewer communication guidelines, or `/quick-pr-review` for a rapid approval pass.
