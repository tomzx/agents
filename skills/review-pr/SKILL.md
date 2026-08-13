---
name: review-pr
description: Conduct the code-craft review of a GitHub pull request (quality, architecture, security, tests, operational concerns). Static only: does not build or run the code (verify-pr's conformance role) or judge whether the target is the right product (validate-pr's validation role).
allowed-tools: Bash(gh:*, ghx:*, git:*, ~/.agents/scripts/get-env:*, ~/.agents/scripts/should-post-to-github:*), Read, Write, Glob, Grep
argument-hint: "<pr-number>"
---

# Review Pull Request

Answers the **craft** question: "is this code well-built?" Covers code quality, architecture, security, tests, and operational concerns as static inspection. It does **not** build or run the code (that is `/verify-pr`'s conformance role) and does **not** judge whether the target is the right product (that is `/validate-pr`'s validation role). Findings about *whether the criteria are met* go to `/verify-pr`; findings about *whether the right problem is solved* go to `/validate-pr`. Writes findings to a structured markdown file.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, target the pull request from `$PR_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with read access to the target repository
- `git worktree` available
- PR number (`$1`) identifying an open pull request

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `review-pr`.

## Workflow

```
Fetch PR metadata + comments ($1)
            |
            v
  Create git worktree on PR branch
            |
            v
  Pre-Review Checklist
  (build, metadata, objective)
            |
            v
  Code Review Checklist
  (quality, tests, architecture,
   ops, security, docs)
            |
            v
  Context-Specific Review
  (feature / bug fix / DB / API?)
            |
            v
  Write review-pr.$SHORT_SHA.md
  (create or update)
             |
             v
   Post review file
   as PR comment
   (gated by should-post-to-github)
