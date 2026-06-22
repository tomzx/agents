---
name: review-issue
description: Review a GitHub issue for completeness, clarity, acceptance criteria quality, and time budget defensibility before development begins.
allowed-tools: Bash(gh:*, gh-cached:*, scripts/get-env:*), Read, Write
argument-hint: "<issue-url-or-number>"
---

# Review Issue

Audits an existing GitHub issue and reports findings across five categories: completeness, clarity, acceptance criteria quality, time budget defensibility, and scope.
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
- Are ACs split into **Must** (the exit gate) and **Should** (deferrable)? If a flat list is used, propose the split.
- Is **Must** minimal? If it exceeds roughly 5 items, flag the issue as likely too broad and recommend splitting the issue.
- Do the **Must** ACs cover the happy path, with edge cases and error handling moved to **Should** (or kept in Must only when they gate "done")?
- Are there duplicate or contradictory ACs?
- Are there ACs implied by the description but not stated?

### Time Budget
- For private repositories, is a total estimate present?
- Is the estimate justified by a **breakdown** (work area : sub-estimate : one-line cost driver) rather than a bare number?- Are the **assumptions** the estimate depends on (what is already in place, what is out of scope) stated?
- Does the total roughly match the sum of the breakdown items, with no unexplained gap?
- Is the scope consistent with the budget? (A large budget for a thin scope, or a thin budget for a broad scope, is a smell.)

### Scope
- Is the issue focused on one thing (not a bundle of unrelated changes)?
- Are there tasks in the body that belong in separate issues?

## Output Format

```markdown
## Completeness

<Findings or "No issues found.">

## Clarity

<Findings or "No issues found.">

## Acceptance Criteria

<Findings or "No issues found.">

## Time Budget

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
Report under Acceptance Criteria. Propose the missing ACs (in **Should**, since they are deferrable edge cases unless they gate "done").

**Scenario 5: Flat acceptance criteria list with no prioritization**
```
/review-issue 77
```
Issue lists 8 ACs in a flat checklist, mixing happy-path items with edge cases and polish.
Report under Acceptance Criteria. Propose splitting into **Must** (the ~3 that define "done") and **Should** (the rest), and flag that 8 Must-level items suggests the issue is too broad and should be split.

**Scenario 6: Undefendable time budget**
```
/review-issue 64
```
Private-repo issue has "Time budget: 8h" with no breakdown or assumptions.
Report under Time Budget. Propose a breakdown such as "schema migration: 2h (new table)", "endpoint: 3h (reuses auth middleware)", and "tests: 2h", plus an assumptions line such as "assumes the auth middleware already exists; no data backfill".

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh-cached issue view <issue> --comments` | Fetch issue details and comments (cached) |
| `gh issue edit <issue> --body "..."` | Update the issue body with improved content |
| `gh issue comment <issue> --body "..."` | Post a comment requesting clarification from the reporter |
