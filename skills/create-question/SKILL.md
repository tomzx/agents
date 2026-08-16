---
name: create-question
description: Record an open question with its context, who can answer it, what it blocks, and when the answer is needed.
argument-hint: "[question or topic]"
---

# Create Question

Records an open question surfaced during the pipeline: what is being asked, the context where it arose, who can answer it, what work stalls without the answer, and when the answer is needed.

Questions differ from assumptions and decisions: an assumption is a belief held without verification; a decision is a deliberate choice between options; a question is missing information that a specific person, team, or source can supply.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- A question worth tracking: it blocks or shapes work, and the answer is not immediately available
- Enough context to say where it arose and who can answer it

## Steps

1. State the question clearly and specifically, so a named source could answer it as written.
2. Describe the context: which feature, artifact, or phase surfaced it, and why the answer matters.
3. Identify the answerer: who (person, team, vendor) or what (document, experiment) can answer, and how they will be reached.
4. Assess what is blocked while the question stays open: which artifact, decision, or task waits on it.
5. Set a needed-by date or milestone after which the block becomes costly.
6. Save the document to `.sdlc/knowledge/questions/` using the filename pattern `N-<slug>.md` where `N` is the next available number (counting existing files in that directory).

When the answer arrives, record it via `/review-question`. When the answer cannot be obtained in time and work proceeds on a belief instead, promote the question to an assumption via `/create-assumption`. When the answer requires choosing between options, record the choice via `/create-decision` and link it from the question.

## Output Format

Use the template at `skills/sdlc/templates/knowledge/question.md` (copied to `.sdlc/templates/knowledge/question.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write the result to the artifact path named in the steps above.

## Example Usage

**Scenario 1: Scope question to a stakeholder**
Question: which export formats must the first release support, PDF only or CSV too?
Context: surfaced by `/create-requirements` for FEAT-12; the data layer differs per format.
Answered by: the product owner, in Thursday's sync.
Impact if unanswered: export module specification is blocked (High).
Needed by: sprint planning on 2026-08-20.

**Scenario 2: External dependency question**
Question: does the payment provider support multi-currency refunds on the plan we purchased?
Context: surfaced by `/create-feasibility` for FEAT-8.
Answered by: vendor support, via the account channel.
Impact if unanswered: refund flow stays generic in the specification (Medium).
Needed by: before specification review.

**Scenario 3: Question that becomes an assumption**
Question: will the database migration finish before the launch freeze? No answer by the needed-by date.
Promoted via `/create-assumption` (work proceeds assuming the migration completes on time), then resolved via `/review-question` with a link to the assumption.

## Completion Checklist

Before handing off to review, confirm:

- [ ] The question is answerable as written (a named source could answer it directly)
- [ ] The needed-by date or milestone is set, and the blocked work is named

Self-check the record against the [`review-question` checklist](../review-question/SKILL.md) and fix what you can, so review finds less to flag.

## Useful Commands Reference

No CLI commands required. This skill operates on information provided in context and writes a Markdown file.
