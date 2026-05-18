---
name: review-plan
description: Review an implementation plan for completeness, feasibility, dependency coverage, and risk assessment.
---

# Review Plan

Audits an implementation plan and reports findings across five categories: completeness, feasibility, dependencies, risk coverage, and timeline realism.

## Prerequisites

- `.sdlc/features/FEAT-NNNN-<slug>/plan.md`, or an implementation plan provided in context or as a file path
- `.sdlc/features/FEAT-NNNN-<slug>/specification.md` (optional, improves coverage analysis)
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there to the produced document

## Steps

1. Read the plan. If reading from `.sdlc/features/FEAT-NNNN-<slug>/plan.md`, update `status: draft` → `status: in-review` in the frontmatter before proceeding.
2. Cross-reference against the specification or requirements if available.
3. Identify issues in each category below.
4. Report findings. Omit any category that has no findings.
5. After all findings are resolved: update `status: in-review` → `status: approved` in the frontmatter. Append unresolved open questions to `.sdlc/features/FEAT-NNNN-<slug>/questions.md` (create the file if it does not exist). For any question that carries meaningful risk to the implementation, also invoke `/create-assumption` to record it formally.

## Review Checklist

### Completeness
- Does the plan cover all requirements and spec deliverables?
- Are all phases clearly defined with success criteria?
- Are setup, deployment, and rollout steps included?

### Feasibility
- Are effort estimates realistic for the described work?
- Does the plan account for ramp-up, reviews, and integration work?
- Are milestones achievable within the stated constraints?

### Dependencies
- Are all internal and external dependencies identified?
- Are critical-path dependencies clearly marked?
- Is there a contingency for delayed or unavailable dependencies?

### Risk Coverage
- Are the most significant risks captured in the risk register?
- Does each risk have a concrete mitigation strategy?
- Are there single points of failure not mentioned as risks?

### Timeline Realism
- Is the timeline consistent with the effort estimates?
- Are there parallel tracks that could reduce total duration?
- Are buffer periods included for testing and review?

## Output Format

```markdown
## Completeness

<Findings or "No issues found.">

## Feasibility

<Findings or "No issues found.">

## Dependencies

<Findings or "No issues found.">

## Risk Coverage

<Findings or "No issues found.">

## Timeline Realism

<Findings or "No issues found.">
```

## Example Usage

**Scenario 1: Missing rollout step**
Plan ends at "integration testing complete" with no deployment or rollout phase.
Report under Completeness.

**Scenario 2: Underestimated effort**
Phase 2 (API + auth) is estimated at 1 day for a spec that describes 8 endpoints with complex permission logic.
Report under Feasibility.

**Scenario 3: Unmitigated critical dependency**
Plan depends on a third-party API but lists no spike or contingency if that API is unavailable.
Report under Risk Coverage.

## Next Step

Once all findings are resolved and `status` is set to `approved`, run `/publish-plan` to commit the plan and open a draft PR for author sign-off, then continue with `/create-tasks-decomposition`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
