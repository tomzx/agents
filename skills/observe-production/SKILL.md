---
name: observe-production
description: Check SLOs/SLIs, review error rates, latency, and throughput for deployed features.
argument-hint: "[service-name or feature-slug]"
---

# Observe Production

Checks the health of a deployed service or feature by reviewing SLOs, error rates, latency, throughput, and recent alerts. Produces a health report suitable for maintenance reviews, post-deploy verification, or incident triage.

## Prerequisites

- Access to observability tooling (logs, metrics, tracing) via CLI, API, or dashboards
- Optional: `$1` — service name or feature slug to scope the check (defaults to the whole project)
- Read `.sdlc/context/architecture.md` to understand which services and infrastructure to check

## What This Skill Checks

| Signal | Source | What It Reveals |
|---|---|---|
| Error rate | Metrics / logs | Increase in 4xx/5xx responses, unhandled exceptions |
| Latency (p50, p95, p99) | Metrics | Performance degradation, slow queries, bottlenecks |
| Throughput | Metrics | Traffic anomalies, load spikes, capacity issues |
| SLO status | SLO dashboard / config | Whether reliability targets are being met |
| Recent alerts | Alerting system | Active or recent incidents, degraded conditions |
| Deployment recency | CI/CD history | Whether a recent deploy correlates with issues |

## Steps

1. Read `.sdlc/context/architecture.md` to identify services, endpoints, and infrastructure to check.

2. Determine available observability tooling. Look for:
   - Metrics: Prometheus, Datadog, CloudWatch, Grafana
   - Logging: ELK, Loki, CloudWatch Logs
   - Tracing: Jaeger, Zipkin, Datadog APM
   - Alerting: PagerDuty, OpsGenie, Grafana alerts
   If no tooling is configured, report that observability is not set up and recommend `/audit-observability`.

3. Check error rates for the target service(s):
   - HTTP 5xx rate over the last 1 hour, 24 hours, and 7 days
   - Unhandled exception count
   - Compare against baseline or SLO target

4. Check latency percentiles:
   - p50, p95, p99 for the primary endpoints
   - Compare against SLO targets or historical baseline
   - Identify any slow endpoints

5. Check throughput:
   - Requests per second over the last hour
   - Compare against capacity limits or historical norms
   - Identify any traffic anomalies

6. Check recent alerts:
   - Active alerts (firing, not resolved)
   - Alerts fired in the last 24 hours
   - Correlate with any recent deployments

7. Check SLO status:
   - Error budget remaining
   - SLO compliance over the current measurement window
   - Any SLO breaches in the last 7 days

8. Produce the health report.

## Output Format

```markdown
# Production Health Report — <service-name>

**Date:** <YYYY-MM-DD HH:MM>
**Scope:** <service or feature being checked>

## Summary

- **Overall status:** Healthy / Degraded / Unhealthy
- **SLO compliance:** <X>% (<measurement window>)
- **Error budget remaining:** <X>%

## Error Rates

| Window | 5xx Rate | Unhandled Exceptions | Status |
|---|---|---|---|
| Last 1h | <value> | <count> | Normal / Elevated |
| Last 24h | <value> | <count> | Normal / Elevated |
| Last 7d | <value> | <count> | Normal / Elevated |

## Latency

| Endpoint | p50 | p95 | p99 | SLO Target | Status |
|---|---|---|---|---|---|
| <path> | <ms> | <ms> | <ms> | <ms> | Within / Breached |

## Throughput

| Metric | Value | Baseline | Status |
|---|---|---|---|
| Requests/s | <value> | <baseline> | Normal / Anomalous |

## Recent Alerts

| Alert | Severity | Triggered | Status |
|---|---|---|---|
| <alert name> | Critical / Warning | <time> | Firing / Resolved |

## Observability Gaps

- <Missing signal that should be monitored>
- <Recommendation for /audit-observability if gaps are found>

## Recommendations

1. <Action to take based on findings>
```

## Example Usage

**Scenario 1: Post-deploy verification**
```
/observe-production notification-service
```
Just deployed a new notification feature. Check that error rates and latency are within normal ranges for the notification service.

**Scenario 2: Routine health check**
```
/observe-production
```
Periodic check across all services. Identify any degraded conditions before they become incidents.

**Scenario 3: Incident investigation**
```
/observe-production api-gateway
```
Alerts are firing on the API gateway. Pull error rates, latency, and throughput to assess the scope of the issue.

## Next Step

If observability gaps are identified, run `/audit-observability` to get a detailed report on missing logging, metrics, tracing, and alerting.
If issues are found, create an issue via `/create-issue` to track the remediation.

## Useful Commands Reference

| Command | Description |
|---|---|
| `curl -s <metrics-endpoint>/api/v1/query?query=rate(http_requests_total[5m])` | Query Prometheus for request rate |
| `kubectl top pods -n <namespace>` | Check pod resource usage |
| `aws cloudwatch get-metric-statistics --namespace ...` | Query CloudWatch metrics |
