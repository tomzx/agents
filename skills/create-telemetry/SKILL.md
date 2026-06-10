---
name: create-telemetry
description: Define analytics events, success metrics, and telemetry for a feature so usage can be measured from day one.
argument-hint: "[specification-doc]"
---

# Create Telemetry

Defines how feature usage will be measured by identifying analytics events, success metrics, funnel steps, and telemetry requirements before implementation begins.

Without this step, features ship without instrumentation, making it impossible to measure adoption, diagnose issues, or make data-driven decisions about iteration.

## Prerequisites

- `.sdlc/features/FEAT-NNNN-<slug>/specification.md` (must have `status: approved`), or a specification document provided in context or as a file path (`$1`)
- `.sdlc/features/FEAT-NNNN-<slug>/requirements.md` (optional, for cross-referencing acceptance criteria)
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there to the produced document

## Steps

1. Read the specification and requirements documents.
2. Identify the key user flows and system interactions from the specification.
3. For each flow, determine what events should be tracked to measure adoption, completion, and failure.
4. Define success metrics that answer: "How do we know this feature is successful?"
5. Define funnel steps for critical user journeys.
6. Specify the event taxonomy: event names, properties, and where they fire.
7. Identify any counter metrics (signs the feature might be causing harm).
8. Determine telemetry infrastructure requirements (existing vs. new instrumentation).
9. Write the output to `.sdlc/features/FEAT-NNNN-<slug>/telemetry.md`.

## Output Format

```markdown
---
issue: "#<N>"
title: "<Feature Name>"
status: draft
---

# Telemetry: <Feature Name>

## Overview

<One paragraph describing the measurement goals for this feature.>

## Success Metrics

| Metric | Target | Measurement Method | Timeframe |
|---|---|---|---|
| <metric name> | <target value or threshold> | <how it is computed> | <over what period> |

## User Funnel

| Step | Event | Entry Criteria | Exit Criteria |
|---|---|---|---|
| 1. <step name> | <event that marks entry> | <precondition> | <what moves user to next step> |
| 2. <step name> | ... | ... | ... |

## Analytics Events

### <event_name>

**Trigger:** <When this event fires (user action, system event, etc.)>
**Location:** <Where in the codebase this is emitted>

| Property | Type | Required | Description |
|---|---|---|---|
| <property_name> | <string/number/boolean> | Yes/No | <What this property captures> |

## Counter Metrics

| Metric | Concern | Threshold |
|---|---|---|
| <metric name> | <what negative signal it detects> | <value that triggers investigation> |

## Telemetry Requirements

| Requirement | Type | Notes |
|---|---|---|
| <e.g., "Add analytics SDK to settings page"> | Infrastructure / Event / Dashboard | <additional context> |

## Dashboards and Alerts

- **Dashboard:** <What dashboard to create or update, and what it shows>
- **Alerts:** <Any automated alerts and their conditions>

## Out of Scope

- <What is explicitly not tracked and why>
```

## Event Naming Conventions

Follow these conventions for consistency across features:

- Use `snake_case` for event names: `user_signup_completed`, `order_payment_failed`
- Use `<entity>_<action>_<status>` pattern where applicable: `invoice_export_started`, `invoice_export_completed`, `invoice_export_failed`
- Prefix with feature name for namespacing when the analytics platform requires it
- Properties should be primitive types (string, number, boolean) to ensure queryability
- Include a `source` property on every event to distinguish client vs. server emission

## Success Metrics Guidance

Good success metrics are:
- **Measurable:** Tied to a specific number or ratio, not subjective
- **Actionable:** If the metric moves in the wrong direction, there is a clear response
- **Time-bound:** Measured over a defined period (first week, first month, etc.)

Common metric types:
- **Adoption:** % of eligible users who use the feature at least once
- **Engagement:** Average uses per user per week
- **Completion rate:** % of users who finish a multi-step flow
- **Time-to-value:** Median time from feature discovery to first successful use
- **Error rate:** % of interactions that result in an error

## Example Usage

**Scenario 1: New notification system**
Requirements describe a notification center with email and in-app notifications.
Success metrics: 70% of users view notifications within 24h, < 2% unsubscribe rate.
Funnel: notification_sent → notification_viewed → notification_clicked → target_action_completed.
Counter metrics: notification_delivery_failure_rate > 1%.

**Scenario 2: API endpoint for file uploads**
Requirements describe a bulk file upload feature.
Success metrics: 95% upload success rate, median upload time < 5s for 10MB files.
Events: upload_started (with file_count, total_bytes), upload_completed, upload_failed (with error_type).
Counter metrics: retry_rate > 10%, user_abandonment_after_failure > 50%.

**Scenario 3: Internal tool dashboard**
Requirements describe an admin analytics dashboard.
Success metrics: 80% of admins use it weekly, average session time 2-5 minutes (not too short = confused, not too long = struggling).
Events: dashboard_viewed, filter_applied (with filter_type), export_clicked.

## Next Step

Run `/review-telemetry` to audit the telemetry plan for completeness, actionability, and consistency before moving on.
Once approved, continue with `/create-plan`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
