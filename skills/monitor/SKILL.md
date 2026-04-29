---
name: monitor
description: Watch post-deployment signals and surface anomalies, regressions, or incidents.
---

# Monitor

Reviews observability data (logs, metrics, traces, alerts) after a deployment and flags anomalies, regressions, or incidents for escalation.

## Prerequisites

- Access to observability tooling (logs, metrics dashboard, alerting system)
- Baseline metrics from before the deployment (or the previous release period)
- Knowledge of what was deployed (release notes or task list)

## Steps

1. Establish the observation window: start time = deployment time, end time = now.
2. Check error rates:
   - Compare current error rate to the pre-deployment baseline.
   - Flag any increase > 10% as a regression candidate.
3. Check latency:
   - Compare p50, p95, p99 latency to baseline.
   - Flag degradation beyond the NFR thresholds.
4. Scan logs for new error patterns:
   - Look for error classes not present in the baseline window.
5. Review active alerts:
   - List any alerts that fired since deployment.
6. Correlate anomalies with the deployed changes.
7. Produce the monitoring report.

## Output Format

```markdown
## Monitoring Report

**Deployment:** <version or commit>
**Window:** <start> to <end>

### Error Rate
- Baseline: N errors/min
- Current: N errors/min
- Status: NORMAL | REGRESSION

### Latency
- p99 baseline: Xms | p99 current: Xms
- Status: NORMAL | DEGRADED

### New Error Patterns
List of error messages/types not seen before deployment.

### Alerts Fired
List of alert names, times, and whether they resolved.

### Verdict: HEALTHY | DEGRADED | INCIDENT

### Recommended Action
- HEALTHY: no action required.
- DEGRADED: investigate and monitor; consider rollback if trend continues.
- INCIDENT: escalate to Triage Agent immediately.
```

## Example Usage

**Scenario 1: Healthy deployment**
Error rate unchanged, latency within NFR, no new errors, no alerts.
Output: `Verdict: HEALTHY`.

**Scenario 2: Regression detected**
Error rate doubled (0.1% → 0.2%), new `TimeoutError` in logs correlating with the new export endpoint.
Output: `Verdict: DEGRADED`, recommend investigating export job queue.
