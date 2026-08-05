---
name: synthesize-feedback
description: Aggregate qualitative signal — support, sales, NPS, reviews — and combine it with the metrics read. Produces the artifact the iterate/sunset gate evaluates. Part of the PDLC Measure phase.
argument-hint: "[initiative-id]"
---

# Synthesize Feedback

Combines the quantitative health report with qualitative signal from support tickets, sales conversations, NPS, reviews, and usage observations. The output (`feedback-loop.md`) is what the Measure gate reads to decide `double-down` / `iterate` / `sunset`, and it feeds back into Discover to close the PDLC loop.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `health-report.md` from `review-metrics`, plus available qualitative sources.

## Steps

1. Gather qualitative signal across channels: support tickets, sales/CS notes, NPS verbatims, reviews, in-product feedback. Time-box the window to match the health report.
2. Code the feedback into themes, each with a frequency and a severity. Separate "the thing doesn't work" (defects) from "the thing isn't valuable" (problem-fit).
3. Cross-reference with the health report: does the qualitative story agree with the numbers? Where they disagree, that disagreement is itself a finding.
4. Identify the highest-leverage next problem to solve (the candidate input to the next Discover cycle).
5. Recommend the gate verdict: `double-down` (scale what works), `iterate` (tune based on feedback), or `sunset` (the value isn't there).
6. Write `feedback-loop.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/feedback-loop.md`.

## Outcome

If `$OUTCOME_YAML` is set:

| Verdict | When |
|---|---|
| `double-down` | Strong value confirmed; scale it |
| `iterate` | Real value, needs tuning; loop back to Discover |
| `sunset` | Value not materializing; run `sunset-product` |

## Completion Checklist

- [ ] Feedback themed with frequency and severity
- [ ] Defects separated from problem-fit issues
- [ ] Qualitative story cross-referenced with the health report
- [ ] Highest-leverage next problem identified
- [ ] Gate recommendation stated with rationale

## Next Step

Run the **Measure gate** via `make-decision` (verdict vocabulary: `double-down` / `iterate` / `sunset`).
- `iterate` → the loop closes: return to `discover-problems` with `feedback-loop.md` as input.
- `sunset` → load `sunset-product`.
- `double-down` → load `build-roadmap` to scale, or capture learnings and close.
