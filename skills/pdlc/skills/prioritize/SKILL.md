---
name: prioritize
description: Rank a backlog of initiatives or features using a transparent scoring framework (RICE / WSJF). End of the PDLC Strategy phase.
argument-hint: "[scope: initiatives|backlog]"
---

# Prioritize

Scores and ranks work so sequencing is transparent and debatable rather than asserted. Uses RICE (Reach x Impact x Confidence / Effort) or WSJF (Cost of Delay / Job Size), recording the inputs so the ranking can be challenged and re-run when estimates change.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `roadmap.md` and `goals.md`; a backlog of items to rank.

## Steps

1. Choose the framework. RICE suits discovery-stage ranking; WSJF suits time-critical sequencing where delay has a cost.
2. For each item, estimate the framework's inputs explicitly (reach, impact, confidence, effort; or cost-of-delay and job size). Record the number and a one-line justification.
3. Compute the score and rank.
4. Sanity-check the ranking against strategic fit and dependencies. If the top item depends on a lower item, note the dependency and reorder.
5. Separate "do" from "consider" vs. "cut": the cut list is as important as the do list. A backlog that never shrinks is not prioritized.
6. Write a prioritized backlog to `.pdlc/context/roadmap.md` (updated Now/Next/Later) or to the initiative directory for initiative-scoped work.

## Output Format

A ranked table with scores and input justifications, plus the explicit cut list. Update the roadmap's Now/Next/Later to reflect the ranking.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: ranked`.

## Completion Checklist

- [ ] Framework chosen and stated
- [ ] Every scored item has its inputs recorded with a justification
- [ ] Dependencies reflected in the final order
- [ ] A cut list exists (items explicitly not doing)

## Next Step

Run the **Strategy gate** via `make-decision`. On `proceed`, load `write-prd` to begin Define.
