---
name: frame-opportunities
description: Convert discovery inputs into a scored opportunity-solution tree. Produces the artifact the first PDLC gate evaluates.
argument-hint: "[initiative-id]"
---

# Frame Opportunities

The convergent end of Discover. Takes `problems.md`, `market.md`, and `competitors.md` and builds an opportunity-solution tree: the desired outcome at the top, opportunities beneath, and candidate solutions under each, scored so the gate can decide what to pursue.

This is the artifact the **Discover gate** evaluates. A low score here should route back to discovery, not forward to validation.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `problems.md`, `market.md`, and `competitors.md` from the other Discover skills.

## Steps

1. State the desired outcome (the customer/business result), not a feature.
2. Branch into 3-7 opportunities that could move that outcome. Each opportunity is a lever, not a solution.
3. Under each opportunity, list 2-4 candidate solutions (these are provisional — Validate will test the riskiest assumptions, not pick a solution yet).
4. Score each opportunity on a transparent rubric: customer value, strategic fit (to `goals.md`), reach, and confidence. Record the score, not just a gut ranking.
5. Recommend the opportunity (or two) to carry into Validate, with the one or two riskiest assumptions called out for testing.
6. Write `opportunity-tree.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/opportunity-tree.md`. Carry the standard initiative frontmatter with `phase: discover`.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted` plus `reason`.

## Completion Checklist

- [ ] Desired outcome stated as a result, not a feature
- [ ] Each opportunity is a lever, distinct from the others
- [ ] Each opportunity scored on a stated rubric (not just ranked)
- [ ] The riskiest assumptions to test are explicitly named for Validate

## Next Step

Run the **Discover gate** via `make-decision`. On `proceed`, load `map-assumptions` to begin Validate. On `pivot`, return to `discover-problems` or `research-market` in revision mode.
