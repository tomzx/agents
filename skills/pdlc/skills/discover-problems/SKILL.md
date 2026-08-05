---
name: discover-problems
description: Synthesize customer interviews, jobs-to-be-done, and signals into structured problem statements. The divergent start of the PDLC Discover phase.
argument-hint: "[initiative-id or topic]"
---

# Discover Problems

The divergent entry point of the PDLC. Turns vague signals (a metric regression, recurring complaints, interview notes, support tickets, a hunch) into structured, solution-agnostic problem statements. Stays strictly in problem space: it refuses to solutionize.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- A signal source: interviews, tickets, usage data, a metric regression, or a stated concern.

## Steps

1. Establish or locate the initiative directory under `.pdlc/initiatives/`. If none exists, create `N-<slug>` (issue number if known, else next `p<seq>`).
2. Gather the raw signals. Where interviews exist, extract jobs-to-be-done (the progress a customer is trying to make, their situation, and the forces holding them back). Where data exists, describe the symptom precisely.
3. For each candidate problem, write a problem statement in the form: *For [who], [current situation/struggle], because [root forces], which results in [measurable harm].*
4. Rank problems by frequency, intensity, and willingness-to-pay signals. Mark each as `observed` (evidence-backed) vs `assumed` (hypothesis).
5. Capture who experiences the problem and how (stakeholders table).
6. Record the cost of inaction: what breaks or degrades today, existing workarounds, and the trend (growing / stable / declining).
7. Write `problems.md` to the initiative directory using the template.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/problems.md`. Frontmatter:

```yaml
---
initiative: INIT-N
title: "<topic>"
status: draft
phase: discover
---
```

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted` and a one-line `reason`.

## Completion Checklist

- [ ] Each problem stated without naming a solution
- [ ] Each problem marked `observed` or `assumed`
- [ ] Stakeholders and cost-of-inaction captured
- [ ] At least one problem has a frequency/intensity signal (even if weak)

## Next Step

Load `research-market` and `analyze-competition` (run in either order), then `frame-opportunities` to convert problems into a scored opportunity tree ahead of the first gate.
