---
name: spec-analytics
description: Specify the events, funnels, dashboards, and guardrails needed to measure an initiative. Guardrail-first by design. Start of the PDLC Measure phase.
argument-hint: "[initiative-id]"
---

# Spec Analytics

Defines how an initiative will be measured at runtime. It is **guardrail-first**: it specifies the guardrail metrics (what must not regress) alongside the success metrics, because the classic failure is moving the metric you measured while breaking three you did not. This artifact is the PDLC counterpart to SDLC's telemetry plan; it can feed SDLC instrumentation.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `acceptance-contract.md` and `goals.md` (the `SM-N` and `GM-N` definitions).

## Steps

1. List the analytics events required to compute every success metric (`SM-N`) and guardrail metric (`GM-N`) from `goals.md`. Each event has a name, trigger, and payload.
2. Define the conversion funnels that reveal where value is created or lost.
3. Define the dashboards: one per objective, showing success and guardrail metrics together so regressions are visible next to gains.
4. For each guardrail, define the alert threshold and the response (who is paged, what is the rollback).
5. Define the measurement windows: the early-window launch signals (from `launch-plan.md`) and the steady-state cadence.
6. Flag metrics whose measurement source is not yet instrumented; route these to SDLC as instrumentation work.
7. Write `analytics-spec.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/analytics-spec.md`. Reference `SM-N` / `GM-N` IDs from `goals.md`.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted`.

## Completion Checklist

- [ ] Every `SM-N` and `GM-N` has a defined event source
- [ ] Guardrails have alert thresholds and a response owner
- [ ] Dashboards pair success and guardrail metrics
- [ ] Uninstrumented metrics flagged for SDLC

## Next Step

After launch, load `review-metrics` to read the actuals.
