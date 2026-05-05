---
name: run-e2e-tests
description: Deploy and run end-to-end and smoke tests against the target environment to validate that the implementation works in production-like conditions.
argument-hint: "[environment]"
---

# Run E2E Tests

Validates the implementation by running end-to-end and smoke tests against the actual target environment.
Catches environment-specific failures (configuration, dependencies, network, infrastructure) that unit and integration tests cannot surface.

## Prerequisites

- Implementation complete and passing unit/integration tests locally
- A target environment available (staging, preview, or production-equivalent)
- E2E test cases defined in the test plan (from `/create-tests`)

## Steps

1. Identify the target environment from `$1` or ask the user (staging, preview, CI, etc.).
2. Confirm the current build is deployed to the target environment; deploy it if not.
3. Run smoke tests first to verify the service is reachable and critical paths function.
4. Run the full E2E test suite against the target environment.
5. Capture results: passed, failed, skipped, and any environment errors.
6. Classify each failure: code defect, environment configuration issue, test data issue, or flaky test.
7. Report results using the output format.
8. If any non-flaky failures exist, block advancement until they are resolved and re-run passes.

## Smoke Test Checklist

Run before the full suite to catch obvious environment failures fast:

- [ ] Service is reachable (health check or root endpoint responds)
- [ ] Authentication works end-to-end
- [ ] At least one read operation succeeds
- [ ] At least one write operation succeeds
- [ ] Key integrations respond (database, external APIs, message queues)

## Failure Classification

| Class | Meaning | Action |
|---|---|---|
| Code defect | Bug in the implementation | Fix in code, re-run |
| Config / env issue | Missing env var, wrong endpoint, infrastructure misconfiguration | Fix environment, re-run |
| Test data issue | Missing seed data, stale fixtures, wrong state | Reset test data, re-run |
| Flaky test | Non-deterministic failure unrelated to this change | Note it, re-run once to confirm |

## Output Format

```markdown
## E2E Test Run: <Feature / Branch>

**Environment:** <staging / preview / etc.>
**Date:** <ISO date>
**Build:** <commit SHA or version>

## Smoke Tests

| Check | Result |
|---|---|
| Service reachable | PASS / FAIL |
| Authentication | PASS / FAIL |
| Read operation | PASS / FAIL |
| Write operation | PASS / FAIL |
| Key integrations | PASS / FAIL |

## Full Suite Results

| Suite | Passed | Failed | Skipped |
|---|---|---|---|
| <suite name> | N | N | N |

## Failures

### <Test name>
**Class:** Code defect / Config issue / Test data issue / Flaky
**Error:** <error message or stack trace excerpt>
**Action:** <what to do next>

## Verdict

PASS — ready to proceed to `/create-documentation`.
FAIL — blocked, resolve failures above and re-run before advancing.
```

## Example Usage

**Scenario 1: All tests pass**
Deploy feature branch to staging, smoke tests pass, full E2E suite runs green.
Verdict: PASS — proceed to `/create-documentation`.

**Scenario 2: Authentication failure on staging**
Smoke test fails: authentication returns 401.
Class: Config issue — staging OAuth credentials not rotated after env refresh.
Fix credentials, re-run, confirm pass before proceeding.

**Scenario 3: Flaky network test**
One test fails intermittently due to a slow third-party API in staging.
Class: Flaky — note in the report, re-run once to confirm it is not a code defect, then proceed.

**Scenario 4: Code defect surfaces only in production config**
An E2E test for the payment flow fails because a feature flag is off in staging but on locally.
Class: Code defect — the implementation incorrectly assumes the flag is always enabled.
Fix the code, re-run locally, deploy again, re-run E2E suite.

## Useful Commands Reference

| Action | Common commands |
|---|---|
| Run E2E suite | `pytest tests/e2e/`, `npx playwright test`, `cypress run` |
| Deploy to staging | `kubectl apply -f k8s/`, `fly deploy`, `vercel deploy --env staging` |
| Check health | `curl https://<host>/health` |
| Reset test data | `python manage.py flush && python manage.py loaddata fixtures/test.json` |
| Stream test output | `pytest tests/e2e/ -v`, `npx playwright test --reporter=line` |
