---
name: audit-outcomes
description: Trace shipped product outcomes back to the original problem and metrics, PDLC's equivalent of backpropagation. Catches drift where the spec was built faithfully but stopped being the right thing.
argument-hint: "[initiative-id]"
---

# Audit Outcomes

Walks the PDLC artifact chain in reverse to verify end-to-end traceability: does what shipped trace to a validated opportunity, and do the health metrics justify the original decision? This is the PDLC analog of `backpropagate-sdlc`, but it judges *outcome coherence*, not spec-to-code consistency.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- A shipped or measured initiative (`$1`), or scan all initiatives under `.pdlc/initiatives/`.

## Steps

1. For the target initiative, gather the chain: `opportunity-tree.md` → `experiment-result.md` → `prd.md` → `acceptance-contract.md` → `health-report.md` → `feedback-loop.md`, plus all decision records.
2. Walk it in reverse, from `health-report.md` back to `problems.md`, checking each link:
   - Do the measured outcomes map back to the success metrics defined in `prd.md` / `analytics-spec.md`?
   - Were guardrail metrics defined up front and checked after launch? (A missing guardrail is itself a finding.)
   - Does the shipped scope trace to the acceptance contract, which traces to the PRD outcomes, which trace to a validated opportunity?
   - Does each gate decision still look defensible in hindsight?
3. Score each link `aligned` / `drifted` / `broken`. A link is `drifted` when the artifact evolved without updating the chain; `broken` when the outcome contradicts the premise.
4. For any `drifted` or `broken` link, regress the relevant gate decision to `pivot` (record in a new decision record) so the forward loop resyncs it.
5. Produce the audit report.

## Findings Categories

- **Traceability gaps** — a shipped outcome with no upstream opportunity, or an opportunity with no measured outcome.
- **Metric drift** — success metrics changed without re-validating the opportunity; guardrails missing or unmeasured.
- **Decision rot** — a gate decision that no longer holds given new evidence.
- **Premature shipping** — launched before the gate chain was complete.

## Output Format

Write the report to `.pdlc/audit-report.md` (repo-only, never mirrored) and summarize:

```
## PDLC Outcome Audit: INIT-N

Chain: problems → opportunity → experiment → prd → acceptance → health → feedback
Links: 6 aligned, 1 drifted, 0 broken

### Findings
- [drifted] Success metric SM-2 has no corresponding measurement in health-report.md
- [decision-rot] Discover gate proceeded on an assumption since invalidated

### Actions
- Regressed the Strategy gate to pivot; re-run set-goals to redefine SM-2
```

## Outcome

If `$OUTCOME_YAML` is set:

| Verdict | When |
|---|---|
| `aligned` | Chain traces end to end; no drift |
| `drift-detected` | One or more links drifted or rotted; gates regressed |
| `broken` | A link is broken; major rework or kill warranted |

## Useful Commands Reference

No CLI commands required. This skill reads `.pdlc/` and writes a report.
