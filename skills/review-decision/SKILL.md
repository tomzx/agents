---
name: review-decision
description: Review a decision record for clarity, completeness, reasoning quality, and consequence coverage.
argument-hint: "[decision document or file path]"
---

# Review Decision

Audits a decision record and reports findings across four categories: clarity, completeness, reasoning quality, and consequence coverage.

## Prerequisites

- A decision document provided in context or as a file path to read

## Steps

1. Read the decision document.
2. Evaluate it against the checklist below.
3. Report findings by category. Omit categories with no findings.

## Review Checklist

### Clarity
- Is the decision stated as a specific, unambiguous choice (not a direction or intent)?
- Is the title a noun phrase that names the decision, not just the topic?
- Is the status field present and accurate (Proposed / Accepted / Deprecated / Superseded)?

### Completeness
- Is the context section present and does it explain what problem or question prompted the decision?
- Are at least two options described, including the one chosen?
- Does each option have at least one pro and one con?
- Are trade-offs (gained vs. sacrificed) explicitly stated?

### Reasoning Quality
- Does the reasoning connect the context and constraints to the chosen option?
- Are pros/cons specific to this situation rather than generic statements?
- Is it clear why the chosen option was preferred over the alternatives?
- Are any options dismissed without justification?

### Consequence Coverage
- Are the practical effects on the codebase or process described?
- Are follow-up decisions or deferred work identified?
- Are risks introduced by this decision acknowledged?

## Output Format

```markdown
## Clarity

<Findings or "No issues found.">

## Completeness

<Findings or "No issues found.">

## Reasoning Quality

<Findings or "No issues found.">

## Consequence Coverage

<Findings or "No issues found.">
```

## Example Usage

**Scenario 1: Vague decision statement**
Decision title is "Database approach" and the decision section says "we'll use PostgreSQL where appropriate."
Report under Clarity: the decision must state specifically what was chosen and for what purpose.

**Scenario 2: Single option considered**
Only the chosen approach is listed; no alternatives are documented.
Report under Completeness: at least one alternative must be described so future readers understand what was ruled out.

**Scenario 3: Unjustified dismissal**
Option B is listed but has no pros and only one con, with no explanation of why it was rejected.
Report under Reasoning Quality.

**Scenario 4: No follow-up captured**
A decision to use a flat-file config acknowledges it won't scale but records no follow-up task to revisit the choice.
Report under Consequence Coverage.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
