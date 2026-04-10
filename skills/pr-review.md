---
description: Conduct a comprehensive code review of a GitHub pull request
allowed-tools: Bash(gh:*, git:*, scripts/get-env:*), Read, Write, Glob, Grep
argument-hint: <pr-number>
---

BASE_DIR=!`scripts/get-env ISSUES_DIR`

## Setup

Pull the information about the PR $1 using `gh pr view issue-number --repo owner/repository --comments` and write the raw output to `{BASE_DIR}/{REPOSITORY}/{ISSUE_NUMBER}/gh-pr-view.md`.

## Pre-Review Checklist

Before diving into the code, verify:

* Build & Tests
	* Verify that the build/tests pass
* PR Metadata
	* Read the PR title and description - is it clear and complete?
	* Verify that the PR links to an issue for traceability purposes
		* If missing, request the author to link an issue
	* Is the change size appropriate for what is implemented?
* Understanding the Objective
	* Read the linked issue title and description (use `gh` to pull issue details)
	* Understand the feature and associated requirements that are supposed to be implemented
	* For bug fixes: understand the root cause being addressed

## Code Review Checklist

### Scope & Relevance

* Identify changes irrelevant to the PR
	* Are there unrelated formatting changes, refactorings, or fixes?
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

* Test Existence
	* Check code contains tests
	* Is all the new code covered by those tests?
* Test Quality
	* Do tests cover edge cases and error scenarios?
	* Are test names descriptive of what they're testing?
	* Are tests testing behavior rather than implementation details?

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
* Reversibility
	* Are any of the design decisions taken single way doors or reversible?

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

* Verify code implements the desired feature and that the requirements are completed
* Are feature flags considered for gradual rollout?
* Is the UX/UI accessible and responsive?
* Are user-facing error messages clear and helpful?

### Bug Fixes

* Verify that the fix is applied at the right location and will not "fix the symptoms, not the cause"
* Does the fix address the root cause?
* Is there a test that would have caught this bug?

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

When reviewing, write the response to `{ISSUES_DIR}/{REPOSITORY}/{PR_NUMBER}/pr-review.md`.
If a file already exists, update the file with the new information and tell me what changes have been made since the last review.
