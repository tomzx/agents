---
name: sunset-product
description: Plan the end-of-life for a product or feature — migration, communications, and timeline. A first-class PDLC phase, triggered when an initiative is net-negative.
argument-hint: "[initiative-id]"
---

# Sunset Product

End-of-life is a normal PDLC outcome, not an admission of failure. When the Measure gate returns `sunset` (or when a product becomes net-negative), this skill produces the plan to retire it responsibly: migrate users, communicate, and wind down without breaking promises.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- A `sunset` gate verdict, or a manual decision to retire, with `health-report.md` and `feedback-loop.md` as evidence.

## Steps

1. Confirm the sunset rationale and record it (the value is no longer there, the cost exceeds it, or it is being superseded). Reference the health/feedback evidence.
2. Identify affected users and data: who depends on this, and what must be migrated or preserved.
3. Define the migration path: where users go, what data exports exist, and the effort required.
4. Build the communication timeline: advance notice, deprecation notice, and final cutover date. State the notice period (give users enough runway).
5. Define the ramp-down: feature flags, access controls, and the order in which capabilities are removed.
6. Capture the learning via `run-retrospective` so the sunset compounds knowledge.
7. Write `eol-plan.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/eol-plan.md`.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: planned`.

## Completion Checklist

- [ ] Rationale recorded and tied to evidence
- [ ] Affected users and data identified
- [ ] Migration path defined (or "no migration needed" justified)
- [ ] Communication timeline with a stated notice period
- [ ] Ramp-down order defined
- [ ] Retrospective captured

## Next Step

Run `brief-stakeholders` for the sunset comms, and `kill-initiative` to free the capacity. Sending any user-facing communication requires explicit confirmation.
