---
name: validator
description: Confirm an implementation satisfies every requirement and acceptance criterion in the approved specification.
---

# Validator

Traces each requirement from the approved specification to its implementation, runs acceptance tests, and produces a validation report marking each criterion as pass, fail, or partial.

## Prerequisites

- Approved specification (with acceptance criteria) available in context or as a file path
- Running build of the implementation accessible (locally or via URL)
- Test suite available

## Steps

1. Read the approved specification and list every acceptance criterion.
2. For each criterion:
   a. Locate the implementation that addresses it (file and function).
   b. Run the corresponding acceptance test or verify manually.
   c. Mark: **PASS**, **FAIL**, or **PARTIAL** (implemented but criterion not fully met).
3. Flag any requirement with no corresponding implementation.
4. Produce the validation report.

## Output Format

```markdown
## Validation Report

**Spec version:** <identifier or date>
**Build:** <branch or commit SHA>
**Date:** <ISO 8601>

### Results

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| FR-1 | <description> | PASS/FAIL/PARTIAL | Evidence or gap description |

### Gaps

Requirements not met, with detail on what is missing.

### Verdict: VALIDATED | NOT VALIDATED
```

## Example Usage

**Scenario 1: All criteria met**
Spec has 8 acceptance criteria. All 8 map to implementations; all acceptance tests pass.
Output: `Verdict: VALIDATED`.

**Scenario 2: Gap found**
FR-4 requires the export to support JSON format. Only CSV is implemented.
Output: FR-4 marked FAIL; `Verdict: NOT VALIDATED` with gap detail.

**Scenario 3: Partial implementation**
NFR-2 requires p99 < 200 ms. Load test shows p99 at 350 ms.
Output: NFR-2 marked PARTIAL; verdict NOT VALIDATED.
