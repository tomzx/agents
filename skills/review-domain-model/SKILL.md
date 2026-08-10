---
name: review-domain-model
description: Review a domain model for entity coverage, relationship correctness, vocabulary consistency, invariant validity, boundary clarity, and alignment with the domain context.
---

# Review Domain Model

Audits a domain model and reports findings across six categories: entity coverage, relationship correctness, vocabulary consistency, invariant validity, boundary clarity, and context alignment.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the most recently created domain model under `.sdlc/features/`.
- The domain model document, or a domain model provided in context or as a file path
- Relevant requirements, specification, or architecture documents (optional, improves coverage and alignment analysis)
- `.sdlc/context/vocabulary.md` (optional, improves vocabulary consistency analysis)

## Steps

1. Read the domain model from its artifact path if present, otherwise from context or as a file path.
2. Cross-reference against available requirements, specification, or architecture documents to confirm entities and quantities cover the relevant domain.
3. Identify issues in each of the six categories below.
4. Report findings. Omit any category that has no findings.
5. Write the findings beside the domain model with frontmatter `artifact: domain-model`, `verdict` (`approved` if there are no blocking findings, `changes-requested` if the author must address findings, `rejected` for a fundamental flaw), and `reviewed_at: <ISO date>`, and the findings as the body, per `skills/sdlc/references/shared.md`. Record any unresolved open questions in the findings body.

## Review Checklist

### Entity Coverage
- Are all entities mentioned in the domain context represented?
- Are there nouns in the requirements or specification that are doing work but have no entity entry?
- Are entities distinct, or do two entries describe the same thing?

### Relationship Correctness
- Are cardinalities correct and consistent in both directions?
- Are relationships between entities that actually interact, or are any spurious?
- Are governing constraints on relationships stated?

### Vocabulary Consistency
- Does the glossary reuse terms from `.sdlc/context/vocabulary.md` rather than redefining them?
- Are overloaded terms (one word, two meanings) disambiguated?
- Is the same concept referred to by a single term throughout, or are synonyms causing confusion?

### Invariant Validity
- Are invariants genuinely always-true domain rules, not implementation choices?
- Are they testable (could you write a check that fails if the invariant breaks)?
- Are any "invariants" actually default behaviors with known exceptions?

### Boundary Clarity
- Is it clear what is in this domain versus adjacent domains?
- Do boundaries align with the feature scope, or has the model drifted beyond it?

### Framing Alignment
- Do the key quantities map to the impact claims and success criteria in the available context?
- Does the model cover the domain the requirements describe, or only part of it?

## Output Format

```markdown
## Entity Coverage

<Findings or "No issues found.">

## Relationship Correctness

<Findings or "No issues found.">

## Vocabulary Consistency

<Findings or "No issues found.">

## Invariant Validity

<Findings or "No issues found.">

## Boundary Clarity

<Findings or "No issues found.">

## Framing Alignment

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

**Scenario 1: Missing entity**
The requirements repeatedly refer to "shipments" but the model has no shipment entity. Flag under Entity Coverage.

**Scenario 2: Redefined project term**
The glossary redefines "tenant" differently from `.sdlc/context/vocabulary.md`. Flag under Vocabulary Consistency: reuse the project term or explicitly note the divergence.

**Scenario 3: Invariant with exceptions**
An "invariant" says "every order has exactly one payment method" but split payments are known to exist. Flag under Invariant Validity.

**Scenario 4: Drift beyond scope**
The model includes a full billing subsystem when the feature is only about export latency. Flag under Boundary Clarity.

## Next Step

If the findings verdict is `changes-requested`, revise the model and re-run this review.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
