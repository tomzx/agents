---
name: handle-pr-ci
description: Diagnose failing CI checks on a GitHub pull request, fix the root cause, push, and confirm CI passes.
argument-hint: "<pr-number>"
---

# Handle PR CI

Fetches failing CI check logs for a pull request, diagnoses the root cause of each failure, implements fixes, pushes, and confirms all checks pass.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, target the pull request from `$PR_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with read/write access to the target repository
- PR number (`$1`) identifying an open pull request with at least one failing CI check

## Workflow

```
Fetch CI check status ($1)
        |
        v
  Any failing checks?
     /         \
   Yes           No
    |             |
    v             v
Fetch logs     Report all
per failure    checks green, stop
    |
    v
Diagnose root cause
    |
    v
Implement fix
    |
    v
Present fix to user for approval
     /         \
 Approved     Rejected
    |             |
    v             v
Commit + push   Stop
    |
    v
Monitor CI re-run
    |
    v
All checks green?
   /      \
 Yes       No
  |         |
  v         v
Done     Loop back to
         fetch logs
```

## Steps

1. Fetch the current CI check status:
   ```
   gh pr checks $1 --watch=false
   ```

2. If all checks are passing, report success and stop.

3. For each failing check, fetch its log output:
   ```
   gh run view <run-id> --log-failed
   ```

4. Diagnose the root cause of each failure. Distinguish between:
   - **Flaky/transient failures** (network timeouts, rate limits): note as transient, suggest re-running rather than a code fix.
   - **Code failures** (test failures, lint errors, type errors, build errors): identify the specific file and line causing the failure.

5. For code failures, implement the fix in the codebase.

6. Present the diagnosis and proposed fix to the user for approval before committing.

7. On approval, commit and push:
   ```
   git add <changed files>
   git commit -m "<fix description>"
   git push
   ```

8. Monitor the CI re-run until checks complete:
   ```
   gh pr checks $1 --watch
   ```

9. If checks pass, report success. If new failures appear, loop back to step 3.

## Example Usage

**Scenario 1: Failing test**
```
/handle-pr-ci 42
```
Check `test` is failing. Log shows `AssertionError` in `test_user_auth.py:88`. Fix: update assertion to match new return shape. Commit, push, CI goes green.

**Scenario 2: Lint error**
```
/handle-pr-ci 77
```
Check `lint` is failing. Log shows `ruff` error: unused import in `utils.py:3`. Fix: remove the import. Commit, push, CI goes green.

**Scenario 3: Transient network failure**
```
/handle-pr-ci 55
```
Check `integration-tests` is failing with a connection timeout to an external service. Diagnosis: transient. Report to user and suggest re-running the check rather than a code fix:
```
gh run rerun <run-id> --failed
```

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh pr checks <pr-number> --watch=false` | Fetch current CI check status |
| `gh run view <run-id> --log-failed` | Fetch logs for failed jobs in a run |
| `gh run rerun <run-id> --failed` | Re-run only failed jobs (for transient failures) |
| `gh pr checks <pr-number> --watch` | Monitor CI checks until completion |
