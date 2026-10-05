---
name: review-team-api
description: Review a Team API for completeness, ownership clarity, dependency accuracy, interaction-mode soundness, and contract quality.
---

# Review Team API

Audits a Team API and reports findings across nine categories: team type, purpose, ownership boundaries, services, inputs and outputs, dependencies, interaction modes, communication interface, and evolution.

The Team API is a contract other teams consume.
This review checks that the contract is complete enough to consume without ad hoc conversation, and that no boundary contradicts a neighboring team's API.

## Prerequisites

- A Team API file, default `teams/<team-slug>/team-api.md`, or a Team API provided in context or as a file path
- The team's charter (`teams/<team-slug>/charter.md`), for purpose and responsibility cross-checks
- Adjacent teams' Team APIs or charters, when available, for dependency and overlap checks

## Steps

1. Read the Team API from `teams/<team-slug>/team-api.md` if present, otherwise from context or as a file path.
2. Read the team's charter and any adjacent Team APIs available.
3. Identify issues in each category below.
4. Report findings using the output format. Omit any category with no findings.
5. Write the findings to `teams/<team-slug>/review-team-api.md` with frontmatter `artifact: team-api`, `verdict` (`approved` if there are no blocking findings, `changes-requested` if the author must address findings, `rejected` for a fundamental flaw), and `reviewed_at: <ISO date>`, and the findings as the body. Record any unresolved open questions in the findings body.
6. On `approved`, also update the Team API's frontmatter: set `status: approved` and `last_reviewed: <ISO date>`.

## Review Checklist

### Team Type
- Is the team classified as stream-aligned, platform, enabling, or complicated-subsystem, with a one-line justification?
- Does the type match the work described (for example, a "platform" team that mostly ships product features is mislabeled)?

### Purpose
- Is the team's purpose stated in one sentence?
- Does it match the charter's purpose, or is the divergence explained?

### Ownership Boundaries
- Does "Owns" cover the services, repositories, domains, data, and infrastructure the team is the approver and incident owner for?
- Is "Does not own" present and concrete, naming the owning team where known?
- Does any ownership claim overlap an adjacent team's, with no resolution?
- Is ownership defined by authority (can approve changes, owns incidents) rather than by proximity?

### Services
- Is each service a consumable capability with a one-line description and a stated way to consume it?
- Are internal activities listed as services?

### Inputs and Outputs
- Does every input name its form (intake path, ticket, API, named owner), not just the need?
- Does every output name its form (versioned API, library, document, SLA)?
- Are outputs discoverable from outside the team?

### Dependencies
- Are upstream dependencies (what the team needs) and downstream dependents (who needs the team) both mapped?
- Is the nature of each dependency stated?
- Where a dependency is on another team, does it reference that team's Team API rather than describing the contract informally?

### Interaction Modes
- Is each partner team assigned a mode: x-as-a-service, collaboration, or facilitating?
- Are collaboration and facilitating modes time-boxed, with an end condition?
- Is x-as-a-service the default wherever an interface can stabilize, with collaboration reserved for genuine uncertainty?

### Communication Interface
- Is there a single intake path for work requests?
- Is an expected response time or SLA stated?
- Is the primary channel named?
- Is the process for announcing and versioning breaking changes defined?

### Evolution
- Are expected changes listed with their trigger or condition?
- Are Open Questions explicit about unresolved ownership, missing dependencies, or interfaces still under negotiation?

## Output Format

```markdown
## Team Type

<Findings or "No issues found.">

## Purpose

<Findings or "No issues found.">

## Ownership Boundaries

<Findings or "No issues found.">

## Services

<Findings or "No issues found.">

## Inputs and Outputs

<Findings or "No issues found.">

## Dependencies

<Findings or "No issues found.">

## Interaction Modes

<Findings or "No issues found.">

## Communication Interface

<Findings or "No issues found.">

## Evolution

<Findings or "No issues found.">
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; the subject passes review |
| `changes-requested` | Findings the author must address before it passes |
| `rejected` | Fundamental flaw requiring rework or stopping |

In the same emission, list the findings file under `artifacts:` (`teams/<team-slug>/review-team-api.md`, plus `teams/<team-slug>/team-api.md` when you updated its status on approval).

## Example Usage

**Scenario 1: Unformed input**
Inputs lists "stakeholder feedback" with no intake path.
🟡 SHOULD replace it with a concrete form, for example "a weekly prioritization meeting with the growth lead".

**Scenario 2: Permanent collaboration**
Every partner team is in collaboration mode, with no end date.
🔴 MUST convert steady-state interfaces to x-as-a-service and time-box the remaining collaboration.

**Scenario 3: Undiscoverable output**
The team produces a library but the output says only "internal library".
🟡 SHOULD state its name, how consumers find it, and how it is versioned.

**Scenario 4: Ownership overlap**
Both this API and a neighboring team's claim ownership of the billing schema.
🔴 MUST name a single owner and move the other claim to "Does not own".

## Next Step

Once approved, share it with every team named in Dependencies and Interaction Modes, since a Team API is a contract both sides must agree to.
Revisit when the team type, a major service, or a key interaction mode changes.
