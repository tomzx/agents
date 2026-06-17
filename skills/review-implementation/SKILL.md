---
name: review-implementation
description: Review a code implementation for correctness, quality, test coverage, security, performance, and spec alignment.
---

# Review Implementation

Audits a code implementation and reports findings across eight categories: correctness, code quality, test coverage, security, performance, spec alignment, reversibility, and forward compatibility.
Each finding is prioritized with 🔴 MUST fix, 🟡 SHOULD fix, or 🟢 MAY fix.

## Prerequisites

- Code to review provided in context, as file paths to read, or as a diff
- Specification or acceptance criteria (optional, improves alignment check)
- `.sdlc/features/FEAT-NNNN-<slug>/telemetry.md` (optional, if a telemetry plan was produced): verify analytics events are implemented correctly
- `.sdlc/features/FEAT-NNNN-<slug>/observability.md` (optional, if an observability plan was produced): verify logging, metrics, tracing, and health checks are implemented correctly
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there to the produced document

## Steps

1. Read the code thoroughly.
2. Cross-reference against the specification or acceptance criteria if provided.
3. Identify issues in each category below.
4. Prioritize each finding: 🔴 MUST, 🟡 SHOULD, 🟢 MAY.
5. Report findings using the output format. Omit categories with no findings.

## Review Checklist

### Correctness
- Does the implementation meet all acceptance criteria?
- Are edge cases and error conditions handled?
- Are there logic errors, off-by-one errors, or incorrect conditionals?
- Is state managed correctly (no races, no stale data)?

### Code Quality
- Are names clear and consistent with codebase conventions?
- Is the code DRY without premature abstraction?
- Is complexity appropriate — are there simpler alternatives?
- Is dead code or commented-out code absent?

### Test Coverage
- Is new code covered by tests?
- Are tests verifying behavior rather than implementation details?
- Do tests cover error paths and edge cases?

### Security
- Is user input validated and sanitized?
- Are there hardcoded secrets or credentials?
- Are authorization checks in place for protected operations?
- Are SQL queries parameterized?

### Performance
- Are there N+1 queries or unnecessary repeated work?
- Is caching used appropriately?
- Are there blocking operations that should be async?

### Spec Alignment
- Does the implementation match the API contract (field names, types, status codes)?
- Are all specified behaviors implemented?
- Are there behaviors implemented that are not in the spec (scope creep)?
- If a telemetry plan exists, are all analytics events emitted at the right locations with correct properties?
- If an observability plan exists, are all metrics, logs, traces, and health checks implemented per the plan?

### Reversibility
- Can we undo this cleanly if the change needs to be reverted?
- Are there irreversible side effects (destructive migrations, permanent data loss, one-way API transformations)?
- Are one-way-door design decisions called out explicitly?

### Forward Compatibility
- Can contracts and persisted data accept future additions without breaking (unknown fields tolerated, unknown enum values handled, additive-only changes)?
- Is there a versioning strategy so future evolution does not force coordinated upgrades on all consumers?
- Are extension points provided for known likely future change, or does the code bake in fixed-set assumptions?

## Output Format

```markdown
## Summary

🔴 / 🟢 <Overall assessment in one sentence.>

## Correctness

<Findings with 🔴/🟡/🟢 priority, or "No issues found.">

## Code Quality

<Findings or "No issues found.">

## Test Coverage

<Findings or "No issues found.">

## Security

<Findings or "No issues found.">

## Performance

<Findings or "No issues found.">

## Spec Alignment

<Findings or "No issues found.">

## Reversibility

<Findings or "No issues found.">

## Forward Compatibility

<Findings or "No issues found.">
```

## Example Usage

**Scenario 1: Missing error handling**
Handler returns 500 for all errors instead of specific codes defined in the spec.
🔴 MUST fix.

**Scenario 2: N+1 query**
A loop fetches user data individually for each item in a list.
🟡 SHOULD fix with a batch query.

**Scenario 3: Variable naming**
Variable `d` used instead of `discount_rate`.
🟢 MAY improve.

## Next Step

Once all 🔴 MUST findings are resolved, continue with `/create-documentation` then `/create-pr`.

## Useful Commands Reference

No CLI commands required. This skill operates on code provided in context or via file reads.
