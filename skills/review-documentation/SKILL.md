---
name: review-documentation
description: Review documentation for completeness, accuracy, clarity, usability, and structure.
---

# Review Documentation

Audits documentation and reports findings across five categories: completeness, accuracy, clarity, usability, and structure.

## Prerequisites

- Documentation provided in context or as a file path to read
- The feature or component being documented (for accuracy checking, if accessible)
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there to the produced document

## Steps

1. Read the documentation thoroughly.
2. Compare it against the feature or component being documented, if accessible.
3. Identify issues in each category below.
4. Report findings. Omit categories with no findings.

## Review Checklist

### Completeness
- Are all public APIs, configuration options, and interfaces documented?
- Are common use cases covered?
- Are error conditions and failure modes documented?
- Is there a getting-started or onboarding path for new users?

### Accuracy
- Are code examples correct and runnable?
- Are parameter types, defaults, and constraints accurately stated?
- Does the described behavior match the actual implementation?
- Are version-specific behaviors called out?

### Clarity
- Is the intended audience clear?
- Are concepts explained before they are used?
- Is jargon avoided or defined on first use?
- Are examples concrete and relevant to real use cases?

### Usability
- Can a user find what they need without reading end-to-end?
- Are there clear headings and a logical flow?
- Are related sections cross-referenced?
- Is the getting-started path achievable in under 10 minutes?

### Structure
- Does the documentation follow the Divio framework (tutorial / how-to / reference / explanation)?
- Is reference documentation separated from conceptual content?
- Are code blocks used for all code, commands, and file paths?

## Output Format

```markdown
## Completeness

<Findings or "No issues found.">

## Accuracy

<Findings or "No issues found.">

## Clarity

<Findings or "No issues found.">

## Usability

<Findings or "No issues found.">

## Structure

<Findings or "No issues found.">
```

## Example Usage

**Scenario 1: Outdated example**
The getting-started guide uses a deprecated API method replaced in v2.
Report under Accuracy.

**Scenario 2: No error documentation**
Reference lists all method parameters but never mentions which errors each method can throw.
Report under Completeness.

**Scenario 3: Mixed content**
Reference section contains conceptual explanations that belong in an Explanation section.
Report under Structure.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
