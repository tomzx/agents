---
name: review-feasibility
description: Review a feasibility assessment for completeness, risk coverage, and soundness of the go/no-go decision.
---

# Review Feasibility Assessment

Audits a feasibility assessment and reports findings across four categories: completeness, risk coverage, decision soundness, and consistency.

## Prerequisites

- `.sdlc/features/FEAT-NNNN-<slug>/feasibility.md`, or a feasibility document provided in context or as a file path
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there to the produced document

## Steps

1. Read the feasibility document. If reading from `.sdlc/features/FEAT-NNNN-<slug>/feasibility.md`, update `status: draft` → `status: in-review` in the frontmatter before proceeding.
2. Identify issues in each of the four categories below.
3. Report findings using the output format. Omit any category that has no findings.
4. After all findings are resolved:
   - If the overall verdict is **Go** or **Go with conditions**: update `status: in-review` → `status: approved` in the frontmatter. The pipeline may proceed to `/create-requirements`.
   - If the overall verdict is **No-go**: update `status: in-review` → `status: rejected` in the frontmatter. Update the GitHub issue with findings and stop the pipeline.
   - Append unresolved open questions to `.sdlc/features/FEAT-NNNN-<slug>/questions.md` (create the file if it does not exist).

## Review Checklist

### Completeness
- Are all three dimensions (technical, financial, operational) assessed?
- Is each assessment criterion filled in, not left blank?
- Are open questions listed where information is missing?

### Risk Coverage
- Are technical risks identified concretely (not just "some risk")?
- Are cost unknowns called out explicitly?
- Are dependency risks (external services, third-party APIs) addressed?
- Are there unstated assumptions that should be recorded via `/create-assumption`?

### Decision Soundness
- Does the overall verdict logically follow from the three dimension verdicts?
- If "Go with conditions", are the conditions specific and actionable?
- If "No-go", is the rationale clear enough to revisit later if conditions change?
- Is the effort estimate realistic given the scope described in the issue?

### Consistency
- Do the verdicts within each dimension match the assessment details?
- Is the feature scope consistent with the original issue?
- Are there contradictions between dimensions (e.g., "high integration complexity" but verdict "Feasible" without conditions)?

## Output Format

```markdown
## Completeness

<Findings or "No issues found.">

## Risk Coverage

<Findings or "No issues found.">

## Decision Soundness

<Findings or "No issues found.">

## Consistency

<Findings or "No issues found.">
```

## Example Usage

**Scenario 1: Missing risk identification**
Technical feasibility says "Integration complexity: High" but the verdict is "Feasible" without any conditions. Flag under Consistency.

**Scenario 2: Vague conditions**
Overall verdict is "Go with conditions" but the only condition is "need to figure out infra." Flag under Decision Soundness: specify what infrastructure and by when.

**Scenario 3: Unstated assumption**
Financial feasibility assumes zero third-party costs, but the feature requires sending email. Flag under Risk Coverage: record as an assumption.

## Next Step

Once all findings are resolved and `status` is set to `approved`, continue with `/create-requirements`.
If `status` is `rejected`, update the issue and stop the pipeline.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
