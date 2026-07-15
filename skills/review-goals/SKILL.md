---
name: review-goals
description: Review goals, objectives, key results, and KPIs for measurability, ownership, and alignment.
---

# Review Goals

Audits a goals document for measurability, ownership, alignment, and focus, so the objectives can reliably drive prioritization.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `.sdlc/context/goals.md`, or a goals document provided in context or as a file path.
- `.sdlc/context/project-overview.md` (to verify purpose and scope alignment).
- Features under `.sdlc/features/` (optional, to spot orphaned work that advances no objective).

## Steps

1. Read the goals document from `.sdlc/context/goals.md` if present, otherwise from context or as a file path.
2. Cross-reference against the project overview and existing features.
3. Identify issues in each category below.
4. Report findings. Omit any category that has no findings.
5. Write the findings to `.sdlc/context/review-goals.md` with frontmatter `artifact: goals`, `verdict` (`approved` if no blocking findings, `changes-requested` if the author must address findings, `rejected` for a fundamental flaw), and `reviewed_at: <ISO date>`, with the findings as the body, per `skills/sdlc/references/shared.md`. Record any unresolved open questions in the findings body.

## Review Checklist

### Measurability
- Is every key result tied to a concrete number, ratio, or threshold (not subjective)?
- Is the measurement method specified for each key result and KPI?
- Are key results distinguished from KPIs (time-bound targets vs. ongoing indicators)?
- Where a measurement method is missing, is it flagged as an open question?

### Ownership
- Is each objective owned by a named team or person?
- Are KPIs assigned to someone who watches them?

### Focus
- Are there three to five key results per objective (not so many that focus dilutes)?
- Are non-goals stated to protect against scope creep?
- Do the objectives cover distinct themes, or do several say the same thing?

### Alignment
- Do the objectives follow from the project overview's purpose and scope?
- Are existing features mapped to the objective they advance (the alignment table)?
- Is there orphaned work: a feature advancing no stated objective?

### Feasibility
- Are the targets achievable given the current baseline and the period length?
- Is the time horizon stated and consistent across all objectives?

## Output Format

```markdown
## Measurability

<Findings or "No issues found.">

## Ownership

<Findings or "No issues found.">

## Focus

<Findings or "No issues found.">

## Alignment

<Findings or "No issues found.">

## Feasibility

<Findings or "No issues found.">
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; the subject passes review |
| `changes-requested` | Findings the author must address before it passes |
| `rejected` | Fundamental flaw requiring rework or stopping |

## Example Usage

**Scenario 1: Output mistaken for outcome**
Key result: "Ship the reporting dashboard."
Report under Measurability: this measures work done, not the change in the world.
Rephrase as the outcome the dashboard enables (e.g., "X% of admins generate a weekly report").

**Scenario 2: Orphaned feature**
Alignment table omits FEAT-17, an in-flight feature.
Report under Alignment: map FEAT-17 to an objective, or flag it as not goal-aligned (a candidate for deprioritization).

**Scenario 3: Unmeasurable objective**
Objective: "Delight users." No key result has a measurement method.
Report under Measurability: every key result needs a measurement method or it is an aspiration, not a target.

## Next Step

Once the findings verdict is `approved`, the goals are ready to drive prioritization.
`create-needs-assessment` reads `.sdlc/context/goals.md` directly when assessing strategic alignment.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
