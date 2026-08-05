---
name: set-pricing
description: Define the pricing model, packaging, and tiers for an initiative. A consumer of the validated value and willingness-to-pay evidence. Part of the PDLC Launch phase.
argument-hint: "[initiative-id]"
---

# Set Pricing

Pricing is the sharpest expression of value. This skill defines the model (how we charge), the packaging (what is bundled), and the tiers — grounded in the validated willingness-to-pay evidence from Validate, not gut feel.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `experiment-result.md` (willingness-to-pay signal), `vision.md`, `competitors.md`.

## Steps

1. Choose the pricing model (flat, per-seat, usage, tiered, freemium, value-based) and justify it against the value mechanics: how the customer derives value and how that grows.
2. Anchor to willingness-to-pay evidence from `experiment-result.md`. Where evidence is weak, mark the price as an assumption with a validation plan.
3. Compare against `competitors.md` pricing to sanity-check positioning (premium / parity / penetration).
4. Define packaging: what is in each tier, and the upgrade triggers between tiers.
5. State the unit economics implication: does the price cover COGS and acquisition at the expected conversion?
6. Define the rollout: is there an introductory price, a grandfathering policy for existing customers?
7. Write the result to `.pdlc/context/pricing.md` (product-level) and/or the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/pricing.md`.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted`.

## Completion Checklist

- [ ] Model justified against value mechanics
- [ ] Price anchored to willingness-to-pay evidence (or flagged as an assumption)
- [ ] Competitor pricing considered
- [ ] Unit economics sanity-checked
- [ ] Grandfathering / rollout policy stated for existing customers

## Next Step

Run the **Launch gate** via `make-decision`. On `proceed`, the launch proceeds; PDLC then moves to Measure (`spec-analytics`).
