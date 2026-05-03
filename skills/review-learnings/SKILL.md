---
name: review-learnings
description: Review a learnings document for actionability, specificity, completeness, and balance.
---

# Review Learnings

Audits a learnings document and reports findings across four categories: actionability, specificity, completeness, and balance.

## Prerequisites

- A learnings document provided in context or as a file path to read

## Steps

1. Read the learnings document.
2. Evaluate it against the checklist below.
3. Report findings by category. Omit categories with no findings.

## Review Checklist

### Actionability
- Do process improvements have a concrete action, an owner, and a target date?
- Are action items specific enough to execute without further clarification?
- Are improvements measurable so progress can be tracked?

### Specificity
- Are observations specific to this project or sprint (not generic platitudes)?
- Do root causes go deeper than symptoms ("we ran late" → "why did we run late")?
- Are technical insights detailed enough to be useful in the next project?

### Completeness
- Are both positive and negative learnings captured?
- Are technical and process dimensions both covered?
- If metrics were available, are they included?
- Are significant events (scope changes, blockers, surprises) addressed?

### Balance
- Is the document balanced between what went well and what didn't?
- Are team contributions recognized in the positives?
- Is the tone constructive rather than critical of individuals?

## Output Format

```markdown
## Actionability

<Findings or "No issues found.">

## Specificity

<Findings or "No issues found.">

## Completeness

<Findings or "No issues found.">

## Balance

<Findings or "No issues found.">
```

## Example Usage

**Scenario 1: Vague improvement**
Process improvement says "communicate better." No owner, no action, no date.
Report under Actionability.

**Scenario 2: Surface-level root cause**
"What didn't go well: we were late." No analysis of why.
Report under Specificity.

**Scenario 3: Only negatives**
Document lists 6 issues and 0 positives. Even challenging projects have practices worth repeating.
Report under Balance.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
