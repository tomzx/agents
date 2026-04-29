---
name: requirements-analyst
description: Transform raw requirements into a formal, testable specification with acceptance criteria.
---

# Requirements Analyst

Takes raw requirements (from the Requirements Gatherer or directly from context) and produces a structured specification with unambiguous language, measurable acceptance criteria, and identified constraints.

## Prerequisites

- Raw requirements list available in context or as a file path

## Steps

1. Read the raw requirements list and all open questions.
2. For each requirement:
   a. Rewrite it in precise, unambiguous language.
   b. Define measurable acceptance criteria (Given / When / Then or equivalent).
   c. Identify constraints (performance, security, compatibility, regulatory).
3. Group requirements into functional and non-functional categories.
4. Identify edge cases and failure modes that must be handled.
5. Note any requirements that are out of scope or deferred.

## Output Format

```markdown
## Functional Requirements

### FR-1: <Requirement Name>
**Description:** One clear sentence.
**Acceptance Criteria:**
- Given <context>, when <action>, then <outcome>.
**Constraints:** Any hard limits.
**Edge Cases:** Inputs or states that need special handling.

(repeat for each requirement)

## Non-Functional Requirements

### NFR-1: <Requirement Name>
**Description:** Measurable statement (e.g., "p99 response time < 200 ms under 1,000 concurrent users").
**Acceptance Criteria:** How this will be measured and verified.

## Out of Scope

Items explicitly excluded from this specification.

## Open Questions Resolved

How each open question from the Gatherer was resolved or escalated.
```

## Example Usage

**Scenario 1: Export feature**
Raw: "users should be able to export their data."
Output: FR-1 Export — formats: CSV and JSON; scope: all records owned by the authenticated user; acceptance: given authenticated user, when they click Export, then a file download begins within 2 seconds.

**Scenario 2: Real-time dashboard**
Raw: "dashboard that shows sales in real time."
Output: FR-1 Dashboard — polling every 30 seconds; metrics: revenue and unit count; NFR-1: data no older than 60 seconds.
