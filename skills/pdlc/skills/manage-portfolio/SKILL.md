---
name: manage-portfolio
description: Assess health across multiple product initiatives and the overall portfolio — balance, bet distribution, and capacity allocation.
---

# Manage Portfolio

A single initiative can look healthy while the portfolio is unbalanced (too many bets in one phase, no discovery pipeline, one segment over-indexed). This skill reads all initiatives and reports portfolio-level health.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- An initialized `.pdlc/` with at least a few initiatives.

## Steps

1. Enumerate `.pdlc/initiatives/*/` and read each `progress.md` and latest gate decision.
2. Compute the distribution of initiatives across the six PDLC phases. A healthy portfolio has flow: some in Discover, some in Validate, fewer in Define/Launch, and a steady Measure loop.
3. Check capacity allocation against `.pdlc/context/roadmap.md` and any team capacity signal. Flag over-allocation (more Now-slot initiatives than capacity) and starvation (empty Discover pipeline).
4. Check bet diversity: segments, customer types, and risk levels. Flag concentration risk.
5. Surface initiatives that are stuck (same phase across multiple sessions with no gate progress) — candidates for `kill-initiative`.
6. Produce the portfolio report and recommended rebalancing actions.

## Output Format

```
## Portfolio Health

Phase distribution: Discover 2 | Validate 1 | Define 3 | Launch 0 | Measure 4 | Killed 1
Capacity: Now-slot initiatives 5 vs capacity 3 — over-allocated by 2
Bets by segment: SMB 6 | Enterprise 1 | Developer 2 — SMB-concentrated
Stuck (>2 sessions, no gate): INIT-3, INIT-9

### Rebalancing
- Move INIT-3 and INIT-9 to kill or deprioritize (run kill-initiative)
- Shift one Define initiative back to Validate (insufficient evidence)
- Seed 1-2 new Discover initiatives to refill the pipeline
```

## Next Step

Act on the recommendations: `kill-initiative` for stuck bets, `prioritize` to rebalance the roadmap, `/pdlc discover` to seed the pipeline.

## Completion Checklist

- [ ] Phase distribution computed
- [ ] Capacity vs roadmap allocation checked
- [ ] Concentration risk assessed
- [ ] Stuck initiatives surfaced with a recommended action each
