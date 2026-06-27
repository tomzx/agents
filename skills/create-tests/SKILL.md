---
name: create-tests
description: Create a test plan and test cases covering acceptance criteria, edge cases, and failure scenarios.
argument-hint: "[requirements or specification]"
---

# Create Tests

Produces a test plan with structured test cases derived from requirements, acceptance criteria, and a specification.
Covers happy paths, edge cases, and failure scenarios across relevant test levels.

## Prerequisites

- `.sdlc/features/FEAT-NNNN-<slug>/requirements.md` and `.sdlc/features/FEAT-NNNN-<slug>/specification.md` (both must have `status: approved`), or documents provided in context or as a file path (`$1`)
- `.sdlc/features/FEAT-NNNN-<slug>/telemetry.md` (optional, if a telemetry plan was produced): include test cases that verify analytics events are emitted correctly
- `.sdlc/features/FEAT-NNNN-<slug>/observability.md` (optional, if an observability plan was produced): include test cases that verify metrics, logs, and traces are emitted correctly
- Information about the testing stack (if available)

## Steps

1. Read the requirements, specification, telemetry plan, and observability plan (if present).
2. List all acceptance criteria that need to be verified.
3. For each acceptance criterion, write at least one test case.
4. For each analytics event in the telemetry plan, write a test case verifying the event is emitted with correct properties.
5. For each metric, log entry, and trace span in the observability plan, write a test case verifying it is emitted correctly.
6. Add edge case and failure scenario tests beyond the acceptance criteria.
7. Organize test cases by test level (unit, integration, end-to-end).
8. Identify test infrastructure and fixtures needed.
9. Write the output to `.sdlc/features/FEAT-NNNN-<slug>/tests.md`.

## Test Case Format

```markdown
### TC-<N>: <Test name>

**Level:** Unit / Integration / E2E
**Covers:** FR-01 / NFR-02 / Edge case
**Setup:** <Preconditions and test data>
**Steps:**
1. <Action>
2. <Action>
**Expected:** <Observable result>
```

## Output Format

```markdown
---
issue: "#<N>"
title: "<Feature Name>"
status: draft
---

# Test Plan: <Feature Name>

## Scope

<What is being tested and what is out of scope.>

## Unit Tests

<TC-01 through TC-N>

## Integration Tests

<TC-N+1 through TC-M>

## End-to-End Tests

<TC-M+1 through TC-P>

## Edge Cases and Failure Scenarios

<TC-P+1 through TC-Q>

## Test Infrastructure

- <Fixtures, mocks, or test data required>
- <Test environment requirements>

## Coverage Matrix

| Requirement | Test Cases |
|---|---|
| FR-01 | TC-01, TC-05 |
| NFR-01 | TC-08 |
```

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md`, mirroring the `status: approved` written to the artifact. If the test plan could not be produced, omit the file.

## Example Usage

**Scenario 1: Password reset feature**
Requirements define a 4-step reset flow.
Create unit tests for token generation and expiry, integration tests for the email dispatch call, and an E2E test for the full user journey.
Edge cases: expired token, already-used token, invalid email.

**Scenario 2: API endpoint**
Spec defines a `POST /orders` endpoint.
Write unit tests for input validation, integration tests for DB writes, E2E test for the full order placement flow, and failure tests for duplicate requests and DB errors.

## Next Step

Run `/review-tests` to audit coverage, correctness, and missing scenarios before moving on.
Once approved, continue with `/create-implementation`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
