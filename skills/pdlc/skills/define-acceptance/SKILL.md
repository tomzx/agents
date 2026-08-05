---
name: define-acceptance
description: Produce the acceptance contract — testable criteria that are the seam between PDLC and SDLC. PDLC owns what/why; SDLC owns how.
argument-hint: "[initiative-id]"
---

# Define Acceptance

This skill produces the **acceptance contract**: the testable, outcome-linked criteria that form the handoff from PDLC to SDLC. It is the seam. SDLC's `create-requirements` consumes this contract directly.

The contract captures *what must be true* for the initiative to be accepted (linked to `SM-N` success metrics and `FR-N` requirements), expressed so an engineer and a PM can both verify it. It deliberately excludes implementation.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `prd.md` with functional requirements and success criteria.

## Steps

1. Translate each functional requirement (`FR-N`) into one or more acceptance criteria in Given/When/Then or measurable form. Each criterion must be verifiable by behavior or measurement, not by code inspection alone.
2. Bind each success metric (`SM-N`) to an acceptance criterion: "accepted only if `SM-N` reaches target within the window."
3. Bind guardrails: list every `GM-N` that must hold post-launch as a hard acceptance line ("must not regress below floor").
4. Define the acceptance boundary: what is in scope (must pass) vs. explicitly out of scope (the non-goals from the PRD).
5. Record the decomposition into SDLC features: one initiative commonly spawns one or more `FEAT-N`. List `spawns_features` in the initiative frontmatter.
6. Note which criteria need runtime/analytics proof (feed `spec-analytics`) vs. functional proof (feed SDLC tests).
7. Write `acceptance-contract.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/acceptance-contract.md`. Each criterion carries an `AC-N` id and links to its `FR-N` / `SM-N` / `GM-N`.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: ready-for-sdlc`.

## The Handoff

After the Define gate `proceed`:
- Point the user to `/sdlc requirements` with this contract as input. PDLC does not run SDLC skills itself.
- SDLC produces `requirements.md` → `specification.md` → plan → code → PR, and the acceptance criteria become SDLC test cases (`TC-N`).
- PDLC resumes at `plan-launch` once the change is shipped.

## Completion Checklist

- [ ] Every `FR-N` has at least one verifiable acceptance criterion
- [ ] Every success metric bound to a criterion with a target and window
- [ ] Every guardrail listed as a hard acceptance line
- [ ] Acceptance boundary (in-scope vs. non-goals) explicit
- [ ] SDLC feature decomposition recorded

## Next Step

Run the **Define gate** via `make-decision`. On `proceed`, hand off to `/sdlc requirements` (PDLC pauses until shipped). Load `spec-analytics` to define how success will be measured at runtime.
