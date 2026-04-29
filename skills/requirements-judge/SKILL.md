---
name: requirements-judge
description: Review a formal specification for completeness, consistency, and testability before implementation begins.
---

# Requirements Judge

Audits a formal specification produced by the Requirements Analyst and either approves it or returns a prioritized list of deficiencies that must be resolved before design begins.

## Prerequisites

- Formal specification document available in context or as a file path

## Steps

1. Read the entire specification.
2. Check each requirement against the criteria below.
3. Produce an approval decision or a deficiency report.

## Review Criteria

### Completeness
- Does every acceptance criterion cover the happy path, edge cases, and failure modes?
- Are all user roles and their permissions accounted for?
- Are error states and recovery paths specified?

### Consistency
- Do any two requirements contradict each other?
- Are terms used uniformly throughout (no synonym drift)?
- Do non-functional requirements align with the functional ones (e.g., a "real-time" feature with a 10-second polling NFR)?

### Testability
- Can every acceptance criterion be verified by a test (automated or manual)?
- Are criteria stated in measurable terms, not subjective ones ("fast", "intuitive")?

### Scope
- Does any requirement creep beyond what was asked for?
- Are deferred items clearly marked out-of-scope?

## Output Format

```markdown
## Verdict: APPROVED | NEEDS REVISION

## Deficiencies

### D-1: <Title> [BLOCKER | MAJOR | MINOR]
**Location:** FR-X / NFR-X
**Issue:** What is wrong.
**Required action:** What must change before approval.

(repeat for each deficiency)

## Notes

Optional observations that do not block approval but are worth addressing.
```

## Example Usage

**Scenario 1: Spec approved**
All acceptance criteria are measurable, no contradictions found, edge cases covered.
Output: `Verdict: APPROVED` with minor note about clarifying error message wording.

**Scenario 2: Spec needs revision**
FR-3 acceptance criterion says "should be fast" with no metric; NFR-2 conflicts with FR-1 timeout.
Output: `Verdict: NEEDS REVISION` — D-1 BLOCKER (untestable criterion), D-2 MAJOR (contradiction).
