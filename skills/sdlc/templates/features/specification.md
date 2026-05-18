---
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
Actor → Service → DB
```

## Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|

## Risks and Unknowns

1. <Risk or open question>

## Out of Scope

- <What is explicitly not covered by this specification>
