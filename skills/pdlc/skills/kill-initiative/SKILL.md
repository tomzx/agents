---
name: kill-initiative
description: Explicitly stop a product initiative — reallocate roadmap capacity, record the sunset-or-pivot rationale, and notify stakeholders. The inverse of prioritize.
argument-hint: "[initiative-id]"
---

# Kill Initiative

Killing an initiative is hard and rarely encoded, so it gets its own skill. It converts a `kill` gate verdict (or a manual decision to stop) into a durable record, frees the capacity the initiative was consuming, and tells stakeholders.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- The initiative to stop (`$1` as `INIT-N`, or resolve from `.pdlc/state.yml`).

## Steps

1. Locate the initiative directory under `.pdlc/initiatives/`.
2. Record the kill via `make-decision` (general decision) if no gate decision already recorded it. The decision body states the rationale: the strongest evidence that killed it (negative experiment, no real problem, cost > value, guardrail breach).
3. Update the initiative's `progress.md`: set `current_phase: killed`, record `killed_at` date, and write a one-line rationale.
4. Reallocate capacity: update `.pdlc/context/roadmap.md` to remove or downgrade the initiative from its Now/Next/Later slot, freeing the slot for the next priority.
5. Capture a learning via `run-retrospective` so the kill produces organizational knowledge, not just a silent deletion. What did we believe that turned out false?
6. Notify stakeholders: produce a brief via `brief-stakeholders` summarizing the decision, the rationale, and the capacity freed. Do not send anything without explicit user confirmation (commit/push/PR gate).
7. If the initiative had already shipped something, consider whether `sunset-product` is also needed for the shipped artifact.

## Output Format

```
## Initiative killed: INIT-N — <title>

Rationale: <one paragraph>
Evidence: <what we learned>
Capacity freed: <roadmap slot / person-weeks>
Stakeholder brief: <drafted, pending send>
Learning: <captured in .pdlc/learnings/>
```

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: killed`.

## Next Step

Run `prioritize` to refill the freed roadmap slot, or `run-retrospective` if not already done.

## Completion Checklist

- [ ] A decision record exists recording the kill rationale
- [ ] `progress.md` marked `killed` with date and rationale
- [ ] Roadmap capacity reallocated
- [ ] A learning captured so the kill compounds knowledge
- [ ] Stakeholder brief drafted (sending requires explicit confirmation)
