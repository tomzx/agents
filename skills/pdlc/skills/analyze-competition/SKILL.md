---
name: analyze-competition
description: Map the competitive landscape and positioning gaps for a candidate problem space. Part of the PDLC Discover phase.
argument-hint: "[initiative-id or topic]"
---

# Analyze Competition

Maps who else addresses the problem, how they position, and where the gaps are. The output is positioning opportunities, not feature checklists. Pairs with `research-market` and feeds `frame-opportunities`.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `problems.md` from `discover-problems`, or an explicit topic.

## Steps

1. Enumerate alternatives the target customer could use, including status-quo and workarounds (the most common "competitor" is doing nothing).
2. For each, capture positioning: who they target, the job they claim to do, their price/range, and their strongest and weakest points.
3. Build a positioning map across two axes that matter to the customer (e.g., ease vs. power, price vs. completeness). Identify empty quadrants.
4. Identify differentiation opportunities: where the problem is underserved, mis-served, or served for the wrong segment.
5. Note moats and switching costs that affect viability, not just desirability.
6. Write `competitors.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/competitors.md`. Carry the standard initiative frontmatter with `phase: discover`.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted`.

## Completion Checklist

- [ ] Status-quo / do-nothing included as an alternative
- [ ] Positioning map with two customer-meaningful axes
- [ ] At least one differentiation opportunity identified and tied to a problem
- [ ] Switching costs / moats noted

## Next Step

Load `frame-opportunities` once discovery inputs are ready.
