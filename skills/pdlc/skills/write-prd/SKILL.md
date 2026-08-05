---
name: write-prd
description: Write a product requirements document — problem, outcomes, success criteria, and non-goals. Start of the PDLC Define phase.
argument-hint: "[initiative-id]"
---

# Write PRD

The PRD captures *what* and *why*, never *how*. It states the problem, the desired outcomes, the success criteria tied to `goals.md`, and the explicit non-goals. Implementation (architecture, data models, code) belongs to SDLC, not here.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- Strategy gate `proceed`: `vision.md`, `goals.md`, and the prioritized opportunity.

## Steps

1. State the problem in one paragraph, drawn from `problems.md`. No solutions.
2. State the desired outcomes (what changes for the customer and the business), tied to objectives in `goals.md`.
3. Define functional requirements (`FR-N`): what the product must do to deliver the outcomes, stated as capabilities, not implementations.
4. Define success criteria: which success metrics (`SM-N`) must move, by how much, by when. Reference `goals.md`.
5. State non-goals explicitly: what is deliberately out of scope, to prevent scope creep and set the acceptance boundary.
6. List assumptions and open questions that the Define gate or SDLC must resolve.
7. Write `prd.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/prd.md`. Functional requirements carry `FR-N` IDs; success criteria reference `SM-N` IDs from `goals.md`.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted`.

## Completion Checklist

- [ ] Problem stated without prescribing a solution
- [ ] Outcomes tied to objectives in `goals.md`
- [ ] Functional requirements are capabilities, not implementations
- [ ] Success criteria numeric and time-bound
- [ ] Non-goals explicit

## Next Step

Load `prototype-ux` (for UI-bearing initiatives) and `define-acceptance` (the SDLC handoff seam).
