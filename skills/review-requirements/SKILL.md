---
name: review-requirements
description: Review a requirements document for clarity, completeness, testability, and feasibility.
---

# Review Requirements

Audits a requirements document and reports findings across five categories: clarity, completeness, testability, feasibility, and conflicts.

## Prerequisites

- A requirements document provided in context or as a file path to read

## Steps

1. Read the requirements document thoroughly.
2. Identify issues in each of the five categories below.
3. Report findings using the output format. Omit any category that has no findings.

## Review Checklist

### Clarity
- Is each requirement unambiguous and precisely worded?
- Does it avoid vague terms ("fast", "user-friendly", "easy")?
- Is the subject and action of each requirement clear?

### Completeness
- Are all stakeholders represented?
- Are happy-path and error/edge cases covered?
- Are non-functional requirements (performance, security, reliability) present?
- Are acceptance criteria defined for every requirement?

### Testability
- Can each requirement be verified with a concrete test?
- Are acceptance criteria measurable and observable?
- Are quantitative thresholds given where applicable (e.g., "< 200 ms")?

### Feasibility
- Are any requirements technically impractical given the stated constraints?
- Are there scope or effort concerns that should be flagged?
- Do dependencies on external systems introduce unaddressed risk?

### Conflicts
- Do any requirements contradict each other?
- Are there priority conflicts between Must/Should requirements?
- Do non-functional requirements conflict with functional ones?

## Output Format

```markdown
## Clarity

<Findings or "No issues found.">

## Completeness

<Findings or "No issues found.">

## Testability

<Findings or "No issues found.">

## Feasibility

<Findings or "No issues found.">

## Conflicts

<Findings or "No issues found.">
```

## Example Usage

**Scenario 1: Missing acceptance criteria**
FR-03 states "the system shall send notifications" but no acceptance criterion defines when, how, or to whom.
Report under Completeness.

**Scenario 2: Untestable requirement**
NFR-02 says "the UI must be intuitive."
Flag under Testability — rewrite as a measurable usability criterion.

**Scenario 3: Conflicting priorities**
FR-01 is marked Must (offline support) while NFR-01 is Must (real-time sync).
These conflict. Report under Conflicts.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
