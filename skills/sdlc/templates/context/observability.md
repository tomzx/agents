# Observability

<!--
This file inventories the project's existing observability infrastructure: metrics,
logging, tracing, and alerting. It gives create-observability, audit-observability, and
audit-reliability the context they need without grepping the codebase each time.
Service-level targets (SLOs, SLIs, error budgets) live in service-levels.md.
Update this file when the monitoring stack changes.
-->

## Monitoring Pillars

| Pillar | System | Status |
|---|---|---|
| Metrics | <e.g., Prometheus, Datadog, CloudWatch> | <In use / Not configured> |
| Logging | <e.g., ELK, Splunk, CloudWatch Logs, Loki> | <In use / Not configured> |
| Tracing | <e.g., Jaeger, Zipkin, Datadog APM> | <In use / Not configured> |
| Profiling | <e.g., py-spy, Datadog Profiler, Parca> | <In use / Not configured> |

## Instrumentation Libraries

| Library | Pillar | Configuration |
|---|---|---|
| <e.g., prometheus-client> | Metrics | <scrape endpoint, port> |
| <e.g., structlog> | Logging | <JSON output, log level> |
| <e.g., opentelemetry-sdk> | Tracing | <sampler, exporter> |
| <e.g., sentry-sdk> | Errors | <DSN, environment> |

## Log Aggregation

<Destination, retention period, structured format, and any sampling or filtering in place.>

## Tracing

<Backend, sampling strategy, propagation format (W3C Trace Context, B3, etc.), and which services emit traces.>

## Alerting

| Alert | Source | Routing | Severity |
|---|---|---|---|
| <e.g., high-error-rate> | <Prometheus rule> | <PagerDuty: <service>> | <Critical> |
| <e.g., disk-space-low> | <CloudWatch alarm> | <email> | <Warning> |

<Where alert rules are defined and how they route to on-call.>

## Dashboards

| Dashboard | Location | Purpose |
|---|---|---|
| <e.g., service-overview> | <Grafana URL> | <Latency, error rate, throughput> |

## SLO Reference

<Service-level objectives, indicators, and error budgets are defined in `service-levels.md` (if present). Reference them here when creating feature-level observability plans.>
