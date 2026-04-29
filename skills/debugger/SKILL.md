---
name: debugger
description: Investigate a failure or bug report, identify the root cause, and apply a minimal targeted fix.
argument-hint: "<bug-report-or-failing-test>"
---

# Debugger

Investigates a bug or failure, reproduces it reliably, identifies the root cause (not just the symptom), applies a minimal fix, and adds a regression test.

## Prerequisites

- Bug report, failing test name, or error output provided
- Access to the codebase and test runner

## Steps

1. Read the bug report or failing test output carefully.
2. Reproduce the failure:
   - Run the failing test or follow the reproduction steps.
   - Confirm you see the same failure before touching any code.
3. Bisect to the root cause:
   - Narrow the call stack or code path responsible.
   - Distinguish symptom (where it crashes) from cause (why it goes wrong).
4. Apply the minimal fix at the root cause.
5. Re-run the failing test — it must now pass.
6. Run the full test suite — no regressions.
7. Add a regression test that would have caught this bug.

## Rules

- Fix the cause, not the symptom.
- Minimal change: do not refactor surrounding code while fixing a bug.
- Never suppress errors or add broad try/except to hide the failure.
- The regression test must fail on the unfixed code and pass on the fixed code.

## Output Format

```markdown
## Root Cause

One paragraph describing exactly why the failure occurs, referencing the specific file and line.

## Fix

Description of the change made and why it addresses the root cause.

## Regression Test

Name and location of the test added, and what scenario it covers.
```

## Example Usage

**Scenario 1: Null pointer**
Bug: "NullPointerException in OrderProcessor line 42."
Reproduce: run the failing test. Find: `cart` can be `null` for guest sessions; code assumed it was always initialized. Fix: guard with null check at the entry point. Regression test: `test_process_order_with_null_cart`.

**Scenario 2: Off-by-one**
Bug: "Last record missing from CSV export."
Reproduce: export 10 records, get 9 in file. Find: loop condition uses `< count` instead of `<= count`. Fix: correct the loop boundary. Regression test: `test_export_includes_last_record`.

## Useful Commands Reference

| Command | Description |
|---|---|
| `git log --oneline` | Find recent commits to bisect |
| `git bisect start` | Begin binary search for regression commit |
