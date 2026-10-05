---
name: review-team-charter
description: Review a team charter for completeness, clarity, boundary soundness, decision-making, metric quality, and ratifiability.
---

# Review Team Charter

Audits a team charter and reports findings across eight categories: purpose and vision, stakeholders, responsibilities and boundaries, roles, operating norms, decision-making, success metrics, and ratifiability.

A charter fails in two ways: it is too vague to guide decisions, or it contradicts a neighboring charter and reopens a boundary dispute.
This review checks both.

## Prerequisites

- A charter file, default `teams/<team-slug>/charter.md`, or a charter provided in context or as a file path
- The parent organization's mission and values, when available (for alignment checks)
- Adjacent team charters, when available (for boundary-overlap checks)

## Steps

1. Read the charter from `teams/<team-slug>/charter.md` if present, otherwise from context or as a file path.
2. Read adjacent charters and the org mission when available.
3. Identify issues in each category below.
4. Report findings using the output format. Omit any category with no findings.
5. Write the findings to `teams/<team-slug>/review-charter.md` with frontmatter `artifact: team-charter`, `verdict` (`approved` if there are no blocking findings, `changes-requested` if the author must address findings, `rejected` for a fundamental flaw), and `reviewed_at: <ISO date>`, and the findings as the body. Record any unresolved open questions in the findings body.
6. On `approved`, also update the charter's frontmatter: set `status: approved` and `last_reviewed: <ISO date>`.

## Review Checklist

### Purpose and Vision
- Does the Purpose name an outcome the team owns, rather than a list of activities?
- Is the Purpose one or two sentences, or does it grow too long?
- Is the Vision a specific future state for the current horizon, not a generic aspiration?

### Stakeholders
- Are customers and stakeholders named concretely, not as "the company" or "internal stakeholders"?
- Does each named group have what it needs from the team stated?
- Is any obvious consumer of the team's output missing?

### Responsibilities and Boundaries
- Are core responsibilities separated from supporting ones?
- Is each responsibility an outcome or service owned outright, not a task?
- Is the Non-responsibilities section present and substantive (not empty or token)?
- Do any responsibilities overlap with an adjacent team's, with no owner named?
- Is every ambiguous boundary captured in Responsibilities, Non-responsibilities, or Open Questions?

### Roles
- Are members and roles listed with a one-line accountability each?
- Is the team lead or owner identified?
- Are accountabilities stated rather than a task inventory?

### Operating Norms
- Do the documented cadences, channels, and working agreements describe how the team actually works, not an aspiration?
- Are the communication channels assigned to specific purposes, not just listed?
- Are on-call or handoff rules covered where the team has them?

### Decision-making
- Is it clear how decisions are made (for example, propose, discuss, lead decides)?
- Is the escalation path for unresolved conflicts named, with an owner?
- Is authority assigned for the decisions the team most often stalls on?

### Success Metrics
- Are metrics framed as outcomes rather than activity?
- Is each metric measurable and attributable to the team?
- Are detailed OKRs linked to `/create-goals` rather than duplicated here?
- If metrics are "to be defined", is that flagged as an Open Question rather than left blank?

### Ratifiability and Alignment
- Can the whole team read the charter in one sitting and agree or disagree in a single review?
- Does it contradict or duplicate the org mission and values without justification?
- Are Open Questions explicit about what is unresolved?

## Output Format

```markdown
## Purpose and Vision

<Findings or "No issues found.">

## Stakeholders

<Findings or "No issues found.">

## Responsibilities and Boundaries

<Findings or "No issues found.">

## Roles

<Findings or "No issues found.">

## Operating Norms

<Findings or "No issues found.">

## Decision-making

<Findings or "No issues found.">

## Success Metrics

<Findings or "No issues found.">

## Ratifiability and Alignment

<Findings or "No issues found.">
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; the subject passes review |
| `changes-requested` | Findings the author must address before it passes |
| `rejected` | Fundamental flaw requiring rework or stopping |

In the same emission, list the findings file under `artifacts:` (`teams/<team-slug>/review-charter.md`, plus `teams/<team-slug>/charter.md` when you updated its status on approval).

## Example Usage

**Scenario 1: Purpose is a task list**
Purpose reads "We write the payments service and run its CI."
🔴 MUST rewrite as the outcome owned, for example "Own reliable money movement for the product."

**Scenario 2: Missing Non-responsibilities**
The charter lists only what the team owns, and a neighboring team also changes checkout code.
🟡 SHOULD add a Non-responsibilities entry naming what the other team owns, or an Open Question if undecided.

**Scenario 3: Activity metric**
Success Metrics lists "number of deploys".
🟡 SHOULD pair it with an outcome (change failure rate, time to restore) or replace it.

**Scenario 4: Unratifiable length**
The charter runs 20 pages with a full task inventory.
🟡 SHOULD cut it to a single-sitting read, moving detail to linked docs.

## Next Step

Once approved, run [`/create-team-api`](../create-team-api/SKILL.md) to formalize the external interface, then share the charter for ratification and set a review cadence.
