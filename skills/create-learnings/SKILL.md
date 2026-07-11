---
name: create-learnings
description: Capture learnings after completing a feature, sprint, or project in a structured retrospective format.
argument-hint: "[feature, sprint, or project description]"
---

# Create Learnings

Facilitates a retrospective to capture actionable learnings after completing a feature, sprint, or project.
Produces a structured document covering what went well, what didn't, process improvements, technical insights, and next actions.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- A completed feature, sprint, or project to reflect on
- Context about what was built, how long it took, and any notable events
- If `.sdlc/features/N-<slug>/questions.md` exists for the feature, review it to surface unresolved questions.
- If any files exist under `.sdlc/knowledge/assumptions/` or `.sdlc/knowledge/decisions/` for this feature, review them for context.

## Steps

1. Gather context: what was delivered, timeline, team involved, and any notable events.
2. Reflect on what went well (practices worth repeating and amplifying).
3. Reflect on what didn't go well, identifying root causes not just symptoms.
4. Identify concrete process improvements with owners and dates.
5. Capture technical insights: decisions that paid off and decisions to revisit.
6. Distill actionable next steps.
7. Write the output to `.sdlc/knowledge/learnings/N-<slug>.md` where N is the next available sequence number in that directory.

## Output Format

Use the template at `skills/sdlc/templates/knowledge/learning.md` (copied to `.sdlc/templates/knowledge/learning.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write the result to the artifact path named in the steps above.

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md` once the learnings artifact is written.

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
