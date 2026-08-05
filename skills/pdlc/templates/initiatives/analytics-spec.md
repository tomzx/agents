---
initiative: INIT-N
title: "<topic>"
status: draft
phase: measure
---

# Analytics Spec: <title>

Guardrail-first: success metrics (what must improve) and guardrail metrics (what must not regress).

## Events

| Event | Trigger | Payload | Feeds metric |
|---|---|---|---|
| <event_name> | <when fired> | <properties> | SM-N / GM-N |

## Funnels

| Funnel | Steps |
|---|---|
| <name> | <step1 → step2 → step3> |

## Dashboards

| Dashboard | Objective | Metrics shown (success + guardrail together) |
|---|---|---|
| <name> | <objective> | SM-N, GM-N |

## Guardrail Alerts

| Metric | Threshold | Response | Owner |
|---|---|---|---|
| GM-N | <floor> | <alert + rollback> | <owner> |

## Measurement Windows

- **Early-window launch signals:** <from launch-plan.md>
- **Steady-state cadence:** <daily/weekly/monthly>

## Instrumentation Gaps (route to SDLC)

- <Metric without a source yet → SDLC instrumentation task>
