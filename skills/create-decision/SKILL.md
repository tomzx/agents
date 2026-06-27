---
name: create-decision
description: Record an architectural or implementation decision with context, alternatives considered, trade-offs, and consequences.
argument-hint: "[decision topic or question]"
---

# Create Decision

Records a decision made during implementation as a lightweight Architecture Decision Record (ADR).
Captures the context, the decision, alternatives considered, trade-offs, and expected consequences so future contributors understand why the code is the way it is.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- A concrete decision that was made (or needs to be made) during implementation
- Enough context to explain the forces that shaped the decision

## Steps

1. Identify the decision: what question was answered or choice was made.
2. Describe the context: what problem exists, what constraints apply, what prompted the decision.
3. List the options that were considered (at least two, including the chosen one).
4. State the decision clearly.
5. Explain the trade-offs: what is gained and what is sacrificed.
6. Describe the consequences: what changes as a result, what follow-up is expected.
7. Save the document to `.sdlc/knowledge/decisions/` (or the project's existing ADR directory if one exists) using the filename pattern `NNNN-<slug>.md` where `NNNN` is the next available number (counting existing files in that directory).

## Output Format

```markdown
---
issue: "#<N>"
status: Proposed
---

# Decision: <Short title — the decision as a noun phrase>

**Date:** <YYYY-MM-DD>
**Status:** <Proposed | Accepted | Deprecated | Superseded by [NNNN]>
**Deciders:** <Names or roles>

---

## Context

<Describe the situation and forces at play. What problem does this decision address?
Include relevant constraints: performance, security, team capability, deadlines, existing architecture.>

## Options Considered

### Option A: <Name> *(chosen)*

<Description of the approach.>

**Pros:**
- <Benefit>

**Cons:**
- <Drawback>

### Option B: <Name>

<Description of the approach.>

**Pros:**
- <Benefit>

**Cons:**
- <Drawback>

## Decision

<State the decision in one or two sentences. Be specific — name the library, pattern, or approach chosen.>

## Trade-offs

- **Gained:** <What improves or is enabled by this decision>
- **Sacrificed:** <What is given up or made harder>

## Consequences

- <What changes in the codebase or process as a result>
- <Any follow-up tasks or future decisions this decision defers>
- <Any risks introduced that need monitoring>
```

## Example Usage

**Scenario 1: Library choice**
Deciding between two HTTP client libraries during implementation.
Decision title: "Use httpx instead of requests for async support."
Context: the service needs to make concurrent outbound calls; `requests` blocks.
Option A (httpx): supports async/await natively, actively maintained. Con: adds a new dependency.
Option B (requests + threads): familiar but increases thread overhead.
Decision: use httpx. Consequence: all HTTP calls must use async context.

**Scenario 2: Data modeling trade-off**
Deciding whether to store computed values or recalculate on read.
Decision title: "Persist derived totals in the orders table."
Context: query load is high, recalculation is expensive.
Trade-off: gained query speed, sacrificed single source of truth (must keep totals in sync on write).

**Scenario 3: Deferring complexity**
Choosing a simple approach now and noting what was deferred.
Decision title: "Use a flat file for config instead of a database."
Consequence: revisit if config grows beyond 50 keys or requires per-user values.

## Useful Commands Reference

No CLI commands required. This skill operates on information provided in context and writes a Markdown file.
