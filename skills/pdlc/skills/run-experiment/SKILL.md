---
name: run-experiment
description: Execute an experiment plan, collect data, and record a proceed/kill verdict against the pre-set threshold. End of the PDLC Validate phase.
argument-hint: "[initiative-id]"
---

# Run Experiment

Executes the `experiment-plan.md`, collects the data, and records a verdict against the threshold that was set *before* the test. This is where the PDLC earns its keep: a negative result here is a successful kill, not a failure.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- `experiment-plan.md` with a pre-set decision threshold.

## Steps

1. Run the test per the plan: stand up the fake-door, run the concierge flow, deploy the prototype, or field the survey.
2. Collect the raw data and observations. Keep both quantitative results and qualitative surprises.
3. Compare the result to the pre-set threshold. State the verdict explicitly: `proceed`, `kill`, or `inconclusive`.
4. If `inconclusive`, diagnose why (sample too small, test not decisive, threshold wrong) and decide whether to re-run with a better test or proceed under reduced confidence (recorded as an assumption).
5. Capture learnings: what surprised you, what you now believe that you didn't before.
6. Watch for false positives: would you have seen this result even if the assumption were false?
7. Write `experiment-result.md` to the initiative directory.

## Output Format

Use the template at `skills/pdlc/templates/initiatives/experiment-result.md`. Carry the standard initiative frontmatter with `phase: validate`.

## Outcome

If `$OUTCOME_YAML` is set:

| Verdict | When |
|---|---|
| `proceed` | Result met or exceeded the threshold |
| `kill` | Result missed the threshold; the assumption is false |
| `inconclusive` | Test could not reach the threshold; re-run or proceed-with-caution |

## Completion Checklist

- [ ] Result compared to the pre-set threshold, not a post-hoc rationalization
- [ ] Verdict stated explicitly (proceed / kill / inconclusive)
- [ ] False-positive risk considered
- [ ] Surprises captured as learnings

## Next Step

Run the **Validate gate** via `make-decision`. On `proceed`, load `define-vision` to begin Strategy. On `kill`, the orchestrator runs `kill-initiative`. On `pivot`, return to `design-experiment` with a revised test.
