---
name: review-assumption
description: Review an assumption record for specificity, basis quality, risk assessment, and validation plan adequacy.
argument-hint: "[assumption document or file path]"
---

# Review Assumption

Audits an assumption record and reports findings across four categories: specificity, basis quality, risk assessment, and validation plan adequacy.

## Prerequisites

- `.sdlc/knowledge/assumptions/NNNN-<slug>.md`, or an assumption document provided in context or as a file path

## Steps

1. Read the assumption document.
2. Evaluate it against the checklist below.
3. Report findings by category. Omit categories with no findings.
4. After the review, update `status` in frontmatter to the appropriate terminal value: `Validated` (assumption confirmed), `Invalidated` (assumption disproved — flag affected work), or `Deferred` (cannot yet be verified).

## Review Checklist

### Specificity
- Is the assumption statement specific enough to be falsifiable?
- Does it name concrete scope (which users, which load, which environment)?
- Is the status field present and accurate?

### Basis Quality
- Is there stated evidence or reasoning supporting the assumption?
- Is the confidence level consistent with the quality of the basis?
- If the basis is weak or absent, is that acknowledged rather than hidden?

### Risk Assessment
- Is the impact level (High / Medium / Low) justified by the description?
- Does the risk description name specific components or flows that depend on the assumption?
- Are downstream assumptions or decisions that inherit this risk identified?

### Validation Plan
- Is a concrete validation method described (not just "we'll check later")?
- Is there a named owner responsible for validation?
- Is there a deadline or milestone tied to validation?
- If the assumption cannot be validated before implementation, is that risk acknowledged?

## Output Format

```markdown
## Specificity

<Findings or "No issues found.">

## Basis Quality

<Findings or "No issues found.">

## Risk Assessment

<Findings or "No issues found.">

## Validation Plan

<Findings or "No issues found.">
```

## Example Usage

**Scenario 1: Unfalsifiable statement**
Assumption says "the system will be fast enough." No metric, no context.
Report under Specificity: restate with a measurable threshold (e.g., "p99 latency under 300ms for search queries under normal load").

**Scenario 2: High confidence, weak basis**
Confidence is marked High but the basis is "we think this is probably true."
Report under Basis Quality: confidence should be Medium or Low, or the basis must be strengthened.

**Scenario 3: High impact, no dependencies named**
Impact is High but the description only says "things would break."
Report under Risk Assessment: name the specific components, decisions, or flows that depend on this assumption.

**Scenario 4: Validation with no owner or deadline**
Validation plan says "run a load test at some point."
Report under Validation Plan: assign an owner and a deadline or milestone.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
