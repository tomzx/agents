---
name: define-vision
description: Define the product vision, target customer, and positioning for a validated opportunity. Start of the PDLC Strategy phase; writes the product-level vision anchor.
argument-hint: "[initiative-id]"
---

# Define Vision

Turns a validated opportunity into a product vision and positioning statement. This skill writes the product-level anchor consumed by every downstream phase: who it is for, what change it creates, and why it wins.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- A validated opportunity (Validate gate `proceed`): `opportunity-tree.md` and `experiment-result.md`.

## Steps

1. State the target customer precisely (the ICP, not "everyone"). Reference segments from `market.md`.
2. Articulate the vision: the future where the customer's problem is solved. One sentence a stranger could repeat.
3. Write the positioning statement: *For [target], who [struggle], our product is [category] that [key benefit]. Unlike [alternative], we [differentiation].* Tie differentiation to gaps from `competitors.md`.
4. Define what winning looks like in 12 months — the world-state, not a feature list.
5. State explicit non-goals: who and what is out of scope, to prevent vision creep.
6. Write the result to `.pdlc/context/vision.md` (the product-level anchor) **and** leave a pointer in the initiative directory noting which initiative established it.

## Output Format

Use the template at `skills/pdlc/templates/context/vision.md`. Because vision is product-level, it lives under `.pdlc/context/`, not the initiative directory. If multiple initiatives coexist, merge rather than overwrite, and note conflicts.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted`.

## Completion Checklist

- [ ] Target customer is specific (an ICP, not "all users")
- [ ] Vision is one repeatable sentence
- [ ] Positioning names a concrete alternative and a concrete differentiation
- [ ] Non-goals stated

## Next Step

Load `set-goals` to translate the vision into measurable objectives and guardrails.
