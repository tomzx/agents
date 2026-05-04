---
name: review-issue
description: Review a GitHub issue for completeness, clarity, and acceptance criteria quality before development begins.
allowed-tools: Bash(gh:*, gh-cached:*, scripts/get-env:*), Read, Write
argument-hint: "<issue-url-or-number>"
---

# Review Issue

Audits an existing GitHub issue and reports findings across four categories: completeness, clarity, acceptance criteria quality, and scope.
If findings exist, either proposes an edited issue body in the conversation or posts a comment requesting improvements.

## Prerequisites

- `gh` CLI authenticated with access to the repository
- Issue URL or number (`$1`)

## Steps

1. Fetch the issue and its comments:
   ```
   gh-cached issue view $1 --comments
   ```
2. Identify the issue type (bug / feature / question / chore).
3. Evaluate using the checklist below.
4. Report findings. If findings exist, choose one of:
   - Propose a revised issue body in the conversation for the user to approve, then apply with `gh issue edit`
   - Post a comment requesting clarification (when the missing information must come from the reporter)

## Review Checklist

### Completeness

**Bug reports:**
- Is the unexpected behavior clearly described?
- Are steps to reproduce provided?
- Are the expected vs. actual behaviors stated?
- Is the affected version or environment mentioned?

**Feature requests:**
- Is the problem or use case described (not just the desired solution)?
- Is the intended user or stakeholder identified?
- Is the scope reasonably bounded?

**All types:**
- Is background/context present?
- Are acceptance criteria present?
- Is there a time budget (for private repositories)?

### Clarity
- Is the title specific enough to understand the issue without reading the body?
- Is the description free of ambiguous terms?
- Are acceptance criteria written as verifiable conditions, not vague goals?

### Acceptance Criteria Quality
- Is each AC testable (can a concrete test be written for it)?
- Is each AC specific about what, not how?
- Do the ACs cover the happy path and key error/edge cases?
- Are there duplicate or contradictory ACs?
- Are there ACs implied by the description but not stated?

### Scope
- Is the issue focused on one thing (not a bundle of unrelated changes)?
- Are there tasks in the body that belong in separate issues?
- Is the scope consistent with the time budget (if present)?

## Output Format

```markdown
## Completeness

<Findings or "No issues found.">

## Clarity

<Findings or "No issues found.">

## Acceptance Criteria

<Findings or "No issues found.">

## Scope

<Findings or "No issues found.">

## Suggested Additions

<Missing ACs or sections that should be added, ready to copy into the issue.>
```

If there are no findings across all categories, confirm: "Issue looks complete and well-formed — ready to proceed to `/create-requirements`."

## Example Usage

**Scenario 1: Bug report missing reproduction steps**
```
/review-issue 42
```
Issue says "login is broken" with no steps to reproduce.
Report under Completeness. Post comment asking for steps, expected behavior, and observed behavior.

**Scenario 2: Feature with untestable ACs**
```
/review-issue https://github.com/owner/repo/issues/88
```
AC says "the UX should be smooth."
Report under Acceptance Criteria. Propose rewrite: "The user can complete checkout in 3 steps or fewer."

**Scenario 3: Issue bundling multiple features**
```
/review-issue 100
```
Issue describes adding dark mode, changing font sizes, and updating the color palette.
Report under Scope — recommend splitting into three focused issues.

**Scenario 4: Missing edge case ACs**
```
/review-issue 55
```
Feature describes a file upload flow. ACs cover the happy path but say nothing about oversized files, unsupported formats, or network failures.
Report under Acceptance Criteria. Propose the missing ACs.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh-cached issue view <issue> --comments` | Fetch issue details and comments (cached) |
| `gh issue edit <issue> --body "..."` | Update the issue body with improved content |
| `gh issue comment <issue> --body "..."` | Post a comment requesting clarification from the reporter |
