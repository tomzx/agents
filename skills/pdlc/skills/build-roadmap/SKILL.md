---
name: build-roadmap
description: Sequence initiatives across Now/Next/Later horizons, aligned to goals and outcomes. Part of the PDLC Strategy phase.
argument-hint: "[initiative-id]"
---

# Build Roadmap

An outcome-based roadmap, not a feature delivery calendar. Initiatives are sequenced by outcome and confidence across Now / Next / Later horizons, aligned to the goals in `goals.md`. The roadmap is a communication of *what we believe will create value and when*, and it is expected to change.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `goals.md` from `set-goals`, plus the set of validated/known initiatives.

## Steps

1. List candidate initiatives (validated opportunities, in-flight work, and known commitments).
2. Place each in a horizon:
   - **Now** — being worked or about to be (high confidence, capacity-assigned).
   - **Next** — validated enough to plan around (medium confidence).
   - **Later** — plausible but not yet validated (low confidence).
3. For each, record the outcome it targets (tie to an objective in `goals.md`), the owning team, and the confidence level.
4. Enforce capacity realism: the Now column must fit available capacity. If it does not, move items down.
5. Make sequencing trade-offs explicit: what comes first and why (dependency, value, learning value, risk reduction).
6. Write the result to `.pdlc/context/roadmap.md`.

## Output Format

Use the template at `skills/pdlc/templates/context/roadmap.md`. Three horizon columns; each row carries initiative, outcome, owner, confidence.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted`.

## Completion Checklist

- [ ] Every initiative tied to an outcome/objective in `goals.md`
- [ ] Now column fits stated capacity (over-allocation flagged)
- [ ] Confidence level recorded per item
- [ ] Sequencing rationale stated

## Next Step

Load `prioritize` to rank within horizons, then run the **Strategy gate** via `make-decision`.
