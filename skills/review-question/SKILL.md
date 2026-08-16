---
name: review-question
description: Review a question record for specificity, answerability, impact, and resolution quality, then record the answer and set the lifecycle status.
argument-hint: "[question document or file path]"
---

# Review Question

Audits a question record and reports findings across five categories: specificity, context, answerability, impact and urgency, and resolution quality.
When an answer is available, records it in the Answer section and closes the question.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- `.sdlc/knowledge/questions/N-<slug>.md`, or a question document provided in context or as a file path

## Steps

1. Read the question document.
2. Evaluate it against the checklist below.
3. Report findings by category. Omit categories with no findings.
4. After the review, update `status` in frontmatter to the appropriate value: `Resolved` (answer recorded in the Answer section), `Deferred` (cannot be answered yet; risk acknowledged and a revisit date set), or `Dismissed` (no longer relevant; reason recorded in the Answer section). Leave `Open` when no resolution applies yet.

## Review Checklist

### Specificity
- Is the question stated so a named source could answer it directly?
- Does it name concrete scope (which system, which plan, which environment)?
- Is the status field present and accurate (Open | Resolved | Deferred | Dismissed)?

### Context
- Does the context say which feature, artifact, or phase surfaced the question?
- Is it clear why the answer matters to that work?

### Answerability
- Is an answerer named (person, team, vendor) or an authoritative source (document, experiment)?
- Is the channel or method for obtaining the answer described?
- If the question is answerable from the codebase or docs alone, is a tracked record even needed?

### Impact and Urgency
- Is the blocking level (High / Medium / Low) justified by the description?
- Does the record name the artifact, decision, or task that waits on the answer?
- Is a needed-by date or milestone present, and is an overdue date flagged?

### Resolution Quality
- If status is Resolved: does the Answer section answer the question as asked?
- Is the answer's source and date recorded?
- If the answer requires choosing between options, is the decision recorded via `/create-decision` and linked?
- If work proceeds on the unverified answer, is it promoted via `/create-assumption` and linked?

## Output Format

```markdown
## Specificity

<Findings or "No issues found.">

## Context

<Findings or "No issues found.">

## Answerability

<Findings or "No issues found.">

## Impact and Urgency

<Findings or "No issues found.">

## Resolution Quality

<Findings or "No issues found." (or "Not applicable: question still Open.")>
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; the subject passes review |
| `changes-requested` | Findings the author must address before it passes |
| `rejected` | Fundamental flaw requiring rework or stopping |

## Example Usage

**Scenario 1: Unanswerable as written**
Question says "what about compliance?" with no scope.
Report under Specificity: restate so a named source can answer directly (e.g., "Does EU user data require residency guarantees under the current data processing agreement?").

**Scenario 2: No answerer named**
Context and impact are clear, but no one is identified to ask.
Report under Answerability: name the person, team, or source that holds the answer.

**Scenario 3: Answer that dodges the question**
Status is Resolved, but the Answer section discusses adjacent work without answering what was asked.
Report under Resolution Quality: reopen (status `Open`) or record the actual answer with its source.

**Scenario 4: Overdue with no consequence named**
The needed-by date passed a week ago and blocking is High.
Report under Impact and Urgency: flag the overdue date, or promote via `/create-assumption` if work proceeded without the answer.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
