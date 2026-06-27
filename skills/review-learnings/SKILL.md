---
name: review-learnings
description: Review a learnings document for actionability, specificity, completeness, and balance.
---

# Review Learnings

Audits a learnings document and reports findings across four categories: actionability, specificity, completeness, and balance.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/knowledge/learnings/NNNN-<slug>.md`, or a learnings document provided in context or as a file path

## Steps

1. Read the learnings document. If reading from `.sdlc/knowledge/learnings/NNNN-<slug>.md`, update `status: draft` → `status: in-review` in the frontmatter before proceeding.
2. Evaluate it against the checklist below.
3. Report findings by category. Omit categories with no findings.
4. After all findings are resolved: update `status: in-review` → `status: complete` in the frontmatter.

## Review Checklist

### Actionability
- Do process improvements have a concrete action, an owner, and a target date?
- Are action items specific enough to execute without further clarification?
- Are improvements measurable so progress can be tracked?

### Specificity
- Are observations specific to this project or sprint (not generic platitudes)?
- Do root causes go deeper than symptoms ("we ran late" → "why did we run late")?
- Are technical insights detailed enough to be useful in the next project?

### Completeness
- Are both positive and negative learnings captured?
- Are technical and process dimensions both covered?
- If metrics were available, are they included?
- Are significant events (scope changes, blockers, surprises) addressed?

### Balance
- Is the document balanced between what went well and what didn't?
- Are team contributions recognized in the positives?
- Is the tone constructive rather than critical of individuals?

## Output Format

```markdown
## Actionability

<Findings or "No issues found.">

## Specificity

<Findings or "No issues found.">

## Completeness

<Findings or "No issues found.">

## Balance

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

**Scenario 1: Vague improvement**
Process improvement says "communicate better." No owner, no action, no date.
Report under Actionability.

**Scenario 2: Surface-level root cause**
"What didn't go well: we were late." No analysis of why.
Report under Specificity.

**Scenario 3: Only negatives**
Document lists 6 issues and 0 positives. Even challenging projects have practices worth repeating.
Report under Balance.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
