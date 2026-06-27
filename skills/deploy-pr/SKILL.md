---
name: deploy-pr
description: Deploy merged changes to the target environment, run smoke tests, and verify the rollback plan.
argument-hint: "<pr-number or merge-sha>"
---

# Deploy PR

Deploys a merged pull request to the target environment, runs smoke tests to verify the deployment, and confirms a rollback plan exists. Bridges the gap between merging code and having it running in production.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `gh` CLI authenticated with write access to the target repository
- A merged PR number or merge SHA provided as `$1`
- Deployment tooling available (CI/CD pipeline, container registry, or manual deployment scripts)
- Read any files present under `.sdlc/context/` for project-level context, especially `architecture.md` for deployment topology

## Workflow

```
Fetch merged PR details ($1)
        |
        v
  Identify target environment
        |
        v
  Confirm rollback plan exists
     /         \
   Yes          No
    |            |
    v            v
  Execute     Document rollback
  deployment  procedure first,
    |         then proceed
    v
  Run smoke tests
     /         \
   Pass         Fail
    |            |
    v            v
  Verify      Execute rollback
  health      Report failure
    |            |
    v            v
  Report      Stop, investigate
  success
```

## Steps

1. Fetch the merged PR details:
   ```
   gh pr view $1 --json title,body,mergeCommit,headRefName,closingIssuesReferences
   ```

2. Identify the target environment(s) from the PR labels, branch name, or project configuration. Common targets:
   - `staging` for non-production validation
   - `production` for user-facing releases
   - Feature-specific environments (e.g., `preview`, `canary`)
   If uncertain, ask the user which environment to deploy to.

3. Check for a rollback plan. Look for:
   - A documented rollback procedure in the PR description or `.sdlc/` artifacts
   - Previous deployment version or tag to roll back to
   - Database migration rollback if applicable
   If no rollback plan exists, document one before proceeding.

4. Execute the deployment using the project's CI/CD pipeline or deployment scripts:
   ```
   gh workflow run deploy.yml --ref main -f environment=<target>
   ```
   Or, if deployment is manual, follow the project's deployment procedure from `architecture.md`.

5. Wait for deployment to complete. Monitor:
   ```
   gh run watch <run-id>
   ```

6. Run smoke tests against the deployed environment:
   - Health check endpoints return 200
   - Key user flows are accessible
   - No increase in error rates
   - Database connectivity is intact
   Use the project's existing smoke test suite if available, otherwise test the critical path manually.

7. If smoke tests pass, verify overall system health:
   - Check monitoring dashboards for anomalies
   - Confirm no new alerts fired
   - Verify key metrics (latency, error rate, throughput) are within normal ranges

8. If smoke tests fail, execute the rollback plan:
   - Redeploy the previous version
   - Run any database rollback migrations
   - Confirm the system is healthy on the previous version
   - Report the failure with details for investigation

9. Report deployment status:
   - Environment deployed to
   - Version or commit SHA deployed
   - Smoke test results
   - Rollback plan location
   - Any issues encountered

## Output Format

```markdown
## Deployment Report

- **PR:** #<N> — <title>
- **Commit:** <merge-sha>
- **Environment:** <staging / production / preview>
- **Deployed at:** <timestamp>
- **Smoke tests:** Pass / Fail (<details if failed>)
- **Rollback plan:** <location or summary>
- **Status:** Success / Rolled back / Failed
```

## Example Usage

**Scenario 1: Standard production deploy**
```
/deploy-pr 42
```
PR #42 was merged to main. Deploy to production via CI/CD pipeline, run smoke tests, confirm healthy.

**Scenario 2: Staging deploy first**
```
/deploy-pr 88
```
Deploy PR #88 to staging first, run smoke tests, then promote to production if all checks pass.

**Scenario 3: Rollback needed**
```
/deploy-pr 55
```
Smoke tests reveal a 500 error on the checkout flow. Roll back to the previous deployment, confirm system health, report the failure.

## Next Step

Once deployment is successful, continue with `/create-learnings` to capture a retrospective on the feature.
If the feature is now running in production, consider running `/observe-production` to establish a baseline for monitoring.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh pr view <N> --json title,body,mergeCommit` | Fetch merged PR details |
| `gh workflow run deploy.yml --ref main -f environment=<env>` | Trigger deployment workflow |
| `gh run watch <run-id>` | Watch CI/CD run until completion |
| `gh run list --workflow=deploy.yml --limit=5` | List recent deployment runs |
