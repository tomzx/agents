---
name: test-writer
description: Write tests that verify an implementation against its acceptance criteria.
---

# Test Writer

Authors unit, integration, and/or end-to-end tests that fully exercise an implementation against its acceptance criteria. Tests must cover the happy path, edge cases, and failure modes.

## Prerequisites

- Acceptance criteria available in context or as a file path
- Implemented code available in the codebase
- Test framework already set up in the project

## Steps

1. Read the acceptance criteria for the feature or task.
2. Read the implementation to understand the interface under test.
3. For each acceptance criterion, write at least one test.
4. Add edge-case tests for boundary values, empty inputs, and concurrent access where applicable.
5. Add failure-mode tests for invalid input, external service errors, and permission violations.
6. Run the tests and confirm they all pass.

## Test Writing Rules

- Test behavior, not implementation details: do not assert on private state or internal call counts unless required by the spec.
- Name tests descriptively: `test_export_returns_csv_for_authenticated_user`, not `test_export`.
- One assertion per concept (a test may have multiple `assert` lines if they verify the same behavior).
- Tests must be deterministic: no random data, no time-dependent logic without mocking.
- Do not test framework behavior or third-party library internals.

## Coverage Targets

- Every acceptance criterion: at least one test.
- Every documented edge case: at least one test.
- Every failure mode: at least one test.

## Output

Tests committed alongside or after the implementation, runnable with the project's standard test command.

Before finishing, confirm:
- [ ] All acceptance criteria have corresponding tests
- [ ] Edge cases and failure modes are covered
- [ ] All tests pass
- [ ] Test names describe the scenario being verified

## Example Usage

**Scenario 1: Export endpoint**
Criteria: authenticated user gets CSV; unauthenticated user gets 401; empty dataset returns empty CSV with header row.
Tests: `test_export_csv_authenticated`, `test_export_returns_401_unauthenticated`, `test_export_empty_dataset_returns_header_only`.

**Scenario 2: Real-time dashboard**
Criteria: data refreshes within 60 seconds; unauthorized users cannot connect.
Tests: `test_dashboard_data_staleness`, `test_dashboard_websocket_rejects_unauthenticated`.
