---
title: "<Feature Name>"
status: draft
---

# Observability: <Feature Name>

## Overview

<One paragraph describing the observability goals for this feature.>

## Logging

### <Log Category>

| Log Level | Event | Fields | When |
|---|---|---|---|
| INFO | <event name> | <structured fields to include> | <trigger condition> |
| WARN | ... | ... | ... |
| ERROR | ... | ... | ... |

## Metrics

### <Metric Name>

| Field | Value |
|---|---|
| Type | Counter / Histogram / Gauge |
| Description | <What this metric measures> |
| Labels | <dimension labels for filtering> |
| Source | <Where in the codebase this is emitted> |

## Tracing

| Span Name | Service | Attributes | Parent Span |
|---|---|---|---|
| <span_name> | <service> | <key attributes to record> | <parent span or "root"> |

## Health Checks

| Check | Type | Endpoint / Method | Healthy Condition |
|---|---|---|---|
| <name> | Liveness / Readiness | <path or method> | <what determines healthy> |

## Alerts

### <Alert Name>

| Field | Value |
|---|---|
| Condition | <PromQL/query expression> |
| Severity | Critical / Warning / Info |
| For | <duration before firing> |
| Runbook | <link or inline steps> |
| Notification | <channel: Slack, PagerDuty, etc.> |

## SLOs

| SLO | Target | SLI | Measurement Window |
|---|---|---|---|
| <name> | <e.g., 99.9%> | <how availability/latency is computed> | <rolling 30d, etc.> |

## Infrastructure Requirements

| Requirement | Type | Notes |
|---|---|---|
| <requirement> | Log / Metric / Trace / Alert | <additional context> |

## Out of Scope

- <What is explicitly not observed and why>
