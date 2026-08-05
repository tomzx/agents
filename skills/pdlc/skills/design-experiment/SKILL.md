---
name: design-experiment
description: Design the cheapest decisive test for an initiative's riskiest assumptions — fake-door, concierge, prototype, or survey. Part of the PDLC Validate phase.
argument-hint: "[initiative-id]"
---

# Design Experiment

For each leap-of-faith assumption, design the test that, at minimum cost, would change your decision. The goal is decisiveness, not completeness: a test whose result cannot flip the verdict is not worth running.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `assumptions.md` with the ranked leap-of-faith assumptions.

## Steps

1. For each top assumption, define the hypothesis in testable form: *If [we do X], then [we expect Y], because [belief].*
2. Choose the cheapest method that can falsify it:
   - **Fake-door / painted-door** — does demand exist before building? (desirability)
   - **Concierge / Wizard-of-Oz** — deliver the value manually; is the outcome real? (viability/feasibility)
   - **Prototype** — can they use it / does the workflow fit? (usability)
   - **Survey / interview** — only for beliefs you cannot observe behaviorally; treat as weak evidence.
3. Set the decision threshold up front: the numeric result that means proceed vs. kill. Decide the threshold *before* running, not after.
4. Define the audience, sample size, duration, and what you will measure. State the smallest sample that could move your confidence.
5. Record what a false positive would look like (how the test could mislead you into proceeding).
6. Write `experiment-plan.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/experiment-plan.md`. Carry the standard initiative frontmatter with `phase: validate`.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: drafted`.

## Completion Checklist

- [ ] Hypothesis stated in if/then/because form
- [ ] Method is the cheapest that can falsify the assumption
- [ ] Decision threshold (proceed vs. kill) set before running
- [ ] Sample and duration justified
- [ ] False-positive risk acknowledged

## Next Step

Load `run-experiment` to execute the plan and record a verdict.
