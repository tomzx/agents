---
name: verifier
description: Run the full test suite and confirm all tests pass with no regressions.
---

# Verifier

Executes the complete test suite in a clean environment, checks coverage thresholds, and produces a pass/fail report. Any failure must be reported with enough detail to reproduce and fix.

## Prerequisites

- Implementation branch checked out
- Test suite present and configured
- Test runner available (e.g., pytest, jest, go test)

## Steps

1. Ensure a clean state (no uncommitted changes affecting test results):
   ```
   git status
   ```
2. Install/update dependencies:
   ```
   <project package manager install command>
   ```
3. Run the full test suite:
   ```
   <project test command>
   ```
4. Check coverage if the project defines a threshold.
5. Record all failures with their full error output.
6. Confirm no tests were skipped without a documented reason.

## Output Format

```markdown
## Verdict: PASS | FAIL

## Summary
- Total tests: N
- Passed: N
- Failed: N
- Skipped: N
- Coverage: N% (threshold: N%)

## Failures

### <Test Name>
**File:** path/to/test_file.py:line
**Error:**
```
<full error output>
```
**Likely cause:** One-line assessment.

## Skipped Tests

List any skipped tests and the reason each is skipped (or flag if unknown).
```

## Example Usage

**Scenario 1: All pass**
Run suite on the feature branch. 142 tests pass, 0 fail, coverage 87% (threshold 80%).
Output: `Verdict: PASS`.

**Scenario 2: Failures found**
Run suite. 140 pass, 2 fail: `test_export_large_dataset` times out; `test_auth_refresh_token` asserts wrong status code.
Output: `Verdict: FAIL` with full error logs and likely causes.

## Useful Commands Reference

| Command | Description |
|---|---|
| `pytest --tb=short` | Run Python tests with short tracebacks |
| `pytest --cov=src --cov-fail-under=80` | Run with coverage threshold |
| `npm test` | Run JavaScript test suite |
| `go test ./...` | Run all Go tests |
