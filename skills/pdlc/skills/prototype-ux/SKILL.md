---
name: prototype-ux
description: Create wireframes or a clickable prototype and run a lightweight usability test, recording findings. Part of the PDLC Define phase.
argument-hint: "[initiative-id]"
---

# Prototype UX

For UI-bearing initiatives, de-risk the experience before build: produce wireframes or a clickable prototype, run a short usability test, and record what was learned. For initiatives with no UI surface, this skill is a no-op (state `surface: none` and skip).

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `prd.md` with functional requirements.

## Steps

1. Determine whether the initiative has a UI surface. If not, write `prototype.md` with `surface: none` and stop.
2. Map the key user journeys the prototype must cover (tie to `FR-N` requirements).
3. Produce the lowest-fidelity artifact that lets a user walk the journey: sketches, wireframes, or a clickable prototype. Fidelity should match the risk — higher fidelity only where a workflow question is unresolved.
4. Run a usability test with 3-5 target users (or teammates role-playing the persona). Task them with the journeys; observe where they struggle.
5. Record findings as usability risks ranked by severity, each tied to a requirement or journey step.
6. Feed material findings back into `write-prd` (revise requirements) or `define-acceptance` (add usability acceptance criteria).
7. Write `prototype.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/prototype.md`. Include the journeys tested, the fidelity used, the findings, and links/references to the artifact itself.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted` (or `surface: none`).

## Completion Checklist

- [ ] UI surface confirmed or `surface: none` recorded
- [ ] Key journeys tied to requirements
- [ ] Usability test run with named participants (or personas)
- [ ] Findings ranked and routed back to PRD or acceptance where material

## Next Step

Load `define-acceptance` if not already run, then run the **Define gate** via `make-decision`.
