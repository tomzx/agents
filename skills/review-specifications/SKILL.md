---
name: review-specifications
description: Review a technical specification for ambiguities, inconsistencies, incoherences, missing information, and implementability concerns.
---

# Review Specifications

Audits a technical specification and reports findings across five categories: ambiguities, inconsistencies, incoherences, missing information, and implementability.

## Prerequisites

- A technical specification document provided in context or as a file path to read
- Requirements document (optional, improves coverage analysis)

## Steps

1. Read the specification thoroughly.
2. Cross-reference against the requirements document if provided.
3. Identify issues in each of the five categories below.
4. Report findings. Omit any category that has no findings.

## Review Checklist

### Ambiguities
- Are field names and types unambiguous?
- Are behavior descriptions precise (no "it should handle errors appropriately")?
- Are state transitions and edge-case handling clearly defined?

### Inconsistencies
- Do data models match the API contracts (field names, types)?
- Are field names consistent across endpoints and schemas?
- Do sequence diagrams match the described API behavior?

### Incoherences
- Do any stated technical decisions contradict each other?
- Is the architecture consistent with the stated constraints?
- Are there self-contradictory statements within a single section?

### Missing Information
- Are all requirements from the requirements document addressed?
- Are error cases and edge conditions handled?
- Are authentication and authorization requirements specified?
- Are performance targets and SLAs stated?

### Implementability
- Are there design choices that are impractical or unnecessarily complex?
- Are there circular dependencies or unresolvable constraints?
- Are external dependencies clearly defined with their interfaces?

## Output Format

```markdown
## Ambiguities

<Findings or "No issues found.">

## Inconsistencies

<Findings or "No issues found.">

## Incoherences

<Findings or "No issues found.">

## Missing Information

<Findings or "No issues found.">

## Implementability

<Findings or "No issues found.">
```

## Example Usage

**Scenario 1: Mismatched schema**
API contract says `user_id: string` but data model defines `id: uuid`.
Report under Inconsistencies.

**Scenario 2: Unspecified auth**
Spec defines endpoints that modify user data but never mentions authentication or authorization rules.
Report under Missing Information.

**Scenario 3: Unnecessary complexity**
Spec requires a distributed lock for a feature that could use a simple DB transaction.
Report under Implementability.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
