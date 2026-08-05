---
name: review-metrics
description: Read the dashboards, compare actuals against goals, surface anomalies, and produce a health report. Part of the PDLC Measure phase.
argument-hint: "[initiative-id]"
---

# Review Metrics

Reads the actuals against the targets defined in `goals.md` and `analytics-spec.md`, and produces a health report. It judges both whether success metrics moved *and* whether guardrails held — a win that breaks a guardrail is not a win.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- A launched initiative with `analytics-spec.md` and instrumentation in place.

## Steps

1. Read the actuals for every success metric (`SM-N`) and guardrail metric (`GM-N`) for the review window.
2. Compare to targets/floors. Classify each as `on-track`, `at-risk`, `missed` (success) or `breached` (guardrail).
3. Surface anomalies: unexpected drops, cohort differences, and changes that coincide with the launch.
4. Distinguish signal from noise: is the change statistically meaningful given sample size and window?
5. Produce the verdict: `healthy`, `mixed`, or `unhealthy`. A guardrail breach forces at least `mixed`, usually `unhealthy`.
6. Recommend actions: double-down (scale), iterate (tune), or roll back.
7. Write `health-report.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/health-report.md`.

## Outcome

If `$OUTCOME_YAML` is set:

| Verdict | When |
|---|---|
| `healthy` | Success metrics on track, no guardrail breach |
| `mixed` | Some metrics on track, others at-risk, or a guardrail near its floor |
| `unhealthy` | Success metrics missed or a guardrail breached |

## Completion Checklist

- [ ] Every `SM-N` and `GM-N` read for the window
- [ ] Each classified with a status
- [ ] Anomalies and cohort splits noted
- [ ] Signal-vs-noise considered (sample/window)
- [ ] Verdict and recommended action stated

## Next Step

Load `synthesize-feedback` to combine the quantitative read with qualitative signal.
