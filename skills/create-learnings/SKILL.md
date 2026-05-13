---
name: create-learnings
description: Capture learnings after completing a feature, sprint, or project in a structured retrospective format.
argument-hint: "[feature, sprint, or project description]"
---

# Create Learnings

Facilitates a retrospective to capture actionable learnings after completing a feature, sprint, or project.
Produces a structured document covering what went well, what didn't, process improvements, technical insights, and next actions.

## Prerequisites

- A completed feature, sprint, or project to reflect on
- Context about what was built, how long it took, and any notable events
- If `.sdlc/<feature>/assumptions.md` or `.sdlc/knowledge/assumptions.md` exists, review it to capture what assumptions were logged and how they resolved

## Steps

1. Gather context: what was delivered, timeline, team involved, and any notable events.
2. Reflect on what went well (practices worth repeating and amplifying).
3. Reflect on what didn't go well, identifying root causes not just symptoms.
4. Identify concrete process improvements with owners and dates.
5. Capture technical insights: decisions that paid off and decisions to revisit.
6. Distill actionable next steps.
7. Write the output to `.sdlc/<feature>/learnings.md`.

## Output Format

```markdown
---
issue: "#<N>"
title: "<Feature Name>"
status: draft
---

# Learnings: <Feature / Sprint / Project Name>

**Date:** <YYYY-MM-DD>
**Duration:** <How long it took>
**Delivered:** <What was shipped>

---

## What Went Well

- <Specific practice, decision, or event that had a positive impact>

## What Didn't Go Well

- <Issue>: <Root cause — not just the symptom>

## Process Improvements

| Improvement | Rationale | Owner | Target Date |
|---|---|---|---|
| <Action to take> | <Why this will help> | <Who> | <When> |

## Technical Insights

### Decisions That Paid Off

- <Decision>: <Why it helped>

### Decisions to Revisit

- <Decision>: <What we'd do differently and why>

## Action Items

- [ ] <Concrete next step> — **Owner:** <name>, **By:** <date>

## Metrics (if available)

| Metric | Planned | Actual |
|---|---|---|
| Duration | X days | Y days |
| Scope changes | — | N additions |
| Bugs found in review | — | N |
```

## Example Usage

**Scenario 1: Feature retrospective**
A payment feature took 3 weeks instead of 2.
Learnings: the third-party API was underdocumented (add a spike phase to future plans involving new integrations), automated integration tests caught 4 regressions early (keep and expand), the spec was changed mid-implementation (add a spec-freeze milestone to the plan template).

**Scenario 2: Sprint retrospective**
End-of-sprint review with the team.
What went well: daily standups kept everyone aligned.
What didn't: unclear task definitions led to rework.
Action item: run `/create-tasks-decomposition` before each sprint starts.

## Useful Commands Reference

No CLI commands required. This skill operates on information provided in context.
