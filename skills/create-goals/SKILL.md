---
name: create-goals
description: Define project goals, objectives, key results, and KPIs so features align to measurable outcomes.
---

# Create Goals

Defines the project's objectives, key results, and ongoing KPIs as a single context-level artifact.

Other skills, especially `create-needs-assessment`, check proposed features against these goals for strategic alignment.
Without stated goals, prioritization is ad hoc: every feature feels equally important, and there is no way to tell whether a need advances the project or is tangential.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `.sdlc/context/project-overview.md` (must exist, for purpose, scope, and stakeholders).
- `.sdlc/context/goals.md` (optional; if present, revise rather than replace, per Revision Mode below).
- Existing features under `.sdlc/features/` (optional, to backfill the alignment table).

## Steps

1. Read `.sdlc/context/project-overview.md` for purpose, scope, and stakeholders.
2. Confirm the time horizon and period type (quarter, half, year) with the user if not already stated.
3. For each objective, write a qualitative statement of what the project wants to achieve this period.
4. Under each objective, define two to five key results: measurable targets with a clear measurement method.
5. Distinguish key results (time-bound, period-scoped targets) from KPIs (ongoing indicators the project watches continuously).
6. Name an owner for each objective.
7. List explicit non-goals to prevent scope creep.
8. Populate the alignment table: map existing features and planned initiatives to the objective they advance.
9. Write the output to `.sdlc/context/goals.md`. If it already exists, revise per Revision Mode.

## Output Format

Use the template at `skills/sdlc/templates/context/goals.md`. Write the result to `.sdlc/context/goals.md`.

## Revision Mode

If `.sdlc/context/review-goals.md` exists with `verdict: changes-requested`, revise the existing `.sdlc/context/goals.md` to address each finding rather than regenerating from scratch.
Preserve content the review did not challenge.

## Goal Design Guidance

- **Objectives are qualitative; key results are quantitative.** An objective says what we want to be true; a key result proves it with a number. "Be the fastest" is an objective; "p99 < 200ms" is a key result.
- **Key results are outcomes, not outputs.** "Ship the notifications feature" is an output. "70% of users view a notification within 24h" is an outcome. Measure the change in the world, not the work done.
- **Three to five key results per objective.** More dilutes focus; fewer is fine.
- **KPIs are ongoing.** A KPI is an indicator you watch indefinitely (conversion rate, uptime). A key result is a target for this period (conversion rate reaches 5% by quarter end). Keep them separate.
- **Name owners.** An objective without an owner has no one to advocate for it when priorities conflict.
- **Non-goals matter as much as goals.** Stating what is deliberately not pursued protects focus.
- **Measurable or it does not belong.** If a key result has no measurement method, it is an aspiration, not a key result.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md`.
If the artifact could not be produced, omit the file.

## Example Usage

**Scenario 1: Growth-focused quarter**
Project overview describes a SaaS product with flat adoption.
Objective: "Make existing users more active."
Key results: weekly active users +30% by quarter end; median sessions per user from 2 to 4; activation rate from 40% to 60%.
KPIs (ongoing): weekly active users, activation rate, churn.
Non-goal: new user acquisition (a separate team owns it this period).

**Scenario 2: Reliability-focused half**
Architecture describes a service with frequent outages.
Objective: "Reduce customer-visible downtime."
Key results: incidents per month from 4 to 1; mean time to recover from 90m to 15m; SLO compliance from 97% to 99.5%.
KPIs (ongoing): uptime, incident count, MTTR.
Alignment: FEAT-42 (automated rollback) advances this objective.

**Scenario 3: Early product, no metrics yet**
No baseline data exists for any key result.
Define objectives and key results with targets, but mark each measurement method as "to be instrumented" and flag it as an open question until telemetry exists.
Recommend running `/create-telemetry` on the next feature to close the gap.

## Next Step

Run `/review-goals` to audit the objectives for measurability, ownership, and alignment soundness before relying on them for prioritization.
Once approved, `create-needs-assessment` reads `.sdlc/context/goals.md` directly when assessing strategic alignment.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
