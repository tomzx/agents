---
name: architect
description: Produce a high-level technical design document from an approved specification.
---

# Architect

Reads an approved specification and the existing codebase to produce a design document covering system boundaries, component interactions, data models, API contracts, and key architectural decisions.

## Prerequisites

- Approved specification available in context or as a file path
- Access to the existing codebase (if applicable)

## Steps

1. Read the approved specification thoroughly.
2. Survey the existing codebase for relevant patterns, conventions, and integration points.
3. Define system boundaries: what is in scope vs. external.
4. Design component interactions and data flow.
5. Specify data models and API contracts where applicable.
6. Record each significant decision as an ADR (Architecture Decision Record).
7. Flag any reversibility concerns (one-way doors vs. two-way doors).

## Output Format

```markdown
## Overview

One paragraph describing the approach and how it satisfies the specification.

## System Boundaries

What this design owns vs. what it delegates to external systems.

## Components

### <Component Name>
**Responsibility:** One sentence.
**Interfaces:** How other components interact with it.

## Data Models

Key entities and their relationships (schema sketch or ER description).

## API Contracts

Endpoints or function signatures with request/response shapes.

## Architecture Decision Records

### ADR-1: <Decision Title>
**Context:** Why a decision was needed.
**Decision:** What was chosen.
**Consequences:** Trade-offs accepted.

## Risks and Reversibility

One-way-door decisions and mitigation strategies.
```

## Example Usage

**Scenario 1: New API feature**
Spec: add user data export. Design: new `/export` endpoint on existing API service, async job queue for large exports, S3 for artifact storage. ADR: chose async over sync because exports can exceed 30-second gateway timeout.

**Scenario 2: Greenfield service**
Spec: real-time sales dashboard. Design: WebSocket server, Redis pub/sub for event fan-out, read replica for queries. Flags cache invalidation as a one-way-door risk.
