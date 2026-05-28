---
name: review-existing-solutions
description: Review an existing solutions survey for search coverage, evaluation rigor, accuracy, due diligence, and a sound build-versus-adopt recommendation.
---

# Review Existing Solutions Survey

Audits an existing solutions survey and reports findings across five categories: coverage, evaluation rigor, accuracy, due diligence, and recommendation soundness.

## Prerequisites

- `.sdlc/features/FEAT-NNNN-<slug>/existing-solutions.md`, or a survey document provided in context or as a file path
- `.sdlc/features/FEAT-NNNN-<slug>/requirements.md` (optional, improves coverage analysis)
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there to the produced document

## Steps

1. Read the survey. If reading from `.sdlc/features/FEAT-NNNN-<slug>/existing-solutions.md`, update `status: draft` → `status: in-review` in the frontmatter before proceeding.
2. Cross-reference against the requirements document if available.
3. Identify issues in each of the five categories below.
4. Report findings. Omit any category that has no findings.
5. After all findings are resolved: update `status: in-review` → `status: approved` in the frontmatter. Append unresolved open questions to `.sdlc/features/FEAT-NNNN-<slug>/questions.md` (create the file if it does not exist). For any question that carries meaningful risk, also invoke `/create-assumption` to record it formally. For a chosen adopt-or-build direction with lasting consequences, invoke `/create-decision`.

## Review Checklist

### Coverage
- Was the internal codebase searched before reaching for external options?
- Are the obvious open-source and commercial candidates present, or are well-known options missing?
- Does the survey map candidates back to the functional and non-functional requirements?

### Evaluation Rigor
- Is each strong candidate evaluated on strengths, weaknesses, integration effort, cost, and risk?
- Are gaps between a candidate and the requirements stated explicitly?
- Are claims backed by the candidate's docs or source rather than assumption?

### Accuracy
- Are licenses, maturity, and maintenance status current and correct?
- Are links valid and pointing at the right project?
- Are version-specific claims tied to a version?

### Due Diligence
- Are license compatibility and security posture considered for adopt candidates?
- Are maintenance health and lock-in risk assessed?
- For commercial options, is cost (and its scaling) accounted for?

### Recommendation Soundness
- Does the recommended direction follow from the evaluation, or contradict it?
- If building, is the reason existing options fall short stated clearly?
- Are sources of information captured so the design can reuse proven patterns even when not adopting?

## Output Format

```markdown
## Coverage

<Findings or "No issues found.">

## Evaluation Rigor

<Findings or "No issues found.">

## Accuracy

<Findings or "No issues found.">

## Due Diligence

<Findings or "No issues found.">

## Recommendation Soundness

<Findings or "No issues found.">
```

## Example Usage

**Scenario 1: Missing an obvious option**
The survey for a JSON schema validator omits the de facto standard library.
Report under Coverage.

**Scenario 2: License overlooked**
The recommendation is to adopt a GPL library into a proprietary product without flagging the license conflict.
Report under Due Diligence.

**Scenario 3: Recommendation contradicts evaluation**
Every candidate is rated a poor fit, yet the recommendation is to adopt one anyway with no rationale.
Report under Recommendation Soundness.

## Next Step

Once all findings are resolved and `status` is set to `approved`, continue with `/create-specifications`.

## Useful Commands Reference

| Command | Description |
|---|---|
| `WebFetch` | Re-check a candidate's license, version, or maintenance status |
| `WebSearch` | Verify that no well-known option was missed |
