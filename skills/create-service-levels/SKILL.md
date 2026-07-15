---
name: create-service-levels
description: Define SLOs, SLIs, SLAs, and error budgets for a service so reliability targets are explicit and measurable.
---

# Create Service Levels

Defines the service-level objectives, indicators, agreements, and error budgets that govern a service's reliability.

Produces a single context-level artifact that `observe-production` checks against and `audit-observability` validates against.
Without explicit SLOs, reliability is judged by gut feel: no one knows when a degradation is acceptable, when to freeze feature work, or what "healthy" even means.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `.sdlc/context/architecture.md` (must exist, to identify the services and their dependencies).
- `.sdlc/context/goals.md` (optional, to align reliability targets with project objectives).
- `.sdlc/context/service-levels.md` (optional; if present, revise rather than replace, per Revision Mode below).

## Steps

1. Read `.sdlc/context/architecture.md` to enumerate the services, endpoints, and critical user journeys.
2. Read `.sdlc/context/goals.md` if present, to align reliability targets with stated objectives.
3. For each critical user journey, define an SLI: what counts as a "good" event and a "total" event, and where that signal comes from.
4. Set an SLO target per SLI (start conservative; tighten as you measure).
5. Compute the error budget for each SLO (100% minus the target) and state the policy that applies when it is exhausted.
6. Define SLAs only where a contractual or external obligation exists; keep SLA targets looser than SLOs so internal headroom protects the agreement.
7. Specify burn-rate or threshold alerts that surface budget depletion before the window ends.
8. Confirm the measurement infrastructure can actually produce each SLI signal; flag gaps as open questions.
9. Write the output to `.sdlc/context/service-levels.md`. If it already exists, revise per Revision Mode.

## Output Format

Use the template at `skills/sdlc/templates/context/service-levels.md`. Write the result to `.sdlc/context/service-levels.md`.

## Revision Mode

If `.sdlc/context/review-service-levels.md` exists with `verdict: changes-requested`, revise the existing `.sdlc/context/service-levels.md` to address each finding rather than regenerating from scratch.
Preserve content the review did not challenge.
Set the artifact frontmatter `status` to `in-review` while revising, and bump `revision: <n>` starting at 1 on the first revision.

## SLO Design Guidance

- **Start with the user, not the system.** Define SLIs over user-visible journeys (a request succeeded and returned fast enough), not internal counters that happen to be easy to measure.
- **SLI = good / total.** A well-formed SLI is always a ratio. "Error rate" is `1 - (good / total)`. State both numerator and denominator explicitly.
- **One window.** Use a single rolling window (commonly 30 days) across all SLOs so error budgets are comparable.
- **Conservative targets first.** 99% is a fine starting SLO; you can tighten once you have measurement. An aspirational 99.99% you cannot meet is worse than a 99% you can.
- **Error budget is the point.** The budget tells you when to freeze features and prioritize reliability. An SLO with no policy is decoration.
- **SLA looser than SLO.** The SLO is what you hold yourself to; the SLA is what you owe a customer. Keep daylight between them.
- **Few SLOs.** Three to five well-chosen SLOs beat twenty. Each one needs an owner and a policy.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md`.
If the artifact could not be produced, omit the file.

## Example Usage

**Scenario 1: HTTP API**
Architecture describes a REST API serving a web app.
User journey: a client makes a request and gets a valid response.
SLI: `good = requests with status < 500 and latency < 800ms`, `total = all requests`. Source: the API gateway access logs.
SLO: 99.9% of requests are good over a rolling 30-day window. Error budget: 0.1%, about 43 minutes per month.
Policy: when budget drops below 25% remaining, freeze non-reliability feature work.
SLA: 99.5% monthly uptime for the enterprise tier; breach triggers a service credit.

**Scenario 2: Background data pipeline**
Architecture describes a nightly batch job that exports records.
User journey: the job completes and every queued record is processed.
SLI: `good = jobs that finish before the deadline with zero dropped records`, `total = all job runs`.
SLO: 95% of runs succeed fully over a rolling 30-day window.
Alert: page if two consecutive runs fail.

**Scenario 3: Library with no external users**
Architecture describes an internal shared library.
No user-facing service exists, so formal SLOs do not apply.
Document this as out of scope and recommend measurement (test pass rate, release cadence) instead of availability SLOs.

## Next Step

Run `/review-service-levels` to audit the objectives for measurability, coverage, and policy soundness before relying on them.
Once approved, `observe-production` and `audit-observability` consume `.sdlc/context/service-levels.md` directly.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
