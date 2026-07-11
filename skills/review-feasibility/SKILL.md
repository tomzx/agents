---
name: review-feasibility
description: Review a feasibility assessment for completeness, risk coverage, and soundness of the go/no-go decision.
---

# Review Feasibility Assessment

Audits a feasibility assessment and reports findings across five categories: completeness, risk coverage, decision soundness, consistency, and reversibility.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/feasibility.md`, or a feasibility document provided in context or as a file path

## Steps

1. Read the feasibility document from `.sdlc/features/N-<slug>/feasibility.md` if present, otherwise from context or as a file path.
2. Identify issues in each of the five categories below.
3. Report findings using the output format. Omit any category that has no findings.
4. Write the findings to `.sdlc/features/N-<slug>/review-feasibility.md` with frontmatter `artifact: feasibility`, `verdict` (`approved` if the overall verdict is Go or Go with conditions, `rejected` if No-go, `changes-requested` if the author must address findings), and `reviewed_at: <ISO date>`, and the findings as the body, per `skills/sdlc/references/shared.md`. Record any unresolved open questions in the findings body.
   - If the overall verdict is **No-go**: also update the GitHub issue with the findings and stop the pipeline.

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

### Reversibility
- If we proceed and it fails, can we undo this cleanly and back out?
- Does the assessment identify one-way-door commitments (sunk costs, irreversible integrations, data migrations)?
- For "Go with conditions", do the conditions include an exit or rollback strategy?

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

## Reversibility

<Findings or "No issues found.">
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; the subject passes review |
| `changes-requested` | Findings the author must address before it passes |
| `rejected` | Fundamental flaw requiring rework or stopping |

## Example Usage

**Scenario 1: Missing risk identification**
Technical feasibility says "Integration complexity: High" but the verdict is "Feasible" without any conditions. Flag under Consistency.

**Scenario 2: Vague conditions**
Overall verdict is "Go with conditions" but the only condition is "need to figure out infra." Flag under Decision Soundness: specify what infrastructure and by when.

**Scenario 3: Unstated assumption**
Financial feasibility assumes zero third-party costs, but the feature requires sending email. Flag under Risk Coverage: record as an assumption.

## Next Step

Once the findings verdict is `approved`, continue with `/create-specifications`.
If the findings verdict is `rejected`, update the issue and stop the pipeline.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
