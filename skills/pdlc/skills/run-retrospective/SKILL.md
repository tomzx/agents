---
name: run-retrospective
description: Capture what to keep, stop, and start after an initiative, sprint, or kill. Closes the PDLC cycle by turning experience into durable knowledge.
argument-hint: "[initiative-id or scope]"
---

# Run Retrospective

Turns a completed initiative, a sprint, or a killed bet into organizational knowledge. Produces a learning record in `.pdlc/learnings/`. A kill without a retrospective is waste — the point of killing is to learn cheaper than building would have taught.

## Prerequisites

- Apply the shared PDLC conventions in `skills/pdlc/references/shared.md`.
- A concluded initiative (shipped, iterated, or killed), or a sprint boundary.

## Steps

1. Frame the scope: which initiative or period, and what outcome occurred (shipped, iterated, killed).
2. Capture what to **keep** (what worked and should be repeated), what to **stop** (what to never do again), and what to **start** (new actions to try).
3. For each item, name the root cause, not just the symptom. "We were slow" is a symptom; "discovery and build ran in series with no handoff contract" is a root cause.
4. Tie each learning back to the artifact chain: which assumption, decision, or gate should have caught this earlier?
5. Convert the strongest start/stop items into concrete next actions with owners (feed the roadmap or a new initiative).
6. Write the record to `.pdlc/learnings/N-<slug>.md`.

## Output Format

Use the template at `skills/pdlc/templates/learning.md`. Keep/stop/start sections, each item with root cause and (where relevant) a traceable artifact link.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: captured`.

## Completion Checklist

- [ ] Keep / stop / start each populated
- [ ] Each item has a root cause, not just a symptom
- [ ] Learnings traced back to the artifact chain where possible
- [ ] Strongest items converted to owned actions

## Next Step

Feed owned actions into `build-roadmap` or a new `/pdlc discover` cycle.
