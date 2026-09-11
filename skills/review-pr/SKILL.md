---
name: review-pr
description: "Conduct the code-craft review of a GitHub pull request (approach and simplicity, quality, architecture, security, tests, operational concerns). Static only: does not build or run the code (verify-pr's conformance role) or judge whether the target is the right product (validate-pr's validation role)."
allowed-tools: Bash(gh:*, ghx:*, git:*, ~/.agents/scripts/get-env:*, ~/.agents/scripts/should-post-to-github:*), Read, Write, Glob, Grep
argument-hint: "<pr-number>"
---

# Review Pull Request

Answers the **craft** question: "is this code well-built?" Covers approach and simplicity, code quality, architecture, security, tests, and operational concerns as static inspection. It does **not** build or run the code (that is `/verify-pr`'s conformance role) and does **not** judge whether the target is the right product (that is `/validate-pr`'s validation role). Findings about *whether the criteria are met* go to `/verify-pr`; findings about *whether the right problem is solved* go to `/validate-pr`. Judging whether the chosen approach is the simplest and most changeable for this codebase is this skill's job (see Approach & Simplicity); approach-level notes arriving from `/validate-pr` or `/verify-pr` land there. Writes findings to a structured markdown file.

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
  review.yaml scope?
  (same head -> stop, return state;
   pure rebase -> bump sha, stop;
   ancestor delta or contained
   tree-diff -> incremental;
   else -> full review)
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
  (approach, quality, tests,
   architecture, ops, security, docs)
            |
            v
  Context-Specific Review
  (feature / bug fix / DB / API?)
            |
            v
  Update review.yaml findings
  Write review-pr.report.md
  (full or delta-focused)
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
- `HEAD_TREE`: content snapshot of the head commit, history-independent: `git fetch origin "$HEAD_BRANCH" >/dev/null 2>&1 || true; git rev-parse "$HEAD_COMMIT^{tree}"`. Two commits with the same tree have byte-identical content regardless of their SHAs.
- `PR_AUTHOR`: the PR author's GitHub username (`author.login`)
- `HEAD_BRANCH`: the PR's head branch name (`headRefName`)
- `PR_STATE`: the PR state (`state` field in the `gh-pr-view.md` cache: `OPEN`, `CLOSED`, or `MERGED`)

```bash
gh pr view $1 --repo "$REPO" --json headRefName --jq '.headRefName'
```

```bash
ISSUE_NUMBER=$(gh pr view $1 --repo "$REPO" --json closingIssuesReferences --jq '.closingIssuesReferences[0].number // empty')
```

### Re-review scope (reuse the previous run when possible)

Read the review state file `$PR_REVIEW_DIR/review.yaml` (schema in `sdlc/references/shared.md`, PR Review Reports). If it does not exist, create it with empty `last_reviewed_sha` and `last_reviewed_tree` and no findings. Let `$LAST_SHA` and `$LAST_TREE` be the `last_reviewed_sha` and `last_reviewed_tree` values read from the state file.

Determine the scope per `sdlc/references/shared.md` (PR Review Reports, Re-review scope), before doing any analysis: same head stops and returns the state, a pure rebase bumps `last_reviewed_sha` and moves the checkpoint tag, an ancestor delta or contained tree-diff runs an incremental review, and a rewritten history with a full-tree change (or an unknown `last_reviewed_tree`) runs the full review. A `CLOSED` or `MERGED` PR deletes the checkpoint tag and stops (shared.md, Review checkpoint tags). This skill's incremental rules:

- Evaluate only the delta `git diff "$LAST_SHA" "$HEAD_COMMIT"` (or the contained tree-diff), re-confirming every `open` finding in the state file against it, flipping `status` to `addressed` or `stale` where the delta resolves or obsoletes them.
- Do not re-evaluate code the delta does not touch, and keep the previous verdict unless the delta invalidates it.
- Add findings for problems in the new code only.

