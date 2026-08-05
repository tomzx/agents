---
name: pdlc-status
description: Display a progress dashboard for product initiatives from .pdlc/ directory data, without modifying any artifacts.
---

# PDLC Status

Reads `.pdlc/` and reports where each initiative sits across the six PDLC phases, plus the latest gate verdict for each. Read-only: produces no side effects.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- An initialized `.pdlc/` directory (if absent, report that and suggest `/pdlc setup`).

## Steps

1. List `.pdlc/initiatives/*/` directories. For each, read `progress.md` frontmatter if present.
2. For each initiative, determine which artifacts exist under its directory and map them to phases:
   - Discover: `problems.md`, `market.md`, `competitors.md`, `opportunity-tree.md`
   - Validate: `assumptions.md`, `experiment-plan.md`, `experiment-result.md`
   - Strategy: (writes to `context/vision.md`, `context/goals.md`, `context/roadmap.md`)
   - Define: `prd.md`, `acceptance-contract.md`, `prototype.md`
   - Launch: `launch-plan.md`, `messaging.md`, `enablement-kit.md`, `pricing.md`
   - Measure: `analytics-spec.md`, `health-report.md`, `feedback-loop.md`, `eol-plan.md`
3. Find the most recent decision record in `.pdlc/decisions/` matching each initiative (`initiative: INIT-N`) and report its `phase` and `gate_verdict`.
4. Read `.pdlc/state.yml` for the currently active run, if any.

## Output Format

```
## PDLC Status

Active run: <current_phase for INIT-N, or "none">

| Initiative | Title | Phase | Last Gate | Next Step |
|---|---|---|---|---|
| INIT-42 | Onboarding redesign | Define | proceed | handoff to SDLC |
| INIT-p1 | Usage-based pricing | Validate | pivot | re-run design-experiment |
| INIT-7 | Mobile app | Measure | iterate | back to Discover |

### INIT-42 — Onboarding redesign
Phase: Define (acceptance contract ready — SDLC handoff)
Gate history: discover:proceed → validate:proceed → strategy:proceed → define:proceed
Artifacts: problems.md ✓, opportunity-tree.md ✓, prd.md ✓, acceptance-contract.md ✓
```

If no initiatives exist, report that `.pdlc/` is empty and suggest `/pdlc discover` to start.

## Useful Commands Reference

No CLI commands required. This skill reads files under `.pdlc/`.
