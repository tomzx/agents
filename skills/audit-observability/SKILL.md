---
name: audit-observability
description: Identify missing logging, metrics, tracing, and alerting for production services.
argument-hint: "[path or service-name]"
---

# Audit Observability

Scans the codebase and running services for missing or insufficient observability: logging, metrics, tracing, and alerting. Produces a gaps report ranked by risk so teams can prioritize adding instrumentation before issues arise in production.

## Prerequisites

- Working directory is the root of the repository
- Optional: `$1` — path or service name to scope the audit (defaults to `.`)
- Access to the codebase to search for instrumentation patterns
- Read `.sdlc/context/architecture.md` to understand the services and infrastructure

## Observability Pillars

| Pillar | Purpose | Examples |
|---|---|---|
| **Logging** | Record discrete events for debugging | Structured logs, error logs, audit logs |
| **Metrics** | Quantitative measurements over time | Request count, latency histogram, error rate |
| **Tracing** | Follow a request across service boundaries | Distributed trace IDs, span propagation |
| **Alerting** | Notify on-call when conditions degrade | PagerDuty, OpsGenie, Grafana alerts |

## Steps

1. Read `.sdlc/context/architecture.md` to identify services, endpoints, databases, and external dependencies.

2. Detect which observability libraries and frameworks are already in use:
   ```
   grep -rn --include="*.py" --include="*.ts" --include="*.js" --include="*.go" \
     -iE "(structlog|logging|logger|prometheus|datadog|opentelemetry|otel|jaeger|zipkin|sentry)" \
     ${1:-.} | head -40
   ```

3. Audit **logging** coverage:
   - Are errors logged with context (request ID, user ID, stack trace)?
   - Are external service calls logged (request/response, latency, status)?
   - Are business-critical operations logged (auth events, data mutations, payments)?
   - Is structured logging used consistently?
   - Are log levels appropriate (not everything at INFO/DEBUG)?
   ```
   grep -rn --include="*.py" --include="*.ts" --include="*.js" --include="*.go" \
     -iE "(except|catch|error|raise|throw)" \
     ${1:-.} | grep -v "log\|logger\|sentry\|capture" | head -30
   ```
   Flag error handlers that swallow exceptions without logging.

4. Audit **metrics** coverage:
   - Are HTTP endpoints instrumented (request count, latency, error rate)?
   - Are database queries instrumented (query latency, connection pool usage)?
   - Are external service calls instrumented (call count, latency, error rate)?
   - Are business metrics tracked (orders placed, emails sent, jobs completed)?
   - Are resource metrics available (CPU, memory, disk, connections)?
   ```
   grep -rn --include="*.py" --include="*.ts" --include="*.js" --include="*.go" \
     -iE "(counter|histogram|gauge|summary|metric|observe|inc\(|time\()" \
     ${1:-.} | head -30
   ```
   Identify endpoints and services with no metrics instrumentation.

5. Audit **tracing** coverage:
   - Is OpenTelemetry or equivalent configured?
   - Are trace IDs propagated across service boundaries (HTTP headers, message queues)?
   - Are database calls and external HTTP calls included in traces?
   - Are spans created for significant operations?
   ```
   grep -rn --include="*.py" --include="*.ts" --include="*.js" --include="*.go" \
     -iE "(trace_id|span_id|opentelemetry|otel|tracer|start_span|propagat)" \
     ${1:-.} | head -30
   ```

6. Audit **alerting** coverage:
   - Are alerts defined for SLO breaches (error rate, latency)?
   - Are alerts defined for infrastructure issues (disk full, memory pressure, connection exhaustion)?
   - Are alerts defined for business anomalies (queue depth, failed jobs, payment failures)?
   - Are alert thresholds appropriate (not too noisy, not too quiet)?
   - Look for alert configuration files:
   ```
   find ${1:-.} -type f \( -name "alerts*" -o -name "alerting*" -o -name "slo*" -o -name "rules*" \) \
     | grep -v node_modules | grep -v .git | head -20
   ```

7. Rank gaps by risk:
   - **High risk:** No error logging on critical paths, no alerts for SLO breaches, no metrics on user-facing endpoints
   - **Medium risk:** Missing tracing on cross-service calls, no metrics on background jobs, inconsistent log levels
   - **Low risk:** Missing business metrics, non-critical paths without tracing, verbose logging in non-critical paths

8. Produce the gaps report.

## Output Format

```markdown
# Observability Audit — <service-name or project>

**Date:** <YYYY-MM-DD>
**Scope:** <path or services audited>

## Summary

- **Logging:** Adequate / Partial / Missing
- **Metrics:** Adequate / Partial / Missing
- **Tracing:** Adequate / Partial / Missing
- **Alerting:** Adequate / Partial / Missing
- **Tools detected:** <prometheus, structlog, opentelemetry, sentry, etc.>
- **High-risk gaps:** N
- **Medium-risk gaps:** N
- **Low-risk gaps:** N

## Logging Gaps

| Risk | Location | Issue | Recommendation |
|---|---|---|---|
| High | `<file>:<line>` | Error swallowed without logging | Add structured error log with context |
| Medium | `<file>:<line>` | External call not logged | Add request/response logging |

## Metrics Gaps

| Risk | Endpoint / Operation | Issue | Recommendation |
|---|---|---|---|
| High | `POST /api/checkout` | No latency or error metrics | Add histogram for latency, counter for errors |
| Medium | Background job processor | No job count or duration metrics | Add counter and histogram |

## Tracing Gaps

| Risk | Boundary | Issue | Recommendation |
|---|---|---|---|
| High | Service A → Service B | Trace ID not propagated | Add trace context headers |
| Medium | Database queries | No span for DB calls | Add DB query spans |

## Alerting Gaps

| Risk | Condition | Issue | Recommendation |
|---|---|---|---|
| High | Error rate > 1% | No alert configured | Add SLO-based alert |
| Medium | Queue depth > 1000 | No alert configured | Add threshold alert |

## Recommended Implementation Order

1. <Highest-priority gap to fix first>
2. <Next priority>
3. ...
```

## Example Usage

**Scenario 1: New project review**
```
/audit-observability
```
Project has logging via structlog but no metrics, tracing, or alerting. Recommends adding Prometheus for metrics and OpenTelemetry for tracing as the top priorities.

**Scenario 2: Pre-production readiness**
```
/audit-observability src/api
```
Scanning the API layer before going to production. Finds 3 endpoints without latency metrics and 2 error handlers that swallow exceptions. Recommends adding metrics and error logging before launch.

**Scenario 3: Post-incident follow-up**
```
/audit-observability
```
After an incident caused by undetected error rate spike. Finds no alerts configured for 5xx rate. Recommends adding SLO-based alerting as the top priority.

## Next Step

If gaps are found, create issues for the highest-priority items via `/create-issue`.
To check current production health, run `/observe-production`.

## Useful Commands Reference

| Command | Description |
|---|---|
| `grep -rn "structlog\|logging\|logger" --include="*.py" . | head -30` | Find logging usage in Python |
| `grep -rn "prometheus\|metrics\|Counter\|Histogram" --include="*.py" . | head -30` | Find metrics instrumentation |
| `grep -rn "opentelemetry\|otel\|trace" --include="*.py" . | head -30` | Find tracing setup |
| `find . -name "alerts*" -o -name "slo*" -o -name "rules*"` | Find alert configuration files |
