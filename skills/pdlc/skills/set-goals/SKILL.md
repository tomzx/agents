---
name: set-goals
description: Define OKRs, success metrics, and guardrail metrics for a product or initiative. Part of the PDLC Strategy phase.
argument-hint: "[initiative-id]"
---

# Set Goals

Translates the vision into measurable objectives, key results, and the two metric types that define success: **success metrics** (what must improve) and **guardrail metrics** (what must not regress). The classic PM failure is moving the measured metric while breaking three unmeasured ones; guardrails are the antidote and are mandatory here.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `vision.md` from `define-vision`.

## Steps

1. Define 1-3 objectives (qualitative outcomes aligned to the vision).
2. For each objective, define 2-4 key results that are measurable and time-bound.
3. List **success metrics** (`SM-N`): the numbers that must move for the initiative to count as a win. Each gets a baseline, a target, and a measurement source.
4. List **guardrail metrics** (`GM-N`): the numbers that must hold (e.g., latency, churn, error rate, cost-per-unit). Each gets a current value and a floor it must not cross. If you cannot name a guardrail, that is a finding — it means you do not know what you could break.
5. Confirm every metric has an owner and a measurement source (instrumentation, report, manual). Metrics without a source are wishes.
6. Write the result to `.pdlc/context/goals.md` (product-level) and/or the initiative directory for initiative-specific goals.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/goals.md` (also used as the context template). Each metric row: ID, name, type (success/guardrail), baseline, target/floor, owner, source.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted`.

## Completion Checklist

- [ ] At least one success metric and at least one guardrail metric
- [ ] Every metric has a baseline, target/floor, owner, and measurement source
- [ ] Key results are time-bound
- [ ] No metric is "we will improve X" without a number

## Next Step

Load `build-roadmap` to sequence initiatives against these goals.
