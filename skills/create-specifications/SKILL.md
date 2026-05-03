---
name: create-specifications
description: Create a technical specification from a requirements document, covering architecture, data models, API contracts, and sequences.
argument-hint: "[requirements-doc]"
---

# Create Specifications

Produces a detailed technical specification from a requirements document, covering architecture, data models, API contracts, component design, and key sequences.

## Prerequisites

- A requirements document provided in context or as a file path (`$1`)
- Existing architecture context (if applicable) provided in context

## Steps

1. Read and understand the requirements document.
2. Identify the major components and their responsibilities.
3. Define data models: entities, attributes, and relationships.
4. Specify API contracts: endpoints, request/response schemas, and error codes.
5. Describe key sequences: user flows, system interactions, and async processes.
6. Document technical decisions and their rationale.
7. Identify risks, unknowns, and deferred decisions.

## Output Format

```markdown
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

## Example Usage

**Scenario 1: Feature with an API and database**
Requirements describe a password reset flow.
Spec defines the `password_reset_tokens` table, `POST /auth/reset-password` endpoint, token expiry sequence, and email dispatch contract.

**Scenario 2: Background job**
Requirements ask for async processing.
Spec defines the job queue schema, worker interface, retry policy, and failure alerting sequence.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