Create a git worktree on the PR branch so full files (not just diff hunks) can be read in context. If `$WORKTREE_DIR` is already set (e.g. by an orchestrator like `review-requested-prs`), use that directory directly and skip creation and cleanup. The orchestrator manages the worktree lifecycle.

```bash
_WORKTREE_OWNER=false
if [ -z "${WORKTREE_DIR:-}" ]; then
  git fetch origin $HEAD_BRANCH
  WORKTREE_DIR=/tmp/sdlc/$REPO/${ISSUE_NUMBER:-pr-$PR_NUMBER}
  mkdir -p /tmp/sdlc/$REPO
  git worktree add $WORKTREE_DIR origin/$HEAD_BRANCH
  _WORKTREE_OWNER=true
fi
```

All subsequent code reading happens inside the worktree directory.

If worktree creation fails, stop.

## Pre-Review Checklist

This skill is static code-craft review. It does not build or run the code (that is `/verify-pr`'s conformance role) and does not judge whether the target is the right product (that is `/validate-pr`'s role). Establish context, then review craft.

Before diving into the code:

* Prior reports
	* If `/verify-pr` has run, read its conformance report and treat the criteria status as settled; do not re-litigate conformance here
* PR Metadata
	* Read the PR title and description - is it clear and complete?
	* Is the change size appropriate for what is implemented?
* Understanding the Objective
	* Read the linked issue title and description (use `gh` to pull issue details) for context only
	* Understand what the PR is meant to do, so craft findings can be weighed against intent

## Code Review Checklist

CI handles linting, formatting, type checking, build, and test suite execution; this review does not report on those. Focus on what requires human judgment.

### Scope & Relevance

Change hygiene only. Whether a change serves an acceptance criterion is a conformance question for `/verify-pr`; whether it serves the real need is a validation question for `/validate-pr`. Here, focus on:

* Changes that obscure or distract from the actual work
	* Unrelated formatting changes, drive-by refactorings, or unrelated fixes mixed in
	* Should these be split into separate PRs for clarity?
	* Do irrelevant changes obscure the actual changes being reviewed?

### Approach & Simplicity

