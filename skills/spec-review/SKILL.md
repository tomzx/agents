---
name: spec-review
description: Review a specification to identify ambiguities, inconsistencies, incoherences, and missing information.
---

# Review Specification

Audits a specification document and reports findings across four categories: ambiguities, inconsistencies, incoherences, and missing information.

## Prerequisites

- A specification document provided in context or accessible for reading

## Steps

1. Read the specification thoroughly.
2. Identify issues in each of the four categories below.
3. Report findings using the output format. Omit any section that has no findings.

## Output Format

```markdown
## Ambiguities

Terms, statements, or requirements that could be interpreted in more than one way.

## Inconsistencies

Contradictions or conflicts between different parts of the specification.

## Incoherences

Statements that do not logically follow or are self-contradictory within context.

## Missing Information

Requirements, edge cases, or constraints that are absent but necessary for a complete implementation.
```

## Example Usage

**Scenario 1: API specification**
Spec says "returns a list of users" in one place and "returns a paginated response" in another without reconciling the two. Report under Inconsistencies.

**Scenario 2: Authentication spec**
Spec states "the user must be authenticated" but never defines what authentication looks like or how tokens are validated. Report under Missing Information.

**Scenario 3: Data format spec**
Spec uses "timestamp" in some places and "datetime" in others without clarifying whether they refer to the same type. Report under Ambiguities.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
