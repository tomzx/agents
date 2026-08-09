# Telemetry

<!--
This file captures the project's product analytics infrastructure: the analytics platform,
event conventions, existing event taxonomy, and privacy constraints. It gives create-telemetry
the context it needs to define new events consistently with the existing taxonomy.
System health monitoring (metrics, logs, traces) lives in observability.md.
Update this file when the analytics platform or event conventions change.
-->

## Analytics Platform

| Property | Value |
|---|---|
| Platform | <e.g., Amplitude, Mixpanel, PostHog, Google Analytics, Segment> |
| SDK | <e.g., @amplitude/analytics-browser, posthog-node> |
| Integration | <client-side / server-side / both> |
| API key location | <e.g., env var, config file> |

## Event Naming Conventions

<Rules for naming events, properties, and user traits. Include the naming format (snake_case, camelCase), any entity-action-status patterns, and reserved or prohibited property names.>

## Existing Event Taxonomy

| Event | Trigger | Key properties |
|---|---|---|
| <e.g., user_signed_up> | <Account creation> | <user_id, plan, source> |
| <e.g., feature_used> | <User interacts with feature> | <user_id, feature_name, context> |

<If the project has an event catalog or registry, link to it here.>

## Identity Resolution

<How user identity is established and persisted across sessions (anonymous ID, authenticated user ID, identity merge behavior).>

## Privacy and Compliance

<Consent requirements (e.g., GDPR opt-in), PII prohibitions (what must not be sent as event properties), data retention policy, and any regulatory constraints on telemetry.>

## Funnels and Key Metrics

| Funnel | Steps | Defined in |
|---|---|---|
| <e.g., activation> | <signup, first-action, second-action> | <platform dashboard link> |
