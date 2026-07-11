---
name: create-observability
description: Define logging, metrics, tracing, and alerting for a feature so production health can be monitored from day one.
argument-hint: "[specification-doc]"
---

# Create Observability

Defines how a feature's production health will be monitored by identifying log statements, service metrics, distributed traces, and alerts before implementation begins.

Without this step, features ship blind: outages go undetected, root causes take hours to find, and on-call engineers lack runbooks.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/specification.md` (must have passed review with findings verdict `approved`), or a specification document provided in context or as a file path (`$1`)
- `.sdlc/features/N-<slug>/telemetry.md` (optional, if a telemetry plan was produced): align observability with business metrics already defined
- `.sdlc/features/N-<slug>/requirements.md` (optional, for cross-referencing NFRs like latency and availability targets)

## Steps

1. Read the specification, telemetry plan (if present), and requirements.
2. Identify the critical paths and failure modes from the specification.
3. For each critical path, determine what log entries are needed for debugging.
4. Define service-level metrics (counters, histograms, gauges) that reflect system health.
5. Identify where distributed traces should be emitted for cross-service flows.
6. Define health checks and readiness probes for new services or endpoints.
7. Specify alerts with clear conditions, severity, and runbook links.
8. Determine observability infrastructure requirements (existing vs. new instrumentation).
9. Write the output to `.sdlc/features/N-<slug>/observability.md`.

## Output Format

Use the template at `skills/sdlc/templates/features/observability.md` (copied to `.sdlc/templates/features/observability.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write the result to the artifact path named in the steps above.

## Logging Guidance

- Use structured logging (JSON or key-value) so logs are queryable.
- Log at the boundary of the system (incoming requests, outgoing calls to external services, state transitions).
- Include a `correlation_id` or `trace_id` on every log entry to enable cross-service debugging.
- Avoid logging sensitive data (PII, secrets, tokens).
- Log levels: `DEBUG` (development only), `INFO` (normal operations), `WARN` (degraded but recoverable), `ERROR` (unexpected failure requiring attention).

## Metrics Guidance

Common metric types for features:

- **Request rate:** Number of requests per second to new endpoints.
- **Error rate:** Percentage of requests resulting in errors (4xx/5xx).
- **Latency:** Histogram of request durations (p50, p95, p99).
- **Queue depth:** Number of items pending processing (for async features).
- **Resource utilization:** CPU, memory, connections consumed by the feature.
- **Business metrics:** Counts tied to domain events (orders placed, files uploaded).

Every metric should answer: "If this number changes unexpectedly, what action do I take?" If no action exists, the metric is noise.

## Alert Guidance

Good alerts are:
- **Actionable:** Every alert triggers a human response. If nobody acts, remove the alert.
- **Specific:** The condition clearly identifies what is wrong, not just "something is slow."
- **Timely:** Fires fast enough to mitigate impact, but with a `for` duration to avoid flapping.
- **Sized correctly:** Critical alerts wake someone up; Warning alerts appear in dashboards; Info alerts are logged.

Every alert must have a runbook: a short list of steps to diagnose and resolve.

## Tracing Guidance

Add spans at service boundaries and for expensive operations (DB queries, external API calls, large computations). Record attributes that help narrow down the issue: user ID, request ID, operation type, resource identifier.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md`, If the artifact could not be produced, omit the file.

## Example Usage

**Scenario 1: REST API endpoint**
Specification defines `POST /orders`.
Metrics: `orders_request_total` (counter), `orders_request_duration_seconds` (histogram), `orders_error_total` (counter by status code).
Logging: INFO on order created (with order_id, user_id), WARN on validation failure, ERROR on DB write failure.
Alert: fire Critical if error rate > 5% for 5 minutes. Runbook: check DB connectivity, check upstream service.
SLO: 99.9% availability, p99 latency < 500ms.

**Scenario 2: Background job**
Specification defines a nightly data export.
Metrics: `export_jobs_total` (counter), `export_duration_seconds` (histogram), `export_records_processed` (counter).
Logging: INFO on job start/complete (with job_id, record_count), WARN on partial failure, ERROR on full failure.
Tracing: root span for the job, child spans for each batch.
Alert: fire Warning if job duration exceeds 2x normal, Critical if job fails 2 consecutive runs.

**Scenario 3: WebSocket connection**
Specification defines a real-time notification feed.
Metrics: `ws_connections_active` (gauge), `ws_messages_sent_total` (counter), `ws_connection_duration_seconds` (histogram).
Logging: INFO on connect/disconnect (with user_id), WARN on reconnect storm, ERROR on message delivery failure.
Health check: readiness probe that verifies the WebSocket server can accept connections.

## Next Step

Run `/review-observability` to audit the observability plan for completeness, actionability, and consistency before moving on.
Once approved, continue with `/create-plan`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
