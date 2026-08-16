---
title: "<Feature Name>"
status: draft
---

# Implementation Plan: <Feature Name>

## Goal

<One paragraph describing what this plan achieves.>

## Phases

### Phase 1: <Name>

**Goal:** <What is complete at the end of this phase.>
**Effort:** <Estimate>
**Depends on:** None

**Deliverables:**
- [ ] <Deliverable>

## Phase Dependencies

```mermaid
flowchart TD
    P1["Phase 1: <name>"]
    P2["Phase 2: <name>"]
    P3["Phase 3: <name>"]
    P1 --> P2
    P2 --> P3
    P1 --> P3
```

Parallel phases (no edge between them) and unintended serialization (an edge that should not exist) are visible at a glance.

## Milestones

| Milestone | Phase | Success Criteria |
|---|---|---|
| M1: <name> | Phase 1 | <Measurable condition> |

## Dependencies

| Dependency | Type | Owner | Risk if Delayed |
|---|---|---|---|
| <name> | Internal / External | <team or person> | <impact> |

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| <description> | High / Med / Low | High / Med / Low | <action> |

## Assumptions

- <Belief the plan depends on but has not verified. Promote risky ones via /create-assumption.>

## Timeline

Render the timeline as a Mermaid `gantt` when calendar dates are estimable, so sequencing and parallel tracks are inspectable at a glance.
When no calendar can be committed yet, keep a duration-only table instead.

```mermaid
gantt
    title <Feature Name>
    dateFormat YYYY-MM-DD
    section Phase 1
    <phase or deliverable> :p1, 2026-01-01, 5d
    section Phase 2
    <phase or deliverable> :p2, after p1, 8d
    section Phase 3
    <phase or deliverable> :p3, after p2, 3d
```
