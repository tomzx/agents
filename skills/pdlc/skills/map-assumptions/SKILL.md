---
name: map-assumptions
description: List the hypotheses, beliefs, and risks that must be true for an opportunity to succeed, ranked by leverage. Start of the PDLC Validate phase.
argument-hint: "[initiative-id]"
---

# Map Assumptions

Validate begins by making the invisible explicit. For the opportunity that survived the Discover gate, enumerate everything that must be true for it to work, then rank by leverage (impact x uncertainty) so the next skill tests the few assumptions whose falsity would kill the whole thing.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `opportunity-tree.md` with a `proceed` gate from Discover.

## Steps

1. Read the chosen opportunity and its candidate solutions from `opportunity-tree.md`.
2. Surface assumptions across four categories:
   - **Desirability** — do they want this? (problem real, willingness to adopt/pay)
   - **Viability** — does it work for the business? (pricing, unit economics, channel)
   - **Feasibility** — can we build/operate it? (tech, data, ops, partners)
   - **Usability** — can they actually use it? (workflow fit, effort)
3. For each assumption, record: the belief, why it matters, current confidence (low/med/high), and the evidence that would change your mind.
4. Rank by leverage = impact (if false, how bad) x uncertainty (how unsure). The top 1-3 are the **leap-of-faith assumptions** — the ones Validate must test.
5. Write `assumptions.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/assumptions.md`. Carry the standard initiative frontmatter with `phase: validate`.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted`.

## Completion Checklist

- [ ] Assumptions cover all four categories (desirability, viability, feasibility, usability)
- [ ] Each assumption has a confidence level and a falsifying signal
- [ ] The top 1-3 leap-of-faith assumptions are explicitly marked

## Next Step

Load `design-experiment` to design the cheapest decisive test for the top leap-of-faith assumptions.
