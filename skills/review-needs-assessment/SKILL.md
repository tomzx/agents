---
name: review-needs-assessment
description: Review a needs assessment for evidence rigor, stakeholder coverage, alternative-path completeness, and verdict soundness.
---

# Review Needs Assessment

Audits a needs assessment and reports findings across four categories: evidence rigor, stakeholder coverage, alternative-path completeness, and verdict soundness.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/needs-assessment.md`, or a needs assessment document provided in context or as a file path

## Steps

1. Read the needs assessment document from `.sdlc/features/N-<slug>/needs-assessment.md` if present, otherwise from context or as a file path.
2. Identify issues in each of the four categories below.
3. Report findings using the output format. Omit any category that has no findings.
4. Write the findings to `.sdlc/features/N-<slug>/review-needs-assessment.md` with frontmatter `artifact: needs-assessment`, `verdict` (`approved` if the overall verdict is Needed or Nice-to-have, `rejected` if Not needed, `changes-requested` if the author must address findings), and `reviewed_at: <ISO date>`, and the findings as the body, per `skills/sdlc/references/shared.md`. Record any unresolved open questions in the findings body.
   - If the overall verdict is **Not needed**: also update the GitHub issue with the findings and stop the pipeline.

## Review Checklist

### Evidence Rigor
- Is the problem stated as a problem (not a solution)?
- Is evidence drawn from concrete sources (tickets, data, feedback) or is it purely assumed?
- If evidence is Weak or None, is this explicitly flagged as an open question?
- Are there evidence sources that were not checked but should have been (support logs, analytics, user interviews)?

### Stakeholder Coverage
- Are all affected stakeholder groups identified, not just the most vocal?
- Is it clear who benefits and who is inconvenienced by the current state?
- Are edge-case stakeholders (admin, internal tools, accessibility) considered?

### Alternative-Path Completeness
- Were existing features, configuration, documentation, and process changes considered?
- Is the assessment of each alternative fair (not dismissed too quickly)?
- If the need can be met without new code, is there a clear rationale for why new code is still proposed?

### Verdict Soundness
- Does the verdict logically follow from the dimension ratings?
- If "Nice-to-have", is it clear what additional evidence would elevate it to "Needed"?
- If "Not needed", is the rationale clear enough to revisit if conditions change?
- Are the conditions to proceed specific and actionable (not vague)?
- Is strategic alignment assessed against the project's actual stated goals?

## Output Format

```markdown
## Evidence Rigor

<Findings or "No issues found.">

## Stakeholder Coverage

<Findings or "No issues found.">

## Alternative-Path Completeness

<Findings or "No issues found.">

## Verdict Soundness

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

**Scenario 1: Solution disguised as problem**
The needs assessment states "We need a bulk export button" but the problem statement just restates the solution. Flag under Evidence Rigor: the underlying problem (users spend too much time exporting one by one) is not articulated.

**Scenario 2: Missing stakeholder**
Stakeholder table lists "end users" but the feature changes an admin workflow. Flag under Stakeholder Coverage.

**Scenario 3: Alternative dismissed without reasoning**
Alternative paths mention an existing CSV export feature but dismiss it as "limited" without explaining what is missing. Flag under Alternative-Path Completeness.

**Scenario 4: Weak evidence, strong verdict**
Evidence rating is Weak but the verdict is Needed. Flag under Verdict Soundness: either gather more evidence or downgrade to Nice-to-have.

## Next Step

Once the findings verdict is `approved`, continue with `/create-requirements`.
If the findings verdict is `rejected`, update the issue and stop the pipeline.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
