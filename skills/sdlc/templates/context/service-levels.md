# Service Levels

## Overview

<One paragraph describing the service(s) covered and the purpose of these objectives.>

## Scope

**Services in scope:**
- <service name>

**Out of scope:**
- <service or component explicitly excluded, and why>

## User Journeys

| Journey | Criticality | Description |
|---|---|---|
| <name> | Critical / High / Medium | <what the user does and why it matters> |

## Service Level Indicators (SLIs)

| SLI | Definition | Good Events | Total Events | Source |
|---|---|---|---|---|
| <name> | <plain-language definition> | <what counts as good> | <what counts as total> | <metric, log, or query> |

## Service Level Objectives (SLOs)

| SLO | SLI | Target | Window | Error Budget | Owner |
|---|---|---|---|---|---|
| <name> | <SLI name> | <e.g., 99.9%> | <rolling 30d> | <e.g., 0.1%> | <team or person> |

## Service Level Agreements (SLAs)

| SLA | Target | Consequence | Customer |
|---|---|---|---|
| <name> | <e.g., 99.5%> | <credit, penalty, escalation> | <contracting party> |

## Error Budget Policy

- <What happens when the budget is exhausted: freeze feature work, prioritize reliability, escalate.>
- <Burn-rate thresholds that trigger alerts before the window ends.>

## Alerting

| Alert | Condition | Severity | Action |
|---|---|---|---|
| <name> | <burn rate or threshold> | Critical / Warning | <response> |

## Measurement Infrastructure

| Requirement | Status | Notes |
|---|---|---|
| <metric source or log stream> | Existing / New | <context> |

## Review Cadence

- **Review frequency:** <e.g., monthly>
- **Last reviewed:** <date>
- **Next review:** <date>

## Open Questions

1. <Unresolved question about targets, measurement, or ownership>
