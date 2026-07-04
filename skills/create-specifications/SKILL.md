---
name: create-specifications
description: Create a technical specification from a requirements document, covering architecture, data models, API contracts, and sequences.
argument-hint: "[requirements-doc]"
---

# Create Specifications

Produces a detailed technical specification from a requirements document, covering architecture, data models, API contracts, component design, and key sequences.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, locate the feature directory under `.sdlc/features/` whose frontmatter `issue` field references `$ISSUE_NUMBER`.
- `.sdlc/features/N-<slug>/requirements.md` (must have `status: approved`), or a requirements document provided in context or as a file path (`$1`)
- `.sdlc/features/N-<slug>/existing-solutions.md` (optional, if a prior-art survey was produced): adopt its recommendation and reuse the patterns it captured
- `.sdlc/features/N-<slug>/codebase-analysis.md` (optional, if existing code was analyzed): honor each component's change disposition and its "must not change" constraints, and follow the migration path for any refactor or replace

## Steps

1. Read and understand the requirements document, the existing solutions survey if present, and the codebase analysis if present.
2. Identify the major components and their responsibilities.
3. Define data models: entities, attributes, and relationships.
4. Specify API contracts: endpoints, request/response schemas, and error codes.
5. Describe key sequences: user flows, system interactions, and async processes.
6. Document technical decisions and their rationale.
7. Identify risks, unknowns, and deferred decisions.
8. Design data models, API contracts, and persisted state for evolution so future versions stay forward compatible (see Forward Compatibility below).
9. Write the output to `.sdlc/features/N-<slug>/specification.md`.

## Forward Compatibility

A forward-compatible design keeps working as the system evolves without forcing coordinated upgrades on every consumer. When specifying data models and API contracts, ensure they can grow additively:

- Tolerate unknown fields: consumers must ignore (or preserve) fields they do not recognize rather than rejecting the payload. Specify this explicitly for every schema.
- Handle unknown enum values gracefully: closed enums that throw on unseen values lock out future additions. Prefer open enums, or require consumers to fail soft on unknown values.
- Prefer additive changes: new optional fields, new endpoints, and new values are safe; removing, renaming, or repurposing existing ones is not. Call out which elements are part of the stable surface versus open to change.
- Version the contract: include a schema/API version field where practical, and state the compatibility policy (e.g., additive-only within a major version).
- Reserve extension points for known likely future change (reserved field numbers, extension columns, feature flags) rather than baking in assumptions that the current shape is final.
- Avoid positional coupling and fixed-set assumptions that would make a future addition a breaking change.

## Output Format

```markdown
---
issue: "#<N>"
title: "<Feature Name>"
status: draft
---

# Specification: <Feature Name>

## Overview

<One paragraph describing the technical approach.>

## Architecture

<ASCII diagram or description showing components and their relationships.>

## Data Models

### <Entity Name>

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | uuid | PK, not null | ... |

## API Contracts

### <METHOD /path>

**Request**

| Field | Type | Required | Description |
|---|---|---|---|

**Response (200 OK)**

| Field | Type | Description |
|---|---|---|

**Error Responses**

| Status | Code | Description |
|---|---|---|
| 400 | INVALID_INPUT | ... |

## Sequences

### <Flow Name>

```
Client → Service → DB
   |                 |
   |   POST /thing   |
   |---------------->|
   |                 |--- INSERT ---
   |    201 Created  |
   |<----------------|
```

## Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|

## Risks and Unknowns

1. <Risk or open question>

## Out of Scope

- <What is explicitly not covered by this specification>
```

## Outcome

If `$OUTCOME_YAML` is set, emit `verdict: approved` there per `skills/sdlc/references/shared.md`, mirroring the `status: approved` written to the artifact. If the artifact could not be produced, omit the file.

## Example Usage

**Scenario 1: Feature with an API and database**
Requirements describe a password reset flow.
Spec defines the `password_reset_tokens` table, `POST /auth/reset-password` endpoint, token expiry sequence, and email dispatch contract.

**Scenario 2: Background job**
Requirements ask for async processing.
Spec defines the job queue schema, worker interface, retry policy, and failure alerting sequence.

## Next Step

Run `/review-specifications` to audit for ambiguities, inconsistencies, and gaps before moving on.
Once approved, continue with `/create-plan`.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