```

## Setup

Fetch PR information by piping the raw `ghx` output directly to a file (do not generate or summarize the content). PR review reports resolve to `$HOME/.sdlc/$REPO/pull-requests/$PR_NUMBER/` per `sdlc/references/shared.md` (PR Review Reports):
```bash
PR_REVIEW_DIR="$HOME/.sdlc/$REPO/pull-requests/$PR_NUMBER"
mkdir -p "$PR_REVIEW_DIR"
ghx pr view $1 --repo "$REPO" --comments --refresh > "$PR_REVIEW_DIR/gh-pr-view.md"
```

Extract:
- `HEAD_COMMIT`: the PR's head commit SHA (`headRefOid`)
- `SHORT_SHA`: first 7 characters of `HEAD_COMMIT`
- `PR_AUTHOR`: the PR author's GitHub username (`author.login`)
- `HEAD_BRANCH`: the PR's head branch name (`headRefName`)

```bash
gh pr view $1 --repo "$REPO" --json headRefName --jq '.headRefName'
```

```bash
ISSUE_NUMBER=$(gh pr view $1 --repo "$REPO" --json closingIssuesReferences --jq '.closingIssuesReferences[0].number // empty')
```

Create a git worktree on the PR branch so full files (not just diff hunks) can be read in context:

```bash
git fetch origin $HEAD_BRANCH
WORKTREE_DIR=/tmp/sdlc/$REPO/${ISSUE_NUMBER:-pr-$PR_NUMBER}
mkdir -p /tmp/sdlc/$REPO
git worktree add $WORKTREE_DIR origin/$HEAD_BRANCH
```

All subsequent code reading happens inside the worktree directory.

If worktree creation fails, stop.

## Pre-Review Checklist

This skill is static code-craft review. It does not build or run the code (that is `/verify-pr`'s conformance role) and does not judge whether the target is the right product (that is `/validate-pr`'s role). Establish context, then review craft.

Before diving into the code:

* Prior reports
	* If `/verify-pr` has run, read its conformance report and treat the build/criteria status as settled; do not rebuild or re-litigate conformance here
* PR Metadata
	* Read the PR title and description - is it clear and complete?
	* Is the change size appropriate for what is implemented?
* Understanding the Objective
	* Read the linked issue title and description (use `gh` to pull issue details) for context only
	* Understand what the PR is meant to do, so craft findings can be weighed against intent

## Code Review Checklist

### Scope & Relevance

Change hygiene only. Whether a change serves an acceptance criterion is a conformance question for `/verify-pr`; whether it serves the real need is a validation question for `/validate-pr`. Here, focus on:

* Changes that obscure or distract from the actual work
	* Unrelated formatting changes, drive-by refactorings, or unrelated fixes mixed in
	* Should these be split into separate PRs for clarity?
	* Do irrelevant changes obscure the actual changes being reviewed?

### Code Quality & Design

* Naming Conventions
	* Verify classes, methods, functions, parameters naming
		* Are they significant of their purpose?
		* Are they clear enough?
		* Are they respecting the naming convention?
* Design Principles
	* Does the code respect [SOLID](https://en.wikipedia.org/wiki/SOLID)?
	* Is the code following existing design patterns in the codebase?
	* Are there code duplications that violate DRY principle?
* Code Style
	* Check code for code style issues
	* Are magic numbers/strings extracted as constants or configuration?
	* Is there dead code or commented-out code that should be removed?
* Type Safety
	* In a weak typed or type hinted language, are parameters and return of functions/methods typed?

### Testing & Coverage

Review tests as code artifacts for quality. Whether a test proves a specific acceptance criterion is `/verify-pr`'s conformance concern.

* Test Existence
	* Is the new code accompanied by tests?
* Test Quality
	* Do tests cover edge cases and error scenarios?
	* Are test names descriptive of what they're testing?
	* Are tests testing behavior rather than implementation details?
* Manual Testing
	* What manual testing was done to confirm the change works as intended (described in the PR, comments, or linked issue)?
	* Do the manual checks cover the key user-facing scenarios, or only the happy path?

### Architecture & Structure

* File Organization
	* Verify the location of new/moved files
		* Are the files in the right directory?
		* Are they appropriately named?
* Dependencies
	* Are new dependencies justified?
	* Are versions pinned appropriately?
	* Are lock files updated?
	* License compatibility verified?
* Backward Compatibility
	* Consider that when functions/methods signature change, code may now be backward incompatible
		* Discuss whether this is necessary
		* Backward incompatible changes should be documented
* Forward Compatibility
	* Can contracts and persisted data accept future additions without breaking (unknown fields tolerated, unknown enum values handled gracefully, additive-only changes)?
	* Is there a versioning strategy so future evolution does not force coordinated upgrades on all consumers?
	* Are extension points (reserved fields, flags) provided for known likely future change, or does the design bake in fixed-set assumptions?
* Reversibility
	* Can we undo this cleanly if the change needs to be rolled back?
	* Are any of the design decisions taken single way doors or reversible?
	* Are schema/data migrations, API changes, and config changes reversible, and is there a documented rollback path?

### Operational Concerns

* Logging
	* Is appropriate logging added?
	* Are log levels appropriate?
	* Is sensitive data being logged?
* Monitoring
	* Are relevant metrics/traces/alerts for monitoring purposes added?
* Error Handling
	* Are errors handled gracefully?
	* Are error messages meaningful and actionable?
	* Is there proper cleanup of resources (connections, memory, subscriptions)?
* Performance
	* Are there any obvious performance issues (N+1 queries, inefficient algorithms)?
	* Is caching used appropriately?

### Security & Data

* Input Validation
	* Is input validated and sanitized?
	* Are boundary conditions and null/undefined cases handled?
* Security Best Practices
	* Authentication/authorization checks in place?
	* No hardcoded secrets or credentials?
	* Parameterized queries to prevent SQL injection?
	* XSS/CSRF protections where applicable?
* Data Handling
	* Is PII handled appropriately?
	* Are data migrations safe and reversible?

### Documentation & Maintenance

* Code Documentation
	* Are complex algorithms or business logic commented?
	* Are public APIs documented?
* Project Documentation
	* Does README or user-facing documentation need updates?
	* Are breaking changes documented in CHANGELOG?
* Technical Debt
	* Are there TODOs that should be completed within this review?
	* Is new technical debt being introduced? Is it necessary?

## Context-Specific Reviews

### New Features

* Are feature flags considered for gradual rollout?
* Is the UX/UI accessible and responsive?
* Are user-facing error messages clear and helpful?

(Whether the feature meets its requirements is `/verify-pr`'s conformance verdict.)

### Bug Fixes

* Is the fix localized to the right place, or does it fan out unnecessary change?
* Is the new or changed test code well-written (clear, behavior-focused)?

(Root cause vs. symptom is `/validate-pr`'s call; a regression test that proves the fix is `/verify-pr`'s.)

### Database Changes

* Are schema migrations safe and reversible?
* Are data migrations idempotent?
* Is there a rollback plan?
* Are indexes added for new queries?

### API Changes

* Are API contracts maintained or versioned appropriately?
* Is pagination, filtering, sorting handled correctly?
* Are rate limits considered?

## Review Communication Guidelines

When providing feedback:

* Be Specific and Actionable
	* Provide specific suggestions, not just problems
	* Include code examples when helpful
* Prioritize Feedback
	* Clearly mark nitpicks and optional comments
	* Use an approach such as [RFC2119](https://datatracker.ietf.org/doc/html/rfc2119) where you indicate whether a change is a MUST, SHOULD, or MAY
	* Prefix each finding with the Code Review Checklist section it maps to, splitting signal, section, and title with `/`, e.g. `### 🔴 MUST / Security & Data / Remove hardcoded API key`, so the table's status rows trace back to the findings
	* Traffic light color emojis: 🔴 MUST, 🟡 SHOULD, 🟢 MAY
	* Another emoji based option is [gitmoji](https://gitmoji.dev/)
* Maintain Positive Tone
	* Assume competence
	* Provide rationale or context for suggestions
	* Consider how comments may be interpreted
	* Don't criticize the person, criticize the code
	* Don't use harsh language

## Output

Put 🔴/🟢 at the top of the document to indicate the overall status of the review (ready to merge, needs work, etc.)

Indicate the date+time (using ISO 8601 format) the file was generated in the file header.

Order findings by importance: 🔴 MUST first, then 🟡 SHOULD, then 🟢 MAY, so blockers surface at the top.

Include a checklist table with one row per Code Review Checklist section (Scope & Relevance, Code Quality & Design, Testing & Coverage, Architecture & Structure, Operational Concerns, Security & Data, Documentation & Maintenance). Use the traffic-light symbols only, consistent with the findings: 🟢 (pass) / 🟡 (needs attention) / 🔴 (issues), and keep notes terse so the table stays scannable.

Include a Coverage section listing what tests exist, what manual testing was done to confirm the change works (from the PR description, comments, or linked issue), what is missing, and the CI status.

When reviewing, write the response to `$PR_REVIEW_DIR/review-pr.$SHORT_SHA.md` (resolving per `sdlc/references/shared.md`), substituting the 7-character short SHA of the head commit being reviewed.
Start the file with the marker `<!-- review-pr:HEAD_COMMIT -->` so the orchestrator can detect which commit was reviewed. Substitute `HEAD_COMMIT` with the full head SHA.
If a file already exists for this `$SHORT_SHA`, update the file with the new information and tell me what changes have been made since the last review.
If reviewing a new `$SHORT_SHA`, create a new file. To find the baseline for the "what changed" summary, glob `$PR_REVIEW_DIR/review-pr.*.md` (excluding `review-pr.$SHORT_SHA.md`), read the reviewed SHA from each filename (the segment between `review-pr.` and `.md`), and select the one whose commit is the most recent ancestor of the current `$SHORT_SHA` (compare with `git merge-base --is-ancestor`); fall back to the newest by file mtime if no ancestor is found. Read that file to summarize what has changed since that review. (This directory is user-global under `$HOME`; where it does not persist across runs, no baseline is found and the review proceeds fresh.)

### Example Output

```
<!-- review-pr:a1b2c3d -->
# Review of PR #42: Add payment processing endpoint

🟢 **Approved with minor suggestions**

Reviewed SHA: `a1b2c3d`

## Summary

The PR implements the Stripe payment endpoint per the acceptance criteria
in #37. Implementation is clean, well-tested, and follows existing patterns
in `src/payments/`. One blocking issue plus two non-blocking suggestions below.

## Checklist

| Section | Status | Notes |
|---|---|---|
| Scope & Relevance | 🟢 | No unrelated changes |
| Code Quality & Design | 🟢 | SOLID, naming, no duplication |
| Testing & Coverage | 🟡 | Webhook signature verification untested |
| Architecture & Structure | 🟢 | Follows existing `src/payments/` patterns |
| Operational Concerns | 🟡 | No rate limiting on `POST /payments` |
| Security & Data | 🔴 | Hardcoded test API key in `client.py` |
| Documentation & Maintenance | 🟢 | No user-facing docs affected |

## Findings

### 🔴 MUST / Security & Data / Remove hardcoded test API key

`src/payments/client.py:8` contains `sk_test_4eC39HqLy...`. Move it to an
environment variable (`STRIPE_API_KEY`) and load via `os.environ`.
Verified it is not in `.env.example` either, so add it there as well.

### 🟡 SHOULD / Operational Concerns / Add rate limiting on the endpoint

`src/payments/routes.py:24` exposes `POST /payments` without a rate limiter.
A malicious client could flood charge attempts. Reuse the existing
`@rate_limit` decorator from `src/api/middleware.py`:

@rate_limit(limit=10, window=60)
@router.post("/payments")
async def create_payment(...): ...

### 🟢 MAY / Code Quality & Design / Extract magic currency multiplier

`src/payments/amount.py:15` uses `amount * 100` to convert dollars to cents.
Consider `CENTS_PER_DOLLAR = 100` as a named constant for readability.

## Coverage

- Tests present: `tests/payments/test_routes.py` (8 cases, happy + error paths)
- Manual testing: author tested Stripe checkout flow end-to-end, verified webhook delivery and retry behavior
- Missing: webhook signature verification not tested
- CI status: passing

## Outcome

No blocking issues remain once the hardcoded key is removed. Rate limiting
should be addressed before exposing this publicly.
```

### Post the review as a PR comment

The review is saved to `$PR_REVIEW_DIR/review-pr.$SHORT_SHA.md`. Posting it as a PR comment is decided by `should-post-to-github`.

After writing `review-pr.$SHORT_SHA.md`, run `~/.agents/scripts/should-post-to-github --repo "$REPO" --author "$PR_AUTHOR"`. If it exits 1, skip posting, the review is already saved to `$PR_REVIEW_DIR/review-pr.$SHORT_SHA.md`.

If it exits 0, post the review file as a comment on the PR so the author and other reviewers can see the verdict. The file already contains the `<!-- review-pr:HEAD_COMMIT -->` marker.

```bash
FOOTER="Posted with [review-pr](${SKILL_FILE_URL}) (\`${SKILL_SHORT_SHA}\`)"
gh pr comment $PR_NUMBER --repo $REPO --body "$(cat "$PR_REVIEW_DIR/review-pr.$SHORT_SHA.md")

${FOOTER}"
```

### Clean up

```bash
git worktree remove $WORKTREE_DIR
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; the subject passes review |
| `changes-requested` | Findings the author must address before it passes |
| `rejected` | Fundamental flaw requiring rework or stopping |

## Example Usage

**Scenario 1: New feature PR**
```
/review-pr 42
```
PR adds a payment processing endpoint. Review checks code quality and architecture, notes test-quality gaps, confirms no hardcoded API keys, and notes a 🟡 SHOULD for adding a rate limit. (Conformance to the acceptance criteria is `/verify-pr`'s verdict.)

**Scenario 2: Bug fix PR**
```
/review-pr 88
```
PR fixes a null pointer. Review checks that the change is localized and the new test is well-written, and marks 🟢 ready to merge. (Root cause vs. symptom is `/validate-pr`'s call; a regression test proving the fix is `/verify-pr`'s.)

**Scenario 3: Re-review after changes**
```
/review-pr 55
```
`review-pr.<previous-sha>.md` already exists from a previous run on an earlier commit. Create `review-pr.<new-sha>.md`, read the previous file to summarize what changed since the last review (e.g., "Test coverage added, rate limit not yet addressed").

## Useful Commands Reference

| Command | Description |
|---|---|
| `ghx pr view <pr-number> --repo <owner>/<repo> --comments --refresh` | Fetch PR details and review comments (fresh) |
| `ghx issue view <issue-number> --repo <owner>/<repo>` | Fetch linked issue details (cached) |
| `gh pr comment <pr-number> --repo <owner>/<repo> --body "..."` | Post review summary comment to the PR |
| `git worktree add /tmp/sdlc/<owner>/<repo>/<issue> origin/<branch>` | Create a worktree on the PR branch for code reading |
| `git worktree remove /tmp/sdlc/<owner>/<repo>/<issue>` | Clean up the worktree after review |
