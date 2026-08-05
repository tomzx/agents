---
name: plan-launch
description: Plan a product launch — readiness checklist, timeline, channels, and success criteria. Start of the PDLC Launch phase.
argument-hint: "[initiative-id]"
---

# Plan Launch

A launch is a coordinated release, not a deploy. This skill produces the launch plan: who needs to be ready, by when, through which channels, and how we will know it worked. It assumes SDLC has shipped (or is about to ship) the change.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- A shipped or near-shipped change; `acceptance-contract.md` and `goals.md`.

## Steps

1. Define the launch type (minimal/quiet, beta, full GA, phased rollout) and justify it against risk and confidence.
2. Build the readiness checklist across functions: product, engineering, design, docs, support, sales, marketing, legal. Each item has an owner and a due date.
3. Define the timeline: readiness start, launch date, and post-launch review checkpoint.
4. Choose channels and sequencing (in-product, email, blog, sales) tied to the target segments.
5. State launch success criteria: the early-window signals (first hours/days) that indicate the launch landed, distinct from the long-term success metrics in `goals.md`.
6. Define the rollback / pause plan: what would trigger pulling back, and who has authority.
7. Write `launch-plan.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/launch-plan.md`.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted`.

## Completion Checklist

- [ ] Launch type justified against risk
- [ ] Readiness checklist has owners and due dates per function
- [ ] Early-window success signals defined (distinct from long-term metrics)
- [ ] Rollback trigger and authority named

## Next Step

Load `craft-messaging` (then `enable-teams`, `set-pricing`) before running the **Launch gate**.