Judge the chosen approach, not just the code. These findings are invisible in the diff alone: before judging, read the surrounding codebase until you can name the existing pattern this change should have followed, and search the codebase and its dependencies for existing implementations of the same concept (grep for the concept's synonyms, check sibling modules).

For each significant mechanism the PR introduces (new dependency, new abstraction, new data format, new pattern), answer:

* Alternatives
	* Name at least one alternative approach and why the chosen one wins
	* If no alternative comes to mind, you have not understood the choice yet; investigate before approving
* Simplest sufficient
	* Could the same behavior ship with meaningfully less machinery (fewer files, no new abstraction, an existing helper)?
	* Speculative generality (a single implementation with no named future consumer) is a finding
* Proportionality
	* Is the machinery proportional to the problem (a plugin system for one implementation, a config framework for three settings)?
* Reinvention
	* Does the codebase or a dependency already provide this?
	* A reinvented utility is a finding even when well-written
* One way to do it
	* Does the PR add a second mechanism for something the codebase already standardizes (logging, config, error types, persistence access, HTTP wrappers)?
* Change-cost scenarios
	* Pick the 1-2 most plausible future changes (new field in the persisted model, swapped storage backend, new caller for this API) and count what would have to change
	* A small requirement change with wide fan-out is a finding; name the touch points
* Wrong layer
	* Is the logic at the layer where the codebase handles similar concerns (validation, formatting, access control)?

Rules for findings in this section:

* Every approach finding must name the concrete future change that becomes expensive, or the alternative it loses to
* If you cannot name a change scenario or an alternative, do not file the finding; unfalsifiable approach critique is taste, not review

### Code Quality & Design

* Naming Conventions
	* Verify classes, methods, functions, parameters naming
		* Are they significant of their purpose?
		* Are they clear enough?
		* Are they respecting the naming convention?
* Design Principles
	* Does the code respect [SOLID](https://en.wikipedia.org/wiki/SOLID)? (class-level judgment; approach-level judgment lives in Approach & Simplicity above)
	* Is the code following existing design patterns in the codebase? (name the pattern; if you cannot, do the directed search in Approach & Simplicity)
	* Are there code duplications that violate DRY principle?
* Magic Numbers & Dead Code
	* Are magic numbers/strings extracted as constants or configuration?
	* Is there dead code or commented-out code that should be removed?

### Testing & Coverage

Delegate the coverage analysis to [`/analyze-test-coverage`](../analyze-test-coverage/SKILL.md): invoke it with the PR diff and worktree context, and embed its three tables (introduced tests, change coverage, uncovered code) into the Coverage section below. Raise its findings (uncovered behavior changes and uncovered code) in the Findings section with severity proportional to risk.

Whether a test proves a specific acceptance criterion is `/verify-pr`'s conformance concern.

Beyond the delegated analysis, also check:

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

Include a checklist table with one row per Code Review Checklist section (Scope & Relevance, Approach & Simplicity, Code Quality & Design, Testing & Coverage, Architecture & Structure, Operational Concerns, Security & Data, Documentation & Maintenance). Use the traffic-light symbols only, consistent with the findings: 🟢 (pass) / 🟡 (needs attention) / 🔴 (issues), and keep notes terse so the table stays scannable.

Include an Approach section right after the Summary: a 2-3 sentence summary of the approach the PR takes (its main mechanism and where it sits in the codebase), followed by an alternatives-considered table (Decision / Alternatives considered / Why chosen / Change-cost). For small PRs a single line ("Approach: ...") is acceptable. Writing this section is the forcing function for the Approach & Simplicity findings: if you cannot fill in the alternatives column, go back and do the directed search before rendering the verdict.

Include a Coverage section built from the `/analyze-test-coverage` output: (1) **Introduced tests** table, (2) **Change coverage** table, (3) **Uncovered code** table. Append (4) what manual testing was done to confirm the change works (from the PR description, comments, or linked issue), and (5) what is missing. Uncovered behavior changes and uncovered code should be raised as findings (severity proportional to risk) in the Findings section, not only listed in the Coverage section.

First update the review state file `$PR_REVIEW_DIR/review.yaml`: set `updated_at` (ISO 8601), `last_reviewed_sha: $HEAD_COMMIT`, `last_reviewed_tree: $HEAD_TREE`, add the newly identified findings, and apply the `status` flips decided during the review (`open` / `addressed` / `stale` / `wontfix`). `title` is a finding's identity: when a delta looks like an existing finding, update that entry instead of adding a duplicate. `first_seen_sha` is informational provenance. Then move the review checkpoint tag to the reviewed head: `git tag -f "prs/$PR_NUMBER/review" "$HEAD_COMMIT" >/dev/null 2>&1 || true` (see `sdlc/references/shared.md`, Review checkpoint tags).

Then write the review to `$PR_REVIEW_DIR/review-pr.report.md`, overwriting the previous report (resolving per `sdlc/references/shared.md`). A full review contains the complete sections below; an incremental review stays short: scope (the delta, with diffstat), findings whose `status` changed, newly added findings, and the verdict.
Start the file with the marker `<!-- {"step":"review-pr","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"MARKER_VERDICT"} -->` so the orchestrator can detect which commit was reviewed. Substitute `HEAD_COMMIT` with the full head SHA, `HEAD_TREE` with the head commit's tree hash, and `MARKER_VERDICT` with the outcome verdict (`approved`, `changes-requested`, or `rejected`).

### Example Output

```
<!-- {"step":"review-pr","sha":"a1b2c3d","tree":"3f9c2e1","verdict":"fail"} -->
# Review of PR #42: Add payment processing endpoint

🟢 **Approved with minor suggestions**

Reviewed SHA: `a1b2c3d`

## Summary

The PR implements the Stripe payment endpoint per the acceptance criteria
in #37. The endpoint follows existing patterns in `src/payments/` and is
well-tested, but the client hand-rolls a retry loop the codebase already
solves. One blocking issue plus three non-blocking suggestions below.

## Approach

The PR adds a `requests`-based client whose `create_payment` hand-rolls a
retry loop (3 fixed attempts, no backoff) over a module-level
`requests.Session`, exposed through a new `POST /payments` route in
`src/payments/routes.py`.

| Decision | Alternatives considered | Why chosen | Change-cost |
|---|---|---|---|
| Hand-rolled retry loop in `client.py` | `@retry` helper (`src/api/middleware.py`) | Not stated in the PR | Any retry-policy change (backoff, jitter, retryable errors) edits the loop in place while every other call site changes one decorator argument |
| Endpoint in `src/payments/routes.py` | Reuse the generic resource router in `src/api/` | Follows the existing `src/payments/` module layout | Low |

## Checklist

| Section | Status | Notes |
|---|---|---|
| Scope & Relevance | 🟢 | No unrelated changes |
| Approach & Simplicity | 🟡 | Retry loop duplicates the existing `@retry` helper |
| Code Quality & Design | 🟢 | SOLID, naming, no duplication |
| Testing & Coverage | 🟡 | Webhook signature verification and API key loading untested |
| Architecture & Structure | 🟢 | Follows existing `src/payments/` patterns |
| Operational Concerns | 🟡 | No rate limiting on `POST /payments` |
| Security & Data | 🔴 | Hardcoded test API key in `client.py` |
| Documentation & Maintenance | 🟢 | No user-facing docs affected |

## Findings

### 🔴 MUST / Security & Data / Remove hardcoded test API key

`src/payments/client.py:8` contains `sk_test_4eC39HqLy...`. Move it to an
environment variable (`STRIPE_API_KEY`) and load via `os.environ`.
Verified it is not in `.env.example` either, so add it there as well.

### 🟡 SHOULD / Approach & Simplicity / Reuse the existing retry helper

`src/payments/client.py:12` hand-rolls a retry loop with 3 fixed attempts and
no backoff. The codebase already has a parameterized `@retry` helper in
`src/api/middleware.py:40`, used by every other outbound call. If the retry
policy ever changes (backoff, jitter, which errors are retryable), this loop
must be edited in place while every other call site changes one decorator
argument. Reuse the helper, or record why it cannot apply here.

### 🟡 SHOULD / Operational Concerns / Add rate limiting on the endpoint

`src/payments/routes.py:24` exposes `POST /payments` without a rate limiter.
A malicious client could flood charge attempts. Reuse the existing
`@rate_limit` decorator from `src/api/middleware.py`:

@rate_limit(limit=10, window=60)
@router.post("/payments")
async def create_payment(...): ...

### 🟡 SHOULD / Testing & Coverage / Add test for API key loading from environment

`src/payments/client.py` loads `STRIPE_API_KEY` from `os.environ` but no test
verifies this behavior. If the key loading logic changes in a future refactor
(e.g. switched to a config file), the regression would go unnoticed. Add a test
that patches the environment and asserts the client uses the expected key.

### 🟢 MAY / Code Quality & Design / Extract magic currency multiplier

`src/payments/amount.py:15` uses `amount * 100` to convert dollars to cents.
Consider `CENTS_PER_DOLLAR = 100` as a named constant for readability.

## Coverage

### Introduced tests

| Test file | Test(s) | What it tests |
|---|---|---|
| `tests/payments/test_routes.py` | `test_create_payment_success` | Successful payment creation returns 200 with charge ID |
| `tests/payments/test_routes.py` | `test_create_payment_invalid_amount` | Rejects negative amounts with 400 |
| `tests/payments/test_routes.py` | `test_create_payment_missing_token` | Rejects missing Stripe token with 400 |
| `tests/payments/test_amount.py` | `test_cents_conversion` | Dollar-to-cents conversion handles edge values |

### Change coverage

| Changed file | Behavior changed | Covered by test? | Gap |
|---|---|---|---|
| `src/payments/routes.py` | New `POST /payments` endpoint | Yes | — |
| `src/payments/routes.py` | Error response for invalid amount | Yes | — |
| `src/payments/client.py` | API key loaded from env var | No | No test verifies key is loaded from environment |
| `src/payments/client.py` | Webhook signature verification | No | No test covers webhook signature verification |

### Uncovered code

| File | Function / branch / path | Why it matters |
|---|---|---|
| `src/payments/client.py` | `verify_webhook_signature()` | No test calls this function at all |
| `src/payments/client.py` | `load_api_key()` env-not-set branch | Test only covers the happy path; missing-key error path unexercised |
| `src/payments/amount.py` | `to_cents()` negative input branch | `test_cents_conversion` covers zero and positive values only |

### Manual testing

- Author tested Stripe checkout flow end-to-end, verified webhook delivery and retry behavior

### Missing

- Webhook signature verification not tested
- API key loading from environment not tested

## Outcome

No blocking issues remain once the hardcoded key is removed. Rate limiting
should be addressed before exposing this publicly.
```

### Post the review as a PR comment

The review is saved to `$PR_REVIEW_DIR/review-pr.report.md`. Posting it as a PR comment is decided by `should-post-to-github`.

After writing `review-pr.report.md`, run `~/.agents/scripts/should-post-to-github --repo "$REPO" --author "$PR_AUTHOR"`. If it exits 1, skip posting, the review is already saved to `$PR_REVIEW_DIR/review-pr.report.md`.

If it exits 0, post the review file as a comment on the PR so the author and other reviewers can see the verdict. The file already contains the `<!-- {"step":"review-pr","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"MARKER_VERDICT"} -->` marker.

```bash
FOOTER="Posted with [review-pr](${SKILL_FILE_URL}) (\`${SKILL_SHORT_SHA}\`)"
gh pr comment $PR_NUMBER --repo $REPO --body "$(cat "$PR_REVIEW_DIR/review-pr.report.md")

${FOOTER}"
```

### Clean up

```bash
if [ "$_WORKTREE_OWNER" = true ]; then
  git worktree remove $WORKTREE_DIR
fi
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When | Marker verdict |
|---|---|---|
| `approved` | No blocking findings; the subject passes review | `pass` |
| `changes-requested` | Findings the author must address before it passes | `fail` |
| `rejected` | Fundamental flaw requiring rework or stopping | `fail` |

## Example Usage

**Scenario 1: New feature PR**
```
/review-pr 42
```
PR adds a payment processing endpoint. Review checks the approach (flags a hand-rolled retry loop that duplicates the existing `@retry` helper), code quality and architecture, notes test-quality gaps, confirms no hardcoded API keys, and notes a 🟡 SHOULD for adding a rate limit. (Conformance to the acceptance criteria is `/verify-pr`'s verdict.)

**Scenario 2: Bug fix PR**
```
/review-pr 88
```
PR fixes a null pointer. Review checks that the change is localized and the new test is well-written, and marks 🟢 ready to merge. (Root cause vs. symptom is `/validate-pr`'s call; a regression test proving the fix is `/verify-pr`'s.)

**Scenario 3: Re-review after changes**
```
/review-pr 55
```
`review.yaml` already carries findings from a previous run on an earlier commit (an ancestor of the new head). Review incrementally: evaluate only the delta against the previous feedback, flip the `status` of findings the new commits resolve (e.g., "Test coverage added, rate limit not yet addressed"), add findings for problems in the new code only, and render a short delta-focused `review-pr.report.md`.

## Useful Commands Reference

| Command | Description |
|---|---|
| `ghx pr view <pr-number> --repo <owner>/<repo> --comments --refresh` | Fetch PR details and review comments (fresh) |
| `ghx issue view <issue-number> --repo <owner>/<repo>` | Fetch linked issue details (cached) |
| `gh pr comment <pr-number> --repo <owner>/<repo> --body "..."` | Post review summary comment to the PR |
| `git worktree add /tmp/sdlc/<owner>/<repo>/<issue> origin/<branch>` | Create a worktree on the PR branch for code reading |
| `git worktree remove /tmp/sdlc/<owner>/<repo>/<issue>` | Clean up the worktree after review |
