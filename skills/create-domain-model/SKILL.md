---
name: create-domain-model
description: Capture the entities, relationships, glossary, invariants, and key quantities of a domain so it is understood structurally before solutioning. Use when the user says /create-domain-model, "model this domain", "what are the entities here", "I do not understand this problem space", or enters an unfamiliar domain during design or architecture work. A standalone skill invoked as a one-off, typically during the design or architecture process.
argument-hint: "[context-or-path]"
---

# Create Domain Model

Captures the structure of a domain: the entities that matter, how they relate, the precise meaning of each term, the rules that always hold, and the quantities the problem turns on.
It makes an unfamiliar domain legible before solutioning, and gives requirements and specifications a shared vocabulary.
It is a one-off skill, most useful when entering an unfamiliar domain during the design or architecture process.
It is richer than the project-level `.sdlc/context/vocabulary.md`, which it reuses rather than redefines.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If working within a feature, locate its directory under `.sdlc/features/N-<slug>/`.
- Read `.sdlc/context/vocabulary.md` if present, and reuse its terms instead of redefining them
- Read any relevant requirements, specification, or architecture documents for context

## Steps

1. Read available context (requirements, specification, architecture, vocabulary) to identify the domain.
2. Read `.sdlc/context/vocabulary.md` if present. Reuse existing project terms; only add terms that are specific to this domain and not already defined.
3. Identify the **core entities**: the nouns in the domain that carry meaning (people, things, events, records, concepts). Capture each with a short description and the attributes that matter.
4. Identify the **relationships** between entities, with cardinality (one-to-one, one-to-many, many-to-many) and any constraint or rule that governs the relationship. Render the entity model as a Mermaid `classDiagram`: one class per entity with its key attributes, edges carrying cardinality, and each invariant attached as a `note` on the entity it constrains.
5. Build a **glossary**: give each term a precise definition, and disambiguate any overloaded term (one word used two ways). Note where a term differs from general usage.
6. State **invariants**: rules that always hold in this domain (business rules, constraints, identities). These are testable truths, not implementation details.
7. Identify the **key quantities and metrics** the domain turns on, why each matters, and its current value if known.
8. Define **boundaries**: what is in this domain versus adjacent domains it touches but does not model.
9. Record **open questions** where the model is uncertain.
10. Write the output to `domain-model.md` under the relevant feature directory (`.sdlc/features/N-<slug>/domain-model.md`), or to a path provided by the user.

## Output Format

Use the template at `skills/sdlc/templates/features/domain-model.md` (copied to `.sdlc/templates/features/domain-model.md` by `/initialize-sdlc-directory`; use the project's customized copy if present). Write the result to the artifact path named in the steps above.

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | Domain model drafted (artifact written with `status: draft`, ready for `/review-domain-model`) |
| `needs-info` | The domain is too unclear to model; state what is needed |

## Example Usage

**Scenario 1: Unfamiliar regulatory domain**
The feature concerns a new tax-reporting requirement. The model captures the entities (transactions, jurisdictions, tax codes), their relationships, the invariants (a transaction maps to exactly one jurisdiction at report time), and the key quantity (reportable volume per period), giving the team a shared vocabulary before any code is written.

**Scenario 2: Overloaded term disambiguated**
"Account" is used to mean both a customer account and a billing account. The glossary disambiguates them as distinct entities and notes the relationship between them.

**Scenario 3: Reusing project vocabulary**
The project's `.sdlc/context/vocabulary.md` already defines "tenant". The model reuses that term verbatim and only adds the domain-specific entity "tenant quota".

**Scenario 4: Too early to model**
The available context is still too vague to identify entities reliably. Verdict: `needs-info`, recommending more requirements detail first.

## Completion Checklist

Before handing off to review, confirm:

- [ ] Entities cover the nouns that matter in the domain
- [ ] Glossary reuses `.sdlc/context/vocabulary.md` terms rather than redefining them
- [ ] Invariants are domain truths, not implementation choices
- [ ] Entity model rendered as a Mermaid `classDiagram` with cardinalities on edges and invariants as notes

Self-check the draft against the [`review-domain-model` checklist](../review-domain-model/SKILL.md) and fix what you can, so review finds less to flag.

## Next Step

Run `/review-domain-model` to audit entity coverage, relationship correctness, vocabulary consistency, invariant validity, boundary clarity, and framing alignment.
When a domain model is confirmed, promote its terms into `.sdlc/context/vocabulary.md` so future work reuses them.

## Useful Commands Reference

| Command | Description |
|---|---|
| `mmdc -i <diagram.mmd>` or `npx -y @mermaid-js/mermaid-cli` | Best-effort Mermaid render check for the class diagram |
